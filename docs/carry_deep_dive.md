# Carry — Deep-Level Technical & Product Summary

> Companion to `carry_high_level_summary.md`. This document is the engineer's map of the system: architecture, data flows, pipelines, data model, API surface, frontend structure, infrastructure, and known trade-offs.
>
> **Naming note:** the product is **Carry** (web: `carry-fin.vercel.app`, API: `carry-api.akshat21.me`). The repo and much of the internal vocabulary retain the original names — "yt-chatter" (the YouTube commentary engine) and "market-chatter"/"TickerFlow" (the social sentiment engine). `COSTING.md` refers to "YT Chatter / Carry" for the same platform.

---

## 1. System Architecture at a Glance

```
┌─────────────────────────────── FRONTEND ────────────────────────────────┐
│  Next.js 16 (App Router) · React 19 · TypeScript · Tailwind v4          │
│  Landing page │ App shell (Search, Overview, Channels, Themes,          │
│  Tickerflow, Investors, Consensus, Activity, Usage, Admin)              │
│  Clerk auth (invite gate) · React Query · Recharts · d3-hierarchy       │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │ REST (JSON) via Vercel edge proxy rewrite
┌────────────────────────────────▼────────────────────────────────────────┐
│                        BACKEND — Python 3.12                            │
│  FastAPI (uvicorn, 4 workers) │ Celery worker + beat │ Nginx + TLS      │
│  Clerk JWT verification on every request                                │
└───────┬──────────────────────────────────────────────┬──────────────────┘
        │                                              │
┌───────▼─────────────────────┐          ┌─────────────▼──────────────────┐
│      PROCESSING PIPELINES   │          │         STORAGE                │
│ 1. YouTube ingestion        │          │ PostgreSQL 16 + pgvector       │
│ 2. LLM structured analysis  │          │  (Cloud SQL, 8 vCPU / 64 GB)   │
│ 3. Theme/ticker mapping     │          │ Redis 7 (Celery broker+cache)  │
│ 4. Embeddings (384-dim)     │          │ Local: FinBERT ONNX, Whisper   │
│ 5. Market outcome tracking  │          │  (ASR fallback), ONNX runtime  │
│ 6. TickerFlow social graph  │          │                                │
│ 7. HFI investor pipeline    │          │                                │
└─────────────────────────────┘          └────────────────────────────────┘
```

**Runtime topology (production):** single GCP VM (`e2-medium`, `asia-southeast1`) runs all backend Docker containers (api, worker, beat, nginx); Postgres runs on GCP Cloud SQL; Redis on Aiven; frontend on Vercel. Celery Beat schedules WebSub lease renewals, RSS fallback polls, and daily performance evaluations.

## 2. Repository Layout

```text
yt-chatter/
├── src/                    # Backend package (FastAPI + pipelines + services)
│   ├── api/                # Routers: search, videos, predictions, tickers,
│   │                       # themes, channels, dashboard, hfi_*, market_chatter,
│   │                       # websub, activity, usage, admin, pipeline
│   ├── models/             # SQLAlchemy 2.0 async ORM models
│   ├── pipeline/           # Ingestion, analysis, theme_mapping, embeddings,
│   │   ├── agents/         # LangGraph nodes (validation, cleaner, finbert,
│   │   │                   #  llm, scoring)
│   │   └── hfi/            # Hedge Fund Intelligence graph (nodes/, prompts/)
│   ├── services/           # Business logic: search, search_answer, query_router,
│   │   ├── market_chatter/ # TickerFlow: collectors, providers, universe, cache
│   │   └── hfi/            # Investor/source/portfolio/alert services, SEC adapter
│   ├── tasks/              # Celery tasks (pipeline_tasks, hfi_jobs, analytics)
│   ├── auth/               # Clerk JWT verification, invite redemption
│   └── analytics/          # Event tracking middleware + daily rollups
├── alembic/versions/       # 001–008 + HFI/TickerFlow/raw-content migrations
├── data/                   # theme_taxonomy.json, etf_mappings.json, FinBERT ONNX
├── web/                    # Next.js 16 app (bun-managed)
│   └── src/app/(app)/      # Authenticated pages; sign-in/sign-up; landing page
├── tests/                  # pytest suite (+ tests/market_chatter/)
└── docs/                   # Architecture & product docs (this file's home)
```

