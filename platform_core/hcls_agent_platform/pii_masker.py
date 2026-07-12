"""
Fail-closed PII/PHI masker for the HCLS agent suite — masks sensitive fields
BEFORE they enter a model prompt (or an audit record).

Two layers, belt-and-suspenders:

  1. Regex Safe-Harbor pass (ALWAYS on, offline, deterministic) — catches the
     structured HIPAA identifiers a free-text NER model is unreliable on:
     SSN, email, phone/fax, MRN/account (label-anchored), and DOB-style dates.

  2. NER pass (Amazon Comprehend Medical DetectPHI + Amazon Comprehend
     DetectPiiEntities) — catches the free-text identifiers regex cannot:
     names, addresses, ages. Runs when real-data mode is on (ALLOW_REAL_DATA=1)
     or MASK_NER=1. In real-data mode it is MANDATORY and FAIL-CLOSED: if the
     NER call errors, mask() raises rather than letting under-masked PHI reach
     the model. This is the same control proven live in
     infra/golden-path-masking-verification/ (see its EVIDENCE.md).

Neither layer alone is complete — a site tunes the regex ID patterns to its own
MRN/account formats during a pilot, and NER covers the free text. Offline/demo
(no AWS) runs the regex pass only; that keeps the unit suite dependency-free
while the deployed hero gets both.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

# --- regex Safe-Harbor patterns for structured identifiers (label -> compiled) ---
_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "SSN"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "EMAIL"),
    (re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"), "PHONE"),
    # label-anchored MRN / medical-record / account / member / patient IDs (site-tunable).
    # Broadened to the common real-world label variants: MR / MR# / MRN, "medical record no|number|#",
    # acct|account, "patient id|no|number", "member id|number", "record no|number". The label may be
    # followed by an optional separator (:, #, -, space) and then a 4+ char alphanumeric id (with
    # optional internal hyphens), so "MR# 12-345678", "Patient ID: A0093281", "Member No 55521234" all mask.
    (re.compile(
        r"\b(?:MRN|MR|medical[-\s]?record|acct|account|patient|member|record)"
        r"(?:\s*(?:id|no\.?|number|#))?\s*[:#-]?\s*[A-Za-z0-9][A-Za-z0-9-]{3,}",
        re.I), "MRN"),
    # DOB-style dates: YYYY-MM-DD and M/D/YYYY
    (re.compile(r"\b\d{4}-\d{2}-\d{2}\b"), "DATE"),
    (re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b"), "DATE"),
]


def _site_patterns() -> list[tuple[re.Pattern, str]]:
    """Site-specific *bare* MRN/account formats, injected at deploy time without a code change.

    Real sites often write MRNs with no label (e.g. an 8-digit Epic MRN, or a "AB-0001234"
    accession). Those are too false-positive-prone to hard-code globally (a bare 8-digit run could
    be a quantity), so a pilot supplies its exact format(s) via the HCLS_MRN_PATTERNS env var — one
    regex per line (newline-separated). Each is applied in the always-on Safe-Harbor pass. An
    un-compilable entry is skipped (it must never crash the masker), but is surfaced on stderr so a
    misconfigured pattern is visible rather than silently dropping coverage.

    Example (Epic 8-digit MRN + a hyphenated accession):
        HCLS_MRN_PATTERNS="\\b\\d{8}\\b\n\\b[A-Z]{2}-\\d{7}\\b"
    """
    raw = os.getenv("HCLS_MRN_PATTERNS", "")
    out: list[tuple[re.Pattern, str]] = []
    for line in raw.splitlines():
        pat = line.strip()
        if not pat:
            continue
        try:
            out.append((re.compile(pat), "MRN"))
        except re.error as exc:  # never crash the masker on a bad site pattern; make it visible
            import sys
            print(f"[pii_masker] ignoring invalid HCLS_MRN_PATTERNS entry {pat!r}: {exc}", file=sys.stderr)
    return out


class RealDataMaskingError(RuntimeError):
    """Raised in real-data mode when the mandatory NER pass is unavailable — fail-closed."""


@dataclass
class MaskResult:
    text: str
    changed: bool
    entity_types: list[str] = field(default_factory=list)
    engine: str = "regex"


def _real_data_mode() -> bool:
    return os.getenv("ALLOW_REAL_DATA", "").strip().lower() in ("1", "true", "yes")


def _ner_requested() -> bool:
    return _real_data_mode() or os.getenv("MASK_NER", "").strip().lower() in ("1", "true", "yes")


def _regex_spans(text: str) -> list[tuple[int, int, str]]:
    spans: list[tuple[int, int, str]] = []
    for pat, label in (*_PATTERNS, *_site_patterns()):
        for m in pat.finditer(text):
            spans.append((m.start(), m.end(), "PII:" + label))
    return spans


def _ner_spans(text: str) -> list[tuple[int, int, str]]:
    """Comprehend Medical DetectPHI + Comprehend DetectPiiEntities. Lazy-imports boto3."""
    import boto3  # lazy — only needed in real-data / NER mode

    region = os.getenv("BEDROCK_REGION", os.getenv("AWS_REGION", "us-east-1"))
    cm = boto3.client("comprehendmedical", region_name=region)
    cp = boto3.client("comprehend", region_name=region)
    spans: list[tuple[int, int, str]] = []
    for e in cm.detect_phi(Text=text)["Entities"]:
        spans.append((e["BeginOffset"], e["EndOffset"], "PHI:" + e["Type"]))
    for e in cp.detect_pii_entities(Text=text, LanguageCode="en")["Entities"]:
        spans.append((e["BeginOffset"], e["EndOffset"], "PII:" + e["Type"]))
    return spans


def _merge(spans: list[tuple[int, int, str]]) -> list[tuple[int, int, str]]:
    spans = sorted(spans, key=lambda s: (s[0], -s[1]))
    out: list[tuple[int, int, str]] = []
    for b, e, lab in spans:
        if out and b <= out[-1][1]:
            pb, pe, plab = out[-1]
            out[-1] = (pb, max(pe, e), plab)
        else:
            out.append((b, e, lab))
    return out


def mask(text: str) -> MaskResult:
    """
    Mask PII/PHI in `text`. Regex Safe-Harbor is always applied. When real-data mode
    (ALLOW_REAL_DATA=1) or MASK_NER=1 is set, the Comprehend Medical + Comprehend NER
    pass is added — and in real-data mode it is mandatory and fail-closed.
    """
    if not text:
        return MaskResult(text=text, changed=False)
    spans = _regex_spans(text)
    engine = "regex"
    if _ner_requested():
        try:
            spans += _ner_spans(text)
            engine = "regex+comprehend-medical+comprehend"
        except Exception as ex:  # noqa: BLE001 — fail closed on ANY NER error
            if _real_data_mode():
                raise RealDataMaskingError(
                    f"mandatory NER masking unavailable in real-data mode — refusing to build a "
                    f"prompt with unmasked free-text PHI: {ex}"
                ) from ex
            # non-real-data (dev/demo) with MASK_NER but no AWS: degrade to regex only.
    merged = _merge(spans)
    out = text
    for b, e, lab in sorted(merged, key=lambda s: s[0], reverse=True):
        out = out[:b] + "[" + lab + "]" + out[e:]
    types = sorted({lab for _, _, lab in merged})
    return MaskResult(text=out, changed=out != text, entity_types=types, engine=engine)
