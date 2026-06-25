"""
Fixture connectors — deterministic, offline backing store for every system.

These let the entire suite run with no AWS account, no vendor credentials, and no
PHI: demos, CI, and the governance eval harness all use these. Returned shapes
mirror the real systems closely enough that agent code is identical in live mode.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .base import GenericConnector


class FixtureRIM(GenericConnector):
    def __init__(self) -> None:
        super().__init__("rim")

    def get_obligations(self, product: str = "DEMO-DRUG", **_: Any) -> List[Dict[str, Any]]:
        return [
            {"id": "OBL-001", "authority": "FDA", "type": "PADER", "product": product,
             "due": "2026-09-30", "status": "open"},
            {"id": "OBL-002", "authority": "EMA", "type": "PSUR", "product": product,
             "due": "2026-08-15", "status": "open"},
        ]

    def search_guidance(self, query: str = "", **_: Any) -> List[Dict[str, Any]]:
        return [
            {"authority": "FDA", "title": "E2B(R3) Electronic Transmission of ICSRs",
             "ref": "FDA-2013-D-XXXX", "relevance": 0.92, "query": query},
            {"authority": "ICH", "title": "M4 Common Technical Document (CTD)",
             "ref": "ICH-M4", "relevance": 0.88, "query": query},
        ]

    def create_submission_draft(self, **kwargs: Any) -> Dict[str, Any]:
        return {"draft_id": "SUBM-DRAFT-0001", "status": "DRAFT", "created": True, "echo": kwargs}


class FixtureDMS(GenericConnector):
    def __init__(self) -> None:
        super().__init__("dms")

    def get_document(self, doc_id: str = "DOC-1", **_: Any) -> Dict[str, Any]:
        return {"doc_id": doc_id, "title": "Approved Core Data Sheet", "version": "3.0",
                "status": "Effective", "text": "Indications, dosage, and approved claims (demo)."}

    def put_draft(self, **kwargs: Any) -> Dict[str, Any]:
        return {"doc_id": "DOC-DRAFT-0001", "status": "DRAFT", "version": "0.1", "echo": kwargs}


class FixtureSafety(GenericConnector):
    def __init__(self) -> None:
        super().__init__("safety")

    def get_case(self, case_id: str = "ICSR-1", **_: Any) -> Dict[str, Any]:
        return {"case_id": case_id, "status": "OPEN", "valid": True}

    def search_duplicates(self, **kwargs: Any) -> List[Dict[str, Any]]:
        return [{"case_id": "ICSR-2024-00041", "match_score": 0.34, "fields": ["product", "reporter_country"]}]

    def write_case_draft(self, **kwargs: Any) -> Dict[str, Any]:
        return {"case_id": "ICSR-DRAFT-0001", "status": "DRAFT", "written": True, "echo": kwargs}

    def submit_report(self, **kwargs: Any) -> Dict[str, Any]:
        return {"submission_id": "E2B-0001", "gateway": "FDA-FAERS", "status": "QUEUED", "echo": kwargs}


class FixtureMedDRA(GenericConnector):
    def __init__(self) -> None:
        super().__init__("meddra")

    def code_term(self, term: str = "headache", **_: Any) -> Dict[str, Any]:
        table = {
            "headache": {"pt": "Headache", "pt_code": "10019211", "soc": "Nervous system disorders"},
            "nausea": {"pt": "Nausea", "pt_code": "10028813", "soc": "Gastrointestinal disorders"},
            "rash": {"pt": "Rash", "pt_code": "10037844", "soc": "Skin and subcutaneous tissue disorders"},
        }
        hit = table.get(term.lower(), {"pt": "Product use issue", "pt_code": "10070031",
                                       "soc": "General disorders and administration site conditions"})
        return {"verbatim": term, "version": "MedDRA 27.0", **hit, "confidence": 0.91}


class FixtureWHODrug(GenericConnector):
    def __init__(self) -> None:
        super().__init__("whodrug")

    def code_drug(self, drug: str = "demo-drug", **_: Any) -> Dict[str, Any]:
        return {"verbatim": drug, "dictionary": "WHODrug Global B3", "drug_record_number": "000123456001",
                "atc": "N02BE01", "confidence": 0.88}


class FixtureMES(GenericConnector):
    """Manufacturing execution system / electronic batch records (review-by-exception)."""

    def __init__(self) -> None:
        super().__init__("mes")

    def get_batch_record(self, batch_id: str = "B-DEMO", **_: Any) -> Dict[str, Any]:
        return {
            "batch_id": batch_id, "product": "DEMO-PRODUCT",
            "required_steps": ["S1", "S2"],
            "steps": [
                {"id": "S1", "name": "Dispensing", "value": 100.0, "lo": 99.0, "hi": 101.0,
                 "unit": "%", "signed": True, "critical": True},
                {"id": "S2", "name": "Compression force", "value": 12.0, "lo": 10.0, "hi": 15.0,
                 "unit": "kN", "signed": True, "critical": False},
            ],
        }

    def write_disposition_draft(self, **kwargs: Any) -> Dict[str, Any]:
        return {"disposition_id": "DISP-DRAFT-0001", "status": "DRAFT", "created": True, "echo": kwargs}

    def record_disposition(self, **kwargs: Any) -> Dict[str, Any]:
        return {"disposition_id": "DISP-0001", "recorded": True, "echo": kwargs}


class FixtureLIMS(GenericConnector):
    """Laboratory information management system — QC test results for a batch."""

    def __init__(self) -> None:
        super().__init__("lims")

    def get_results(self, batch_id: str = "B-DEMO", **_: Any) -> List[Dict[str, Any]]:
        return [
            {"test": "Assay", "result": 99.5, "lo": 95.0, "hi": 105.0, "unit": "%", "status": "PASS"},
            {"test": "Dissolution Q30", "result": 88.0, "lo": 80.0, "hi": 100.0, "unit": "%", "status": "PASS"},
        ]


class FixtureGeneric(GenericConnector):
    """Backs EDC, CTMS, eTMF, RWD, QMS, CRM, MLR with canned, safe responses."""

    _RESPONSES: Dict[str, Dict[str, Any]] = {
        "edc.get_subject_data": {"subject": "[SUBJECT-ID-REDACTED]", "visits": 6, "open_queries": 2},
        "edc.create_query": {"query_id": "Q-0001", "status": "OPEN", "created": True},
        "ctms.get_study_status": {"study": "STUDY-001", "sites": 42, "enrolled": 318, "target": 450},
        "etmf.get_completeness": {"study": "STUDY-001", "completeness_pct": 87.4, "missing": 23},
        "rwd.run_cohort_query": {"cohort": "T2DM-adults", "eligible_estimate": 12840, "deidentified": True},
        "qms.get_complaint": {"complaint_id": "CMP-0001", "product": "DEVICE-X", "severity": "medium"},
        "qms.search_similar": {"matches": [{"id": "CMP-0044", "similarity": 0.71}]},
        "qms.create_capa_draft": {"capa_id": "CAPA-DRAFT-0001", "status": "DRAFT", "created": True},
        "qms.close_capa": {"capa_id": "CAPA-0001", "status": "CLOSED", "closed": True},
        "crm.get_hcp": {"hcp_id": "HCP-0001", "specialty": "Endocrinology", "recent_publications": 3},
        "mlr.submit_for_review": {"mlr_id": "MLR-0001", "status": "IN_REVIEW", "submitted": True},
    }

    def __getattr__(self, method: str) -> Any:  # dynamic method resolution
        def call(**kwargs: Any) -> Dict[str, Any]:
            key = f"{self.kind}.{method}"
            base = dict(self._RESPONSES.get(key, {"ok": True}))
            base["echo"] = kwargs
            return base
        return call