## 3. Pipeline 1 — YouTube Commentary Engine (`src/pipeline/`)

The original core of the product. Five stages run per video (orchestrated in `pipeline/ingestion.py` → `analysis.py` → `theme_mapping.py` → `embeddings.py` → `market_tracking.py`, executed as Celery tasks from `tasks/pipeline_tasks.py`):

1. **Ingestion** — fetch video metadata via YouTube Data API v3; retrieve timestamped transcript segments. Transcript acquisition is tiered: `youtube-transcript-api` (free, primary) → Supadata API (fallback) → `yt-dlp` + local faster-Whisper (`tiny.en`) ASR (last resort). Caption retries are scheduled (captions often lag behind publish).
2. **LLM structured analysis** — transcripts are batched and sent to Claude/OpenAI models which return structured JSON: predictions (direction, confidence, horizon), sentiment, ticker mentions (explicit cashtags + implicit thematic ties), and theme assignments.
3. **Theme & ticker mapping** — claims are linked to the seeded taxonomy in `data/theme_taxonomy.json` (Sector → Industry → Theme → Ticker). Implicit ticker references are resolved; an ETF mapping service (`services/etf_mapping_service.py`, backed by `data/etf_mappings.json`) resolves themes to representative ETFs and prevents ETFs (SPY, XLF, …) from being misread as single-name stocks.
4. **Embeddings** — transcript segments are embedded with OpenAI `text-embedding-3-small` (384-dim) into `pgvector` for semantic search.
5. **Market tracking** — `yfinance` historical prices are matched against each prediction's publish date to compute realized 1-day / 1-week / 1-month returns, grading every prediction as accurate/inaccurate (`performance` tables; daily refresh via Celery Beat).

**Near-real-time discovery (WebSub):** every ingested channel is subscribed to Google's PubSubHubbub hub (`pubsubhubbub.appspot.com`). The hub pushes Atom notifications to `POST /api/websub/callback` (HMAC-signature verified, no quota cost). New uploads emit `video_detected` activity events; Celery then auto-ingests (`auto_ingest_video`), emitting `video_processed` / `video_failed`. Beat renews WebSub leases and runs a rare RSS fallback poll (`DISCOVERY_FALLBACK_POLL_HOURS`). A simulate endpoint (`/api/websub/simulate`, `make simulate-websub`) enables testing without a real publish.

**Channel classification:** `gpt-4o-mini` classifies channels (type/quality) at ingest; scripts like `classify_existing_channels.py` handle backfill.

## 4. Search Engine (`services/search_service.py`, `query_router.py`, `search_answer_service.py`, `search_coverage_service.py`)

Documented in detail in `docs/search_scenarios.md`.

- **Hybrid retrieval:** Postgres FTS (`tsvector`) keyword search + `pgvector` cosine semantic search, fused with Reciprocal Rank Fusion (`RRF, k=60`), capped at `max_per_video=4` segments. Modes: `keyword | semantic | hybrid` (default).
- **Query intent routing (`QueryRouter`):** a heuristic classifier first (free), falling back to `gpt-5.4-nano` (T=0, ~100 tokens) only when heuristics are inconclusive. Intents: `ticker_narrative`, `sentiment_check`, `sector_discovery`, `factual_search`, plus `instrument_type` (stocks vs ETFs) and ticker/sector hints. Sector discovery queries route to a stock universe table (`search_stocks_for_query`); ticker queries to `search_ticker_narrative`.
- **AI answers (`GET /api/search/answer`):** takes the top-12 segment IDs from search results and synthesizes a summary + up to 4 key points with `gpt-5.4-nano` (JSON mode, 8s timeout). The system prompt enforces **per-claim channel attribution**, bans hallucination and bracketed citations. Answers are cached 24h keyed by `sha256(normalized query) + source_segment_ids`; a set-mismatch busts the cache (fixes cross-query poisoning), per-process asyncio locks prevent LLM stampedes, and `<3` segments return `available:false` without paying the LLM.
- **Coverage (`GET /api/search/coverage`):** aggregates how many channels/videos discussed the query in a lookback window (6h cache) to feed the answer's "what we heard" context.
- **Frontend:** React Query with `keepPreviousData`; answer fetch is gated on settled results (fixing a previously documented race where stale segment IDs poisoned cached answers).

