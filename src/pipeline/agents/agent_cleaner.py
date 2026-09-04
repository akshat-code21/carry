"""Agent 3 Node - Cleaning, cashtag extraction, and MinHash near-deduplication."""

from __future__ import annotations

import logging
import re
from typing import Any

try:
    from datasketch import MinHash, MinHashLSH

    HAS_DATASKETCH = True
except ImportError:
    HAS_DATASKETCH = False
    MinHash = Any  # type: ignore
    MinHashLSH = Any  # type: ignore

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


def _build_minhash(text: str) -> Any:
    if not HAS_DATASKETCH:
        return set(text.lower().split())
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
    lsh = MinHashLSH(threshold=0.85, num_perm=128) if HAS_DATASKETCH else None
    seen_token_sets: list[set[str]] = []

    for idx, item in enumerate(validated_items):
        raw_text = str(item.get("text", ""))
        cleaned_text = _clean_text(raw_text)
        if len(cleaned_text) < 10:
            continue

        cashtags = _extract_cashtags(raw_text)
        tokens_or_minhash = _build_minhash(cleaned_text)

        if HAS_DATASKETCH and lsh is not None:
            duplicates = lsh.query(tokens_or_minhash)
            if duplicates:
                continue
            item_id = str(item.get("id", f"item_{idx}"))
            try:
                lsh.insert(item_id, tokens_or_minhash)
            except ValueError:
                pass
        else:
            # Jaccard set similarity fallback
            tok_set = (
                tokens_or_minhash
                if isinstance(tokens_or_minhash, set)
                else set(cleaned_text.lower().split())
            )
            is_duplicate = False
            for prev_set in seen_token_sets:
                intersection = len(tok_set & prev_set)
                union = len(tok_set | prev_set)
                if union > 0 and (intersection / union) >= 0.85:
                    is_duplicate = True
                    break
            if is_duplicate:
                continue
            seen_token_sets.append(tok_set)
            item_id = str(item.get("id", f"item_{idx}"))

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
