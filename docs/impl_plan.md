# SentimentAI implementation plan — MVP to 10-agent pipeline

## Summary

Build a plain monorepo optimized for a small team, targeting US equities. Deliver the MVP through a simple sequential worker pipeline first, then migrate the same contracts and persisted data to the LangGraph 10-agent workflow. Develop locally with Docker Compose; defer cloud-specific manifests until the deployment decision is made.

Use Redis Streams for durable event processing and consumer groups, PostgreSQL/TimescaleDB for relational and score time-series data, Qdrant for Phase-2 embeddings, and MinIO for local immutable raw-object storage.

## Core interfaces and boundaries

- Define a canonical Pydantic `RawContent` model and versioned event envelope; persist raw payloads immutably before processing.
- Define async protocols:
  - `SourceConnector.collect(request) -> CollectionPage`
  - `SentimentModel.analyze(items) -> ItemSentiment`
  - `StructuredAnalysisProvider.analyze(items) -> LlmAnalysis`
  - `EmbeddingProvider.embed(items) -> EmbeddingBatch`
  - `MarketDataProvider.history(symbol, range) -> OHLCV`
- Generate the TypeScript client from FastAPI OpenAPI. Keep a plain folder-based monorepo: `apps/web`, `services/api`, `services/worker`, `packages/python`, `infra`, and `docs`; do not use Turborepo.
- Version every processing result and score configuration. MVP OCS v0.1 is `70% RISS + 30% SMS`; retain the weights in a versioned configuration record, never in application logic.

## Implementation phases

### Phase 0 — Foundation and developer platform

- Create the Python 3.12 FastAPI/worker and Next.js/TypeScript application shells, environment validation, secret handling, linting, typing, tests, and GitHub Actions.
- Add Docker Compose services for PostgreSQL with TimescaleDB, Redis, Qdrant, MinIO, and local observability.
- Create Alembic migrations for tickers, sources, authors, raw/processed content, analyses, scores, alerts, and backtests.
- Seed the S&P 100 ticker master and implement structured logs, trace IDs, health checks, and basic pipeline metrics.

### Phase 1 — Agents 1–3: collection, validation, and cleaning

- Implement the connector framework with cursors, source rate limits, retries, source-health status, and idempotent collection events.
- Implement adapters only after receiving the source-specific requirements document; use a fixture connector meanwhile so the whole pipeline is runnable without external credentials.
- Store raw payloads in MinIO and metadata in PostgreSQL before publishing Redis Stream events.
- Build Agent 2 validation: schema integrity, timestamp/lookback checks, English-only filtering, ticker/company relevance, and content-length rules.
- Build Agent 3 cleaning: encoding repair, HTML/URL removal, preserved financial tokens, hashtag/cashtag extraction, boilerplate removal, exact SHA-256 deduplication, and MinHash near-duplicate handling.
- Surface partial-source coverage as a data-quality penalty rather than failing a whole run unless every source fails.

### Phase 2 — Agent 5 plus MVP Agents 8–9: sentiment and scoring

- Run FinBERT through a replaceable inference adapter; use CPU/local inference for development and preserve a production GPU-provider boundary.
- Persist class probabilities, score, model version, confidence, and processing failures per item.
- Implement the quality-weighted RISS formula for retail sources and accounts, then SMS from the 24-hour mention volume against the 30-day baseline.
- Start passive collection before exposing SMS publicly; do not manufacture a 30-day baseline. Use fixtures for development and unlock SMS/OCS only after sufficient historical coverage.
- Implement Agent 9 aggregation, Redis score caching, score freshness tracking, threshold-change events, and deterministic score explanations/drivers for the MVP.

### Phase 3 — Agent 10 MVP reporting, API, and dashboard