## 5. Pipeline 2 — TickerFlow / Market Chatter (`src/pipeline/agents/`, `services/market_chatter/`)

Social sentiment engine, mounted at `/api/v1` (separate from the `/api/tickers` YouTube routes). Ticker universe is currently the **S&P 100** (`universe.py`) to bound provider costs; symbol normalization accepts `BRK.B`-style dots.

- **Collectors** (`collectors/`): Reddit (OAuth), X via `twikit`, StockTwits, news via GDELT; an Adanos gateway adapter exists but is unused (`provider = native_raw`). Every run is recorded in `collection_runs` with per-source status and request counts (quota accounting in `quota_usage`).
- **LangGraph multi-agent graph** (`pipeline/graph.py`, `pipeline/agents/`, `langgraph==1.2.10`) — a compiled state graph with parallel branches:
  - *Agent 2 — Validation:* length, lookback-window, ticker-relevance filters.
  - *Agent 3 — Cleaner:* HTML/URL stripping, cashtag extraction, **MinHash LSH near-dedup** (128 permutations, Jaccard 0.85).
  - *Agent 4 — FinBERT (parallel):* local ProsusAI FinBERT via ONNX (512-token limit) → bullish/bearish/neutral + confidence.
  - *Agent 5 — LLM narrative (parallel):* top-engagement items → catalyst themes + representative quotes.
  - *Agents 8/9 — Scoring & aggregation:* **RISS** = engagement-weighted (sqrt) sentiment mean ×100; **SMS** = mention volume vs 30-day baseline; **OCS v0.1** = `0.70·RISS + 0.30·SMS`; trend = rising (≥65) / falling (≤40) / stable; outputs `ScoreDriverCard`s for the UI.
- **Caching & price overlay:** Redis-backed ticker caches; daily `price_bars` from yfinance enable sentiment-vs-price charts. The dashboard service (`dashboard_service.py`) powers the Overview page and the market-chatter component suite (`web/src/components/market-chatter/`).

## 6. Pipeline 3 — HFI (Hedge Fund Intelligence) (`src/pipeline/hfi/`, `services/hfi/`)

A per-user tracking system for individual investors / funds ("smart money"), exposed at `/api/hfi/*` and surfaced in the **Investors** and **Consensus** pages.

- **Investors** (`investor_service.py`): user-owned records with name, description, and optional **CIK number** (SEC identity). Full CRUD.
- **Sources** (`source_service.py`, `ingestion/`): per-investor content sources — websites, RSS, and an SEC adapter (`sec_adapter.py`) for filings. Raw content is fetched, **content-hashed** (`content_hasher.py`, dedupe), and stored as `content_item` / `raw_content` rows via `raw_ingestion_service.py`.
- **LangGraph HFI pipeline** (`pipeline/hfi/`): nodes for normalizer → entity extractor → thesis extractor → embedder (vector store: `services/hfi/vector_store.py`) → portfolio tracker (`portfolio_node.py` → `portfolio_change` records) → report generator (LLM-written investor reports, `hfi_report`) → alert checker (`hfi_alert` thresholds). Prompts live in `pipeline/hfi/prompts/`; Celery jobs in `tasks/hfi_jobs.py`.
- **Analytics:** `hfi_analytics.py` exposes per-investor stats (content items, reports, unread alerts).
- **Consensus page:** aggregates portfolio positions/changes across tracked investors into a "Smart Money Consensus" view; a Compare page exists but is currently commented out of the sidebar.

