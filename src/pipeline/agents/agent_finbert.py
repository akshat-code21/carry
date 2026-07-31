import asyncio
import logging
from typing import Any

from src.pipeline.agents.agent_cleaner import CleanedItem
from src.schemas.agent_pipeline import FinBertSentiment, PipelineGraphState
from src.services.finbert_service import FinBertService

log = logging.getLogger(__name__)

# Global singleton FinBertService instance
_finbert_service: FinBertService | None = None


def _get_finbert_service() -> FinBertService:
    global _finbert_service
    if _finbert_service is None:
        _finbert_service = FinBertService()
    return _finbert_service


async def agent_finbert_node(state: PipelineGraphState) -> dict[str, Any]:
    """Agent 4: Runs local ONNX FinBERT batch inference on cleaned content asynchronously."""
    symbol = state.get("symbol", "").upper()
    cleaned_items = state.get("cleaned_items", [])
    errors = list(state.get("errors", []))

    if not cleaned_items:
        return {"finbert_results": {}, "errors": errors}

    service = _get_finbert_service()
    texts = [str(item.get("cleaned_text", "")) for item in cleaned_items]

    try:
        results = await asyncio.to_thread(service.analyze_texts, texts)
        finbert_map: dict[str, dict[str, Any]] = {}

        for item, res in zip(cleaned_items, results):
            item_id = str(item.get("id"))
            finbert_map[item_id] = FinBertSentiment(
                sentiment=res.sentiment,
                confidence=res.confidence,
                probabilities=res.probabilities,
            ).model_dump(mode="json")

        log.info("Agent 4 FinBERT: Processed %d items for symbol %s", len(finbert_map), symbol)
        res = {"finbert_results": finbert_map}
        if errors:
            res["errors"] = errors
        return res
    except Exception as exc:
        log.warning("FinBERT inference failed (%s), falling back to heuristic sentiment", exc)
        # Fallback heuristic mapping if ONNX runtime model missing
        finbert_map = {}
        for item in cleaned_items:
            item_id = str(item.get("id"))
            text = str(item.get("cleaned_text", "")).lower()
            if any(w in text for w in ["rally", "call", "buy", "bull", "growth", "high", "upgrade"]):
                sent = "bullish"
                probs = {"positive": 0.8, "negative": 0.1, "neutral": 0.1}
            elif any(w in text for w in ["drop", "put", "sell", "bear", "down", "risk", "downgrade"]):
                sent = "bearish"
                probs = {"positive": 0.1, "negative": 0.8, "neutral": 0.1}
            else:
                sent = "neutral"
                probs = {"positive": 0.2, "negative": 0.2, "neutral": 0.6}

            finbert_map[item_id] = FinBertSentiment(
                sentiment=sent, confidence=0.75, probabilities=probs
            ).model_dump(mode="json")

        res = {"finbert_results": finbert_map}
        if errors:
            res["errors"] = errors
        return res
