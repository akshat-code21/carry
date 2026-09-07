# Carry 📈

> **Hear what the market is saying.**

**Carry** is an end-to-end market-commentary intelligence platform. It ingests finance commentary from **YouTube, Reddit, X/Twitter, StockTwits, and news**, uses LLMs and NLP to extract **tickers, predictions, sentiment, and themes** timestamped to the second, and holds every call **accountable against real market outcomes** from `yfinance` price history.

- **Product name:** Carry — live at `carry-fin.vercel.app` (frontend) and `carry-api.akshat21.me` (API)
- **Repo name:** `yt-chatter` (YouTube-first origin); internal vocabulary also says "Market Chatter" / "TickerFlow"
- **Status:** invite-only beta

> ⚠️ **Naming note (important for context):** the repo, package, tables, and most docs say `yt-chatter` / `market-chatter` / `TickerFlow`; only user-facing surfaces say **Carry**. They are the same product. A renaming pass is planned but not yet done — when reading code, map: `yt-chatter` → Carry, `market-chatter`/`TickerFlow` → the social-sentiment engine, `HFI` → the smart-money (hedge-fund intelligence) engine.

This README is written to be a **complete project brief**: if you (a human or an AI agent) read only this file, you should understand what the product does, how every subsystem works, where the code lives, and how to run and extend it.

---

## 1. Product Pillars (What Carry Does)

