# Data Collection Agent plan — gateway-first Phase 1

## Architecture decision

Replace per-platform collectors with two gateway integrations:

1. **Adanos Social Gateway** — the primary social/news source for Reddit, X, and financial news, using one API key and a consistent ticker-oriented API. Its Professional tier exposes raw mention rows and permits commercial use; Reddit/X update hourly and news refreshes every 10 minutes. [Adanos API](https://adanos.org/), [raw social data and commercial tier](https://adanos.org/x-stock-sentiment), [news coverage](https://adanos.org/stock-news-sentiment)

2. **OpenBB Market Gateway**, configured with the `openbb-fmp` provider — the single internal interface for ticker resolution, US-equity price bars, and market metadata. OpenBB is valuable as a self-hosted abstraction layer, but it is not a hosted data supplier and does not currently include a maintained Reddit/X/StockTwits provider. [OpenBB provider model](https://docs.openbb.co/odp/python/extensions/providers)

Do not use MCP in the collection path. OpenBB MCP exposes a FastAPI/OpenBB server as agent tools; it is useful later for interactive research, not for scheduled, durable ingestion. [OpenBB MCP](https://docs.openbb.co/odp/python/extensions/interface/openbb-mcp)

**StockTwits is excluded from the Phase-1 gateway baseline.** Adanos does not list it as a source, while FMP’s social-sentiment endpoints are legacy. Add it only when a gateway vendor supplies licensed raw StockTwits content, rather than creating a direct platform integration that defeats this design. [FMP legacy social API](https://site.financialmodelingprep.com/developer/docs/social-sentiment-api)

## Agent interface and flow

- A user ticker request creates one `TickerCollectionRequest` with symbol, canonical company identity, 24-hour scoring window, seven-day chart window, and refresh mode.
- The Data Collection Agent makes gateway-level calls only:
  - Adanos raw mentions for Reddit, X, and news.
  - OpenBB/FMP for hourly OHLCV price data and ticker metadata.
- Persist the unmodified gateway responses to object storage, then create canonical `RawContent` records and publish `raw.content.v1` events for Agents 2–10.
- Return a `CollectionRunResult` containing per-domain counts, freshness, quota state, source coverage, chart readiness, and errors.
- Keep gateway-provided sentiment, buzz, and labels as `provider_annotations`; they must not become SentimentAI scores. Our scoring pipeline remains independent and auditable.

## Implementation phases

### Phase 1 — Gateway proof of capability

- Run a ten-ticker evaluation against Adanos and OpenBB/FMP using their official SDKs/generated clients and REST APIs; do not write Reddit, X, StockTwits, or news-specific request code.
- Confirm the Adanos Professional contract covers commercial storage, display, and permitted reuse of raw mention snippets before production use.
- Verify fields required for the product: native source ID, source, timestamp, author if available, engagement, text snippet, URL, source sentiment metadata, and historical window limits.
- Confirm OpenBB/FMP returns hourly price bars for all S&P 100 tickers and handles market closures correctly.
- Record gateway latency, quota use, retention limits, raw-field completeness, and source freshness. Promote only if the gateway can support the selected ticker set and user-request rate.

### Phase 2 — Collection-agent implementation

- Add a small `SocialGateway` client for Adanos and a `MarketDataGateway` client for OpenBB. These are the only upstream integrations in the agent.
- Define canonical models:
  - `RawContent`: gateway/source IDs, text snippet, author/engagement, timestamps, URL, ticker evidence, and provider annotations.
  - `MarketPriceBar`: ticker, UTC interval, OHLCV, provider, market-session status.
  - `CollectionRunResult`: requested/returned source domains, data freshness, failure reason, and coverage state.
- Store gateway response payloads immutably, deduplicate by `source + native_id` and normalized-text fingerprint, and checkpoint the latest successful collection window.
- Coalesce identical ticker requests: reuse a result newer than 15 minutes; otherwise run one collection job and let concurrent users join it.
- Require market price data plus at least two of the three social/news domains to produce a fresh score. Otherwise return prior data only when labeled stale/degraded.

### Phase 3 — SwaggyStocks-style validation chart

- Use **hourly**, not 15-minute, mention buckets because the social gateway’s Reddit and X feeds refresh hourly.
- Build `MentionBucket` records by source and UTC hour from canonical raw items; join them with hourly close-price bars.
- Render a default seven-day double-line chart: hourly mentions and normalized stock-price movement, with source filters and a visible coverage/freshness label.
- Support a 24-hour view for the live score. Do not interpolate price during market closures; retain social mentions and mark price as unavailable outside trading sessions.
- Add top source items with links back to their originals where permitted by the gateway’s terms.

### Phase 4 — Reliability, observability, and handoff

- Track gateway request latency, errors, quota remaining, cached-response rate, social-domain freshness, raw-item count, duplicate rate, and price-bar gaps.
- Test gateway response normalization, missing optional fields, quota exhaustion, stale cache behavior, date-window boundaries, duplicate delivery, and chart alignment.
- Acceptance criteria:
  - A supported ticker returns source data and price bars through the two gateways without platform-specific code.
  - A refreshed request completes within the gateway freshness budget and produces a traceable raw-data audit record.
  - The seven-day mentions-vs-price chart accurately represents hourly buckets and clearly reports incomplete source coverage.

## Assumptions

- Phase 1 uses Adanos Professional for commercial raw Reddit/X/news mention access; procurement is required before beta.
- OpenBB is the internal market-data façade, initially backed by FMP, with provider replacement possible through OpenBB configuration.
- Full post/article bodies are not assumed: use only fields the gateway explicitly licenses. Deeper LLM narrative analysis remains gated on obtaining full-text rights or an approved future data feed.
