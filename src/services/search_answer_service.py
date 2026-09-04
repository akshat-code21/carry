"""Search answer service - synthesizes cached LLM answers from transcript segments.

Given a query and a ranked set of transcript segments, produces a concise
summary with key points and clip citations. Answers are cached per normalized
query for 24h so repeat searches never pay the LLM cost twice.
"""

import asyncio
import hashlib
import json
import logging
import re
import time
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.analytics.service import analytics
from src.config import get_settings
from src.models.channel import Channel
from src.models.raw_content import RawContent
from src.models.search_answer import SearchAnswer
from src.models.transcript_segment import TranscriptSegment
from src.models.video import Video
from src.services.interfaces import EmbeddingProvider
from src.services.query_router import QueryRouter
from src.services.search_coverage_service import (
    SearchCoverageService,
    format_coverage_for_prompt,
)
from src.services.search_service import SearchService
from src.services.social_context_service import SocialContextService

logger = logging.getLogger(__name__)
settings = get_settings()

CACHE_TTL = timedelta(hours=24)
MAX_INPUT_SEGMENTS = 12
SEGMENT_TEXT_LIMIT = 400
CITATION_TEXT_LIMIT = 240
MIN_SEGMENTS_FOR_ANSWER = 3
LLM_TIMEOUT_SECONDS = 8.0
MAX_KEY_POINTS = 4
ANSWER_MODEL = "gpt-5.4-nano"

ANSWER_SYSTEM_PROMPT = """You are a financial intelligence assistant synthesizing what financial creators, media channels, and analysts said on YouTube regarding the user's query, based on transcript excerpts.

Rules:
1. Answer ONLY from the provided transcript excerpts and aggregate coverage context. Never add outside knowledge, speculate, or hallucinate.
2. COMPULSORY CHANNEL ATTRIBUTION: Every single claim, valuation metric, price target, thesis, or sentiment point MUST explicitly state the specific YouTube channel name that said it (e.g., "According to CNBC...", "Meet Kevin argues that...", "Bloomberg reported...", "Both Graham Stephan and Plain Bagel noted..."). Never make generic unattributed statements.
3. NO META-LANGUAGE: Do NOT refer to "the clips", "the excerpts", "one segment", "the transcripts", or "the video commentary". Synthesize the commentary directly as spoken thoughts and analyses from the respective channels.
4. NO BRACKETED CITATIONS: Do NOT output citation numbers, brackets, or UUIDs (such as [1], [2], or [uuid]) in the summary or key points.
5. The summary must directly answer the user's query in 2-4 cohesive sentences with explicit channel attributions.
6. Provide up to 4 key points as short standalone bullet points. Each bullet point MUST explicitly name the channel that made the point.
7. If the excerpts do not contain enough relevant information to answer, set summary to a single sentence stating that monitored channels have not discussed this topic, and leave key_points empty.

Return ONLY valid JSON:
{"summary": "...", "key_points": ["..."], "cited_segment_ids": ["id1", "id2"]}"""

# Per-process locks keyed by query hash - concurrent identical queries share
# one synthesis instead of stampeding the LLM.
_locks: dict[str, asyncio.Lock] = {}


def normalize_query(query: str) -> str:
    """Collapse whitespace and lowercase so near-identical queries share cache."""
    return re.sub(r"\s+", " ", query.strip().lower())


def hash_query(query: str) -> str:
    return hashlib.sha256(normalize_query(query).encode("utf-8")).hexdigest()


def build_user_prompt(query: str, segments: list[dict[str, Any]]) -> str:
    """Render the numbered excerpt block sent to the model."""
    lines = [f"Query: {query}", "", "Excerpts:"]
    for seg in segments:
        channel = seg.get("channel_title") or "Unknown channel"
        title = seg.get("video_title") or "Unknown video"
        text = (seg.get("text") or "")[:SEGMENT_TEXT_LIMIT]
        lines.append(f'[{seg["id"]}] (Channel: "{channel}" - "{title}"): {text}')
    return "\n".join(lines)


SOCIAL_PROMPT_POST_LIMIT = 160


