## Adanos-based implementation plan - Phases 0–1

This replaces the earlier connector/Meltano-first data-collection plan. Adanos becomes the single social/news sentiment gateway; the application makes one vendor integration, not separate Reddit/X/news collectors.

Adanos Free is for local validation only: 250 requests/month, 30-day history, no raw mentions, and no commercial use. Professional currently adds commercial use, raw mentions, 365-day history, and 2.5M monthly requests. [Adanos pricing](https://adanos.org/pricing)

### Phase 0 - Foundation and Adanos gateway

- Create the local stack: FastAPI API/worker, PostgreSQL, Redis, and Next.js dashboard in Docker Compose.
- Add server-only configuration:
  - `ADANOS_API_KEY`
  - `ADANOS_PLAN=free`
  - `ADANOS_MONTHLY_BUDGET=225`
  - `ADANOS_BASE_URL=https://api.adanos.org`
  - `PRICE_PROVIDER=yfinance_local`
- Define a provider-neutral `MarketSentimentProvider` interface so the rest of the pipeline calls:
  - `get_ticker_snapshot(symbol, sources)`
  - `get_trending(source, period)`
  - `get_market_snapshot(source)`
- Implement `AdanosProvider` as the sole external social/news integration. It owns `httpx`, auth headers, retries, timeout, response validation, and error mapping; no other application layer contacts Reddit, X, or news APIs.
- Create a fixture provider with recorded Adanos-shaped responses, allowing development and tests without consuming quota.
- Persist:
  - `collection_runs` - request, status, quota consumed, errors.
  - `source_snapshots` - immutable Adanos response JSON plus normalized fields.
  - `ticker_daily_metrics` - source/date/buzz/mentions/sentiment/bullish/bearish values.
  - `quota_usage` - atomic monthly counter and per-endpoint telemetry.
- Add Redis cache and circuit breaking:
  - Free-plan effective cache TTL: 24 hours per ticker/source.
  - On cache miss, reserve quota before calling Adanos.
  - On budget exhaustion, return the latest cached record with `data_status: stale_budget_limited`.
  - On `429` or vendor failure, do not retry aggressively; preserve partial-source results.

### Phase 1 - Adanos data collection and ticker experience

- Enable exactly three stock sources:
  - Reddit: `https://api.adanos.org/reddit/stocks/v1`
  - X/FinTwit: `https://api.adanos.org/x/stocks/v1`
  - Financial news: `https://api.adanos.org/news/stocks/v1`

  Each uses `GET /stock/{ticker}` with the shared `X-API-Key` authentication model. Adanos provides aggregate buzz, mentions, sentiment, bullish/bearish percentages, trend direction, and daily history for these sources. [Reddit API](https://adanos.org/reddit-stock-sentiment), [X API](https://adanos.org/x-stock-sentiment), [News API](https://adanos.org/stock-news-sentiment)

- For a first-time ticker request:
  1. Validate the symbol against the S&P 100 ticker master.
  2. Read local snapshots.
  3. If absent or older than 24 hours, make at most three Adanos calls-one per enabled source.
  4. Normalize and store the vendor payloads.
  5. Fetch daily price history through local-only yfinance and cache it for 24 hours.
  6. Return the cached/new aggregate snapshot and chart payload.

- Free-tier quota policy:
  - Reserve 25 requests/month for smoke tests and recovery.
  - Limit normal use to 225 requests: approximately 75 fully refreshed ticker lookups/month.
  - Do not schedule a full S&P 100 refresh.
  - Allow a two-ticker pilot watchlist to refresh daily: 180 calls/month, leaving 45 calls for manual exploration.
  - Use Adanos-provided daily history for the chart rather than repeatedly polling intraday data.

- Add a temporary, clearly labeled `Phase1SignalV0`:
  - Normalize each source sentiment from `[-1, +1]` to `[0, 100]`.
  - Compute source-weighted sentiment: Reddit 45%, X 30%, news 25%; renormalize when a source is unavailable.
  - Compute attention separately from vendor `buzz_score`; do not treat buzz as sentiment.
  - Display `Phase 1 Signal`, `Sentiment`, `Attention`, `Confidence`, and per-source values. Do not label this as final OCS.

- Build the SwaggyStocks-style ticker view:
  - Default chart: **Reddit daily mentions vs. daily closing price**, over 7 or 30 days.
  - Source selector: Reddit, X, or news; do not sum raw mention counts across sources because their collection universes differ.
  - If a source payload lacks daily mention history, show its buzz history instead and disclose the substitution.
  - Add source cards showing sentiment, buzz, bullish/bearish mix, trend, freshness, and coverage metadata.
  - Use a clear informational-only/not-investment-advice disclaimer.

### Phase 1 test and acceptance criteria

- Unit-test Adanos response validation, missing fields, unsupported tickers, auth failures, rate limits, and schema-version changes.
- Test quota reservation atomically under concurrent ticker requests.
- Test partial results: e.g. Reddit succeeds while X/news fail; return a lower-confidence score rather than an error.
- Test cache freshness, stale-budget fallback, daily chart alignment, market-closed gaps, and source-specific chart selection.
- Validate AAPL, NVDA, and TSLA end-to-end with both fixtures and the Free API key.
- Confirm no API key reaches the browser and no Adanos request occurs outside `AdanosProvider`.

### Professional upgrade path

- Change only configuration and quota policy: `ADANOS_PLAN=professional`.
- Reduce cache TTLs to match vendor cadence: news 15 minutes; Reddit/X 60 minutes.
- Enable `/stock/{ticker}/mentions` evidence ingestion, MinIO raw-payload retention, Agent 2/3 validation-cleaning, FinBERT re-scoring, and the real OCS pipeline.
- Enable commercial deployment only after the Professional plan is active; Adanos defines Free and Hobby as non-commercial, while Professional allows commercial applications. [Adanos terms](https://adanos.org/terms)