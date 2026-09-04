"""Search coverage service - per-topic video coverage stats with sentiment.

Given a query, finds every video with matching transcript content in a time
window, classifies one representative snippet per video with FinBERT (local,
free), and aggregates: total coverage, stance distribution, weekly volume
buckets, and week-over-week momentum. Cached per (query, window) for 6h.
"""

import asyncio
import hashlib
import logging
import math
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.models.channel import Channel
from src.models.search_answer import SearchAnswer
from src.models.transcript_segment import TranscriptSegment
from src.models.video import Video
from src.services.finbert_service import FinBertService
from src.services.interfaces import EmbeddingProvider
from src.services.query_router import QueryRouter
from src.services.search_service import SearchService
from src.services.social_context_service import (
    SocialContextService,
    social_coverage_stats,
)

logger = logging.getLogger(__name__)
settings = get_settings()

COVERAGE_CACHE_TTL = timedelta(hours=6)
DEFAULT_WINDOW_DAYS = 14
LOW_CONFIDENCE_FLOOR = 0.5
SNIPPET_TEXT_LIMIT = 600

# FinBERT emits bullish/bearish; the UI speaks positive/negative/neutral
STANCE_MAP = {"bullish": "positive", "bearish": "negative", "neutral": "neutral"}

_locks: dict[str, asyncio.Lock] = {}


def normalize_query(query: str) -> str:
    return query.strip().lower()


def coverage_cache_key(query: str, window_days: int) -> str:
    normalized = " ".join(normalize_query(query).split())
    return hashlib.sha256(f"{normalized}|coverage|{window_days}".encode()).hexdigest()