def build_social_prompt_block(snapshot_dict: dict[str, Any]) -> str:
    """Render the TickerFlow social-sentiment context appended to the prompt."""
    sources = snapshot_dict.get("sources") or []
    source_lines = []
    for src in sources:
        sentiment = src.get("sentiment_score")
        sentiment_str = f"{sentiment:+.2f}" if sentiment is not None else "n/a"
        source_lines.append(
            f"- {str(src.get('source') or 'unknown').title()}: "
            f"mentions={src.get('mentions') or 0}, sentiment={sentiment_str}, "
            f"bullish={src.get('bullish_pct') if src.get('bullish_pct') is not None else 'n/a'}%, "
            f"bearish={src.get('bearish_pct') if src.get('bearish_pct') is not None else 'n/a'}%"
        )
    lines = [
        "Social sentiment context (Reddit/X/News aggregate from TickerFlow, "
        f"as of {snapshot_dict.get('as_of') or 'unknown'}):",
        *source_lines,
    ]
    posts = snapshot_dict.get("sample_posts") or []
    if posts:
        lines.append("Representative posts:")
        for post in posts:
            lines.append(f'- "{post[:SOCIAL_PROMPT_POST_LIMIT]}"')
    return "\n".join(lines)


# Matches bracketed UUID citations like "[28442ada-dea1-4b3b-8859-80c026260635]" or numbered markers like "[1]"
_CITATION_BRACKET_RE = re.compile(
    r"\[\s*([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|\d+)\s*\]",
    re.IGNORECASE,
)
_RAW_UUID_RE = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)


def sanitize_citation_text(text: str, cited_ids: list[str] | None = None) -> str:
    """Strip bracketed citations, numbered markers [1], and stray UUIDs from the text."""
    if not text:
        return text
    text = _CITATION_BRACKET_RE.sub("", text)
    text = _RAW_UUID_RE.sub("", text)
    # Clean artefacts left after stripping unknown citations
    text = re.sub(r"\(\s*,\s*", "(", text)
    text = re.sub(r",\s*\)", ")", text)
    text = re.sub(r"\(\s*\)", "", text)
    text = re.sub(r"\[\s*\]", "", text)
    text = re.sub(r",\s*,", ",", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\s+([.,;:)])", r"\1", text)
    return text.strip()


def parse_llm_response(content: str, valid_ids: set[str]) -> dict[str, Any] | None:
    """Parse + validate the model's JSON payload.

    Returns {"summary", "key_points", "cited_segment_ids"} with citations
    filtered to known segment ids, or None when unusable. Summary and
    key_points are sanitized so bracketed UUIDs become numbered citations.
    """
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict):
        return None

    summary = data.get("summary")
    key_points_raw = data.get("key_points")
    cited_raw = data.get("cited_segment_ids")

    if not isinstance(summary, str) or not summary.strip():
        return None

    key_points = (
        [kp.strip()[:200] for kp in key_points_raw if isinstance(kp, str) and kp.strip()][
            :MAX_KEY_POINTS
        ]
        if isinstance(key_points_raw, list)
        else []
    )

    cited_ids = []
    if isinstance(cited_raw, list):
        seen: set[str] = set()
        for cid in cited_raw:
            if isinstance(cid, str) and cid in valid_ids and cid not in seen:
                seen.add(cid)
                cited_ids.append(cid)

    # Sanitize UUID citations → numbered markers; stray UUIDs are stripped
    summary_clean = sanitize_citation_text(summary.strip(), cited_ids)
    key_points_clean = [sanitize_citation_text(kp, cited_ids) for kp in key_points]
    # Drop any key points that became empty after sanitization
    key_points_clean = [kp for kp in key_points_clean if kp]

    return {
        "summary": summary_clean,
        "key_points": key_points_clean,
        "cited_segment_ids": cited_ids,
    }