## 7. Cross-Cutting Subsystems

### 7.1 Authentication & invites (`src/auth/`, `web/src/components/InviteGate.tsx`)
- Clerk (email+password, Google OAuth, magic link) on the frontend; session JWTs verified server-side (`clerk-backend-api` / PEM) via `auth/dependencies.py::get_current_user`; admin routes gated by `require_admin`.
- **Invite-only gate:** sign-up requires a single-use invite code (`make invite email=...`, `scripts/create_invite.py`, `provision_pilot_users.py`). Codes can be captured pre-signup via `InviteCodeCapture`.

### 7.2 Usage analytics & admin (`src/analytics/`, `api/usage.py`, `api/admin.py`)
- Every authenticated request is instrumented: searches, entity views, page views, pipeline triggers, LLM token spend, per-request latency. Daily rollup tables with a retention policy (`tasks/analytics_tasks.py`).
- `/usage` shows personal stats; `/admin` (admin-only) manages invites and platform-wide metrics. Admin scripts include `promote_admin.py` and `sync_users_from_clerk.py`.

### 7.3 Activity feed (`services/activity_service.py`, `api/activity.py`)
- Idempotent (`event_type`, `youtube_video_id`) activity events — `video_detected` / `video_processed` / `video_failed` — surfaced in the bell-icon Activity feed.

### 7.4 Caching & performance
- Redis: Celery broker + TickerFlow response caches. Postgres: search answers (24h), coverage (6h), ticker caches, query-router heuristic bypass. Performance indexes added in migration `008`; latency audits live in `docs/prod-latency-audit-2026-08-27.md` and `api_performance_chat.md`.

## 8. Data Model (key tables)

| Domain | Tables |
|---|---|
| YouTube core | `channels`, `videos`, `transcript_segments` (with embeddings), `predictions`, `performance`, `themes`, `speaker_tickers` (unique speaker+ticker aggregation), `extracted_mentions` |
| Taxonomy | seeded from `data/theme_taxonomy.json` (Sector → Industry → Theme → Ticker) |
| Social / TickerFlow | `collection_runs`, `content_item`, `raw_content`, `price_bars`, `quota_usage`, `source_snapshot`, `ticker_daily_metric`, `ticker_cache` |
| HFI | `investors`, `hfi_source`, `hfi_report`, `hfi_alert`, `portfolio_change` |
| Search | `search_answer` |
| Platform | `users`, `activity_event`, analytics rollups, invite tables (migration `006`) |

Migrations are Alembic (001–008 plus `e4e38ec36752_add_tickerflow_tables`, `f8a92b113478_add_raw_content_table`, and HFI migrations).

## 9. API Surface (FastAPI)

| Prefix | Purpose |
|---|---|
| `/api/search`, `/api/search/answer`, `/api/search/coverage` | Hybrid search + AI answers + coverage |
| `/api/videos`, `/api/channels` | Video & channel browsing |
| `/api/predictions` | Prediction ledger + accuracy views |
| `/api/tickers` | YouTube-derived ticker stats, sentiment, performance |
| `/api/themes` | Theme taxonomy & narratives |
| `/api/dashboard` | Overview summary aggregates |
| `/api/v1/tickers/{symbol}` (+ `/refresh`, `/health`) | TickerFlow social sentiment |
| `/api/hfi/investors`, `/api/hfi/reports`, `/api/hfi/alerts`, `/api/hfi/analytics` | Smart-money tracking |
| `/api/websub` | Hub callback, subscribe, simulate |
| `/api/activity` | Notification feed |
| `/api/usage`, `/api/admin` | Personal analytics; admin ops |
| `/api/pipeline` | On-demand processing triggers |

Interactive Swagger docs at `/docs` on the API host.

## 10. Frontend (`web/`)

