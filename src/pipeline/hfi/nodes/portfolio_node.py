"""Portfolio node: turns 13F holdings into PortfolioChange rows."""

import structlog

from src.pipeline.hfi.state import PipelineState

logger = structlog.get_logger()


def portfolio_node(state: PipelineState) -> PipelineState:
    if state.get("content_type") != "filing":
        return {**state, "portfolio_changes": []}

    holdings = state.get("holdings") or []
    if not holdings:
        return {**state, "portfolio_changes": []}

    from src.services.hfi.portfolio_service import process_filing

    changes = process_filing(
        content_item_id=state["content_item_id"],
        investor_id=state["investor_id"],
        holdings=holdings,
        filing_period=state.get("filing_period") or "N/A",
        report_date=state.get("report_date"),
    )

    logger.info(
        "Portfolio node complete",
        content_item_id=state.get("content_item_id"),
        changes=len(changes),
    )
    return {**state, "portfolio_changes": changes}