### 1.1 Commentary Intelligence Engine (YouTube-first)
- Monitors curated finance YouTube channels; detects new uploads **near real-time via WebSub** (Google's free PubSubHubbub hub — zero YouTube API quota for discovery).
- Transcripts every video with **tiered fallbacks**: `youtube-transcript-api` → Supadata API → `yt-dlp` + local **faster-Whisper** ASR (`WHISPER_MODEL_SIZE`, default `tiny.en`).
- Failed caption fetches are retried on a schedule (`TRANSCRIPT_RETRY_DELAYS_MINUTES=0,15,60,360,1440` — captions often lag behind publish).
- An LLM pipeline (Claude / OpenAI) extracts structured JSON per video: **predictions** (direction, confidence, horizon), **sentiment**, **ticker mentions** (explicit cashtags + implicit thematic ties), and **theme assignments**.
- Commentary maps into a seeded hierarchy: **Sector → Industry → Theme → Ticker** (e.g., Tech → Semiconductors → AI Chips → NVDA, AMD) from `data/theme_taxonomy.json`. An ETF mapping service (`data/etf_mappings.json`) prevents ETFs (SPY, XLF…) being misread as single-name stocks.

### 1.2 Hybrid Search & AI Answers
- **Hybrid retrieval** over transcript segments: Postgres FTS (`tsvector`) keyword search + `pgvector` semantic search (OpenAI `text-embedding-3-small`, **384-dim**), fused with **Reciprocal Rank Fusion (RRF, k=60)**, capped at `max_per_video=4` segments. Modes: `keyword | semantic | hybrid` (default).
- **Query intent routing** (`services/query_router.py`): free heuristic classifier first; falls back to a small OpenAI model (T=0, ~100 tokens) only when heuristics are inconclusive. Intents route between stock-picks vs. sentiment-checks vs. factual questions vs. ETF discovery.
- **AI answer summaries with mandatory attribution**: every synthesized claim names the creator who said it, with clickable clip citations (`search_answer` table, cached 24h). Search coverage snapshots are cached 6h.

### 1.3 Predictions, Verified
- Every prediction is logged at extraction time, then scored against what the market actually did — **1-day / 1-week / 1-month returns** from `yfinance` historical prices matched to the video publish date.
- Daily refresh via Celery Beat. Users can see **who's consistently right — not just who's loud** (per-speaker accuracy via `speaker_tickers`, prediction ledger, accuracy charts sized by confidence).

### 1.4 Social Sentiment Signal (TickerFlow / Market Chatter)
- **Native raw ingestion** from Reddit (OAuth or public JSON fallback), StockTwits (symbol stream), Financial News (Google/Yahoo RSS), and Twitter/X cashtag chatter → `raw_content` table with **SHA-256 content-hash dedup** (idempotent re-runs).
- Scores chatter with a **locally-hosted FinBERT ONNX model** (pre-loaded at API startup to avoid a ~4s cold-start penalty) plus LLM narrative extraction, via a **LangGraph multi-agent graph** (see §5.4).
- Produces transparent, formula-driven scores: **RISS** (Retail Investor Sentiment Score), **SMS** (Social Mention Score), and composite **OCS = 0.70·RISS + 0.30·SMS**, normalized across sources. Universe: **S&P 100 by design** (budget control).
- Provider selection via `SENTIMENT_PROVIDER` (`native_raw` default; `adanos`, `fixture` for dev/tests) and `PRICE_PROVIDER` (`yfinance_local`).

### 1.5 Smart-Money Tracking (HFI — Hedge Fund Intelligence)
- Track individual investors/funds; ingest their published content (websites, letters, **SEC filings** via adapter) into `hfi_source`.
- A second **LangGraph pipeline** (`src/pipeline/hfi/`) runs: `normalizer → chunker → entity_extractor → thesis_extractor → embedder → portfolio_node → report_generator → alert_checker` (thesis step skipped for filings; reports only when triggered).
- Extracts theses and **portfolio changes** (`portfolio_change`), generates investor **reports** and **alerts**, and aggregates a cross-investor **Smart Money Consensus** view.

### 1.6 Platform: Auth, Analytics, Activity
- **Clerk authentication** (email+password, Google OAuth, magic link) with an **invite-only signup gate**; session JWTs verified server-side on every request; role-based admin.
- **Usage analytics**: every authenticated request instrumented (searches, entity views, page views, pipeline triggers, LLM token spend, per-request latency) with daily rollups and a retention policy.
- **Activity feed**: idempotent `video_detected` / `video_processed` / `video_failed` events surfaced in a bell-icon feed.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js 16, bun)                    │
│  Landing │ Search │ Dashboard │ Videos │ Channels │ Themes      │
│  Tickerflow │ Investors │ Consensus │ Activity │ Usage │ Admin  │
│  Clerk auth (invite gate) · React Query · Recharts · d3-hierarchy│
└──────────────────────────┬──────────────────────────────────────┘
                           │ REST (JSON) — /api/* proxied via
                           │ next.config.ts rewrite → API host
┌──────────────────────────▼──────────────────────────────────────┐
│                    BACKEND (Python 3.12)                         │
│  FastAPI (uvicorn) · Clerk JWT verification · AnalyticsMiddleware│
│  Routers: search, videos, predictions, tickers, themes,          │
│  channels, dashboard, market_chatter (/api/v1), hfi_*, websub,   │
│  activity, usage, admin, pipeline, auth                          │
└───────────┬──────────────────────────────────┬──────────────────┘
            │                                  │
┌───────────▼───────────────────┐  ┌───────────▼──────────────────┐
│      PROCESSING PIPELINES     │  │          STORAGE             │
│ 1. YouTube ingestion (WebSub) │  │ PostgreSQL 16 + pgvector     │
│ 2. LLM structured analysis    │  │  (Cloud SQL in prod)         │
│ 3. Theme/ticker/ETF mapping   │  │ Redis 7 (Celery broker,      │
│ 4. Embeddings (384-dim)       │  │  TickerFlow + JsonCache)     │
│ 5. Market outcome tracking    │  │ FinBERT ONNX + faster-Whisper│
│ 6. TickerFlow LangGraph graph │  │  run locally on the API host │
│ 7. HFI LangGraph pipeline     │  └──────────────────────────────┘
└───────────────────────────────┘
```

**Production topology:** a single GCP VM (`e2-medium`, `asia-southeast1`) runs all backend Docker containers (`api`, `worker`, `beat`, nginx with Let's Encrypt TLS); Postgres on **GCP Cloud SQL**; Redis on **Aiven**; frontend on **Vercel**. GitHub Actions (`.github/workflows/deploy.yml`) automates deploys.

---

## 3. Tech Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.12, FastAPI, Uvicorn, Pydantic v2 + pydantic-settings, `uv` package manager |
| **Database** | PostgreSQL 16 + `pgvector`, SQLAlchemy 2.0 (async), AsyncPG, Alembic, psycopg2 (sync) |
| **Task queue** | Celery + Redis 7 (broker & result backend), Celery Beat schedules |
| **LLMs** | Anthropic `claude-sonnet-4` (claim extraction), OpenAI `gpt-4o` (chat), `text-embedding-3-small` (embeddings, 384-dim), small OpenAI model for query routing, `gpt-4o-mini` for channel classification |
| **NLP / ML** | LangGraph (multi-agent graphs), LangChain core/splitters/postgres, FinBERT ONNX (`onnxruntime` + `transformers`), faster-Whisper (ASR fallback), `datasketch` (MinHash LSH dedup) |
| **Data sources** | YouTube Data API v3, `youtube-transcript-api`, Supadata (fallback), `yt-dlp`, `yfinance`, `fredapi`, Reddit/StockTwits/Twitter/news collectors, `curl-cffi`, `twikit` |
| **Auth** | Clerk (`@clerk/nextjs` frontend, `clerk-backend-api` JWT verification on FastAPI), invite-only gate |
| **Frontend** | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4 (OKLCH design tokens), TanStack React Query, Recharts, `d3-hierarchy` (theme circle-pack), `lightweight-charts`, framer-motion, lucide icons, shadcn-style primitives, `bun` |
| **Infra & tooling** | Docker + Docker Compose (dev & prod variants), nginx, GitHub Actions, Makefile, `ruff`, `pytest`, structlog |

---

## 4. Prerequisites

Ensure you have the following installed on your local system before getting started:

1. **Python**: `3.12` or higher
2. **`uv`**: High-performance Python package manager ([Installation Guide](https://docs.astral.sh/uv/getting-started/installation/))
3. **`bun`**: All-in-one JavaScript runtime & package manager ([Installation Guide](https://bun.sh/))
4. **Docker & Docker Compose**: For running PostgreSQL (`pgvector`) and Redis containers

---

## 5. Quick Start Guide (Local Development)

Follow these steps to set up the project locally for development and contributions.

### 1. Clone the Repository & Configure Environment

```bash
# Clone the repository
git clone https://github.com/akshat-code21/yt_chatter.git
cd yt-chatter

# Create environment configuration file from template
cp .env.example .env
```

Open `.env` and fill in your API keys:
- `YOUTUBE_API_KEY`: YouTube Data API v3 key
- `OPENAI_API_KEY`: OpenAI API Key (used for vector embeddings and chat)
- `ANTHROPIC_API_KEY`: Anthropic Claude API Key (used for structured LLM claim extraction)
- `FRED_API_KEY`: *(Optional)* Federal Reserve Economic Data API key
- `CLERK_SECRET_KEY`: Clerk secret key — **required**, every API route is authenticated (see §15)
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`: set in `web/.env.local` for the frontend

Optional: `PUBLIC_BASE_URL` + `WEBSUB_SECRET` (WebSub push discovery, §14), `REDDIT_CLIENT_ID`/`REDDIT_CLIENT_SECRET` (TickerFlow OAuth mode).

---

### 2. Start Infrastructure Services (Database & Redis)

Start PostgreSQL (with `pgvector`) and Redis containers:

```bash
make up-db
```
*Alternatively: `docker compose up -d postgres redis`*

---

### 3. Backend Setup & Data Seeding

Install backend dependencies using `uv`, run database migrations, and seed the theme taxonomy:

```bash
# Install Python dependencies into virtual environment
uv sync

# Run database migrations with Alembic
make migrate

# Seed initial theme taxonomy (data/theme_taxonomy.json)
make seed
```

---

### 4. Run the API Server & Worker

In your primary terminal, start the FastAPI dev server:

```bash
make run
```
> The API will be available at **`http://localhost:8000`**  
> Interactive Swagger API Documentation: **`http://localhost:8000/docs`**

In a **separate terminal**, start the Celery worker process:

```bash
make worker
```

---

### 5. Frontend Setup (using Bun)

In a new terminal window, navigate to the `web` directory and start the Next.js development server:

```bash
cd web

# Install frontend dependencies using Bun
bun install

# Start Next.js development server
bun dev
```

> The web application will be accessible at **`http://localhost:3000`**

---

## 6. Alternative: Full-Stack Docker Setup

If you prefer running the entire stack (API, Worker, Postgres, Redis) in Docker containers:

```bash
# Build and launch all services in detached mode
make up

# Stop all services
make down
```

---

## 7. Developer Command Reference (`Makefile`)

The project includes a `Makefile` with convenience shortcuts for common development tasks:

| Command | Description |
|---|---|
| `make up` | Build and start all services via Docker Compose |
| `make up-db` | Start only PostgreSQL & Redis background containers |
| `make down` | Stop and remove Docker containers |
| `make migrate` | Apply latest Alembic database migrations (`uv run alembic upgrade head`) |
| `make migration msg="..."` | Generate a new auto-detected Alembic migration |
| `make seed` | Seed the database with default theme taxonomy from `data/theme_taxonomy.json` |
| `make run` | Launch FastAPI app locally with hot reloading (`http://localhost:8000`) |
| `make worker` | Launch Celery task worker for background video processing |
| `make beat` | Launch Celery Beat scheduler (WebSub renewals, RSS fallback, daily performance) |
| `make invite email=...` | Create a single-use invite code for the signup gate |
| `make promote-admin email=...` | Promote an existing user to admin |
| `make sync-users` | Reconcile app users with Clerk (delete stale rows; `dry-run=1` to preview) |
| `make provision-users csv=users.csv` | Bulk-provision pilot users from a CSV with generated credentials |
| `make subscribe-websub` | Queue WebSub subscribe for all channels (needs `PUBLIC_BASE_URL`) |
| `make simulate-websub channel=<ID> video=<ID>` | Fake a "channel just uploaded" hub push (`mode=full` or `discovery_only`) |
| `make test` | Run test suite via `pytest` |
| `make lint` | Run code quality & formatting checks via `ruff` |
| `make format` | Automatically fix formatting issues via `ruff format` |
| `make process-video id=<ID>` | Process a single YouTube video ID through the ingestion pipeline |
| `make backfill channel=<ID>` | Trigger backfill pipeline for a channel ID |

---

## 8. Repository Layout

```text
yt-chatter/
├── alembic/                  # Alembic migrations (001–008 core + HFI, TickerFlow, raw_content)
│   └── versions/
├── data/                     # Seed/static data
│   ├── theme_taxonomy.json   # Sector → Industry → Theme → Ticker hierarchy
│   ├── etf_mappings.json     # Theme → representative ETF mappings
│   └── models/               # FinBERT ONNX model artifacts
├── deploy/                   # Production deploy helpers (nginx.conf, setup-ec2.sh)
├── docs/                     # Architecture & product docs (deep dives, plans, audits)
├── scripts/                  # Ops utilities (invites, WebSub sim, FinBERT export, user sync…)
├── src/                      # Backend Python package
│   ├── main.py               # FastAPI entrypoint (lifespan: TickerFlow init, FinBERT preload)
│   ├── config.py             # pydantic-settings env config
│   ├── database.py           # Async SQLAlchemy engine/session factory
│   ├── api/                  # Routers (see API Surface section)
│   ├── auth/                 # Clerk JWT verification, user service, invite redemption
│   ├── analytics/            # Request middleware + daily rollup service
│   ├── models/               # SQLAlchemy ORM models (~28 tables across all engines)
│   ├── schemas/              # Pydantic schemas (agent pipeline, HFI, market chatter)
│   ├── pipeline/             # YouTube pipeline: ingestion, analysis, theme_mapping,
│   │   │                     #   embeddings, market_tracking
│   │   ├── graph.py          # TickerFlow LangGraph graph assembly
│   │   ├── agents/           # TickerFlow LangGraph agent nodes
│   │   └── hfi/              # HFI LangGraph graph (nodes/, prompts/)
│   ├── services/             # Business logic: search*, query_router, llm, finbert,
│   │   │                     #   market_data, performance, websub, youtube…
│   │   ├── market_chatter/   # TickerFlow collectors/providers/cache/universe
│   │   └── hfi/              # HFI investor/source/portfolio/alert services, SEC adapter
│   └── tasks/                # Celery tasks (pipeline_tasks, hfi_jobs, analytics_tasks)
├── tests/                    # pytest suite (+ tests/market_chatter/)
├── web/                      # Frontend Next.js 16 app (bun-managed)
│   └── src/
│       ├── app/              # App Router: landing page, sign-in/sign-up, (app)/ route group
│       ├── components/       # AppShell, Sidebar, CommandPalette, DataTable, landing/,
│       │                     # market-chatter/, themes/, ui/ primitives, skeletons/
│       └── lib/              # Typed API client (api.ts), hooks, analytics helpers
├── docker-compose.yml        # Dev: postgres, redis, api, worker, beat
├── docker-compose.prod.yml   # Prod: api, worker, beat (uses .env.prod)
├── Dockerfile                # Backend image (uv + uvicorn/celery)
├── Makefile                  # Developer commands
├── pyproject.toml            # Python deps + ruff/pytest config
└── README.md
```

---

## 9. Subsystem Deep Dive

### 9.1 YouTube commentary engine (`src/pipeline/`)
Five stages per video, orchestrated as Celery tasks (`tasks/pipeline_tasks.py`): ingestion → LLM analysis → theme/ticker/ETF mapping → embeddings → market tracking (detailed in §12). New-upload discovery is push-based via **WebSub** (see §14).

### 9.2 Search engine (`services/search_service.py`, `query_router.py`, `search_answer_service.py`, `search_coverage_service.py`)
- Hybrid FTS + `pgvector` retrieval fused with RRF (k=60); per-video cap of 4 segments; modes `keyword | semantic | hybrid`.
- Query intent routing: heuristics first (free), small OpenAI model as fallback.
- AI answers with mandatory creator attribution + clip citations (cached 24h); coverage snapshots (cached 6h). See `docs/search_scenarios.md`.

### 9.3 TickerFlow / Market Chatter (`services/market_chatter/`, `pipeline/agents/`)
- **Collectors** (`collectors/`): `RedditCollector` (OAuth, public-JSON fallback), `StockTwitsCollector` (symbol stream), `NewsCollector` (Google/Yahoo News RSS), `TwitterCollector` (cashtag chatter) — all return Pydantic `RawItem` objects.
- **`RawIngestionService`** runs collectors concurrently (`asyncio.gather`) and upserts to `raw_content` with SHA-256 content-hash dedup (idempotent re-runs).
- **`NativeRawProvider`** computes daily mention buckets / buzz / net sentiment and invokes the LangGraph agent pipeline for FinBERT + LLM narrative scoring.
- **`CollectionService`** is initialized at API startup (lifespan) with a Redis `JsonCache`; universe management in `universe.py` (S&P 100); runs tracked in `collection_run`.
- Architecture docs: `docs/native_raw_ingestion_architecture.md`, `docs/langgraph_multi_agent_pipeline.md`.

### 9.4 HFI — Hedge Fund Intelligence (`services/hfi/`, `pipeline/hfi/`, `api/hfi_*.py`)
- **Sources:** `ingestion/sec_adapter.py` (SEC filings) + `base_adapter.py` (websites/letters) with `content_hasher.py` dedup; vector storage via `services/hfi/vector_store.py` (`langchain-postgres`).
- **Graph:** `pipeline/hfi/pipeline.py` — normalizer → chunker → entity extraction → thesis extraction (skipped for filings) → embedder → portfolio changes → conditional report generation → alert checking.
- **Services:** `investor_service`, `source_service`, `portfolio_service`, `alert_service`; Celery jobs in `tasks/hfi_jobs.py`.
- UI: `/investors`, `/investors/[id]`, plus the cross-investor **Consensus** page.

### 9.5 Auth, analytics & activity (cross-cutting)
- **Auth** (`src/auth/`): Clerk session JWTs verified via `clerk-backend-api` (JWKS by default; optional static PEM), `azp` authorized-party checks, invite-only signup, `require_admin` gating. First signup is auto-promoted admin; extra bootstrap admins via `ADMIN_CLERK_USER_IDS`.
- **Analytics** (`src/analytics/`): `AnalyticsMiddleware` logs every authenticated request (latency, user attribution); daily rollups + retention cleanup via Celery Beat; `/usage` (personal) and `/admin` (platform metrics + invite management).
- **Activity feed** (`services/activity_service.py`): idempotent `(event_type, youtube_video_id)` events powering the bell-icon feed.

---

## 10. API Surface (FastAPI)

All user-facing routers require an authenticated Clerk session (exceptions noted). Swagger docs at `/docs` on the API host.

| Prefix | Purpose |
|---|---|
| `/api/search`, `/api/search/answer`, `/api/search/coverage` | Hybrid search, AI answers, coverage |
| `/api/videos`, `/api/channels` | Video & channel browsing |
| `/api/predictions` | Prediction ledger + accuracy views |
| `/api/tickers` | YouTube-derived ticker stats, sentiment, performance |
| `/api/themes` | Theme taxonomy & narratives |
| `/api/dashboard` | Overview summary aggregates |
| `/api/v1/tickers/{symbol}` (+ `/refresh`, `/health`) | TickerFlow social sentiment |
| `/api/hfi/investors`, `/api/hfi/reports`, `/api/hfi/alerts`, `/api/hfi/analytics` | Smart-money tracking |
| `/api/websub` | Hub callback (HMAC-verified, public), subscribe, simulate (admin-gated) |
| `/api/activity` | Notification feed |
| `/api/usage`, `/api/admin` | Personal analytics; admin ops |
| `/api/pipeline` | On-demand processing triggers (self-guards: auth + admin) |
| `/api/auth` (auth router) | Session sync, invite redemption |
| `/`, `/health` | Public infrastructure probes |

---

## 11. Background Jobs (Celery Beat)

| Schedule (UTC) | Task | Purpose |
|---|---|---|
| every 6h at :30 | `pipeline.renew_websub_leases` | Renew WebSub subscriptions before lease expiry |
| daily 06:00 | `pipeline.update_performance` | Re-grade predictions against latest prices |
| daily 01:00 | `analytics.aggregate_platform_daily` | Finalize previous day's analytics rollups |
| daily 03:30 | `analytics.retention_cleanup` | Prune raw analytics rows per retention policy |
| every `DISCOVERY_FALLBACK_POLL_HOURS` at :15 | `pipeline.poll_channels_for_new_videos` | RSS fallback if WebSub misses (0 disables) |

Worker runs with `prefetch=1` (one task at a time, respecting API rate limits); HFI jobs live in `tasks/hfi_jobs.py`.

---

## 12. Data Pipeline Workflow

### YouTube commentary pipeline (per video, Celery-orchestrated)
1. **Ingestion (`src/pipeline/ingestion.py`)** — fetch metadata via YouTube Data API v3; retrieve timestamped transcript segments. Transcript acquisition is tiered: `youtube-transcript-api` (free, primary) → Supadata (fallback) → `yt-dlp` + local faster-Whisper ASR (last resort). Failed fetches are retried per `TRANSCRIPT_RETRY_DELAYS_MINUTES`.
2. **LLM analysis (`src/pipeline/analysis.py`)** — transcripts are batched and sent to Claude/OpenAI which return structured JSON: predictions (direction, confidence, horizon), sentiment, ticker mentions (explicit cashtags + implicit thematic ties), and theme assignments.
3. **Theme & ticker mapping (`src/pipeline/theme_mapping.py`)** — links claims to the seeded taxonomy; resolves implicit ticker references; `services/etf_mapping_service.py` resolves themes to representative ETFs and prevents ETFs (SPY, XLF, …) being misread as single-name stocks.
4. **Embeddings (`src/pipeline/embeddings.py`)** — transcript segments embedded with OpenAI `text-embedding-3-small` (384-dim) into `pgvector` for semantic search.
5. **Market tracking (`src/pipeline/market_tracking.py`)** — `yfinance` historical prices matched against each prediction's publish date to compute realized 1-day / 1-week / 1-month returns, grading accuracy (daily refresh via Celery Beat).

### TickerFlow social-sentiment graph (`src/pipeline/agents/`, `src/pipeline/graph.py`)
A compiled **LangGraph** state-graph (`PipelineGraphState` with `Annotated` reducers `operator.add` / `operator.or_` for safe parallel-branch merging):

```
START → Agent 2: Validation (length / lookback window / cashtag relevance)
      → Agent 3: Cleaner + MinHash LSH dedup (datasketch, Jaccard 0.85)
      → ┌ Agent 4: FinBERT ONNX inference (ProsusAI/finbert, softmax → bull/bear/neutral)
        └ Agent 5: LLM narrative extraction (catalyst themes, key quotes)  [parallel]
      → Agent 8/9: Scoring & aggregation (RISS, SMS, OCS, trend, driver cards)
      → END
```

- **RISS** = engagement-weighted (√-scaled) average of FinBERT sentiment probabilities × 100.
- **SMS** = mention volume relative to baseline benchmark.
- **OCS** = `0.70·RISS + 0.30·SMS`; trend is `rising` (≥65), `falling` (≤40), else `stable`.
- Invoked by `NativeRawProvider` (`services/market_chatter/providers.py`) which powers `/api/v1/tickers/{symbol}` and the `/tickerflow` UI.

### HFI smart-money graph (`src/pipeline/hfi/pipeline.py`)
```
START → normalizer → chunker → entity_extractor → thesis_extractor
      → embedder → portfolio_node → report_generator → alert_checker → END
```
Conditional edges: thesis extraction is skipped for `content_type == "filing"`; report generation runs only when `report_triggered` is set. Chunks are 4000/400-char LangChain splits; embeddings go to a `langchain-postgres` vector store.

---

## 13. Data Model (key tables)

| Domain | Tables |
|---|---|
| YouTube core | `channels`, `videos`, `transcript_segments` (with embeddings), `predictions`, `performance`, `themes`, `speaker_tickers` (unique speaker+ticker aggregation), `extracted_mentions` |
| Taxonomy | seeded from `data/theme_taxonomy.json` (Sector → Industry → Theme → Ticker) |
| Social / TickerFlow | `collection_runs`, `content_item`, `raw_content`, `price_bars`, `quota_usage`, `source_snapshot`, `ticker_daily_metric`, `ticker_cache` |
| HFI | `investors`, `hfi_source`, `hfi_report`, `hfi_alert`, `portfolio_change` |
| Search | `search_answer` |
| Platform | `users`, `activity_event`, analytics rollups, invite tables (migration `006`) |

Migrations are Alembic: `001`–`008` (core, FinBERT columns, channel type, WebSub/activity, auth & analytics, search answers, performance indexes) plus `add_hfi_tables`, `add_tickerflow_tables`, `add_raw_content_table`, and a portfolio-ticker nullability fix.

---

## 14. Automatic channel monitoring (WebSub)

Once a channel is backfilled, future uploads are discovered automatically via **YouTube WebSub** (Google’s free PubSubHubbub hub at `pubsubhubbub.appspot.com`). No YouTube API quota is used for the push itself.

### Flow

1. App subscribes each channel’s Atom feed topic to the hub with callback `{PUBLIC_BASE_URL}/api/websub/callback`.
2. On new upload, the hub POSTs Atom XML → API verifies signature → Celery discovers the video → activity `video_detected`.
3. `auto_ingest_video` fetches captions with retries (captions often lag after publish), then runs the normal process pipeline → activity `video_processed` (or `video_failed`).
4. Celery Beat renews WebSub leases and optionally runs a rare RSS fallback poll.

### Local testing with ngrok

```bash
# terminal 1 - API + worker + beat (or: make up)
make up-db && make migrate
make run          # :8000
make worker       # separate terminal
make beat         # separate terminal

# terminal 2 - public HTTPS tunnel to the API
ngrok http 8000
# copy the https URL, e.g. https://abc123.ngrok-free.app
```

Add to `.env` (no trailing slash):

```env
PUBLIC_BASE_URL=https://abc123.ngrok-free.app
WEBSUB_SECRET=some-long-random-string
```

Restart the API, then:

```bash
make subscribe-websub
```

Watch API logs for a hub **GET** verification on `/api/websub/callback`. New uploads on subscribed channels should appear under **Activity** in the UI (bell icon).

**Note:** Free ngrok URLs change on restart - update `PUBLIC_BASE_URL` and run `make subscribe-websub` again.

### Test “new upload” without waiting for a real publish

You do **not** need to wait for Prof G (or any channel) to upload. Simulate the same Atom push the Google hub would send:

```bash
# discovery only → Activity "Detected" (no LLM)
make simulate-websub channel=UCp4CBeq4nzeg9smAvdjPrig video=SOME_UNUSED_ID mode=discovery_only

# full path → Detected → process → Ready
# Prefer a REAL YouTube video id that is NOT already in your DB
# (e.g. an older episode you never backfilled):
make simulate-websub channel=UCp4CBeq4nzeg9smAvdjPrig video=REAL_YOUTUBE_VIDEO_ID mode=full
```

Or `POST /api/websub/simulate` with JSON body  
`{ "youtube_channel_id", "youtube_video_id", "title?", "mode": "full"|"discovery_only" }`.

| Goal | What to do |
|---|---|
| Test activity “Detected” only | `mode=discovery_only` with any unused video id |
| Test full auto pipeline | `mode=full` + real video id **not** in DB yet |
| Test live Google hub push | Wait for a real new upload on a subscribed channel (or publish to a test channel you control) |

### Related env vars

See `.env.example` for `WEBSUB_*`, `DISCOVERY_FALLBACK_POLL_HOURS`, and `TRANSCRIPT_RETRY_DELAYS_MINUTES`.

---

## 15. Authentication & Usage Analytics

The API is fully authenticated (Clerk session JWTs) with an **invite-only
signup gate**. All user activity - searches, entity views, page views,
pipeline triggers, LLM token spend, per-request latency - is tracked in the
app's own Postgres with daily rollups and a retention policy. Personal usage
is visible at `/usage`; admins manage invites and platform metrics at
`/admin`.

Setup: create a Clerk app, fill `CLERK_*` vars in `.env` and
`NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` in `web/.env.local`, then run
`make migrate`. Full guide: **[docs/authentication.md](docs/authentication.md)**.

Quick invite creation:

```bash
make invite email=friend@example.com   # prints a single-use code
```

---

## 16. Environment Variables

All configuration flows through `src/config.py` (pydantic-settings) reading `.env`. See `.env.example` for the full annotated template. Key groups:

| Group | Variables |
|---|---|
| **Storage** | `DATABASE_URL` (asyncpg), `DATABASE_URL_SYNC`, `REDIS_URL` |
| **APIs & LLMs** | `YOUTUBE_API_KEY`, `ANTHROPIC_API_KEY` + `ANTHROPIC_MODEL`, `OPENAI_API_KEY` + `OPENAI_MODEL`, `FRED_API_KEY` (optional), `SUPADATA_API_KEY` (transcript fallback) |
| **Embeddings** | `EMBEDDING_MODEL` (`text-embedding-3-small`), `EMBEDDING_DIMENSIONS` (384) |
| **WebSub discovery** | `PUBLIC_BASE_URL` (empty disables WebSub; RSS poll fallback still works), `WEBSUB_HUB_URL`, `WEBSUB_SECRET`, `WEBSUB_LEASE_SECONDS`, `WEBSUB_RENEW_MARGIN_HOURS`, `DISCOVERY_FALLBACK_POLL_HOURS` |
| **Transcripts** | `TRANSCRIPT_RETRY_DELAYS_MINUTES` (`0,15,60,360,1440`), `WHISPER_MODEL_SIZE` (`tiny.en` default) |
| **Clerk auth** | `CLERK_SECRET_KEY` (required), `CLERK_JWT_KEY` (optional static PEM — leave empty; JWKS is rotation-safe), `CLERK_AUTHORIZED_PARTIES` (azp origins), `ADMIN_CLERK_USER_IDS` |
| **Usage analytics** | `ANALYTICS_ENABLED` (true), `ANALYTICS_RETENTION_DAYS` (180; rollups kept forever) |
| **TickerFlow** | `SENTIMENT_PROVIDER` (`native_raw`\|`adanos`\|`fixture`), `PRICE_PROVIDER` (`yfinance_local`\|`fixture`), `ADANOS_*`, `REDDIT_CLIENT_ID`/`REDDIT_CLIENT_SECRET` (blank = public JSON), `TWITTER_*`, `PILOT_WATCHLIST` (`AAPL,NVDA`), `ENABLE_WATCHLIST_WORKER` |
| **Frontend (web/.env.local)** | `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `NEXT_PUBLIC_API_URL` (API host for the `/api` rewrite) |
| **Misc** | `APP_ENV`, `LOG_LEVEL`, `API_CORS_ORIGINS` |

---

## 17. Deployment

**Dev:** `make up` runs the full stack in Docker (`postgres`, `redis`, `api`, `worker`, `beat`); `make down` stops it. Source dirs are volume-mounted for hot reload.

**Prod:** GitHub Actions (`.github/workflows/deploy.yml`) deploys to a single GCP VM (`e2-medium`):
- Docker Compose (`docker-compose.prod.yml`, uses `.env.prod`) runs `api`, `worker`, `beat` behind **nginx** with Let's Encrypt TLS (`deploy/nginx.conf`, `deploy/setup-ec2.sh`).
- **PostgreSQL** on GCP Cloud SQL; **Redis** on Aiven; **frontend** on Vercel (API requests proxied via the Next.js rewrite to `carry-api.akshat21.me`).
- Health check: `GET /health` reports environment, configured API keys, and TickerFlow provider status.
- Cost profile & LLM economics documented in `COSTING.md` (Cloud SQL dominates; ≈$625–790/mo total at beta scale).

---

## 18. Testing & Code Quality

Before opening a pull request, run the test suite and verify code quality checks:

```bash
# Run backend test suite (pytest; includes tests/market_chatter/)
make test

# Run just the LangGraph agent pipeline tests
uv run pytest tests/test_langgraph_pipeline.py

# Check linting and formatting (ruff)
make lint

# Auto-format Python code
make format

# Check frontend linting (eslint)
cd web && bun run lint
```

Backend tests cover ticker extraction, FinBERT service, the LangGraph agent pipeline, search grouping/answers/coverage, WebSub, auth, analytics, ETF mapping, social context, instrument-type routing, YouTube transcript handling, and the `market_chatter` collector/provider suite. Run manually-triggered pipeline work with `make process-video id=<ID>` and `make backfill channel=<ID>`.

---

## 19. Documentation Map

Deeper docs live in `docs/` — useful when this README isn't enough:

| Document | Contents |
|---|---|
| `docs/carry_deep_dive.md` + `docs/carry_high_level_summary.md` | The most complete architecture + product brief (engineer's map) |
| `docs/langgraph_multi_agent_pipeline.md` | TickerFlow agent graph mechanics, state reducers, scoring formulas |
| `docs/native_raw_ingestion_architecture.md` | Collector architecture, `RawItem` contract, dedup strategy |
| `docs/search_scenarios.md` | Search engine behavior across query types |
| `docs/authentication.md` | Clerk setup, invites, admin bootstrap |
| `docs/data_collection_*.md` | Data-source strategy (native vs. OSS vs. Adanos) |
| `COSTING.md` | Infra & LLM cost model |
| `plan_1.md` / `plan_2.md`, `docs/Initial_Plan.md` | Original build plans & product lineage |

---

## 20. Notes for AI Coding Agents

If you are an AI assistant working in this repo:

1. **Naming:** repo/package = `yt-chatter`; product = **Carry**. `market-chatter`/`TickerFlow` = social sentiment; `HFI` = smart money. Don't rename things casually — a renaming pass is pending.
2. **Next.js 16 has breaking changes** from older Next versions — read `web/AGENTS.md` and the bundled docs in `web/node_modules/next/dist/docs/` before writing frontend code.
3. **Config:** add new settings to `src/config.py` (`Settings`) and document them in `.env.example`. Never hardcode keys.
4. **Migrations:** generate with `make migration msg="..."`, then review the autogenerated file; apply with `make migrate`.
5. **Tests:** add/adjust pytest coverage for backend changes (`make test`); keep `ruff` clean (`make lint`). Frontend changes need `bun run lint` passing.
6. **Conventions:** async SQLAlchemy everywhere in request paths; Celery tasks for background work; Pydantic schemas at API boundaries; typed API client in `web/src/lib/api.ts`.
7. **Provider pattern:** TickerFlow sentiment/price providers are selected via `SENTIMENT_PROVIDER`/`PRICE_PROVIDER` — `fixture` providers exist for deterministic tests; keep the `MarketSentimentProvider` protocol intact.
8. **Lineage context:** product evolved SentimentAI blueprint → YT Chatter → Carry. Current positioning: "Hear what the market is saying", invite-only beta.