- **Stack:** Next.js 16 App Router, React 19, TypeScript, Tailwind v4 (OKLCH design tokens: `--ink`, `--signal`, `bullish/bearish`, …), shadcn-style primitives, framer-motion, Recharts, `d3-hierarchy` (theme circle-pack), TanStack React Query, Clerk.
- **Routing:** public landing page (`/`) with hero, features, testimonials, invite capture; `(app)` route group for the authenticated product; `sign-in` / `sign-up` catch-all Clerk routes.
- **Notable components:** `CommandPalette` (⌘K), `Sidebar`/`AppShell`/`Topbar`, `DataTable`, `SentimentBadge`, `PredictionSentimentChart` (accuracy halo sized by confidence), `ThemeCirclePack`/`ThemeInspector`, `market-chatter/DashboardOverview`, skeleton loaders (`components/skeletons/`).
- **API client:** typed client in `web/src/lib/api.ts` (interfaces incl. `MCDashboardSummary`, `HfiInvestor`), hooks in `lib/hooks.ts`, analytics helpers in `lib/analytics.ts`. `/api` requests are proxied through a Vercel edge rewrite to the API host (`web/src/proxy.ts`).

## 11. Infrastructure & Deployment

- **Docker Compose** (dev): Postgres+pgvector, Redis, api, worker; a prod compose variant exists. `.github/workflows/deploy.yml` automates deploys to the GCP VM (`deploy/setup-ec2.sh`, `deploy/nginx.conf`, Let's Encrypt TLS).
- **LLM economics:** all chat/extraction/routing workloads on `gpt-5.4-nano` (~$1–5/mo); `gpt-4o-mini` only for channel classification; embeddings `text-embedding-3-small`. FinBERT + Whisper run locally on the VM.
- **Cost profile (from `COSTING.md`):** ≈$625–790/mo total, of which Cloud SQL (~$600–750) dominates; downsizing would cut ~75% of per-user infra cost. Unit costs: <$0.01/video analyzed, ~$0.001–0.005/search, ~$0.70–0.90/user/month at growth scale.

## 12. Testing & Tooling

- `make test` (pytest) — unit tests cover ticker extraction, FinBERT service, LangGraph pipeline, search grouping/answers/coverage, WebSub, auth, analytics, ETF mapping, social context, instrument-type routing, plus a dedicated `tests/market_chatter/` suite.
- `make lint` / `make format` (ruff); frontend `bun run lint` (eslint-config-next). `make process-video id=...` and `make backfill channel=...` run the pipeline manually.

## 13. Known Trade-offs & Watch Items

- **Single-VM backend** (`e2-medium`, 1 vCPU / 4 GB) runs API + Celery + Beat + Whisper + FinBERT — fine at beta scale, first bottleneck at public-launch traffic.
- **Cloud SQL sizing** is the dominant cost; downsizing is the single biggest lever (per `COSTING.md`).
- **yfinance is unofficial** (ToS risk) as the market-data source; FinBERT's 512-token limit truncates long social posts.
- **TickerFlow universe** is limited to the S&P 100 by design (budget control).
- **Product-name drift:** repo/internal docs still say "yt-chatter" / "SentimentAI" / "Market Chatter"; only user-facing surfaces and `COSTING.md` say "Carry" — a renaming pass is pending.
- **Security note (from audit):** the live Clerk secret in `web/.env.prod` is gitignored but sensitive; rotate if ever shared.

## 14. Product Lineage (for context)

1. **SentimentAI blueprint** (`docs/Initial_Plan.md`) — an ambitious 10-agent, seven-score platform vision.
2. **Competitive analysis** (`docs/competitve_analysis.md`) — found the "sentiment API" layer commoditized; recommended differentiating on narrative intelligence, credibility modeling, and validated backtesting.
3. **YT Chatter build-out** — shipped the YouTube commentary engine, hybrid search, prediction verification, and WebSub ingestion first.
4. **Carry** — the current multi-source product: commentary intelligence + social sentiment (TickerFlow) + smart-money tracking (HFI), under the "Hear what the market is saying" positioning, in invite-only beta.