def weekly_volume(
    published_dates: list[datetime | None],
    window_days: int,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Bucket dated videos into consecutive 7-day slices ending at ``now``.

    The window is split into ceil(window_days/7) buckets, oldest first:
    [{week_start: ISO-date-str, count: int}]. Undated and out-of-window
    entries are ignored.
    """
    reference = now or datetime.now(UTC)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=UTC)

    n_buckets = max(1, math.ceil(window_days / 7))
    bucket_len = timedelta(days=window_days / n_buckets)
    window_start = reference - timedelta(days=window_days)

    counts = [0] * n_buckets
    for published in published_dates:
        if published is None:
            continue
        ts = published if published.tzinfo else published.replace(tzinfo=UTC)
        if ts < window_start or ts > reference:
            continue
        idx = int((ts - window_start) / bucket_len)
        counts[min(idx, n_buckets - 1)] += 1

    buckets = []
    for i, count in enumerate(counts):
        week_start = (window_start + i * bucket_len).date().isoformat()
        buckets.append({"week_start": week_start, "count": count})
    return buckets


def wow_delta_pct(volume: list[dict[str, Any]]) -> float | None:
    """Percent change of the last weekly bucket vs the previous one.

    None when fewer than two buckets exist or the previous bucket is empty
    (a percentage from zero is meaningless).
    """
    if len(volume) < 2:
        return None
    previous = volume[-2]["count"]
    current = volume[-1]["count"]
    if previous == 0:
        return None
    return round((current - previous) / previous * 100.0, 1)


def aggregate_stances(classifications: list[dict[str, Any]]) -> dict[str, int]:
    """Fold FinBERT outputs into {positive, neutral, negative} counts."""
    counts = {"positive": 0, "neutral": 0, "negative": 0}
    for item in classifications:
        sentiment = STANCE_MAP.get(item.get("sentiment", ""), "neutral")
        confidence = item.get("confidence") or 0.0
        if confidence < LOW_CONFIDENCE_FLOOR:
            sentiment = "neutral"
        counts[sentiment] += 1
    return counts


def format_coverage_for_prompt(payload: dict[str, Any] | None) -> str | None:
    """Render coverage stats as a compact context block for answer synthesis."""
    if not payload or not payload.get("total_videos"):
        return None

    total = payload["total_videos"]
    pos = payload.get("positive", 0)
    neu = payload.get("neutral", 0)
    neg = payload.get("negative", 0)
    window = payload.get("window_days", DEFAULT_WINDOW_DAYS)
    line = (
        f"Coverage: {total} videos discussed this topic in the last {window} days "
        f"(stance: {pos} positive / {neu} neutral / {neg} negative)."
    )
    delta = payload.get("wow_delta_pct")
    if delta is not None:
        direction = "up" if delta >= 0 else "down"
        line += f" Weekly discussion volume is {direction} {abs(delta):g}% week-over-week."
    return line


class SearchCoverageService:
    """Computes (and caches) per-query video coverage intelligence."""

    def __init__(
        self,
        db: AsyncSession,
        embedding_provider: EmbeddingProvider,
        finbert: FinBertService | None = None,
        social_service: "SocialContextService | None" = None,
    ) -> None:
        self.db = db
        self.embedding_provider = embedding_provider
        self.finbert = finbert or FinBertService()
        self.social_service = social_service
        self._search_service: SearchService | None = None

    async def get_or_create(
        self,
        query: str,
        segment_ids: list[str] | None = None,
        window_days: int = DEFAULT_WINDOW_DAYS,
    ) -> dict[str, Any]:
        """Return cached-or-fresh coverage stats for the query.

        On any failure returns an empty (total_videos=0) payload so callers
        can simply hide the card.
        """
        unavailable = {
            "query": query,
            "total_videos": 0,
            "positive": 0,
            "neutral": 0,
            "negative": 0,
            "weekly_volume": [],
            "wow_delta_pct": None,
            "window_days": window_days,
        }

        key = coverage_cache_key(query, window_days)
        lock = _locks.setdefault(key, asyncio.Lock())
        async with lock:
            cached = await self._read_cache(key, window_days)
            if cached is not None:
                return cached

            snippets = await self._resolve_video_snippets(query, segment_ids, window_days)
            if not snippets:
                await self._write_cache(key, query, unavailable)
                return unavailable

            try:
                classifications = await asyncio.to_thread(
                    self.finbert.analyze_texts,
                    [s["text"][:SNIPPET_TEXT_LIMIT] for s in snippets],
                )
                classification_dicts = [
                    {
                        "sentiment": res.sentiment,
                        "confidence": res.confidence,
                    }
                    for res in classifications
                ]
            except Exception as exc:
                logger.warning(f"search/coverage: FinBERT classification failed: {exc}")
                return unavailable  # don't cache degraded stats

            stances = aggregate_stances(classification_dicts)
            dates = [s.get("published_at") for s in snippets]
            volume = weekly_volume(dates, window_days)

            payload = {
                "query": query,
                "total_videos": len(snippets),
                "positive": stances["positive"],
                "neutral": stances["neutral"],
                "negative": stances["negative"],
                "weekly_volume": volume,
                "wow_delta_pct": wow_delta_pct(volume),
                "window_days": window_days,
            }

            # TickerFlow social-sentiment stats for the resolved ticker (if any)
            if self.social_service is not None:
                ticker = QueryRouter._extract_ticker_heuristic(query)
                if ticker:
                    try:
                        stats = await social_coverage_stats(
                            self.db, ticker, window_days, social_service=self.social_service
                        )
                        if stats is not None:
                            payload["social"] = stats.model_dump(mode="json")
                    except Exception as exc:
                        logger.warning(f"search/coverage: social stats unavailable: {exc}")
                        await self._safe_rollback()

            await self._write_cache(key, query, payload)
            return payload

    async def _resolve_video_snippets(
        self,
        query: str,
        segment_ids: list[str] | None,
        window_days: int,
    ) -> list[dict[str, Any]]:
        """One best-matching snippet per distinct video inside the window.

        Primary path is a single DISTINCT ON query over full-text matches;
        falls back to deriving per-video best segments from hybrid retrieval.
        """
        cutoff = datetime.now(UTC) - timedelta(days=window_days)
        ts_query = func.plainto_tsquery("english", query)
        rank_expr = func.ts_rank(
            func.to_tsvector("english", TranscriptSegment.text), ts_query
        ).label("rank")

        stmt = (
            select(
                TranscriptSegment.id,
                TranscriptSegment.video_id,
                TranscriptSegment.text,
                Video.title.label("video_title"),
                Video.youtube_video_id,
                Channel.title.label("channel_title"),
                Video.published_at,
            )
            .join(Video, TranscriptSegment.video_id == Video.id)
            .join(Channel, Video.channel_id == Channel.id)
            .where(
                func.to_tsvector("english", TranscriptSegment.text).op("@@")(ts_query),
                Video.published_at.isnot(None),
                Video.published_at >= cutoff,
            )
            .distinct(TranscriptSegment.video_id)
            .order_by(TranscriptSegment.video_id, rank_expr.desc())
        )

        try:
            rows = (await self.db.execute(stmt)).all()
            return [
                {
                    "video_id": str(row.video_id),
                    "text": row.text,
                    "video_title": row.video_title,
                    "youtube_video_id": row.youtube_video_id,
                    "channel_title": row.channel_title,
                    "published_at": row.published_at,
                }
                for row in rows
            ]
        except Exception as exc:
            logger.warning(f"search/coverage: snippet query failed ({exc}); using fallback")
            await self._safe_rollback()

        try:
            return await self._fallback_snippets(query, segment_ids, window_days)
        except Exception as exc:
            logger.warning(f"search/coverage: fallback snippet resolution failed: {exc}")
            await self._safe_rollback()
            return []

    async def _safe_rollback(self) -> None:
        """Clear a poisoned transaction so the session stays usable."""
        try:
            await self.db.rollback()
        except Exception:  # noqa: BLE001 - rollback is best-effort
            pass

    async def _fallback_snippets(
        self,
        query: str,
        segment_ids: list[str] | None,
        window_days: int,
    ) -> list[dict[str, Any]]:
        """Derive per-video best segments from the hybrid search pool."""
        if self._search_service is None:
            self._search_service = SearchService(self.db, self.embedding_provider)

        cutoff = datetime.now(UTC) - timedelta(days=window_days)
        results = await self._search_service.hybrid_search(query, limit=100)
        best_per_video: dict[str, dict[str, Any]] = {}
        for seg in results.get("segments", []):
            vid = seg["video_id"]
            if vid in best_per_video:
                continue
            v_info = results.get("videos", {}).get(vid, {})
            published_raw = v_info.get("published_at")
            try:
                published = datetime.fromisoformat(published_raw) if published_raw else None
            except ValueError:
                published = None
            if published is None or published < cutoff or published > datetime.now(UTC):
                continue
            best_per_video[vid] = {
                "video_id": vid,
                "text": seg["text"],
                "video_title": v_info.get("title"),
                "youtube_video_id": v_info.get("youtube_video_id"),
                "channel_title": seg.get("channel_title"),
                "published_at": published,
            }

        # When the client supplied ranked ids, prefer those videos first
        if segment_ids:
            id_set = set(segment_ids)
            ordered: list[dict[str, Any]] = []
            seen: set[str] = set()
            for seg in results.get("segments", []):
                if seg["id"] in id_set and seg["video_id"] not in seen:
                    seen.add(seg["video_id"])
                    snippet = best_per_video.get(seg["video_id"])
                    if snippet:
                        ordered.append(snippet)
            return ordered

        return list(best_per_video.values())

    async def _read_cache(self, key: str, window_days: int) -> dict[str, Any] | None:
        try:
            stmt = select(SearchAnswer).where(SearchAnswer.query_hash == key)
            row = (await self.db.execute(stmt)).scalar_one_or_none()
        except Exception as exc:
            logger.warning(f"search/coverage: cache read failed: {exc}")
            await self._safe_rollback()
            return None
        if row is None:
            return None
        created = row.created_at if row.created_at.tzinfo else row.created_at.replace(tzinfo=UTC)
        if datetime.now(UTC) - created > COVERAGE_CACHE_TTL:
            return None
        payload = dict(row.answer_json)
        payload["window_days"] = window_days
        return payload

    async def _write_cache(self, key: str, query: str, payload: dict[str, Any]) -> None:
        try:
            await self.db.execute(delete(SearchAnswer).where(SearchAnswer.query_hash == key))
            self.db.add(SearchAnswer(query_hash=key, query_text=query[:500], answer_json=payload))
            await self.db.commit()
        except Exception as exc:
            logger.warning(f"search/coverage: cache write failed: {exc}")
            await self.db.rollback()
