# agent/persistence.py
# ============================================================
# Checkpointer factory — durable state for human-in-the-loop interrupts.
#
# Dev/demo: MemorySaver (in-process). Production: PostgresSaver when DATABASE_URL
# is set, giving resumable batch review, audit-trail persistence across restarts,
# and the record-retention cGMP requires (batch records: ≥1 year past expiry,
# often much longer per product).
# ============================================================
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def get_checkpointer():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        try:  # pragma: no cover - requires postgres
            from langgraph.checkpoint.postgres import PostgresSaver

            cp = PostgresSaver.from_conn_string(database_url)
            logger.info("Using PostgresSaver for durable checkpointing.")
            return cp
        except Exception as exc:  # pragma: no cover
            logger.warning("PostgresSaver unavailable (%s); falling back to MemorySaver.", exc)

    from langgraph.checkpoint.memory import MemorySaver

    return MemorySaver()
