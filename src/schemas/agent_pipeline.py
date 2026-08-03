"""Typed Pydantic schemas and state contracts for the LangGraph agent pipeline."""

from __future__ import annotations

import operator
from datetime import datetime
from typing import Annotated, Any, TypedDict

from pydantic import BaseModel, Field

from src.schemas.market_chatter import SourceName


class CleanedItem(BaseModel):
    """Cleaned, validated, and de-noised social/news content record."""

    id: str
    symbol: str
    source: SourceName
    cleaned_text: str
    title: str | None = None
    author: str | None = None
    url: str | None = None
    engagement_score: int = 0
    cashtags: list[str] = Field(default_factory=list)
    created_at: datetime
    raw_metadata: dict[str, Any] = Field(default_factory=dict)


class FinBertSentiment(BaseModel):
    """Calibrated ONNX FinBERT sentiment result."""

    sentiment: str  # "bullish" | "bearish" | "neutral"
    confidence: float
    probabilities: dict[str, float]


class LlmNarrativeItem(BaseModel):
    """Qualitative narrative & catalyst extraction from LLM node."""

    item_id: str
    catalyst_theme: str
    sentiment_label: str
    key_quote: str
    explanation: str


class ScoreDriverCard(BaseModel):
    """Human-readable driver card for SwaggyStocks dashboard."""

    title: str
    driver_type: str  # "bullish" | "bearish" | "neutral"
    impact: float
    summary: str
    source_links: list[str] = Field(default_factory=list)


class TickerScoreOutput(BaseModel):
    """Final aggregated score output from the LangGraph multi-agent pipeline."""

    symbol: str
    riss_score: float  # Retail Investor Sentiment Score (0–100)
    sms_score: float  # Social Mention Score (0–100)
    ocs_score: float  # Overall Composite Score (0–100)
    trend: str  # "rising" | "stable" | "falling"
    confidence_pct: float
    mention_count: int
    driver_cards: list[ScoreDriverCard] = Field(default_factory=list)


class PipelineGraphState(TypedDict, total=False):
    """LangGraph state container passed between graph nodes."""

    symbol: str
    period_days: int
    raw_items: Annotated[list[dict[str, Any]], operator.add]
    validated_items: Annotated[list[dict[str, Any]], operator.add]
    cleaned_items: Annotated[list[dict[str, Any]], operator.add]
    finbert_results: Annotated[dict[str, dict[str, Any]], operator.or_]
    llm_analyses: Annotated[list[dict[str, Any]], operator.add]
    final_score: dict[str, Any] | None
    errors: Annotated[list[str], operator.add]
