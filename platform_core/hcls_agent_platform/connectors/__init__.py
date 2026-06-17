"""Connector framework — typed adapters to HCLS systems of record."""
from .factory import get_connector  # noqa: F401

__all__ = ["get_connector"]
