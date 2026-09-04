# Data Collection Agent - Free/OSS Phase 1 Plan

## Summary

Build Phase 1 as a local-validation product: a ticker lookup returns a preliminary sentiment score plus a SwaggyStocks-style, dual-axis chart of hourly mention volume versus price. Use **Meltano + Singer** as the single internal integration gateway; the application never owns per-platform `httpx` clients. Meltano is MIT-licensed and supports standard/custom Singer connectors. [Meltano](https://github.com/meltano/meltano)

Do not use Adanos, OpenBB, Airbyte, X, or StockTwits in this phase. OpenBB validates the “connect once, consume everywhere” concept, but its runtime is AGPLv3 and does not solve social-data access/licensing. [OpenBB](https://github.com/OpenBB-finance/OpenBB)

## Phase 1 - Central ingestion gateway

- Add a Dockerized Meltano service, configured solely through versioned source profiles and environment-injected secrets.
- Implement a small internal Collection Orchestrator that submits Meltano jobs, records job state, and emits `raw_content.available` only after a successful source run.
- Keep all provider-specific code inside Singer taps. The API/agent layer calls only `CollectionRequest`; it must not know API URLs, cursors, authentication, or pagination.
- Use a custom MinIO Singer target to persist immutable raw Singer records, run manifests, and connector state. Store normalized/indexed records in PostgreSQL.

## Phase 2 - Local-validation sources

- **Reddit:** use the existing Singer Reddit tap with official OAuth, limited to `wallstreetbets`, `stocks`, and `investing`; ingest new posts and comments every 15 minutes. This is source-first ingestion, allowing any subsequently requested S&P 100 ticker to resolve from local data.
- **News:** implement a custom `tap-gdelt-doc` using the legacy GDELT DOC 2.0 API. On a stale ticker request, query the company’s approved name/alias set and retain only URL, title, publication time, source domain, and result metadata-not article bodies. [GDELT DOC API](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/amp/)
- **Price:** implement `tap-yfinance-local` for local chart validation only. It emits hourly or daily OHLCV bars through the same gateway. yfinance itself warns that Yahoo data is for personal use, so this connector is permanently blocked from public deployment. [yfinance usage notice](https://github.com/ranaroussi/yfinance)
- Provide deterministic fixture taps for all three sources so the full pipeline and dashboard run without credentials.

## Data contract and ticker flow

- Define `CollectionRequest { symbol, freshness_window, sources, force }`, `CollectionRun`, `RawContent`, `PriceBar`, and `TickerMention`.
- `RawContent` includes source, immutable external ID, original URL, published/fetched UTC timestamps, content hash, raw-object path, and detected ticker candidates.
- De-duplicate by `(source, external_id)` and normalized-content hash; preserve source cursors/checkpoints so reruns are idempotent.
- Resolve tickers with an S&P 100 symbol/company alias dictionary, cashtag preference, deny lists for common-word symbols, and proximity checks. Store confidence rather than silently treating every token as a ticker.
- Retain raw social text for 30 days in restricted MinIO storage; serve only source links and short provenance metadata. Do not use Reddit content for model training or fine-tuning.

## Query, score, and chart behavior

- A ticker request first reads local materialized data:
  - Fresh data: return the latest provisional score and chart immediately.
  - Stale data: return cached data with `collection_state: refreshing`, enqueue a bounded Meltano refresh, then let the client poll for completion.
  - No local data: return `202 collecting` and a transparent “no score yet” state.
- Aggregate `ticker_activity_hour` with mention count, unique authors, source count, bullish/bearish/neutral counts once the downstream sentiment node labels content, and coverage/freshness.
- Render a 7-day hourly double-line chart: mentions on the left axis and local-validation price bars on the right. Preserve gaps when markets are closed; never interpolate prices.
- Label the score as **“Phase 1 Sentiment”**, not final OCS. Show source coverage and evidence links so the product is validated as an explainable SwaggyStocks-like activity/sentiment layer. SwaggyStocks itself exposes mentions, bullish/bearish/neutral counts, net sentiment, and momentum; those are the Phase 1 comparison metrics. [SwaggyStocks methodology](https://swaggystocks.com/dashboard/wallstreetbets/how-it-works)

## Validation and release gates

- Test connector state resume, pagination, malformed records, duplicate replay, stale refresh, rate-limit failure, and partial-source success.
- Test ticker collisions (`A`, `ALL`, `IT`), timezone bucketing, market-closed chart gaps, and no-data/stale-data API responses.
- Demonstrate AAPL, NVDA, and TSLA end-to-end using both fixtures and permitted local credentials.
- Treat `TauricResearch/TradingAgents` as an architecture reference only-not a collector dependency-because its collectors are research-time dataflows rather than durable ingestion infrastructure. [TradingAgents](https://github.com/TauricResearch/TradingAgents)
- Keep X and StockTwits disabled. X’s recent-search endpoint requires a bearer token and only covers seven days; no free OSS wrapper changes those access requirements. [X recent search](https://docs.x.com/x-api/posts/search-recent-posts)
- Before any closed/public beta, replace local-only price data and obtain written commercial permission for every enabled source. Reddit’s terms explicitly require a separate agreement for commercial or revenue-generating data use. [Reddit Data API Terms](https://redditinc.com/policies/data-api-terms)

## Assumptions

- Phase 1 is local validation only, as selected.
- The target universe is S&P 100 US equities.
- No paid gateway or data provider is introduced.
- A future production phase may add licensed Reddit, X, StockTwits, and market-data sources behind the same Singer/Meltano contracts without changing the agent-facing API.
