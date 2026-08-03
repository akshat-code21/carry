"""Agent 3 Node — Cleaning, cashtag extraction, and MinHash near-deduplication."""

from __future__ import annotations

import logging
import re
from typing import Any

from datasketch import MinHash, MinHashLSH

from src.schemas.agent_pipeline import CleanedItem, PipelineGraphState
from src.schemas.market_chatter import SourceName

log = logging.getLogger(__name__)

URL_REGEX = re.compile(r"https?://\S+|www\.\S+")
HTML_TAG_REGEX = re.compile(r"<[^>]+>")
CASHTAG_REGEX = re.compile(r"\$([A-Za-z]{1,6})\b")


def _clean_text(raw_text: str) -> str:
    cleaned = HTML_TAG_REGEX.sub(" ", raw_text)
    cleaned = URL_REGEX.sub(" ", cleaned)
    return " ".join(cleaned.split())


def _extract_cashtags(text: str) -> list[str]:
    matches = CASHTAG_REGEX.findall(text)
    return sorted({m.upper() for m in matches})


def _build_minhash(text: str) -> MinHash:
    m = MinHash(num_perm=128)
    tokens = set(text.lower().split())
    for token in tokens:
        m.update(token.encode("utf-8"))
    return m


def agent_cleaner_node(state: PipelineGraphState) -> dict[str, Any]:
    """Agent 3: Cleans text, extracts cashtags, and removes near-duplicates via MinHash LSH."""
    symbol = state.get("symbol", "").upper()
    validated_items = state.get("validated_items", [])
    errors = list(state.get("errors", []))

    cleaned_records: list[dict[str, Any]] = []
    lsh = MinHashLSH(threshold=0.85, num_perm=128)

    for idx, item in enumerate(validated_items):
        raw_text = str(item.get("text", ""))
        cleaned_text = _clean_text(raw_text)
        if len(cleaned_text) < 10:
            continue

        cashtags = _extract_cashtags(raw_text)
        minhash = _build_minhash(cleaned_text)

        # Query LSH for near duplicates
        duplicates = lsh.query(minhash)
        if duplicates:
            continue  # Near-duplicate detected, skip

        item_id = str(item.get("id", f"item_{idx}"))
        try:
            lsh.insert(item_id, minhash)
        except ValueError:
            pass

        source_val = item.get("source", SourceName.REDDIT)
        if isinstance(source_val, str):
            try:
                source_val = SourceName(source_val)
            except ValueError:
                source_val = SourceName.REDDIT

        record = CleanedItem(
            id=item_id,
            symbol=symbol,
            source=source_val,
            cleaned_text=cleaned_text,
            title=item.get("title"),
            author=item.get("author"),
            url=item.get("url"),
            engagement_score=int(item.get("engagement_score", 0)),
            cashtags=cashtags,
            created_at=item.get("created_at"),
            raw_metadata=item.get("raw_metadata", {}),
        )
        cleaned_records.append(record.model_dump(mode="json"))

    log.info(
        "Agent 3 Cleaner: %d of %d items retained after near-deduplication for %s",
        len(cleaned_records),
        len(validated_items),
        symbol,
    )
    res = {"cleaned_items": cleaned_records}
    if errors:
        res["errors"] = errors
    return res
