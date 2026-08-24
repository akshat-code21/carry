"""
LangGraph pipeline assembly for HFI.

Flow:
  START → normalizer → chunker → entity_extractor → thesis_extractor
        → embedder → portfolio_node → report_generator → alert_checker → END

Conditional edges:
  - thesis_extractor is skipped for content_type == 'filing'
  - report_generator is skipped unless report_triggered == True
"""

import structlog
from langgraph.graph import END, START, StateGraph

from src.pipeline.hfi.state import PipelineState
from src.pipeline.hfi.nodes.normalizer import normalizer_node
from src.pipeline.hfi.nodes.entity_extractor import entity_extractor_node
from src.pipeline.hfi.nodes.thesis_extractor import thesis_extractor_node
from src.pipeline.hfi.nodes.embedder import embedder_node
from src.pipeline.hfi.nodes.portfolio_node import portfolio_node
from src.pipeline.hfi.nodes.report_generator import report_generator_node
from src.pipeline.hfi.nodes.alert_checker import alert_checker_node

logger = structlog.get_logger()


def _chunker_node(state: PipelineState) -> PipelineState:
    """Inline chunking node — splits cleaned_text into LangChain Documents."""
    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    cleaned = state.get("cleaned_text", "") or ""
    if not cleaned:
        return {**state, "chunks": []}

    doc = Document(
        page_content=cleaned,
        metadata={
            "source": state.get("source_url", ""),
            "investor_id": state.get("investor_id", ""),
            "content_type": state.get("content_type", ""),
        },
    )
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=4000,
        chunk_overlap=400,
        separators=["\n\n", "\n", ". ", " "],
    )
    chunks = splitter.split_documents([doc])
    return {**state, "chunks": chunks}


def _should_run_thesis(state: PipelineState) -> str:
    if state.get("content_type") == "filing":
        return "skip_thesis"
    if state.get("error"):
        return "skip_thesis"
    return "run_thesis"


def _should_run_report(state: PipelineState) -> str:
    if state.get("report_triggered") and not state.get("error"):
        return "run_report"
    return "skip_report"


def build_pipeline() -> StateGraph:
    graph = StateGraph(PipelineState)

    graph.add_node("normalizer", normalizer_node)
    graph.add_node("chunker", _chunker_node)
    graph.add_node("entity_extractor", entity_extractor_node)
    graph.add_node("thesis_extractor", thesis_extractor_node)
    graph.add_node("embedder", embedder_node)
    graph.add_node("portfolio_node", portfolio_node)
    graph.add_node("report_generator", report_generator_node)
    graph.add_node("alert_checker", alert_checker_node)

    graph.add_edge(START, "normalizer")
    graph.add_edge("normalizer", "chunker")
    graph.add_edge("chunker", "entity_extractor")

    graph.add_conditional_edges(
        "entity_extractor",
        _should_run_thesis,
        {"run_thesis": "thesis_extractor", "skip_thesis": "embedder"},
    )
    graph.add_edge("thesis_extractor", "embedder")

    graph.add_edge("embedder", "portfolio_node")

    graph.add_conditional_edges(
        "portfolio_node",
        _should_run_report,
        {"run_report": "report_generator", "skip_report": "alert_checker"},
    )
    graph.add_edge("report_generator", "alert_checker")
    graph.add_edge("alert_checker", END)

    return graph


_compiled_pipeline = None


def get_pipeline():
    global _compiled_pipeline
    if _compiled_pipeline is None:
        _compiled_pipeline = build_pipeline().compile()
    return _compiled_pipeline


def run_pipeline(initial_state: PipelineState) -> PipelineState:
    """Run the full pipeline synchronously. Called from background jobs."""
    pipeline = get_pipeline()
    try:
        final_state = pipeline.invoke(initial_state)
        logger.info(
            "Pipeline complete",
            content_item_id=initial_state.get("content_item_id"),
            entities=len(final_state.get("entities", [])),
            theses=len(final_state.get("theses", [])),
            embeddings_stored=final_state.get("embeddings_stored"),
            report_generated=final_state.get("report_generated"),
        )
        return final_state
    except Exception as e:
        logger.error(
            "Pipeline failed", error=str(e), content_item_id=initial_state.get("content_item_id")
        )
        return {**initial_state, "error": str(e)}
