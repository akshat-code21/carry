"""LangGraph Multi-Agent Pipeline Graph Builder."""

from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, START, StateGraph

from src.pipeline.agents import (
    agent_cleaner_node,
    agent_finbert_node,
    agent_llm_node,
    agent_scoring_node,
    agent_validation_node,
)
from src.schemas.agent_pipeline import PipelineGraphState

log = logging.getLogger(__name__)


def build_pipeline_graph():
    """Builds and compiles the 10-Agent LangGraph StateGraph workflow."""
    builder = StateGraph(PipelineGraphState)

    # Register nodes
    builder.add_node("validation", agent_validation_node)
    builder.add_node("cleaner", agent_cleaner_node)
    builder.add_node("finbert", agent_finbert_node)
    builder.add_node("llm", agent_llm_node)
    builder.add_node("scoring", agent_scoring_node)

    # Define linear & parallel edges
    builder.add_edge(START, "validation")
    builder.add_edge("validation", "cleaner")
    builder.add_edge("cleaner", "finbert")
    builder.add_edge("cleaner", "llm")
    builder.add_edge("finbert", "scoring")
    builder.add_edge("llm", "scoring")
    builder.add_edge("scoring", END)

    return builder.compile()


# Compiled Singleton Graph
pipeline_graph = build_pipeline_graph()


async def run_pipeline_for_raw_items(
    symbol: str, raw_items: list[dict[str, Any]], period_days: int = 7
) -> dict[str, Any]:
    """Helper function to execute the LangGraph pipeline asynchronously."""
    initial_state: PipelineGraphState = {
        "symbol": symbol.upper(),
        "period_days": period_days,
        "raw_items": raw_items,
        "validated_items": [],
        "cleaned_items": [],
        "finbert_results": {},
        "llm_analyses": [],
        "final_score": None,
        "errors": [],
    }

    final_state = await pipeline_graph.ainvoke(initial_state)
    return final_state.get("final_score") or {}
