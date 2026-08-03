"""Agent 8 & 9 Node — Scoring, Aggregation, and Driver Card Generation."""

from __future__ import annotations

import logging
from typing import Any

from src.schemas.agent_pipeline import (
    PipelineGraphState,
    ScoreDriverCard,
    TickerScoreOutput,
)

log = logging.getLogger(__name__)


def agent_scoring_node(state: PipelineGraphState) -> dict[str, Any]:
    """Agent 8 & 9: Aggregates sentiment, computes RISS, SMS, OCS, and driver cards."""
    symbol = state.get("symbol", "").upper()
    cleaned_items = state.get("cleaned_items", [])
    finbert_results = state.get("finbert_results", {})
    llm_analyses = state.get("llm_analyses", [])
    errors = list(state.get("errors", []))

    total_mentions = len(cleaned_items)
    if total_mentions == 0:
        output = TickerScoreOutput(
            symbol=symbol,
            riss_score=50.0,
            sms_score=0.0,
            ocs_score=50.0,
            trend="stable",
            confidence_pct=50.0,
            mention_count=0,
            driver_cards=[],
        )
        return {"final_score": output.model_dump(mode="json"), "errors": errors}

    # Compute RISS (70% weight in OCS v0.1)
    bullish_weight = 0.0
    total_weight = 0.0

    for item in cleaned_items:
        item_id = str(item.get("id"))
        fb = finbert_results.get(item_id, {})
        probs = fb.get("probabilities", {})
        pos = float(probs.get("positive", 0.33))
        neg = float(probs.get("negative", 0.33))
        engagement = max(1, int(item.get("engagement_score", 1)))

        weight = engagement**0.5
        score = (pos - neg + 1.0) / 2.0  # normalize [-1, 1] to [0, 1]
        bullish_weight += score * weight
        total_weight += weight

    riss_score = round((bullish_weight / total_weight) * 100.0 if total_weight > 0 else 50.0, 1)

    # Compute SMS (30% weight in OCS v0.1) — mention volume vs 30-day baseline
    # benchmark (e.g. 50 mentions/day)
    expected_mentions = 30.0
    sms_score = round(min(100.0, (total_mentions / expected_mentions) * 50.0), 1)

    # Composite OCS v0.1: 70% RISS + 30% SMS
    ocs_score = round(0.70 * riss_score + 0.30 * sms_score, 1)

    # Determine trend
    if ocs_score >= 65.0:
        trend = "rising"
    elif ocs_score <= 40.0:
        trend = "falling"
    else:
        trend = "stable"

    confidence_pct = round(min(98.0, 60.0 + (total_mentions * 0.8)), 1)

    # Build driver cards from top LLM analyses
    driver_cards: list[ScoreDriverCard] = []

    for analysis in llm_analyses[:3]:
        sentiment_label = analysis.get("sentiment_label", "bullish")
        driver_type = (
            "bullish"
            if sentiment_label == "bullish"
            else ("bearish" if sentiment_label == "bearish" else "neutral")
        )
        card = ScoreDriverCard(
            title=str(analysis.get("catalyst_theme", "Market Chatter Catalyst")),
            driver_type=driver_type,
            impact=+15.0
            if driver_type == "bullish"
            else (-15.0 if driver_type == "bearish" else 0.0),
            summary=str(analysis.get("explanation", "Community discussion driver")),
            source_links=[],
        )
        driver_cards.append(card)

    if not driver_cards:
        driver_cards.append(
            ScoreDriverCard(
                title=f"{symbol} Discussion Volume Surge",
                driver_type="bullish" if ocs_score >= 55.0 else "neutral",
                impact=10.0,
                summary=f"Elevated retail trader engagement across social channels for {symbol}.",
                source_links=[],
            )
        )

    output = TickerScoreOutput(
        symbol=symbol,
        riss_score=riss_score,
        sms_score=sms_score,
        ocs_score=ocs_score,
        trend=trend,
        confidence_pct=confidence_pct,
        mention_count=total_mentions,
        driver_cards=driver_cards,
    )

    log.info(
        "Agent 8/9 Scoring: %s final OCS=%.1f (RISS=%.1f, SMS=%.1f) trend=%s",
        symbol,
        ocs_score,
        riss_score,
        sms_score,
        trend,
    )
    res = {"final_score": output.model_dump(mode="json")}
    if errors:
        res["errors"] = errors
    return res
