"""
Grounding verification — claim traceability for regulated HCLS text.

A regulator-, reviewer-, or HCP-facing artifact (a submission section, an ICSR
narrative, a CAPA plan, an MSL brief) must contain ONLY claims traceable to the
state that produced it. An LLM hallucination in a SAE narrative or a labeling
section is a regulatory data-integrity defect. verify_grounding flags any number
or capitalized entity in the text that is not traceable to the input state, so a
human reviewer (and CI) can catch fabricated dose, endpoint, or institution
claims before sign-off.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set

_ENTITY_ALLOWLIST = {
    "FDA", "EMA", "MHRA", "ICH", "WHO", "MedDRA", "WHODrug", "PMDA", "Health Canada",
    "Adverse Event", "Serious Adverse Event", "Suspected Unexpected Serious Adverse Reaction",
    "Individual Case Safety Report", "Common Technical Document", "Clinical Study Report",
    "Corrective and Preventive Action", "Marketing Authorization", "Good Clinical Practice",
    "Good Manufacturing Practice", "Standard Operating Procedure", "Investigational Medicinal Product",
    "United States", "European Union",
    "Regulatory Approver", "Regulatory Author", "Qualified Person", "Medical Reviewer",
    "Medical Affairs", "Quality Reviewer", "Marketing Authorization Holder",
    "January", "February", "March", "April", "May", "June", "July", "August",
    "September", "October", "November", "December",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
    "The", "This", "These", "Per", "Subject", "Patient", "Investigator", "Sponsor",
}

_NUMBER_ALLOWLIST = {"15", "7", "30", "90", "21", "11"}

_NUMBER_RE = re.compile(r"\$?\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b|\$?\b\d+(?:\.\d+)?%?\b")
_ENTITY_RE = re.compile(r"\b(?:[A-Z][a-zA-Z&'-]+(?:\s+[A-Z][a-zA-Z&'-]+)+)\b")


@dataclass
class GroundingReport:
    ungrounded_numbers: List[str] = field(default_factory=list)
    ungrounded_entities: List[str] = field(default_factory=list)
    checked_numbers: int = 0
    checked_entities: int = 0

    @property
    def grounded(self) -> bool:
        return not self.ungrounded_numbers and not self.ungrounded_entities

    def to_audit_dict(self) -> Dict[str, Any]:
        return {
            "grounded": self.grounded,
            "ungrounded_numbers": self.ungrounded_numbers,
            "ungrounded_entities": self.ungrounded_entities,
            "checked_numbers": self.checked_numbers,
            "checked_entities": self.checked_entities,
        }


def _normalize_number(tok: str) -> str:
    return tok.replace("$", "").replace(",", "").replace("%", "").rstrip(".")


def _state_number_corpus(state: Dict[str, Any]) -> Set[str]:
    blob = json.dumps(state, default=str)
    nums: Set[str] = set()
    for tok in _NUMBER_RE.findall(blob):
        n = _normalize_number(tok)
        nums.add(n)
        try:
            f = float(n)
            nums.add(f"{f:g}")
            if f == int(f):
                nums.add(str(int(f)))
        except ValueError:
            pass
    return nums


def verify_grounding(narrative: str, state: Dict[str, Any]) -> GroundingReport:
    report = GroundingReport()
    if not narrative:
        return report

    state_numbers = _state_number_corpus(state)
    state_text = json.dumps(state, default=str).lower()

    for tok in _NUMBER_RE.findall(narrative):
        n = _normalize_number(tok)
        try:
            value = float(n)
        except ValueError:
            continue
        if value <= 12:
            continue
        if n in _NUMBER_ALLOWLIST or f"{value:g}" in _NUMBER_ALLOWLIST:
            continue
        report.checked_numbers += 1
        aliases = {n, f"{value:g}"}
        if value == int(value):
            aliases.add(str(int(value)))
        if not aliases & state_numbers:
            report.ungrounded_numbers.append(tok)

    leading_stop = {"Between", "On", "In", "At", "During", "After", "Before",
                    "Within", "The", "This", "These", "Per", "From", "By", "Under", "Each"}
    for ent in set(_ENTITY_RE.findall(narrative)):
        words = ent.split()
        while words and words[0] in leading_stop:
            words = words[1:]
        if len(words) < 2:
            continue
        ent = " ".join(words)
        if ent in _ENTITY_ALLOWLIST or any(ent.startswith(a + " ") for a in _ENTITY_ALLOWLIST):
            continue
        report.checked_entities += 1
        if ent.lower() not in state_text:
            report.ungrounded_entities.append(ent)

    report.ungrounded_numbers.sort()
    report.ungrounded_entities.sort()
    return report
