# Data Collection Agent plan — ticker-first Phase 1

## Validation and product target

- **TauricResearch/TradingAgents is a strong reference, not a codebase to fork.** Its LangGraph and provider-routing design are valuable, and it already has Reddit, StockTwits, Yahoo Finance, and Alpha Vantage dataflows. But those collectors return small formatted text samples for immediate LLM prompting rather than immutable, complete content records for replay, scoring, and backtesting. Reuse the adapter and graceful-failure ideas; build this agent independently. [TradingAgents](https://github.com/TauricResearch/TradingAgents), [its Reddit collector](https://raw.githubusercontent.com/TauricResearch/TradingAgents/main/tradingagents/dataflows/reddit.py)
- Use **SwaggyStocks as the Phase-1 product benchmark**: per-ticker mention volume, bull/bear/neutral breakdown, net sentiment, momentum, and a mentions-vs-price chart. Its intentionally transparent rules-based methodology confirms that this initial experience is useful, but our raw multi-source history enables later narrative and credibility differentiation. [SwaggyStocks methodology](https://swaggystocks.com/dashboard/wallstreetbets/how-it-works)

## Agent contract and data model

- Implement a ticker-first `DataCollectionAgent` invoked for a requested US ticker with a default 24-hour window and 15-minute refresh cadence.
- Input: `analysis_id`, canonical ticker/company aliases, window, requested sources, run mode (`on_demand` or `scheduled`), and prior source cursors.
- Output: `CollectionRunResult` with per-source status, item count, time coverage, quota state, errors, next cursors, and a `coverage_status` of `complete`, `degraded`, or `failed`.
- Persist:
  - Immutable vendor payloads in MinIO before any transformation.
  - Canonical `RawContent` records in PostgreSQL with native ID, source, author data, engagement, published/collected times, URL, ticker evidence, raw payload reference, and exact-text fingerprint.
  - `ingestion_runs`, `source_cursors`, `source_health`, and 15-minute `market_price_bars`.
- Publish only successfully persisted items to `raw.content.v1` in Redis Streams. Agent 2 owns validation/near-duplicate filtering; Agent 1 owns idempotency and exact duplicate prevention.

## Source connectors

- Build a common async `SourceConnector.collect(request, cursor) -> SourcePage` protocol using `httpx`, typed provider payloads, timeouts, retry-after handling, jittered exponential backoff, per-source token buckets, and circuit breakers.
- Implement these connectors in parallel behind that contract:
  - **Reddit OAuth:** search new submissions and comments for the ticker across `r/wallstreetbets`, `r/stocks`, and `r/investing`; retain post/comment structure, vote/comment metrics, author metadata, and subreddit. Do not use unauthenticated JSON/RSS as the production path.
  - **StockTwits:** ingest the symbol stream and preserve native bullish/bearish labels as provider metadata only—never as SentimentAI’s score.
  - **X API v2:** use recent search with cashtag, symbol, and company-name query variants; request author, engagement, conversation, media, and referenced-post expansions. Recent search covers the prior seven days, so longer history must accrue in SentimentAI’s store. [X recent search](https://docs.x.com/x-api/posts/search-recent-posts)
  - **News + prices:** use Alpha Vantage `NEWS_SENTIMENT` filtered by ticker and time window for article metadata/content, and its intraday price endpoint for 15-minute chart bars. Persist vendor sentiment only as a QA reference. [Alpha Vantage documentation](https://www.alphavantage.co/documentation/)
- Add a canonical ticker registry with company aliases and an allow/deny collision list. A match must be based on cashtag, unambiguous symbol context, or company-name evidence; common-word tickers require stricter rules.

## Collection workflow and failure rules

- When a user requests a score, return a score cached within 15 minutes; otherwise enqueue one collection run and expose job progress to the API/UI.
- Run the four source connectors concurrently while obeying independent quotas. Persist each page immediately, checkpoint its cursor, then continue until the window is covered or the source cap is reached.
- A run proceeds to validation when at least three of four sources complete. With fewer than three, mark the new analysis `insufficient_coverage`; return a prior score only if clearly labeled stale/degraded.
- Compute no sentiment in this agent. The later aggregation stage derives 15-minute mention buckets from validated content and joins them to the stored price bars for the SwaggyStocks-style double-line chart.
- Track source latency, API quota, cursor lag, items fetched/persisted/duplicate, coverage gap, and failure reasons by ticker and source.

## Tests and release gates

- Contract fixtures for every connector, including pagination, missing fields, timestamp normalization, native labels, ticker collisions, duplicate delivery, rate limits, auth failure, and malformed vendor responses.
- Integration tests verify raw-object-first persistence, PostgreSQL idempotency, Redis event publishing, cursor resume, partial-source degradation, and 15-minute price/chart alignment.
- Acceptance criteria: a ticker request retrieves and persists all available source data in under 60 seconds under normal provider conditions; repeated runs create no duplicate canonical records; a 24-hour ticker view can render mention counts against aligned price bars with source coverage shown.
- Production activation requires each provider’s credentials, rate limits, and commercial redistribution/storage terms to be recorded in source configuration. No scraping bypasses or undocumented endpoints.
