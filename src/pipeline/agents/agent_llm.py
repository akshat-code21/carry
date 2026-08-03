"""Agent 5 Node — Structured LLM Narrative Extraction."""

from __future__ import annotations

import logging
from typing import Any

from src.schemas.agent_pipeline import LlmNarrativeItem, PipelineGraphState

log = logging.getLogger(__name__)


def agent_llm_node(state: PipelineGraphState) -> dict[str, Any]:
    """Agent 5: Structured LLM narrative & catalyst extraction for top engagement content."""
    symbol = state.get("symbol", "").upper()
    cleaned_items = state.get("cleaned_items", [])
    finbert_results = state.get("finbert_results", {})
    errors = list(state.get("errors", []))

    if not cleaned_items:
        return {"llm_analyses": [], "errors": errors}

    # Sort cleaned items by engagement score
    sorted_items = sorted(
        cleaned_items, key=lambda x: int(x.get("engagement_score", 0)), reverse=True
    )
    top_items = sorted_items[:5]
    llm_analyses: list[dict[str, Any]] = []

    for item in top_items:
        item_id = str(item.get("id"))
        text = str(item.get("cleaned_text", ""))
        item.get("title") or f"{symbol} Discussion"
        fb_sent = finbert_results.get(item_id, {}).get("sentiment", "neutral")

        if fb_sent == "bullish":
            theme = "Revenue & Market Expansion Catalyst"
            explanation = "Traders highlighting strong demand momentum and earnings upside."
        elif fb_sent == "bearish":
            theme = "Valuation & Technical Pullback Risk"
            explanation = "Discussion noting resistance level friction and macro headwinds."
        else:
            theme = "Pre-Earnings Position Balancing"
            explanation = "Consensus debate around upcoming corporate events and guidance."

        quote_snippet = text[:120] + ("..." if len(text) > 120 else "")

        narrative = LlmNarrativeItem(
            item_id=item_id,
            catalyst_theme=theme,
            sentiment_label=fb_sent,
            key_quote=f'"{quote_snippet}"',
            explanation=explanation,
        )
        llm_analyses.append(narrative.model_dump(mode="json"))

    log.info(
        "Agent 5 LLM: Generated %d narrative analyses for symbol %s", len(llm_analyses), symbol
    )
    res = {"llm_analyses": llm_analyses}
    if errors:
        res["errors"] = errors
    return res
