"""Search service — hybrid keyword + semantic search via PostgreSQL."""

import logging
import uuid as uuid_mod

from sqlalchemy import func, select, text
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.prediction import Prediction
from src.models.speaker_ticker import SpeakerTickerAggregation
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

    async def search_ticker_narrative(self, ticker: str) -> list[dict]:
        """Get aggregated narrative intelligence for a specific ticker.

        Directly queries structured data (predictions, themes, aggregation stats)
        rather than doing text search. Returns a single-item list with the
        StockDiscoveryResult-compatible dict for the ticker.

        This solves the problem where "Microsoft narrative" fails text search
        because predictions are tagged with ticker "MSFT", not the word "Microsoft".
        """
        ticker = ticker.upper()

        # --- Get predictions for this ticker ---
        pred_stmt = select(Prediction).where(
            Prediction.ticker == ticker
        ).order_by(Prediction.created_at.desc())
        pred_result = await self.db.execute(pred_stmt)
        predictions = pred_result.scalars().all()

        # --- Get aggregation stats ---
        agg_stmt = select(SpeakerTickerAggregation).where(
            SpeakerTickerAggregation.ticker == ticker
        )
        agg_result = await self.db.execute(agg_stmt)
        aggregations = agg_result.scalars().all()

        total_mentions = sum(a.total_mentions or 0 for a in aggregations)
        avg_sentiment = 0.0
        last_mentioned = None
        if aggregations:
            sentiments = [a.avg_sentiment for a in aggregations if a.avg_sentiment is not None]
            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
            dates = [a.last_mentioned_at for a in aggregations if a.last_mentioned_at]
            last_mentioned = max(dates) if dates else None

        # --- Get themes linked to this ticker ---
        theme_stmt = (
            select(ThemeHierarchy.name)
            .join(ThemeTickerMapping, ThemeTickerMapping.theme_id == ThemeHierarchy.id)
            .where(ThemeTickerMapping.ticker == ticker)
            .distinct()
        )
        theme_result = await self.db.execute(theme_stmt)
        themes = [row[0] for row in theme_result.all()]

        # --- Compute stats ---
        sample_predictions = []
        for pred in predictions[:3]:
            sample_predictions.append({
                "text": pred.prediction_text[:200],
                "direction": pred.direction,
                "confidence": pred.confidence,
            })

        prediction_count = len(predictions)
        confidences = [p.confidence for p in predictions if p.confidence is not None]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        directions = [p.direction for p in predictions if p.direction]
        bullish_pct = 0.0
        bearish_pct = 0.0
        if directions:
            bullish_pct = round(sum(1 for d in directions if d == "bullish") / len(directions) * 100)
            bearish_pct = round(sum(1 for d in directions if d == "bearish") / len(directions) * 100)

        # --- Compute composite score ---
        import math
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        mention_score = min(math.log1p(total_mentions) / 5.0, 1.0)
        sentiment_score = abs(avg_sentiment)
        confidence_score = avg_confidence
        recency_score = 0.3
        if last_mentioned:
            days_ago = (now - last_mentioned.replace(tzinfo=timezone.utc)).days
            recency_score = max(0.1, 1.0 - (days_ago / 90.0))

        composite_score = round(
            (mention_score * 0.30)
            + (sentiment_score * 0.20)
            + (confidence_score * 0.20)
            + (recency_score * 0.15)
            + (0.15 if prediction_count > 0 else 0.0),  # bonus for having predictions
            4,
        )

        return [{
            "ticker": ticker,
            "composite_score": composite_score,
            "theme_relevance": len(themes) * 0.5,
            "themes": themes,
            "mention_count": total_mentions,
            "avg_sentiment": avg_sentiment,
            "prediction_count": prediction_count,
            "avg_confidence": avg_confidence,
            "bullish_pct": bullish_pct,
            "bearish_pct": bearish_pct,
            "sample_predictions": sample_predictions,
            "last_mentioned_at": last_mentioned.isoformat() if last_mentioned else None,
        }]

    async def search_stocks_for_query(
        self, query: str, sector_hint: str | None = None, limit: int = 10
    ) -> list[dict]:
        """Aggregated stock discovery search — finds top tickers for a sector/theme query.

        Multi-signal scoring combines:
        1. Theme relevance (keyword + semantic matching against theme taxonomy)
        2. Mention frequency (from SpeakerTickerAggregation across all channels)
        3. Sentiment strength (bullish/bearish direction)
        4. Prediction confidence (average confidence of predictions for this ticker)
        5. Recency (more recently discussed tickers get a boost)

        Args:
            query: The user's search query
            sector_hint: Optional sector/industry/theme hint from query router
            limit: Max results to return
        """
        search_text = sector_hint or query

        # --- Step 1: Find matching themes (keyword + semantic) ---
        matched_themes = await self._match_themes(search_text)

        if not matched_themes:
            logger.info(f"No themes matched for stock discovery query: '{query}'")
            return []

        theme_ids = [t["id"] for t in matched_themes]
        theme_names_map = {t["id"]: t["name"] for t in matched_themes}

        # --- Step 2: Get ticker mappings from matched themes ---
        ticker_stmt = select(ThemeTickerMapping).where(
            ThemeTickerMapping.theme_id.in_(theme_ids)
        )
        ticker_result = await self.db.execute(ticker_stmt)
        mappings = ticker_result.scalars().all()

        if not mappings:
            logger.info(f"No ticker mappings found for matched themes")
            return []

        # Build initial ticker data from theme mappings
        ticker_data: dict[str, dict] = {}
        for mapping in mappings:
            ticker = mapping.ticker.upper()
            if ticker not in ticker_data:
                ticker_data[ticker] = {
                    "ticker": ticker,
                    "theme_relevance": 0.0,
                    "themes": [],
                    "mention_count": 0,
                    "avg_sentiment": 0.0,
                    "prediction_count": 0,
                    "avg_confidence": 0.0,
                    "bullish_pct": 0.0,
                    "bearish_pct": 0.0,
                    "sample_predictions": [],
                    "last_mentioned_at": None,
                }
            ticker_data[ticker]["theme_relevance"] += mapping.relevance_score or 0.5
            theme_name = theme_names_map.get(mapping.theme_id)
            if theme_name and theme_name not in ticker_data[ticker]["themes"]:
                ticker_data[ticker]["themes"].append(theme_name)

        # --- Step 3: Enrich with aggregation stats (mentions, sentiment, recency) ---
        all_tickers = list(ticker_data.keys())
        agg_stmt = select(SpeakerTickerAggregation).where(
            SpeakerTickerAggregation.ticker.in_(all_tickers)
        )
        agg_result = await self.db.execute(agg_stmt)
        aggregations = agg_result.scalars().all()

        # Aggregate across all channels for each ticker
        for agg in aggregations:
            ticker = agg.ticker.upper()
            if ticker in ticker_data:
                ticker_data[ticker]["mention_count"] += agg.total_mentions or 0
                if agg.avg_sentiment is not None:
                    ticker_data[ticker]["avg_sentiment"] = agg.avg_sentiment
                if agg.last_mentioned_at:
                    current = ticker_data[ticker]["last_mentioned_at"]
                    if current is None or agg.last_mentioned_at > current:
                        ticker_data[ticker]["last_mentioned_at"] = agg.last_mentioned_at

        # --- Step 4: Enrich with prediction data ---
        pred_stmt = select(Prediction).where(
            Prediction.ticker.in_(all_tickers)
        )
        pred_result = await self.db.execute(pred_stmt)
        predictions = pred_result.scalars().all()

        for pred in predictions:
            ticker = pred.ticker.upper()
            if ticker in ticker_data:
                ticker_data[ticker]["prediction_count"] += 1
                if len(ticker_data[ticker]["sample_predictions"]) < 2:
                    ticker_data[ticker]["sample_predictions"].append({
                        "text": pred.prediction_text[:200],
                        "direction": pred.direction,
                        "confidence": pred.confidence,
                    })

        # Compute avg confidence and sentiment percentages
        for ticker in all_tickers:
            td = ticker_data[ticker]
            preds_for_ticker = [p for p in predictions if p.ticker and p.ticker.upper() == ticker]
            if preds_for_ticker:
                confidences = [p.confidence for p in preds_for_ticker if p.confidence is not None]
                td["avg_confidence"] = sum(confidences) / len(confidences) if confidences else 0.0

                directions = [p.direction for p in preds_for_ticker if p.direction]
                if directions:
                    td["bullish_pct"] = round(
                        sum(1 for d in directions if d == "bullish") / len(directions) * 100
                    )
                    td["bearish_pct"] = round(
                        sum(1 for d in directions if d == "bearish") / len(directions) * 100
                    )

        # --- Step 5: Compute composite score ---
        import math
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        for ticker, td in ticker_data.items():
            # Normalize components to 0-1 range
            theme_score = min(td["theme_relevance"] / 3.0, 1.0)  # cap at 3.0
            mention_score = min(math.log1p(td["mention_count"]) / 5.0, 1.0)  # log scale, cap
            sentiment_score = abs(td["avg_sentiment"])  # 0-1, strength of conviction
            confidence_score = td["avg_confidence"]  # 0-1

            # Recency score: 1.0 for today, decaying to 0.1 over 90 days
            recency_score = 0.3  # default if no date
            if td["last_mentioned_at"]:
                days_ago = (now - td["last_mentioned_at"].replace(tzinfo=timezone.utc)).days
                recency_score = max(0.1, 1.0 - (days_ago / 90.0))

            # Weighted composite: theme relevance matters most, then mentions + sentiment
            td["composite_score"] = round(
                (theme_score * 0.30)
                + (mention_score * 0.25)
                + (sentiment_score * 0.15)
                + (confidence_score * 0.15)
                + (recency_score * 0.15),
                4,
            )

            # Serialize datetime for JSON
            td["last_mentioned_at"] = (
                td["last_mentioned_at"].isoformat() if td["last_mentioned_at"] else None
            )

        # Sort by composite score and return top N
        sorted_tickers = sorted(
            ticker_data.values(),
            key=lambda x: x["composite_score"],
            reverse=True,
        )
        return sorted_tickers[:limit]

    async def _match_themes(self, search_text: str) -> list[dict]:
        """Find themes matching the search text using keyword + semantic search.

        Returns list of {"id": uuid, "name": str, "score": float} dicts.
        """
        matched: dict[str, dict] = {}  # keyed by theme id string

        # --- Keyword matching ---
        ts_query = func.plainto_tsquery("english", search_text)
        keyword_stmt = (
            select(ThemeHierarchy)
            .where(
                func.to_tsvector(
                    "english",
                    func.coalesce(ThemeHierarchy.name, "")
                    + " "
                    + func.coalesce(ThemeHierarchy.description, ""),
                ).op("@@")(ts_query)
            )
            .limit(20)
        )
        keyword_result = await self.db.execute(keyword_stmt)
        for theme in keyword_result.scalars().all():
            tid = str(theme.id)
            matched[tid] = {"id": theme.id, "name": theme.name, "score": 1.0}

        # --- Semantic matching (embed query, compare against theme names) ---
        try:
            # Get all themes with their names for semantic comparison
            all_themes_stmt = select(ThemeHierarchy).where(
                ThemeHierarchy.level.in_(["theme", "industry"])
            )
            all_themes_result = await self.db.execute(all_themes_stmt)
            all_themes = all_themes_result.scalars().all()

            if all_themes:
                # Embed the query
                query_embeddings = await self.embedding_provider.embed([search_text])
                query_vec = query_embeddings[0]

                # Embed all theme names (batch)
                theme_texts = [
                    f"{t.name}: {t.description or ''}" for t in all_themes
                ]
                theme_embeddings = await self.embedding_provider.embed(theme_texts)

                # Compute cosine similarity (pure Python, no numpy needed)
                import math as _math

                def _cosine_sim(a: list[float], b: list[float]) -> float:
                    dot = sum(x * y for x, y in zip(a, b))
                    norm_a = _math.sqrt(sum(x * x for x in a))
                    norm_b = _math.sqrt(sum(x * x for x in b))
                    return dot / (norm_a * norm_b + 1e-8)

                for theme, theme_emb in zip(all_themes, theme_embeddings):
                    similarity = _cosine_sim(query_vec, theme_emb)
                    if similarity > 0.4:  # threshold for relevance
                        tid = str(theme.id)
                        if tid not in matched or similarity > matched[tid]["score"]:
                            matched[tid] = {
                                "id": theme.id,
                                "name": theme.name,
                                "score": similarity,
                            }
        except Exception as e:
            logger.warning(f"Semantic theme matching failed, using keyword results only: {e}")

        return list(matched.values())
