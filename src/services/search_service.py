"""Search service — hybrid keyword + semantic search via PostgreSQL."""

import logging
import uuid as uuid_mod

from sqlalchemy import func, select, text
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.prediction import Prediction
from src.models.theme import ThemeHierarchy, ThemeMention, ThemeTickerMapping
from src.models.transcript_segment import TranscriptSegment
from src.models.video import Video
from src.services.interfaces import EmbeddingProvider

logger = logging.getLogger(__name__)


class SearchService:
    """Hybrid search combining PostgreSQL full-text search (tsvector) and pgvector semantic search."""

    def __init__(self, db: AsyncSession, embedding_provider: EmbeddingProvider) -> None:
        self.db = db
        self.embedding_provider = embedding_provider

    async def hybrid_search(
        self,
        query: str,
        search_type: str = "hybrid",
        channel_id: uuid_mod.UUID | None = None,
        ticker: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """Perform hybrid search across transcript segments and predictions.

        Args:
            query: Search query string
            search_type: "keyword", "semantic", or "hybrid"
            channel_id: Optional filter by channel
            ticker: Optional filter by ticker
            limit: Max results
            offset: Pagination offset

        Returns:
            Dict with segments, predictions, and total count
        """
        results = {
            "segments": [],
            "predictions": [],
            "total": 0,
        }

        if search_type in ("keyword", "hybrid"):
            keyword_segments = await self._keyword_search_segments(
                query, channel_id, limit, offset
            )
            keyword_predictions = await self._keyword_search_predictions(
                query, ticker, limit, offset
            )
            results["segments"].extend(keyword_segments)
            results["predictions"].extend(keyword_predictions)

        if search_type in ("semantic", "hybrid"):
            semantic_segments = await self._semantic_search_segments(
                query, channel_id, limit, offset
            )
            results["segments"].extend(semantic_segments)

        # Deduplicate segments by ID
        seen_ids = set()
        unique_segments = []
        for seg in results["segments"]:
            if seg["id"] not in seen_ids:
                seen_ids.add(seg["id"])
                unique_segments.append(seg)
        results["segments"] = unique_segments[:limit]

        # Deduplicate predictions by ID
        seen_pred_ids = set()
        unique_preds = []
        for pred in results["predictions"]:
            if pred["id"] not in seen_pred_ids:
                seen_pred_ids.add(pred["id"])
                unique_preds.append(pred)
        results["predictions"] = unique_preds[:limit]

        # Fetch Video and Channel metadata for all matched items
        video_uuid_strings = list(
            {s["video_id"] for s in results["segments"] if s.get("video_id")}
            | {p["video_id"] for p in results["predictions"] if p.get("video_id")}
        )

        videos_map = {}
        channels_map = {}

        if video_uuid_strings:
            try:
                valid_uuids = [uuid_mod.UUID(v_id) for v_id in video_uuid_strings]
                stmt = (
                    select(Video)
                    .options(joinedload(Video.channel))
                    .where(Video.id.in_(valid_uuids))
                )
                res = await self.db.execute(stmt)
                videos_db = res.scalars().unique().all()

                for v in videos_db:
                    v_id_str = str(v.id)
                    c_id_str = str(v.channel_id) if v.channel_id else None

                    if v.channel and c_id_str:
                        channels_map[c_id_str] = {
                            "id": c_id_str,
                            "youtube_channel_id": v.channel.youtube_channel_id,
                            "title": v.channel.title,
                            "thumbnail_url": v.channel.thumbnail_url,
                        }

                    videos_map[v_id_str] = {
                        "id": v_id_str,
                        "channel_id": c_id_str,
                        "youtube_video_id": v.youtube_video_id,
                        "title": v.title,
                        "thumbnail_url": v.thumbnail_url,
                        "published_at": (
                            v.published_at.isoformat() if v.published_at else None
                        ),
                    }
            except Exception as exc:
                logger.warning(f"Error loading video metadata for search: {exc}")

        # Attach video & channel titles directly to segments and predictions
        for seg in results["segments"]:
            v_info = videos_map.get(seg["video_id"], {})
            c_info = channels_map.get(v_info.get("channel_id"), {})
            seg["video_title"] = v_info.get("title")
            seg["channel_title"] = c_info.get("title")
            seg["youtube_video_id"] = v_info.get("youtube_video_id")
            seg["thumbnail_url"] = v_info.get("thumbnail_url")

        for pred in results["predictions"]:
            v_info = videos_map.get(pred["video_id"], {})
            c_info = channels_map.get(v_info.get("channel_id"), {})
            pred["video_title"] = v_info.get("title")
            pred["channel_title"] = c_info.get("title")
            pred["youtube_video_id"] = v_info.get("youtube_video_id")

        results["videos"] = videos_map
        results["channels"] = channels_map
        results["total"] = len(results["segments"]) + len(results["predictions"])
        return results

    async def _keyword_search_segments(
        self,
        query: str,
        channel_id: uuid_mod.UUID | None,
        limit: int,
        offset: int,
    ) -> list[dict]:
        """Full-text search over transcript segments using PostgreSQL tsvector."""
        # Build the query using to_tsvector and plainto_tsquery
        ts_query = func.plainto_tsquery("english", query)

        stmt = (
            select(
                TranscriptSegment,
                func.ts_rank(
                    func.to_tsvector("english", TranscriptSegment.text),
                    ts_query,
                ).label("rank"),
            )
            .where(
                func.to_tsvector("english", TranscriptSegment.text).op("@@")(ts_query)
            )
            .order_by(text("rank DESC"))
            .limit(limit)
            .offset(offset)
        )

        if channel_id:
            stmt = stmt.join(Video, TranscriptSegment.video_id == Video.id).where(
                Video.channel_id == channel_id
            )

        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            {
                "id": str(seg.id),
                "video_id": str(seg.video_id),
                "start_sec": seg.start_sec,
                "end_sec": seg.end_sec,
                "text": seg.text,
                "rank": float(rank),
                "search_type": "keyword",
            }
            for seg, rank in rows
        ]

    async def _keyword_search_predictions(
        self,
        query: str,
        ticker: str | None,
        limit: int,
        offset: int,
    ) -> list[dict]:
        """Full-text search over predictions."""
        ts_query = func.plainto_tsquery("english", query)

        stmt = (
            select(
                Prediction,
                func.ts_rank(
                    func.to_tsvector("english", Prediction.prediction_text),
                    ts_query,
                ).label("rank"),
            )
            .where(
                func.to_tsvector("english", Prediction.prediction_text).op("@@")(
                    ts_query
                )
            )
            .order_by(text("rank DESC"))
            .limit(limit)
            .offset(offset)
        )

        if ticker:
            stmt = stmt.where(Prediction.ticker == ticker.upper())

        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            {
                "id": str(pred.id),
                "video_id": str(pred.video_id),
                "prediction_text": pred.prediction_text,
                "ticker": pred.ticker,
                "direction": pred.direction,
                "confidence": pred.confidence,
                "accurate": pred.accurate,
                "rank": float(rank),
                "search_type": "keyword",
            }
            for pred, rank in rows
        ]

    async def _semantic_search_segments(
        self,
        query: str,
        channel_id: uuid_mod.UUID | None,
        limit: int,
        offset: int,
    ) -> list[dict]:
        """Semantic search using pgvector cosine similarity."""
        # Generate embedding for the query
        embeddings = await self.embedding_provider.embed([query])
        query_embedding = embeddings[0]

        # Use pgvector's <=> operator for cosine distance
        stmt = (
            select(
                TranscriptSegment,
                TranscriptSegment.embedding.cosine_distance(query_embedding).label(
                    "distance"
                ),
            )
            .where(TranscriptSegment.embedding.isnot(None))
            .order_by(text("distance ASC"))
            .limit(limit)
            .offset(offset)
        )

        if channel_id:
            stmt = stmt.join(Video, TranscriptSegment.video_id == Video.id).where(
                Video.channel_id == channel_id
            )

        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            {
                "id": str(seg.id),
                "video_id": str(seg.video_id),
                "start_sec": seg.start_sec,
                "end_sec": seg.end_sec,
                "text": seg.text,
                "rank": 1.0 - float(distance),  # Convert distance to similarity
                "search_type": "semantic",
            }
            for seg, distance in rows
        ]

    async def search_stocks_for_query(
        self, query: str, limit: int = 10
    ) -> list[dict]:
        """Search for stocks relevant to a query by finding matching themes.

        Returns top tickers implied by the search query's themes.
        """
        # First, find matching themes via keyword search
        ts_query = func.plainto_tsquery("english", query)

        theme_stmt = (
            select(ThemeHierarchy)
            .where(
                func.to_tsvector(
                    "english",
                    func.coalesce(ThemeHierarchy.name, "")
                    + " "
                    + func.coalesce(ThemeHierarchy.description, ""),
                ).op("@@")(ts_query)
            )
            .limit(10)
        )

        result = await self.db.execute(theme_stmt)
        themes = result.scalars().all()

        if not themes:
            return []

        # Get ticker mappings for matched themes
        theme_ids = [t.id for t in themes]
        ticker_stmt = select(ThemeTickerMapping).where(
            ThemeTickerMapping.theme_id.in_(theme_ids)
        )
        ticker_result = await self.db.execute(ticker_stmt)
        mappings = ticker_result.scalars().all()

        # Aggregate by ticker
        ticker_scores: dict[str, dict] = {}
        for mapping in mappings:
            ticker = mapping.ticker
            if ticker not in ticker_scores:
                ticker_scores[ticker] = {
                    "ticker": ticker,
                    "total_relevance": 0.0,
                    "themes": [],
                }
            ticker_scores[ticker]["total_relevance"] += mapping.relevance_score or 0.5
            # Find the theme name
            for theme in themes:
                if theme.id == mapping.theme_id and theme.name not in ticker_scores[ticker]["themes"]:
                    ticker_scores[ticker]["themes"].append(theme.name)

        # Sort by relevance and return top N
        sorted_tickers = sorted(
            ticker_scores.values(),
            key=lambda x: x["total_relevance"],
            reverse=True,
        )
        return sorted_tickers[:limit]