def map_citations(cited_ids: list[str], segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build citation payloads (in LLM order) from the input segment pool."""
    by_id = {seg["id"]: seg for seg in segments}
    citations = []
    for seg_id in cited_ids:
        seg = by_id[seg_id]
        citations.append(
            {
                "segment_id": seg["id"],
                "video_id": seg["video_id"],
                "start_sec": seg["start_sec"],
                "text": (seg.get("text") or "")[:CITATION_TEXT_LIMIT],
                "video_title": seg.get("video_title"),
                "channel_title": seg.get("channel_title"),
                "youtube_video_id": seg.get("youtube_video_id"),
            }
        )
    return citations


class SearchAnswerService:
    """Produces (and caches) synthesized search answers."""

    def __init__(
        self,
        db: AsyncSession,
        embedding_provider: EmbeddingProvider,
        coverage_service: SearchCoverageService | None = None,
        social_service: "SocialContextService | None" = None,
    ) -> None:
        self.db = db
        self.embedding_provider = embedding_provider
        self.coverage_service = coverage_service
        self.social_service = social_service
        self._client = None

    def _get_client(self):
        """Lazily initialize the OpenAI client."""
        if self._client is None:
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY is not set.")
            from openai import OpenAI

            self._client = OpenAI(api_key=settings.openai_api_key)
        return self._client

    async def get_or_create(
        self,
        query: str,
        segment_ids: list[str] | None = None,
        max_input: int = MAX_INPUT_SEGMENTS,
    ) -> dict[str, Any]:
        """Return a cached answer for the query, synthesizing one if needed.

        Response shape matches SearchAnswerResponse; `available=False` tells
        the client to hide the answer card.
        """
        unavailable = {
            "query": query,
            "summary": "",
            "key_points": [],
            "citations": [],
            "available": False,
            "cached": False,
            "social_context": [],
        }

        qhash = hash_query(query)
        lock = _locks.setdefault(qhash, asyncio.Lock())
        async with lock:
            cached_payload = await self._read_cache(qhash)
            if cached_payload is not None:
                # Validate that cached entry was built from the same segment set;
                # frontend race (keepPreviousData) previously sent NVDA ids for an MSFT
                # query, poisoning the MSFT cache with a fallback answer. Bust it.
                if segment_ids is not None:
                    cached_source = cached_payload.get("source_segment_ids")
                    if cached_source is not None:
                        if set(cached_source) != set(segment_ids):
                            logger.info(
                                f"search/answer: cache bust for '{query[:60]}' - "
                                f"segment set changed ({len(cached_source)} vs {len(segment_ids)})"
                            )
                            try:
                                await self.db.execute(
                                    delete(SearchAnswer).where(SearchAnswer.query_hash == qhash)
                                )
                                await self.db.commit()
                            except Exception as exc:
                                logger.warning(f"search/answer: cache bust delete failed: {exc}")
                                await self._safe_rollback()
                            cached_payload = None
                        else:
                            cached_payload["cached"] = True
                            return cached_payload
                    else:
                        # Legacy entry without source ids - be conservative: if it is
                        # a fallback empty answer ("don't mention ...") but the caller now
                        # has real clips, force re-synthesis.
                        summary_l = (cached_payload.get("summary") or "").lower()
                        is_fallback = (
                            "don't mention" in summary_l
                            or "doesn't mention" in summary_l
                            or "don't provide" in summary_l
                            or "don't contain" in summary_l
                            or "doesn't provide" in summary_l
                        )
                        if is_fallback and len(segment_ids) >= 3:
                            logger.info(
                                f"search/answer: cache bust legacy fallback for '{query[:60]}'"
                            )
                            try:
                                await self.db.execute(
                                    delete(SearchAnswer).where(SearchAnswer.query_hash == qhash)
                                )
                                await self.db.commit()
                            except Exception as exc:
                                logger.warning(f"search/answer: legacy bust failed: {exc}")
                                await self._safe_rollback()
                            cached_payload = None
                        else:
                            cached_payload["cached"] = True
                            return cached_payload
                else:
                    cached_payload["cached"] = True
                    return cached_payload

            # Cache miss or bust - synthesize fresh
            try:
                segments = await self._resolve_segments(query, segment_ids, max_input)
            except Exception as exc:
                logger.warning(f"search/answer: segment resolution failed: {exc}")
                await self._safe_rollback()
                segments = []
            if len(segments) < MIN_SEGMENTS_FOR_ANSWER:
                # Not enough evidence - don't cache negatives, cheap to recheck
                return unavailable

            started = time.perf_counter()
            coverage_summary = await self._build_coverage_summary(query, segment_ids)
            social_context, social_prompt_block = await self._build_social_context(query)
            llm_out = await self._synthesize(
                query,
                segments,
                {s["id"] for s in segments},
                coverage_summary=coverage_summary,
                social_prompt_block=social_prompt_block,
            )
            duration_ms = (time.perf_counter() - started) * 1000.0

            if llm_out is None:
                return unavailable

            payload = {
                "query": query,
                "summary": llm_out["summary"],
                "key_points": llm_out["key_points"],
                "citations": map_citations(llm_out["cited_segment_ids"], segments),
                "source_segment_ids": [s["id"] for s in segments],
                "available": True,
                "cached": False,
                "social_context": [social_context] if social_context else [],
            }
            await self._write_cache(qhash, query, payload, duration_ms)
            return payload

    async def _resolve_segments(
        self,
        query: str,
        segment_ids: list[str] | None,
        max_input: int,
    ) -> list[dict[str, Any]]:
        """Fetch metadata for the given segment ids (client-ranked order), or
        fall back to a fresh hybrid retrieval when none are supplied."""
        if segment_ids:
            try:
                import uuid as uuid_mod

                valid_uuids = [uuid_mod.UUID(s) for s in segment_ids]
            except ValueError:
                logger.warning("search/answer: invalid segment id supplied")
                return []

            stmt = (
                select(TranscriptSegment, Video.title, Video.youtube_video_id, Channel.title)
                .join(Video, TranscriptSegment.video_id == Video.id)
                .join(Channel, Video.channel_id == Channel.id)
                .where(TranscriptSegment.id.in_(valid_uuids))
            )
            res = await self.db.execute(stmt)
            rows = res.all()

            by_id = {
                str(seg.id): {
                    "id": str(seg.id),
                    "video_id": str(seg.video_id),
                    "start_sec": seg.start_sec,
                    "end_sec": seg.end_sec,
                    "text": seg.text,
                    "video_title": title,
                    "channel_title": channel_title,
                    "youtube_video_id": youtube_id,
                }
                for seg, title, youtube_id, channel_title in rows
            }
            # Preserve caller-supplied ranking order, capped at max_input
            return [by_id[sid] for sid in segment_ids if sid in by_id][:max_input]

        # No ids provided - derive top fused-rank segments server-side
        search_service = SearchService(self.db, self.embedding_provider)
        results = await search_service.hybrid_search(query, limit=max_input)
        return list(results.get("segments", []))[:max_input]

    async def _build_coverage_summary(
        self,
        query: str,
        segment_ids: list[str] | None,
    ) -> str | None:
        """Best-effort coverage context for the synthesis prompt. Never raises."""
        if self.coverage_service is None:
            return None
        try:
            payload = await self.coverage_service.get_or_create(query, segment_ids)
            return format_coverage_for_prompt(payload)
        except Exception as exc:
            logger.warning(f"search/answer: coverage context unavailable: {exc}")
            return None

    async def _build_social_context(
        self,
        query: str,
    ) -> tuple[dict[str, Any] | None, str | None]:
        """Best-effort TickerFlow social snapshot for the query's ticker.

        Returns (serialized_snapshot, prompt_block); (None, None) when the
        query has no ticker hint or social data is unavailable. Never raises.
        """
        if self.social_service is None:
            return None, None
        try:
            ticker = QueryRouter._extract_ticker_heuristic(query)
            if not ticker:
                return None, None
            snapshot = await self.social_service.get_snapshot(ticker)
            if snapshot is None:
                return None, None

            snapshot_dict = snapshot.model_dump(mode="json")
            # Attach 1-2 representative raw posts (highest engagement) if stored
            try:
                stmt = (
                    select(RawContent.text)
                    .where(RawContent.symbol == ticker)
                    .order_by(RawContent.engagement_score.desc())
                    .limit(2)
                )
                posts = (await self.db.execute(stmt)).scalars().all()
                if posts:
                    snapshot_dict["sample_posts"] = list(posts)
            except Exception as exc:  # noqa: BLE001 - posts are optional garnish
                logger.warning(f"search/answer: sample posts unavailable: {exc}")
                await self._safe_rollback()

            return snapshot_dict, build_social_prompt_block(snapshot_dict)
        except Exception as exc:
            logger.warning(f"search/answer: social context unavailable: {exc}")
            await self._safe_rollback()
            return None, None

    async def _synthesize(
        self,
        query: str,
        segments: list[dict[str, Any]],
        valid_ids: set[str],
        coverage_summary: str | None = None,
        social_prompt_block: str | None = None,
    ) -> dict[str, Any] | None:
        """Call the cheap LLM under a hard timeout; returns parsed output or None."""
        user_prompt = build_user_prompt(query, segments)
        if coverage_summary:
            user_prompt += (
                "\n\nAggregate coverage context:\n"
                f"{coverage_summary}\n"
                "You may reference this momentum data when relevant, "
                "but never invent numbers beyond it."
            )
        if social_prompt_block:
            user_prompt += (
                "\n\n"
                f"{social_prompt_block}\n"
                "You may reference this Reddit/X/News sentiment when relevant and "
                "attribute it to the corresponding platform; never invent numbers beyond it."
            )
        started = time.perf_counter()
        try:
            client = self._get_client()

            def _call() -> str | None:
                response = client.chat.completions.create(
                    model=ANSWER_MODEL,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": ANSWER_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.2,
                    max_completion_tokens=600,
                )
                content = response.choices[0].message.content
                usage = getattr(response, "usage", None)
                analytics.record_llm_usage(
                    provider="openai",
                    model=ANSWER_MODEL,
                    purpose="search_answer",
                    input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                    output_tokens=getattr(usage, "completion_tokens", 0) or 0,
                    duration_ms=(time.perf_counter() - started) * 1000.0,
                )
                return content

            content = await asyncio.wait_for(asyncio.to_thread(_call), timeout=LLM_TIMEOUT_SECONDS)
            return parse_llm_response(content or "", valid_ids)

        except TimeoutError:
            logger.warning(f"search/answer: synthesis timed out after {LLM_TIMEOUT_SECONDS}s")
            analytics.record_llm_usage(
                provider="openai",
                model=ANSWER_MODEL,
                purpose="search_answer",
                success=False,
                error_summary="timeout",
                duration_ms=(time.perf_counter() - started) * 1000.0,
            )
            return None
        except Exception as exc:
            logger.warning(f"search/answer: synthesis failed: {exc}")
            analytics.record_llm_usage(
                provider="openai",
                model=ANSWER_MODEL,
                purpose="search_answer",
                success=False,
                error_summary=str(exc)[:280],
                duration_ms=(time.perf_counter() - started) * 1000.0,
            )
            return None

    async def _safe_rollback(self) -> None:
        """Clear a poisoned transaction so the session stays usable."""
        try:
            await self.db.rollback()
        except Exception:  # noqa: BLE001 - rollback is best-effort
            pass

    async def _read_cache(self, qhash: str) -> dict[str, Any] | None:
        """Return a fresh cached payload, or None (lazily dropping stale rows)."""
        try:
            stmt = select(SearchAnswer).where(SearchAnswer.query_hash == qhash)
            row = (await self.db.execute(stmt)).scalar_one_or_none()
        except Exception as exc:
            logger.warning(f"search/answer: cache read failed: {exc}")
            await self._safe_rollback()
            return None

        if row is None:
            return None
        created = row.created_at if row.created_at.tzinfo else row.created_at.replace(tzinfo=UTC)
        if datetime.now(UTC) - created > CACHE_TTL:
            try:
                await self.db.execute(delete(SearchAnswer).where(SearchAnswer.query_hash == qhash))
                await self.db.commit()
            except Exception as exc:
                logger.warning(f"search/answer: stale cache eviction failed: {exc}")
                await self._safe_rollback()
            return None
        payload = dict(row.answer_json)
        payload.pop("cached", None)
        # Retrofit sanitization for legacy cached rows that still contain UUID brackets
        try:
            citations = payload.get("citations") or []
            cited_ids = [c.get("segment_id") for c in citations if c.get("segment_id")]
            if payload.get("summary"):
                payload["summary"] = sanitize_citation_text(payload["summary"], cited_ids)
            if payload.get("key_points"):
                payload["key_points"] = [
                    sanitize_citation_text(kp, cited_ids) for kp in payload["key_points"]
                ]
                payload["key_points"] = [kp for kp in payload["key_points"] if kp]
        except Exception:  # noqa: BLE001 - sanitization must never break cache reads
            pass
        return payload

    async def _write_cache(
        self,
        qhash: str,
        query: str,
        payload: dict[str, Any],
        duration_ms: float,
    ) -> None:
        """Best-effort cache write; failures never surface to the caller."""
        try:
            await self.db.execute(delete(SearchAnswer).where(SearchAnswer.query_hash == qhash))
            self.db.add(SearchAnswer(query_hash=qhash, query_text=query[:500], answer_json=payload))
            await self.db.commit()
            analytics.record_event(
                "search_answer_synthesized",
                payload={
                    "duration_ms": round(duration_ms, 1),
                    "citation_count": len(payload.get("citations", [])),
                    "key_point_count": len(payload.get("key_points", [])),
                },
            )
        except Exception as exc:
            logger.warning(f"search/answer: cache write failed: {exc}")
            await self.db.rollback()
