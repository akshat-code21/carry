"""Unit and Integration tests for the LangGraph Multi-Agent Pipeline."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.pipeline.agents.agent_cleaner import agent_cleaner_node
from src.pipeline.agents.agent_finbert import agent_finbert_node
from src.pipeline.agents.agent_llm import agent_llm_node
from src.pipeline.agents.agent_scoring import agent_scoring_node
from src.pipeline.agents.agent_validation import agent_validation_node
from src.pipeline.graph import pipeline_graph, run_pipeline_for_raw_items


@pytest.fixture
def sample_raw_items() -> list[dict]:
    now = datetime.now(UTC)
    return [
        {
            "id": "reddit:p1",
            "symbol": "NVDA",
            "source": "reddit",
            "text": "Why $NVDA is poised for a massive rally this quarter! Revenue growth looks unstoppable.",
            "title": "$NVDA Rally",
            "author": "bullish_trader",
            "created_at": now.isoformat(),
            "engagement_score": 150,
        },
        {
            "id": "stocktwits:m1",
            "symbol": "NVDA",
            "source": "reddit",
            "text": "$NVDA break out coming soon! Bullish momentum.",
            "author": "chart_king",
            "created_at": now.isoformat(),
            "engagement_score": 80,
        },
        {
            "id": "reddit:p2_dup",
            "symbol": "NVDA",
            "source": "reddit",
            "text": "Why $NVDA is poised for a massive rally this quarter! Revenue growth looks unstoppable.",
            "title": "$NVDA Rally",
            "author": "bullish_trader",
            "created_at": now.isoformat(),
            "engagement_score": 150,
        },
        {
            "id": "news:n1",
            "symbol": "NVDA",
            "source": "news",
            "text": "NVIDIA Reports Record Quarterly Revenue Driven by Enterprise Demand",
            "title": "NVIDIA Reports Record Quarterly Revenue",
            "author": "Reuters",
            "created_at": now.isoformat(),
            "engagement_score": 90,
        },
        {
            "id": "short_noise",
            "symbol": "NVDA",
            "source": "twitter",
            "text": "bad",
            "created_at": now.isoformat(),
            "engagement_score": 1,
        },
    ]


def test_agent_validation_node(sample_raw_items: list[dict]) -> None:
    state = {
        "symbol": "NVDA",
        "period_days": 7,
        "raw_items": sample_raw_items,
        "errors": [],
    }
    result = agent_validation_node(state)
    validated = result["validated_items"]
    # Should filter out "short_noise" (len < 10)
    assert len(validated) == 4
    assert not any(item["id"] == "short_noise" for item in validated)


def test_agent_cleaner_node(sample_raw_items: list[dict]) -> None:
    val_state = agent_validation_node({
        "symbol": "NVDA",
        "period_days": 7,
        "raw_items": sample_raw_items,
        "errors": [],
    })
    result = agent_cleaner_node(val_state)
    cleaned = result["cleaned_items"]
    # MinHash deduplication should drop the near-duplicate p2_dup
    assert len(cleaned) == 3
    assert any(item["id"] == "reddit:p1" for item in cleaned)


@pytest.mark.asyncio
async def test_agent_finbert_node(sample_raw_items: list[dict]) -> None:
    val_state = agent_validation_node({"symbol": "NVDA", "period_days": 7, "raw_items": sample_raw_items, "errors": []})
    clean_state = agent_cleaner_node(val_state)
    result = await agent_finbert_node(clean_state)
    finbert_results = result["finbert_results"]
    assert len(finbert_results) == 3
    assert "reddit:p1" in finbert_results
    assert finbert_results["reddit:p1"]["sentiment"] in ["bullish", "bearish", "neutral"]


@pytest.mark.asyncio
async def test_full_langgraph_pipeline_execution(sample_raw_items: list[dict]) -> None:
    final_score = await run_pipeline_for_raw_items("NVDA", sample_raw_items, period_days=7)
    assert final_score is not None
    assert final_score["symbol"] == "NVDA"
    assert 0.0 <= final_score["ocs_score"] <= 100.0
    assert 0.0 <= final_score["riss_score"] <= 100.0
    assert final_score["trend"] in ["rising", "stable", "falling"]
    assert len(final_score["driver_cards"]) > 0
