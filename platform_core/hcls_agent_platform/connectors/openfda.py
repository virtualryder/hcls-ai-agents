"""
openFDA drug-event connector — a REAL external safety data source (read-only).

This is Build A of the "one real connector per vertical" work: it replaces the
fixture safety source with the **openFDA drug-event API** (FAERS adverse-event
reports) — a genuine, public, **de-identified** system of record. It proves the
governed pattern (deny-by-default gateway → scoped token → masking → human gate →
append-only audit) against a real API instead of a fixture, and needs **no BAA**
because the data is already de-identified.

  Endpoint : https://api.fda.gov/drug/event.json   (public; optional API key)
  Docs     : https://open.fda.gov/apis/drug/event/

Design contract (matches connectors/base.py SafetyConnector so it is drop-in
interchangeable with FixtureSafety / LiveSafetyConnector):

  * get_case / search_duplicates      -> READ real FAERS data (implemented here)
  * write_case_draft / submit_report  -> NOT SUPPORTED. openFDA is a read-only
    public source; drafting and submission target the customer's own **validated**
    safety system (Argus/ArisGlobal) and stay **human-gated**. Calling them raises,
    which is the correct, fail-closed behavior and reinforces the governance story:
    the agent can read the real world but cannot write to it.

  * stdlib-only HTTP (urllib), timeouts, fail-closed (any error raises).
  * PHI masking still runs downstream on the returned text even though FAERS is
    de-identified — the control is exercised, not assumed.

The regulated/PHI variant (AWS HealthLake FHIR `AdverseEvent` under a BAA) is a
documented follow-on with the same interface; swap the adapter, keep the agent.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional
from urllib import request as _urllib_request
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

from .base import SafetyConnector

_DEFAULT_BASE = "https://api.fda.gov"
_TIMEOUT = 20

# openFDA / E2B coded-value maps (documented, stable) --------------------------
_SEX = {"0": "Unknown", "1": "Male", "2": "Female"}
_AGE_UNIT = {"800": "decade", "801": "year", "802": "month", "803": "week", "804": "day", "805": "hour"}
_DRUG_CHAR = {"1": "suspect", "2": "concomitant", "3": "interacting"}
_OUTCOME = {
    "1": "Recovered/resolved", "2": "Recovering/resolving", "3": "Not recovered/not resolved",
    "4": "Recovered/resolved with sequelae", "5": "Fatal", "6": "Unknown",
}
_SERIOUSNESS_FLAGS = {
    "seriousnessdeath": "Death",
    "seriousnesslifethreatening": "Life-threatening",
    "seriousnesshospitalization": "Hospitalization",
    "seriousnessdisabling": "Disability",
    "seriousnesscongenitalanomali": "Congenital anomaly",
    "seriousnessother": "Other medically important condition",
}


def _api_key() -> str:
    """Optional openFDA API key (raises the rate limit). Env or Secrets Manager."""
    key = os.getenv("OPENFDA_API_KEY", "")
    if key:
        return key
    try:
        from hcls_agent_platform.secrets import get_secret
        return get_secret("openfda_api_key", default="") or ""
    except Exception:
        return ""


class OpenFDASafetyConnector(SafetyConnector):
    """Real, read-only FAERS adverse-event connector (kind='safety')."""

    kind = "safety"
    source = "openFDA FAERS (public, de-identified)"

    def __init__(self, base_url: str = "", api_key: str = "") -> None:
        self._base_url = (base_url or os.getenv("OPENFDA_BASE_URL", _DEFAULT_BASE)).rstrip("/")
        self._api_key = api_key  # empty -> resolved lazily

    # -- HTTP -----------------------------------------------------------------
    def _get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """GET /drug/event.json with params. Fail-closed: any error raises."""
        key = self._api_key or _api_key()
        if key:
            params = {**params, "api_key": key}
        url = f"{self._base_url}/drug/event.json?{urlencode(params)}"
        req = _urllib_request.Request(url, headers={"Accept": "application/json"}, method="GET")
        try:
            with _urllib_request.urlopen(req, timeout=_TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as exc:
            # openFDA returns 404 with an error body when a query has no matches.
            if exc.code == 404:
                return {"results": []}
            raise RuntimeError(f"openFDA API error [{exc.code}] for {url}: {exc}") from exc
        except (URLError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"openFDA API call failed for {url}: {exc}") from exc

    # -- Mapping FAERS report -> ICSR record ----------------------------------
    @staticmethod
    def _map_report(r: Dict[str, Any]) -> Dict[str, Any]:
        patient = r.get("patient", {}) or {}
        drugs_raw = patient.get("drug", []) or []
        reactions_raw = patient.get("reaction", []) or []

        suspect = [d.get("medicinalproduct") for d in drugs_raw
                   if str(d.get("drugcharacterization")) == "1" and d.get("medicinalproduct")]
        all_drugs = [d.get("medicinalproduct") for d in drugs_raw if d.get("medicinalproduct")]
        reactions = [rx.get("reactionmeddrapt") for rx in reactions_raw if rx.get("reactionmeddrapt")]
        outcomes = sorted({_OUTCOME.get(str(rx.get("reactionoutcome")), "Unknown")
                           for rx in reactions_raw})
        serious = str(r.get("serious")) == "1"
        criteria = [label for flag, label in _SERIOUSNESS_FLAGS.items() if str(r.get(flag)) == "1"]

        age = patient.get("patientonsetage")
        age_unit = _AGE_UNIT.get(str(patient.get("patientonsetageunit")), "")
        sex = _SEX.get(str(patient.get("patientsex")), "Unknown")

        record = {
            "case_id": r.get("safetyreportid", ""),
            "status": "OPEN",
            "valid": True,
            "source": OpenFDASafetyConnector.source,
            "serious": serious,
            "seriousness_criteria": criteria,
            "suspect_drugs": suspect,
            "all_drugs": all_drugs,
            "reactions": reactions,
            "outcomes": outcomes,
            "demographics": {
                "age": f"{age} {age_unit}".strip() if age else "Unknown",
                "sex": sex,
                "weight_kg": patient.get("patientweight"),
            },
            "country": r.get("occurcountry") or r.get("primarysourcecountry") or "Unknown",
            "receive_date": r.get("receivedate", ""),
        }
        record["narrative_text"] = OpenFDASafetyConnector._compose_narrative(record)
        return record

    @staticmethod
    def _compose_narrative(rec: Dict[str, Any]) -> str:
        """
        FAERS/openFDA has no free-text narrative, so compose a factual one from the
        structured fields. Deliberately claims ONLY what the record contains (this
        is also what the grounding eval scores against in Build B).
        """
        demo = rec["demographics"]
        who = f"A {demo['sex'].lower()} patient" + (f", age {demo['age']}," if demo["age"] != "Unknown" else "")
        drugs = ", ".join(rec["suspect_drugs"] or rec["all_drugs"] or ["an unspecified product"])
        rxns = ", ".join(rec["reactions"] or ["an unspecified adverse event"])
        sev = ("a SERIOUS adverse event (" + "; ".join(rec["seriousness_criteria"]) + ")") if rec["serious"] \
            else "a non-serious adverse event"
        outcome = "; ".join(rec["outcomes"]) if rec["outcomes"] else "unknown outcome"
        country = rec["country"]
        return (f"{who} reported from {country} experienced {sev} following administration of "
                f"{drugs}. Reported reaction term(s): {rxns}. Outcome: {outcome}. "
                f"(Source: FAERS report {rec['case_id']}, openFDA.)")

    # -- SafetyConnector interface --------------------------------------------
    def get_case(self, case_id: Optional[str] = None, drug: Optional[str] = None,
                 serious_only: bool = True, **_: Any) -> Dict[str, Any]:
        """
        READ a real FAERS case. Priority: explicit case_id → by drug → most-recent
        serious case. Returns the ICSR record shape (superset of FixtureSafety).
        """
        if case_id:
            search = f'safetyreportid:"{case_id}"'
        elif drug:
            q = f'patient.drug.medicinalproduct:"{drug}"'
            search = f"{q}+AND+serious:1" if serious_only else q
        else:
            search = "serious:1"
        data = self._get({"search": search, "limit": 1})
        results = data.get("results", [])
        if not results:
            return {"case_id": case_id or "", "status": "NOT_FOUND", "valid": False,
                    "source": self.source, "narrative_text": ""}
        return self._map_report(results[0])

    def search_duplicates(self, drug: Optional[str] = None, reaction: Optional[str] = None,
                          exclude_case_id: Optional[str] = None, limit: int = 5,
                          **_: Any) -> List[Dict[str, Any]]:
        """
        Find candidate duplicate/related ICSRs in FAERS by shared suspect drug and
        reaction term. match_score is a transparent heuristic (drug match = 0.5,
        reaction match = 0.5) — real duplicate detection is a customer-validated
        algorithm; this demonstrates the governed read against real data.
        """
        if not drug and not reaction:
            return []
        clauses = []
        if drug:
            clauses.append(f'patient.drug.medicinalproduct:"{drug}"')
        if reaction:
            clauses.append(f'patient.reaction.reactionmeddrapt:"{reaction}"')
        data = self._get({"search": "+AND+".join(clauses), "limit": max(1, min(limit + 1, 20))})
        out: List[Dict[str, Any]] = []
        for r in data.get("results", []):
            cid = r.get("safetyreportid", "")
            if exclude_case_id and cid == exclude_case_id:
                continue
            patient = r.get("patient", {}) or {}
            drugs = {d.get("medicinalproduct") for d in patient.get("drug", []) or []}
            rxns = {rx.get("reactionmeddrapt") for rx in patient.get("reaction", []) or []}
            score = (0.5 if drug and drug in drugs else 0.0) + (0.5 if reaction and reaction in rxns else 0.0)
            fields = ([f"drug:{drug}"] if drug and drug in drugs else []) + \
                     ([f"reaction:{reaction}"] if reaction and reaction in rxns else [])
            out.append({"case_id": cid, "match_score": round(score, 2), "fields": fields})
            if len(out) >= limit:
                break
        return out

    # -- Writes are intentionally unsupported (read-only public source) -------
    def write_case_draft(self, **kwargs: Any) -> Dict[str, Any]:
        raise NotImplementedError(
            "openFDA is a READ-ONLY public data source. Case drafting writes to the "
            "customer's validated safety system (e.g., Argus) and remains human-gated. "
            "Use the LiveSafetyConnector (SAFETY_BASE_URL) or FixtureSafety for write paths."
        )

    def submit_report(self, **kwargs: Any) -> Dict[str, Any]:
        raise NotImplementedError(
            "openFDA is a READ-ONLY public data source. ICSR submission is a "
            "consequential, human-gated action performed against the customer's "
            "validated safety gateway — never by the agent, never against openFDA."
        )
