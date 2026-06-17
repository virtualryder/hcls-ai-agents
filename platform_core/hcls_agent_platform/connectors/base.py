"""
Connector framework — one interface, two implementations (fixture / live).

A *connector* is the typed adapter to a system of record (RIM, DMS, Safety DB,
EDC, CTMS, eTMF, RWD platform, QMS, CRM, MedDRA/WHODrug). Agents never call a
vendor SDK directly: they call the MCP gateway, which (after authorizing) calls a
connector method. That keeps three properties true:

  * One validated integration surface per system (GxP / CSV scope is bounded).
  * Fixture mode runs the entire suite offline for demos, CI, and evals.
  * Live mode swaps in the real client behind the SAME method signatures, so no
    agent code changes between demo and production.

Add a system of record by subclassing the relevant Connector and registering it
in connectors/factory.py. Method names here must match policy.TOOL_REGISTRY.
"""
from __future__ import annotations

import abc
from typing import Any, Dict, List


class Connector(abc.ABC):
    """Base class for all system-of-record connectors."""

    kind: str = "base"


class RIMConnector(Connector):
    kind = "rim"

    @abc.abstractmethod
    def get_obligations(self, **kwargs: Any) -> List[Dict[str, Any]]: ...

    @abc.abstractmethod
    def search_guidance(self, **kwargs: Any) -> List[Dict[str, Any]]: ...

    @abc.abstractmethod
    def create_submission_draft(self, **kwargs: Any) -> Dict[str, Any]: ...


class DMSConnector(Connector):
    kind = "dms"

    @abc.abstractmethod
    def get_document(self, **kwargs: Any) -> Dict[str, Any]: ...

    @abc.abstractmethod
    def put_draft(self, **kwargs: Any) -> Dict[str, Any]: ...


class SafetyConnector(Connector):
    kind = "safety"

    @abc.abstractmethod
    def get_case(self, **kwargs: Any) -> Dict[str, Any]: ...

    @abc.abstractmethod
    def search_duplicates(self, **kwargs: Any) -> List[Dict[str, Any]]: ...

    @abc.abstractmethod
    def write_case_draft(self, **kwargs: Any) -> Dict[str, Any]: ...

    @abc.abstractmethod
    def submit_report(self, **kwargs: Any) -> Dict[str, Any]: ...


class CodingConnector(Connector):
    """MedDRA / WHODrug dictionary coding."""

    @abc.abstractmethod
    def code_term(self, **kwargs: Any) -> Dict[str, Any]: ...

    def code_drug(self, **kwargs: Any) -> Dict[str, Any]:  # WHODrug subclasses override
        raise NotImplementedError


class GenericConnector(Connector):
    """
    Catch-all for the remaining systems (EDC, CTMS, eTMF, RWD, QMS, CRM, MLR).

    Methods are resolved dynamically against the fixture/live backing store so we
    don't need a bespoke abstract class per system to demonstrate the pattern;
    production replaces each with a typed subclass + validated client.
    """

    def __init__(self, kind: str) -> None:
        self.kind = kind
