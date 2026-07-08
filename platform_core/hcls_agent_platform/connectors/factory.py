"""
Connector factory -- resolve a connector by kind and mode.

    get_connector("safety")                 # mode from CONNECTOR_MODE (default fixture)
    get_connector("safety", mode="live")    # explicit live

Modes:
    fixture  deterministic offline store (demos, CI, evals)   [default]
    live     production adapters (connectors/live.py)

Live mode for kind='safety': returns LiveSafetyConnector when SAFETY_BASE_URL
is set (real HTTP round-trip to Argus/Veeva Safety or the local reference
service). Falls back to LiveConnector NotImplemented stub when SAFETY_BASE_URL
is not set so the intent is explicit.

MedDRA and WHODrug connectors remain fixture-backed even in live mode for this
demo: they require a licensed API (MSSO / UMC). Implement LiveMedDRA /
LiveWHODrug in live.py when the customer provides credentials.
"""
from __future__ import annotations

import os
from typing import Optional

from .base import Connector
from .fixtures import (
    FixtureDMS,
    FixtureLIMS,
    FixtureMES,
    FixtureGeneric,
    FixtureMedDRA,
    FixtureRIM,
    FixtureSafety,
    FixtureWHODrug,
)
from .live import LiveConnector, LiveSafetyConnector

_FIXTURE_BUILDERS = {
    "rim": FixtureRIM,
    "dms": FixtureDMS,
    "safety": FixtureSafety,
    "meddra": FixtureMedDRA,
    "whodrug": FixtureWHODrug,
    "mes": FixtureMES,
    "lims": FixtureLIMS,
}
_GENERIC_KINDS = {"edc", "ctms", "etmf", "rwd", "qms", "crm", "mlr"}


def get_connector(kind: str, mode: Optional[str] = None) -> Connector:
    mode = (mode or os.getenv("CONNECTOR_MODE", "fixture")).strip().lower()

    if mode == "live":
        if kind == "safety":
            # SAFETY_SOURCE=openfda -> real, public, de-identified FAERS data
            # (read-only; writes/submission stay human-gated against the customer's
            # validated safety system). This is the "one real connector" reference.
            if os.getenv("SAFETY_SOURCE", "").strip().lower() == "openfda":
                from .openfda import OpenFDASafetyConnector
                return OpenFDASafetyConnector()
            base_url = os.getenv("SAFETY_BASE_URL", "")
            if base_url:
                return LiveSafetyConnector(base_url=base_url)
            # Neither SAFETY_SOURCE nor SAFETY_BASE_URL set: informative stub.
            return LiveConnector(kind)
        # MedDRA / WHODrug: remain fixture-backed in demo; implement live
        # subclasses when licensed API credentials are available.
        if kind in ("meddra", "whodrug"):
            return _FIXTURE_BUILDERS[kind]()
        # All other kinds: generic live stub (raises NotImplementedError per method)
        return LiveConnector(kind)

    # fixture mode (default)
    if kind in _FIXTURE_BUILDERS:
        return _FIXTURE_BUILDERS[kind]()
    if kind in _GENERIC_KINDS:
        return FixtureGeneric(kind)
    raise ValueError(f"unknown connector kind {kind!r}")
