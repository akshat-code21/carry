"""CollectionService - main TickerFlow orchestrator.

Coordinates sentiment collection from multiple sources, caching, quota
management, price data, and signal computation.  Ported from market-chatter
with imports rewritten for the yt-chatter package layout.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.config import Settings
from src.models.collection_run import CollectionRun
from src.models.price_bar import PriceBarRecord
from src.models.quota_usage import QuotaUsage
from src.models.source_snapshot import SourceSnapshot
from src.models.ticker_daily_metric import TickerDailyMetric
from src.schemas.market_chatter import (
    SOURCE_WEIGHTS,
    ChartPoint,
    DailyMetric,
    MCTickerResponse,
    PriceBar,
    ProviderSnapshot,
    SignalSummary,
    SourceCard,
    SourceName,
)
from src.services.market_chatter.cache import JsonCache
from src.services.market_chatter.providers import (
    MarketSentimentProvider,
    PriceProvider,
    ProviderError,
)
from src.services.market_chatter.universe import is_supported_symbol, normalize_symbol


class UnsupportedTickerError(ValueError):
    pass


@dataclass
class CollectionOutcome:
    snapshots: dict[SourceName, ProviderSnapshot]
    statuses: dict[SourceName, str]
    errors: dict[SourceName, str]
    request_count: int
    quota_limited: bool


def utcnow() -> datetime:
    return datetime.now(UTC)


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class QuotaManager:
    def __init__(self, settings: Settings) -> None:
        self._limit = settings.adanos_monthly_budget

    @staticmethod
    def _period() -> str:
        return utcnow().strftime("%Y-%m")

    async def reserve(self, session: AsyncSession, count: int = 1) -> bool:
        """Atomically reserve calls so concurrent API requests cannot overspend."""
        statement = text(
            """
            INSERT INTO quota_usage (provider, period, used_requests)
            VALUES ('adanos', :period, :count)
            ON CONFLICT (provider, period) DO UPDATE
              SET used_requests = quota_usage.used_requests + :count
              WHERE quota_usage.used_requests + :count <= :quota_limit
            RETURNING used_requests
            """
        )
        result = await session.execute(
            statement,
            {"period": self._period(), "count": count, "quota_limit": self._limit},
        )
        return result.scalar_one_or_none() is not None

    async def remaining(self, session: AsyncSession) -> int:
        usage = await session.scalar(
            select(QuotaUsage.used_requests).where(
                QuotaUsage.provider == "adanos", QuotaUsage.period == self._period()
            )
        )
        return max(0, self._limit - (usage or 0))


class CollectionService:
    def __init__(
        self,
        settings: Settings,
        session_factory: async_sessionmaker[AsyncSession],
        cache: JsonCache,
        sentiment_provider: MarketSentimentProvider,
        price_provider: PriceProvider,
    ) -> None:
        self._settings = settings
        self._session_factory = session_factory
        self._cache = cache
        self._sentiment_provider = sentiment_provider
        self._price_provider = price_provider
        self._quota = QuotaManager(settings)

    def _assert_supported(self, symbol: str) -> str:
        normalized = normalize_symbol(symbol)
        if not is_supported_symbol(normalized):
            raise UnsupportedTickerError(f"{normalized} is not in the configured S&P 100 universe")
        return normalized

    def _cache_key(self, symbol: str, source: SourceName) -> str:
        return f"source-snapshot:{symbol}:{source.value}"

    def _is_fresh(self, fetched_at: datetime, source: SourceName) -> bool:
        return utcnow() - _as_utc(fetched_at) <= timedelta(
            seconds=self._settings.source_ttl_seconds(source.value)
        )

    def _collection_period_days(self) -> int:
        return max(30, self._settings.adanos_collection_days)

    @staticmethod
    def _history_start(period_days: int) -> date:
        return datetime.now(UTC).date() - timedelta(days=period_days - 1)

    @staticmethod
    def _from_record(record: SourceSnapshot) -> ProviderSnapshot:
        return ProviderSnapshot(
            symbol=record.symbol,
            company_name=record.company_name,
            source=SourceName(record.source),
            found=record.found,
            buzz_score=record.buzz_score,
            mentions=record.mentions,
            sentiment_score=record.sentiment_score,
            bullish_pct=record.bullish_pct,
            bearish_pct=record.bearish_pct,
            trend=record.trend,
            unique_posts=record.unique_posts,
            coverage_count=record.coverage_count,
            daily_trend=[],
            fetched_at=_as_utc(record.fetched_at),
            raw_payload=record.raw_payload,
        )

    async def _latest_snapshot(
        self, session: AsyncSession, symbol: str, source: SourceName
    ) -> ProviderSnapshot | None:
        cache_payload = await self._cache.get(self._cache_key(symbol, source))
        if cache_payload:
            try:
                return ProviderSnapshot.model_validate(cache_payload)
            except Exception:
                pass
        record = await session.scalar(
            select(SourceSnapshot)
            .where(
                SourceSnapshot.symbol == symbol,
                SourceSnapshot.source == source.value,
            )
            .order_by(SourceSnapshot.fetched_at.desc())
            .limit(1)
        )
        if not record:
            return None
        daily_trend = await self._stored_daily_metrics(
            session, symbol, source, self._collection_period_days()
        )
        snapshot = self._from_record(record).model_copy(update={"daily_trend": daily_trend})
        await self._cache.set(
            self._cache_key(symbol, source),
            snapshot.model_dump(mode="json"),
            self._settings.source_ttl_seconds(source.value),
        )
        return snapshot

    async def _stored_daily_metrics(
        self,
        session: AsyncSession,
        symbol: str,
        source: SourceName,
        period_days: int,
    ) -> list[DailyMetric]:
        rows = (
            await session.scalars(
                select(TickerDailyMetric)
                .where(
                    TickerDailyMetric.symbol == symbol,
                    TickerDailyMetric.source == source.value,
                    TickerDailyMetric.metric_date >= self._history_start(period_days),
                )
                .order_by(TickerDailyMetric.metric_date)
            )
        ).all()
        return [
            DailyMetric(
                date=row.metric_date,
                mentions=row.mentions,
                buzz_score=row.buzz_score,
                sentiment_score=row.sentiment_score,
                bullish_pct=row.bullish_pct,
                bearish_pct=row.bearish_pct,
            )
            for row in rows
        ]

    async def _has_metric_coverage(
        self,
        session: AsyncSession,
        symbol: str,
        source: SourceName,
        period_days: int,
    ) -> bool:
        earliest = await session.scalar(
            select(func.min(TickerDailyMetric.metric_date)).where(
                TickerDailyMetric.symbol == symbol,
                TickerDailyMetric.source == source.value,
                TickerDailyMetric.metric_date >= self._history_start(period_days),
            )
        )
        return bool(earliest and earliest <= self._history_start(period_days))

    async def _store_snapshot(
        self,
        session: AsyncSession,
        run_id: int,
        snapshot: ProviderSnapshot,
    ) -> None:
        record = SourceSnapshot(
            collection_run_id=run_id,
            symbol=snapshot.symbol,
            company_name=snapshot.company_name,
            source=snapshot.source.value,
            found=snapshot.found,
            buzz_score=snapshot.buzz_score,
            mentions=snapshot.mentions,
            sentiment_score=snapshot.sentiment_score,
            bullish_pct=snapshot.bullish_pct,
            bearish_pct=snapshot.bearish_pct,
            trend=snapshot.trend,
            unique_posts=snapshot.unique_posts,
            coverage_count=snapshot.coverage_count,
            fetched_at=snapshot.fetched_at,
            raw_payload=snapshot.raw_payload,
        )
        session.add(record)
        if snapshot.daily_trend:
            metrics_by_date = {metric.date: metric for metric in snapshot.daily_trend}
            existing_metrics = (
                await session.scalars(
                    select(TickerDailyMetric).where(
                        TickerDailyMetric.symbol == snapshot.symbol,
                        TickerDailyMetric.source == snapshot.source.value,
                        TickerDailyMetric.metric_date.in_(list(metrics_by_date.keys())),
                    )
                )
            ).all()
            existing_map = {row.metric_date: row for row in existing_metrics}

            for metric_date, metric in metrics_by_date.items():
                if metric_date in existing_map:
                    existing = existing_map[metric_date]
                    existing.mentions = metric.mentions
                    existing.buzz_score = metric.buzz_score
                    existing.sentiment_score = metric.sentiment_score
                    existing.bullish_pct = metric.bullish_pct
                    existing.bearish_pct = metric.bearish_pct
                    existing.observed_at = snapshot.fetched_at
                else:
                    session.add(
                        TickerDailyMetric(
                            symbol=snapshot.symbol,
                            source=snapshot.source.value,
                            metric_date=metric_date,
                            mentions=metric.mentions,
                            buzz_score=metric.buzz_score,
                            sentiment_score=metric.sentiment_score,
                            bullish_pct=metric.bullish_pct,
                            bearish_pct=metric.bearish_pct,
                            observed_at=snapshot.fetched_at,
                        )
                    )
        await self._cache.set(
            self._cache_key(snapshot.symbol, snapshot.source),
            snapshot.model_dump(mode="json"),
            self._settings.source_ttl_seconds(snapshot.source.value),
        )

    async def collect(self, symbol: str, force: bool = False) -> CollectionOutcome:
        symbol = self._assert_supported(symbol)
        snapshots: dict[SourceName, ProviderSnapshot] = {}
        statuses: dict[SourceName, str] = {}
        errors: dict[SourceName, str] = {}
        request_count = 0
        quota_limited = False

        async with self._session_factory() as session:
            run = CollectionRun(
                symbol=symbol,
                provider=self._sentiment_provider.name,
                requested_sources=[source.value for source in SourceName],
            )
            session.add(run)
            await session.flush()

            collection_period_days = self._collection_period_days()

            async def _process_source(src: SourceName):
                latest = await self._latest_snapshot(session, symbol, src)
                has_required_history = await self._has_metric_coverage(
                    session, symbol, src, collection_period_days
                )
                if (
                    latest
                    and not force
                    and self._is_fresh(latest.fetched_at, src)
                    and has_required_history
                ):
                    return src, latest, "cached", None

                try:
                    snapshot = await asyncio.wait_for(
                        self._sentiment_provider.get_ticker_snapshot(
                            symbol, src, collection_period_days
                        ),
                        timeout=15.0,
                    )
                    return src, snapshot, "collected", None
                except TimeoutError:
                    st_val = "stale_provider_timeout" if latest else "unavailable"
                    return src, latest, st_val, f"{src.value} collection timed out (15s)"
                except ProviderError as exc:
                    st_val = "stale_provider_unavailable" if latest else "unavailable"
                    return src, latest, st_val, str(exc)

            results = await asyncio.gather(*[_process_source(src) for src in SourceName])
            for src, snap, stat, err in results:
                statuses[src] = stat
                if err:
                    errors[src] = err
                if snap:
                    snapshots[src] = snap
                    if stat == "collected":
                        await self._store_snapshot(session, run.id, snap)

            run.completed_sources = [source.value for source in snapshots]
            run.request_count = request_count
            run.error_summary = "; ".join(errors.values()) or None
            run.completed_at = utcnow()
            run.status = (
                "completed" if len(snapshots) == 3 else "partial" if snapshots else "failed"
            )
            await session.commit()

        return CollectionOutcome(snapshots, statuses, errors, request_count, quota_limited)

    async def _ensure_prices(self, symbol: str, period_days: int) -> list[PriceBar]:
        async with self._session_factory() as session:
            newest = await session.scalar(
                select(func.max(PriceBarRecord.fetched_at)).where(PriceBarRecord.symbol == symbol)
            )
            is_fresh = newest and utcnow() - _as_utc(newest) <= timedelta(hours=24)
            if not is_fresh:
                try:
                    bars = await asyncio.wait_for(
                        self._price_provider.get_daily_bars(symbol, max(period_days, 30)),
                        timeout=10.0,
                    )
                except Exception:  # noqa: BLE001 - includes TimeoutError
                    bars = []
                fetched_at = utcnow()
                bars_by_date = {bar.date: bar for bar in bars}
                if bars_by_date:
                    existing_records = (
                        await session.scalars(
                            select(PriceBarRecord).where(
                                PriceBarRecord.symbol == symbol,
                                PriceBarRecord.trade_date.in_(list(bars_by_date.keys())),
                            )
                        )
                    ).all()
                    existing_map = {row.trade_date: row for row in existing_records}

                    for trade_date, bar in bars_by_date.items():
                        if trade_date in existing_map:
                            record = existing_map[trade_date]
                            record.close = bar.close
                            record.provider = self._price_provider.name
                            record.fetched_at = fetched_at
                        else:
                            session.add(
                                PriceBarRecord(
                                    symbol=symbol,
                                    trade_date=trade_date,
                                    close=bar.close,
                                    provider=self._price_provider.name,
                                    fetched_at=fetched_at,
                                )
                            )
                    try:
                        await session.commit()
                    except IntegrityError:
                        await session.rollback()
            rows = (
                await session.scalars(
                    select(PriceBarRecord)
                    .where(
                        PriceBarRecord.symbol == symbol,
                        PriceBarRecord.trade_date >= self._history_start(period_days),
                    )
                    .order_by(PriceBarRecord.trade_date)
                )
            ).all()
        return [PriceBar(date=row.trade_date, close=row.close) for row in rows]

    @staticmethod
    def _signal(
        snapshots: dict[SourceName, ProviderSnapshot],
    ) -> SignalSummary:
        sentiment_total = 0.0
        attention_total = 0.0
        weight_total = 0.0
        for source, snapshot in snapshots.items():
            if snapshot.sentiment_score is None or snapshot.buzz_score is None:
                continue
            weight = SOURCE_WEIGHTS[source]
            sentiment_total += ((snapshot.sentiment_score + 1) * 50) * weight
            attention_total += snapshot.buzz_score * weight
            weight_total += weight
        if not weight_total:
            return SignalSummary(
                score=None,
                sentiment=None,
                attention=None,
                confidence=0,
                source_count=0,
            )
        sentiment = sentiment_total / weight_total
        attention = attention_total / weight_total
        return SignalSummary(
            score=round(0.70 * sentiment + 0.30 * attention, 1),
            sentiment=round(sentiment, 1),
            attention=round(attention, 1),
            confidence=round(weight_total, 2),
            source_count=len(snapshots),
        )

    async def ticker_response(
        self,
        symbol: str,
        chart_source: SourceName,
        period_days: int,
        force: bool = False,
    ) -> MCTickerResponse:
        if period_days not in {7, 30}:
            raise ValueError("period_days must be 7 or 30")
        symbol = self._assert_supported(symbol)
        # Run collection and price fetch concurrently — they are independent
        # and running them sequentially was the main cause of outer timeouts.
        collection, prices = await asyncio.gather(
            self.collect(symbol, force=force),
            self._ensure_prices(symbol, period_days),
        )

        start_date = date.today() - timedelta(days=period_days - 1)
        async with self._session_factory() as session:
            metrics = (
                await session.scalars(
                    select(TickerDailyMetric)
                    .where(
                        TickerDailyMetric.symbol == symbol,
                        TickerDailyMetric.source == chart_source.value,
                        TickerDailyMetric.metric_date >= start_date,
                    )
                    .order_by(TickerDailyMetric.metric_date)
                )
            ).all()
            daily_mentions_sources = set(
                (
                    await session.scalars(
                        select(TickerDailyMetric.source)
                        .where(
                            TickerDailyMetric.symbol == symbol,
                            TickerDailyMetric.metric_date >= start_date,
                            TickerDailyMetric.mentions.is_not(None),
                        )
                        .group_by(TickerDailyMetric.source)
                    )
                ).all()
            )
            remaining = (
                await self._quota.remaining(session)
                if self._sentiment_provider.name == "adanos"
                else None
            )

        cards = []
        for source in SourceName:
            snapshot = collection.snapshots.get(source)
            if not snapshot:
                cards.append(
                    SourceCard(
                        source=source,
                        status=collection.statuses.get(source, "unavailable"),
                        message=collection.errors.get(source),
                    )
                )
                continue
            cards.append(
                SourceCard(
                    source=source,
                    status=collection.statuses[source],
                    as_of=snapshot.fetched_at,
                    sentiment_score=snapshot.sentiment_score,
                    buzz_score=snapshot.buzz_score,
                    mentions=snapshot.mentions,
                    bullish_pct=snapshot.bullish_pct,
                    bearish_pct=snapshot.bearish_pct,
                    trend=snapshot.trend,
                    coverage_count=snapshot.coverage_count,
                    daily_mentions_available=source.value in daily_mentions_sources,
                )
            )

        metric_by_date = {metric.metric_date: metric for metric in metrics}
        price_by_date = {bar.date: bar.close for bar in prices}
        dates = sorted(set(metric_by_date) | set(price_by_date))
        # Extract top catalyst card or quote from snapshots if available
        top_driver_card = None
        for snapshot in collection.snapshots.values():
            d_cards = snapshot.raw_payload.get("driver_cards") or []
            if d_cards:
                top_driver_card = d_cards[0]
                break

        chart = []
        for metric_date in dates:
            metric_item = metric_by_date.get(metric_date)
            close_price = price_by_date.get(metric_date)
            mentions_val = metric_item.mentions if metric_item else None
            buzz_val = metric_item.buzz_score if metric_item else None

            sig_type: str | None = None
            sig_label: str | None = None
            conf_val: float | None = None
            theme_val: str | None = None
            quote_val: str | None = None

            if metric_item and metric_item.bullish_pct is not None:
                b_pct = metric_item.bullish_pct
                if b_pct >= 65.0:
                    sig_type = "buy"
                    sig_label = "B"
                    conf_val = round(b_pct / 100.0, 2)
                    theme_val = (
                        top_driver_card.get("driver")
                        if top_driver_card
                        else "Bullish Chatter & Catalyst Momentum"
                    )
                    quote_val = (
                        top_driver_card.get("evidence")
                        if top_driver_card
                        else f"Social chatter consensus reached {b_pct:.1f}% bullish sentiment."
                    )
                elif b_pct <= 40.0:
                    sig_type = "sell"
                    sig_label = "S"
                    conf_val = round((100.0 - b_pct) / 100.0, 2)
                    theme_val = (
                        top_driver_card.get("driver")
                        if top_driver_card
                        else "Bearish Chatter & Pullback Risk"
                    )
                    quote_val = (
                        top_driver_card.get("evidence")
                        if top_driver_card
                        else f"Social chatter consensus dropped to {b_pct:.1f}% bullish sentiment."
                    )
                else:
                    sig_type = "neutral"
                    sig_label = None
                    conf_val = 0.5

            chart.append(
                ChartPoint(
                    date=metric_date,
                    mentions=mentions_val,
                    buzz_score=buzz_val,
                    close=close_price,
                    signal=sig_type,
                    signal_label=sig_label,
                    confidence=conf_val,
                    catalyst_theme=theme_val,
                    key_quote=quote_val,
                )
            )
        chart_metric = (
            "mentions" if any(metric.mentions is not None for metric in metrics) else "buzz_score"
        )
        as_of_values = [snapshot.fetched_at for snapshot in collection.snapshots.values()]
        data_status = (
            "unavailable"
            if not collection.snapshots
            else "stale_budget_limited"
            if collection.quota_limited
            else "partial"
            if collection.errors
            else "fresh"
        )
        return MCTickerResponse(
            symbol=symbol,
            company_name=next(
                (
                    snapshot.company_name
                    for snapshot in collection.snapshots.values()
                    if snapshot.company_name
                ),
                None,
            ),
            data_status=data_status,
            as_of=max(as_of_values) if as_of_values else None,
            signal=self._signal(collection.snapshots),
            sources=cards,
            chart_source=chart_source,
            chart_metric=chart_metric,
            chart_period_days=period_days,
            chart=chart,
            quota_remaining=remaining,
        )
