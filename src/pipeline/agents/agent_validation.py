"""Agent 2 Node — Validation and Filtering."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from src.schemas.agent_pipeline import PipelineGraphState

log = logging.getLogger(__name__)


def agent_validation_node(state: PipelineGraphState) -> dict[str, Any]:
    """Agent 2: Validates raw content integrity, lookback windows, and ticker relevance."""
    symbol = state.get("symbol", "").upper()
    period_days = state.get("period_days", 7)
    raw_items = state.get("raw_items", [])
    errors = list(state.get("errors", []))

    if not symbol:
        errors.append("Validation failed: Missing symbol in state")
        return {"validated_items": [], "errors": errors}

    cutoff = datetime.now(UTC) - timedelta(days=period_days)
    validated: list[dict[str, Any]] = []

    for item in raw_items:
        text = str(item.get("text", "")).strip()
        if len(text) < 10:
            continue

        created_raw = item.get("created_at")
        if created_raw:
            try:
                if isinstance(created_raw, str):
                    dt = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
                else:
                    dt = created_raw
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                if dt < cutoff:
                    continue
            except Exception:
                pass

        # Relevance check: symbol cashtag or symbol substring
        text_upper = text.upper()
        if symbol not in text_upper and f"${symbol}" not in text_upper:
            # If item explicitly tagged with symbol, allow it
            if item.get("symbol", "").upper() != symbol:
                continue

        validated.append(item)

    log.info("Agent 2 Validation: %d of %d items validated for %s", len(validated), len(raw_items), symbol)
    res = {"validated_items": validated}
    if errors:
        res["errors"] = errors
    return res
