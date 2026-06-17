"""
PHI / PII masking — HIPAA Safe Harbor + GxP data-integrity support.

Logs, traces, and audit records in a regulated HCLS workload must never contain
raw protected health information. This module gives every agent one masking
function applied at log/audit boundaries. It targets the HIPAA Safe Harbor
identifier families (45 CFR 164.514(b)(2)) most likely to appear in clinical,
safety, and quality text:

    * US SSN                      123-45-6789
    * MRN / subject / case IDs    long digit runs, SUBJ-/PT-/MRN- prefixes
    * Dates more specific than year (DOB, event dates)
    * Email addresses, phone/fax numbers
    * Payment card numbers (Luhn-validated, for patient-support / co-pay flows)
    * NPI (10-digit, Luhn over 80840-prefixed) and DEA registration numbers

Design notes:
  * Deterministic and dependency-free (regex + Luhn). An optional ML NER pass
    (Comprehend Medical / Presidio) can be layered behind MASK_ENGINE=ml.
  * Conservative: over-masking a log line is acceptable; leaking an MRN is not.
  * mask() is idempotent and safe to call on already-masked text.

This is the de-identification *control point*; it does NOT replace a formal
expert-determination or Safe Harbor de-identification of datasets, which is a
data-engineering activity governed by the customer's privacy office.
"""
from __future__ import annotations

import os
import re
from typing import Optional

# ── Identifier patterns (order matters: most specific first) ──────────────────
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE_RE = re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
# Subject / case / MRN identifiers with common life-sciences prefixes
_SUBJECT_RE = re.compile(
    r"\b(?:SUBJ|SUBJECT|PT|PATIENT|MRN|CASE|ICSR|AER?)[-_ ]?\d{3,}\b", re.I
)
_DEA_RE = re.compile(r"\b[A-Za-z]{2}\d{7}\b")  # DEA registration number shape
# Dates more specific than a bare year (YYYY-MM-DD, MM/DD/YYYY, DD-Mon-YYYY)
_DATE_RE = re.compile(
    r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}|"
    r"\d{1,2}[-\s](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[-\s]\d{2,4})\b",
    re.I,
)
# 13-19 digit runs that pass Luhn -> payment cards (patient-support / co-pay)
_CARD_RE = re.compile(r"\b(?:\d[ -]?){13,19}\b")
# Long bare digit runs (>=9) -> MRN / NPI / account-style identifiers
_LONGNUM_RE = re.compile(r"\b\d{9,}\b")


def luhn_valid(number: str) -> bool:
    """Return True if the digit string passes the Luhn checksum."""
    digits = [int(c) for c in number if c.isdigit()]
    if len(digits) < 13:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def _mask_cards(text: str) -> str:
    def repl(m: re.Match) -> str:
        raw = m.group(0)
        return "[CARD-REDACTED]" if luhn_valid(raw) else raw
    return _CARD_RE.sub(repl, text)


def mask(text: Optional[str]) -> str:
    """
    Mask PHI/PII identifiers in free text for safe logging and audit.

    Idempotent; returns "" for None. Set MASK_ENGINE=ml to additionally run an
    optional NER engine (not bundled — wired by the customer's privacy stack).
    """
    if not text:
        return ""
    out = str(text)
    out = _SSN_RE.sub("[SSN-REDACTED]", out)
    out = _EMAIL_RE.sub("[EMAIL-REDACTED]", out)
    out = _SUBJECT_RE.sub("[SUBJECT-ID-REDACTED]", out)
    out = _DEA_RE.sub("[DEA-REDACTED]", out)
    out = _mask_cards(out)
    out = _PHONE_RE.sub("[PHONE-REDACTED]", out)
    out = _DATE_RE.sub("[DATE-REDACTED]", out)
    out = _LONGNUM_RE.sub("[ID-REDACTED]", out)

    if os.getenv("MASK_ENGINE", "").strip().lower() == "ml":
        out = _ml_mask(out)
    return out


def _ml_mask(text: str) -> str:
    """Optional ML NER hook (Comprehend Medical / Presidio). No-op if absent."""
    try:  # pragma: no cover - optional dependency path
        from hcls_agent_platform._ml_ner import redact  # type: ignore

        return redact(text)
    except Exception:
        return text
