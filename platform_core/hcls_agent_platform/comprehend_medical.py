"""
Amazon Comprehend Medical — OPT-IN REFERENCE STUB (not live-validated here).

STATUS: This module is a documented, opt-in *reference* of the AWS-native PHI /
adverse-event entity-extraction path for this life-sciences suite. It mirrors the
LIVE implementation shipped in the sibling healthcare payer/provider suite
(``healthcare_ai_agents``: ``platform_core/hpp_agent_platform/comprehend_medical.py``,
selected by ``PHI_ENGINE=comprehend_medical``, fail-closed, belt-and-suspenders
with the deterministic Safe-Harbor masker). In THIS suite it is provided so the
AWS HCLS-native fit for Agent 02 (Pharmacovigilance / ICSR) is concrete and
callable — but it is **not** wired into the live masking path by default and is
**not** live-validated against AWS here. Treat it as architectural fit / roadmap.

Where it fits (Agent 02): adverse-event narrative understanding. Comprehend
Medical ``DetectPHI`` extracts PHI spans for masking; ``DetectEntitiesV2``
extracts medication / dosage / medical-condition entities that can enrich AE
intake upstream of MedDRA/WHO Drug coding. Only ``DetectPHI`` is used by the
masking contract below.

Contract (mirrors the healthcare implementation):
  * **Opt-in.** Selected by ``PHI_ENGINE=comprehend_medical``. Otherwise unused.
  * **Optional dependency.** ``boto3`` is imported lazily; not required by default.
  * **Fail closed.** ANY error (boto3 missing, client build failure, throttling,
    ClientError, malformed response, bad offsets) is RAISED to the caller, which
    must fall back to the deterministic Safe-Harbor masker. This module NEVER
    returns the unmasked input on an error path.

HIPAA / residency: Amazon Comprehend Medical is a HIPAA-eligible service, usable
for PHI under an executed AWS BAA, reached over the regional Comprehend Medical
API — in a native deployment via an interface VPC endpoint (AWS PrivateLink), so
traffic to the regional service stays on AWS private networking. PHI is processed
by the AWS managed service, not sent to any non-AWS third-party AI API.
"""
from __future__ import annotations

import os
from typing import List, Optional, Tuple

# Environment flag value that selects this engine.
PHI_ENGINE_COMPREHEND_MEDICAL = "comprehend_medical"

# Default minimum confidence for a detected entity to be redacted (0..1).
DEFAULT_CONFIDENCE_THRESHOLD = 0.5


def _confidence_threshold() -> float:
    """Resolve the confidence threshold from env, falling back to the default."""
    raw = os.getenv("PHI_COMPREHEND_MIN_CONFIDENCE", "").strip()
    if not raw:
        return DEFAULT_CONFIDENCE_THRESHOLD
    try:
        val = float(raw)
    except ValueError:
        return DEFAULT_CONFIDENCE_THRESHOLD
    if val < 0.0 or val > 1.0:
        return DEFAULT_CONFIDENCE_THRESHOLD
    return val


def _client(region: Optional[str] = None):
    """
    Construct a boto3 ``comprehendmedical`` client. boto3 is imported lazily so
    the dependency is optional. Any failure here propagates (fail closed).
    """
    import boto3  # lazy import — optional dependency

    region = region or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
    if region:
        return boto3.client("comprehendmedical", region_name=region)
    return boto3.client("comprehendmedical")


def detect_phi_spans(
    text: str,
    *,
    confidence_threshold: Optional[float] = None,
    client=None,
) -> List[Tuple[int, int, str, float]]:
    """
    Call Comprehend Medical ``DetectPHI`` and return PHI spans that meet the
    confidence threshold, as ``(begin_offset, end_offset, type, score)`` tuples.
    Raises on any boto3/client/response error (caller fails closed).
    """
    if confidence_threshold is None:
        confidence_threshold = _confidence_threshold()

    cm = client if client is not None else _client()
    resp = cm.detect_phi(Text=text)
    entities = resp["Entities"]  # KeyError here also fails closed (malformed resp)

    spans: List[Tuple[int, int, str, float]] = []
    for ent in entities:
        score = float(ent.get("Score", 0.0))
        if score < confidence_threshold:
            continue
        begin = int(ent["BeginOffset"])
        end = int(ent["EndOffset"])
        etype = str(ent.get("Type", "PHI"))
        if begin < 0 or end > len(text) or begin >= end:
            raise ValueError(
                f"Comprehend Medical returned out-of-range offsets: {begin}-{end} "
                f"for text length {len(text)}"
            )
        spans.append((begin, end, etype, score))
    return spans


def redact(
    text: str,
    *,
    confidence_threshold: Optional[float] = None,
    client=None,
) -> str:
    """
    Redact PHI spans detected by Comprehend Medical ``DetectPHI`` in ``text``,
    replacing each span with ``[<TYPE>-REDACTED]``.

    FAIL CLOSED: any boto3/client/response error propagates to the caller, which
    must apply the deterministic Safe-Harbor fallback. Never returns unmasked
    input on an error path. (Opt-in / reference — not live-validated in this suite.)
    """
    if not text:
        return ""

    spans = detect_phi_spans(
        text, confidence_threshold=confidence_threshold, client=client
    )
    if not spans:
        return text

    spans.sort(key=lambda s: s[0], reverse=True)
    out = text
    for begin, end, etype, _score in spans:
        out = out[:begin] + f"[{etype.upper()}-REDACTED]" + out[end:]
    return out


def enabled() -> bool:
    """True when PHI_ENGINE selects Comprehend Medical (opt-in)."""
    return (
        os.getenv("PHI_ENGINE", "").strip().lower()
        == PHI_ENGINE_COMPREHEND_MEDICAL
    )
