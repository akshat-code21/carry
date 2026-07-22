"""Aggregation service — speaker-ticker stats and top stocks computation."""

import logging
import uuid as uuid_mod
from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.prediction import Prediction
from src.models.speaker_ticker import SpeakerTickerAggregation
from src.models.theme import ThemeMention, ThemeTickerMapping
from src.models.video import Video

logger = logging.getLogger(__name__)


class AggregationService:
    """Computes and maintains speaker-ticker aggregation stats and top stocks rankings."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def update_channel_aggregation(self, channel_id: uuid_mod.UUID) -> None:
        """Recompute the speaker_ticker_aggregation table for a channel.

        Aggregates across all processed videos for the channel, counting both
        explicit ticker mentions (from predictions) and implicit mentions
        (from theme→ticker mappings).
        """
        # Get all processed videos for this channel
        video_result = await self.db.execute(
            select(Video).where(
                Video.channel_id == channel_id,
                Video.processed.is_(True),
            )
        )
        videos = video_result.scalars().all()
        video_ids = [v.id for v in videos]

        if not video_ids:
            return

        # Count explicit mentions (tickers mentioned in predictions)
        explicit_counts: dict[str, dict] = {}
        pred_result = await self.db.execute(
            select(Prediction).where(
                Prediction.video_id.in_(video_ids),
                Prediction.ticker.isnot(None),
            )
        )
        for pred in pred_result.scalars().all():
            ticker = pred.ticker.upper()
            if ticker not in explicit_counts:
                explicit_counts[ticker] = {
                    "count": 0,
                    "sentiments": [],
                    "last_mentioned": None,
                }
            explicit_counts[ticker]["count"] += 1
            if pred.direction:
                explicit_counts[ticker]["sentiments"].append(pred.direction)
            video = next((v for v in videos if v.id == pred.video_id), None)
            if video and video.published_at:
                current_last = explicit_counts[ticker]["last_mentioned"]
                if current_last is None or video.published_at > current_last:
                    explicit_counts[ticker]["last_mentioned"] = video.published_at

        # Count implicit mentions (from theme_mentions → theme_ticker_mappings)
        implicit_counts: dict[str, dict] = {}
        mention_result = await self.db.execute(
            select(ThemeMention).where(ThemeMention.video_id.in_(video_ids))
        )
        mentions = mention_result.scalars().all()

        for mention in mentions:
            # Get ticker mappings for this theme
            ticker_result = await self.db.execute(
                select(ThemeTickerMapping).where(
                    ThemeTickerMapping.theme_id == mention.theme_id
                )
            )
            for mapping in ticker_result.scalars().all():
                ticker = mapping.ticker.upper()
                if ticker not in implicit_counts:
                    implicit_counts[ticker] = {
                        "count": 0,
                        "relevance_sum": 0.0,
                        "sentiments": [],
                    }
                implicit_counts[ticker]["count"] += 1
                implicit_counts[ticker]["relevance_sum"] += (
                    mapping.relevance_score or 0.5
                )
                if mention.sentiment:
                    implicit_counts[ticker]["sentiments"].append(mention.sentiment)

        # Merge and upsert aggregations
        all_tickers = set(explicit_counts.keys()) | set(implicit_counts.keys())

        for ticker in all_tickers:
            explicit = explicit_counts.get(ticker, {"count": 0, "sentiments": [], "last_mentioned": None})
            implicit = implicit_counts.get(ticker, {"count": 0, "relevance_sum": 0.0, "sentiments": []})

            total = explicit["count"] + implicit["count"]
            all_sentiments = explicit["sentiments"] + implicit["sentiments"]
            avg_sentiment = self._compute_avg_sentiment(all_sentiments)
            weighted_relevance = (
                implicit["relevance_sum"] / implicit["count"]
                if implicit["count"] > 0
                else 0.5
            )

            # Upsert
            existing_result = await self.db.execute(
                select(SpeakerTickerAggregation).where(
                    SpeakerTickerAggregation.channel_id == channel_id,
                    SpeakerTickerAggregation.ticker == ticker,
                )
            )
            existing = existing_result.scalar_one_or_none()

            if existing:
                existing.total_mentions = total
                existing.explicit_mentions = explicit["count"]
                existing.implicit_mentions = implicit["count"]
                existing.avg_sentiment = avg_sentiment
                existing.weighted_relevance = weighted_relevance
                existing.last_mentioned_at = explicit.get("last_mentioned")
            else:
                agg = SpeakerTickerAggregation(
                    channel_id=channel_id,
                    ticker=ticker,
                    total_mentions=total,
                    explicit_mentions=explicit["count"],
                    implicit_mentions=implicit["count"],
                    avg_sentiment=avg_sentiment,
                    weighted_relevance=weighted_relevance,
                    last_mentioned_at=explicit.get("last_mentioned"),
                )
                self.db.add(agg)

        await self.db.flush()

    async def get_channel_top_stocks(
        self, channel_id: uuid_mod.UUID, limit: int = 20
    ) -> list[dict]:
        """Get top stocks for a channel ranked by weighted_relevance × total_mentions × |avg_sentiment|."""
        result = await self.db.execute(
            select(SpeakerTickerAggregation).where(
                SpeakerTickerAggregation.channel_id == channel_id
            )
        )
        aggregations = result.scalars().all()

        # Rank by the formula from plan_1.md
        ranked = sorted(
            aggregations,
            key=lambda a: (
                (a.weighted_relevance or 0)
                * (a.total_mentions or 0)
                * abs(a.avg_sentiment or 0)
            ),
            reverse=True,
        )

        return [
            {
                "ticker": a.ticker,
                "total_mentions": a.total_mentions,
                "explicit_mentions": a.explicit_mentions,
                "implicit_mentions": a.implicit_mentions,
                "avg_sentiment": a.avg_sentiment,
                "weighted_relevance": a.weighted_relevance,
                "last_mentioned_at": (
                    a.last_mentioned_at.isoformat() if a.last_mentioned_at else None
                ),
            }
            for a in ranked[:limit]
        ]

    async def get_video_top_stocks(
        self, video_id: uuid_mod.UUID, limit: int = 10
    ) -> list[dict]:
        """Get top stocks for a specific video based on theme mentions and predictions."""
        ticker_scores: dict[str, dict] = {}

        # From predictions
        pred_result = await self.db.execute(
            select(Prediction).where(
                Prediction.video_id == video_id,
                Prediction.ticker.isnot(None),
            )
        )
        for pred in pred_result.scalars().all():
            ticker = pred.ticker.upper()
            if ticker not in ticker_scores:
                ticker_scores[ticker] = {
                    "ticker": ticker,
                    "mentions": 0,
                    "sentiment": [],
                    "source": "explicit",
                }
            ticker_scores[ticker]["mentions"] += 1
            if pred.direction:
                ticker_scores[ticker]["sentiment"].append(pred.direction)

        # From theme mentions → ticker mappings
        mention_result = await self.db.execute(
            select(ThemeMention).where(ThemeMention.video_id == video_id)
        )
        for mention in mention_result.scalars().all():
            ticker_result = await self.db.execute(
                select(ThemeTickerMapping).where(
                    ThemeTickerMapping.theme_id == mention.theme_id
                )
            )
            for mapping in ticker_result.scalars().all():
                ticker = mapping.ticker.upper()
                if ticker not in ticker_scores:
                    ticker_scores[ticker] = {
                        "ticker": ticker,
                        "mentions": 0,
                        "sentiment": [],
                        "source": "implicit",
                    }
                ticker_scores[ticker]["mentions"] += 1
                if mention.sentiment:
                    ticker_scores[ticker]["sentiment"].append(mention.sentiment)

        # Compute avg sentiment and sort
        results = []
        for ticker_data in ticker_scores.values():
            avg_sent = self._compute_avg_sentiment(ticker_data["sentiment"])
            results.append(
                {
                    "ticker": ticker_data["ticker"],
                    "mentions": ticker_data["mentions"],
                    "avg_sentiment": avg_sent,
                    "source": ticker_data["source"],
                }
            )

        results.sort(key=lambda x: x["mentions"], reverse=True)
        return results[:limit]

    async def get_ticker_daily_sentiment(
        self, ticker: str, days: int | None = None
    ) -> list[dict]:
        """Get daily bullish/bearish/neutral mention counts for a ticker.

        Combines explicit mentions (Prediction.direction, tied directly to
        the ticker) and implicit mentions (ThemeMention.sentiment, tied to
        the ticker via ThemeTickerMapping), grouped by the calendar date of
        the mentioning video's published_at.
        """
        ticker = ticker.upper()
        daily_counts: dict[date, dict[str, int]] = {}

        def _bump(day: date | None, sentiment: str | None) -> None:
            if day is None:
                return
            bucket = daily_counts.setdefault(
                day, {"bullish": 0, "bearish": 0, "neutral": 0}
            )
            key = (sentiment or "neutral").lower()
            if key not in bucket:
                key = "neutral"
            bucket[key] += 1

        # Explicit mentions: predictions directly tagged with this ticker
        pred_result = await self.db.execute(
            select(Prediction, Video.published_at)
            .join(Video, Prediction.video_id == Video.id)
            .where(Prediction.ticker == ticker)
        )
        for pred, published_at in pred_result.all():
            _bump(published_at.date() if published_at else None, pred.direction)

        # Implicit mentions: theme mentions mapped to this ticker
        mapping_result = await self.db.execute(
            select(ThemeTickerMapping.theme_id).where(
                ThemeTickerMapping.ticker == ticker
            )
        )
        theme_ids = [row[0] for row in mapping_result.all()]

        if theme_ids:
            mention_result = await self.db.execute(
                select(ThemeMention, Video.published_at)
                .join(Video, ThemeMention.video_id == Video.id)
                .where(ThemeMention.theme_id.in_(theme_ids))
            )
            for mention, published_at in mention_result.all():
                _bump(
                    published_at.date() if published_at else None,
                    mention.sentiment,
                )

        if days is not None:
            cutoff = datetime.utcnow().date() - timedelta(days=days)
            daily_counts = {d: c for d, c in daily_counts.items() if d >= cutoff}

        return [
            {
                "date": d.isoformat(),
                "bullish_count": counts["bullish"],
                "bearish_count": counts["bearish"],
                "neutral_count": counts["neutral"],
                "total_count": counts["bullish"] + counts["bearish"] + counts["neutral"],
            }
            for d, counts in sorted(daily_counts.items())
        ]

    @staticmethod
    def _compute_avg_sentiment(sentiments: list[str]) -> float:
        """Compute average sentiment from a list of sentiment strings.

        bullish = +1, bearish = -1, neutral = 0.
        Returns value between -1 and +1.
        """
        if not sentiments:
            return 0.0

        sentiment_map = {"bullish": 1.0, "bearish": -1.0, "neutral": 0.0}
        values = [sentiment_map.get(s.lower(), 0.0) for s in sentiments]
        return sum(values) / len(values)