- Implement authenticated REST endpoints for ticker scores, history, and ranked driving content; validate Supabase JWTs, store hashed API keys, and apply Redis-backed rate limits.
- Build the dashboard for score, direction, coverage/confidence, history, and top five drivers. Add a persistent informational-not-advice disclosure to all score surfaces.
- Implement alert configuration and email delivery for OCS threshold crossings.
- Add Stripe test-mode subscription gating for Starter and Pro capabilities; use test webhooks and idempotent billing-event handling.
- Add price-history ingestion and a backtest job that calculates IC, hit rate, and calibration outputs without presenting the results as forecasts.

### Phase 4 — MVP hardening and beta gate

- Run the pipeline continuously for an initial 10-ticker canary, then 25, then the S&P 100 after coverage, cost, and failure-rate gates pass.
- Load test ingestion and score retrieval, execute backup/restore drills, and verify dead-letter replay and duplicate-event safety.
- Require: complete audit trail from raw item to score, reliable scheduled refresh, documented methodology, no critical security findings, and initial backtest results before beta.

### Phase 5 — Agent 4 and LangGraph migration

- Replace only the orchestration layer with LangGraph; reuse the collectors, schemas, storage, scoring, and API from the MVP.
- After cleaning, run FinBERT and structured LLM analysis in parallel. Route short items to FinBERT-only, ordinary content to the fast model, and long/high-engagement content to the strong model.
- Enforce structured Pydantic LLM output, cache by fingerprint, batch calls, retry malformed outputs once, and record provider/model/cost metadata.
- Implement merge and disagreement handling: reuse the original FinBERT result, retry only the LLM branch once with the stronger tier, then reduce or exclude high-disagreement items. Redis-backed checkpoints must make a run resumable and bounded to one retry.

### Phase 6 — Agents 6–7: narrative and credibility intelligence

- Generate Qdrant embeddings for eligible enriched items and cluster per ticker/window with UMAP plus HDBSCAN.
- Persist narrative fingerprints, cluster summaries, coherence, momentum, and historical matching; add narrative APIs and dashboard views.
- Implement author reputation storage and feature extraction. Begin with transparent rule-based bot-risk scoring; introduce the XGBoost model only after a labelled dataset and held-out precision/recall evaluation exist.
- Exclude high bot-risk items, proportionally discount uncertain items, and make bot/coverage penalties visible in report metadata.

### Phase 7 — Full Agents 8–10 suite and near-real-time delivery

- Add STSS, LTCS, MNSS, confidence score, bootstrap confidence intervals, and versioned OCS v2 scoring.
- Expand Agent 10 into LLM-assisted reports with citations to stored source items, narrative summaries, anomalies, and data-quality caveats. Never emit trade recommendations or price targets.
- Add incremental scoring, scheduled full recalculation, WebSocket updates, webhooks with signed deliveries and retries, and alert deduplication.
- Keep CrewAI sector/competitive sub-workflows outside this scope; introduce them only after the 10-agent graph, backtesting, and data-quality gates are stable.

## Test plan and acceptance criteria

- Unit tests for each connector contract, validation rule, cleaner transformation, deduplication rule, scoring formula, and score-version migration.
- Golden-data tests for RISS, SMS, OCS, confidence intervals, and explanatory drivers.
- Integration tests in Compose for event idempotency, retries, dead-letter replay, cache invalidation, PostgreSQL/Qdrant writes, and authenticated API access.
- LangGraph tests cover normal flow, partial-source degradation, malformed LLM output, low/high model disagreement, exactly one escalation retry, and human-escalation routing.
- End-to-end fixtures prove that a raw item can be traced through to a displayed score and backtest record.

## Assumptions

- The MVP is US/S&P-100 focused and uses local-first infrastructure.
- The forthcoming source document determines concrete connector adapters and market-data licensing; the connector contract and fixture source remove that dependency from the rest of the build.
- Anthropic/OpenAI, Supabase, Stripe, and any production data providers remain environment-configured adapters, with no credentials committed to the repository.
- Public launch remains contingent on legal review of US financial-product disclosures and data-source licensing terms.
