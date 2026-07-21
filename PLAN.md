# YT Chatter — Search Engine for Financial Market Commentary

## Problem Statement

Build a search engine for people involved in financial/stock markets that ingests YouTube channels (starting with **Prof G Markets**), processes video content to extract predictions, opinions, and analysis, then maps what was said against how it actually performed in the markets. Users can search across channels, topics, tickers, and people to see what was predicted vs what happened.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                   FRONTEND (Next.js)                      │
│  Search UI  │  Video Browser  │  Prediction Dashboard     │
│  (keyword + semantic)          │  (table + chart)         │
└────────────────────────┬─────────────────────────────────┘
                         │ REST API
┌────────────────────────▼─────────────────────────────────┐
│                API LAYER (FastAPI / Python)               │
│  Search (hybrid)  │  CRUD  │  Auth (future)              │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────────┐
│              PROCESSING PIPELINE (Python)                 │
│                                                          │
│  ┌──────────┐  ┌────────────┐  ┌───────────────────┐   │
│  │ YouTube  │→ │ Transcript │→ │  LLM Analyzer     │   │
│  │ Fetcher  │  │ Extractor  │  │  (predictions,    │   │
│  │ (API v3) │  │ (YT API +  │  │   tickers,        │   │
│  │          │  │  Whisper)  │  │   sentiment,      │   │
│  │          │  │            │  │   topics)         │   │
│  └──────────┘  └────────────┘  └────────┬──────────┘   │
│                                          │               │
│  ┌──────────┐  ┌────────────┐           │               │
│  │ Market   │← │ Ticker     │←──────────┘               │
│  │ Data     │  │ Extractor  │                           │
│  │ (yfinance│  └────────────┘                           │
│  │  + more) │                                           │
│  └────┬─────┘                                           │
│       │                                                 │
│  ┌────▼─────┐                                           │
│  │Perf Calc │  → PostgreSQL + pgvector ──→ API ──→ UI   │
│  └──────────┘                                           │
└─────────────────────────────────────────────────────────┘
```

---

## Database Schema

### `channels`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| youtube_channel_id | VARCHAR | Unique YouTube channel ID |
| title | VARCHAR | |
| description | TEXT | |
| thumbnail_url | VARCHAR | |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### `videos`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| channel_id | UUID | FK → channels |
| youtube_video_id | VARCHAR | Unique |
| title | VARCHAR | |
| description | TEXT | |
| published_at | TIMESTAMPTZ | |
| duration_sec | INT | |
| thumbnail_url | VARCHAR | |
| view_count | BIGINT | |
| transcript_status | VARCHAR | `pending`, `fetched`, `failed` |
| processed | BOOLEAN | |
| created_at | TIMESTAMPTZ | |

### `transcript_segments`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| video_id | UUID | FK → videos |
| start_sec | FLOAT | |
| end_sec | FLOAT | |
| text | TEXT | |
| embedding | vector(384) | pgvector |

### `predictions`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| video_id | UUID | FK → videos |
| segment_id | UUID | FK → transcript_segments |
| ticker | VARCHAR | e.g., `NVDA` |
| prediction_text | TEXT | What was said |
| direction | VARCHAR | `bullish`, `bearish`, `neutral` |
| confidence | FLOAT | LLM confidence score (0-1) |
| timeframe_hint | VARCHAR | e.g., `short-term`, `long-term`, `earnings` |
| extracted_by | VARCHAR | LLM model used |
| accurate | BOOLEAN | NULL until evaluated |

### `performance_records`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| ticker | VARCHAR | |
| video_id | UUID | FK → videos |
| prediction_id | UUID | FK → predictions |
| price_at_video | FLOAT | Close price on video date |
| price_1d | FLOAT | Close 1 trading day after |
| price_1w | FLOAT | Close 5 trading days after |
| price_1m | FLOAT | Close 21 trading days after |
| return_1d | FLOAT | Percentage return |
| return_1w | FLOAT | |
| return_1m | FLOAT | |
| direction_accurate | BOOLEAN | Prediction direction matched actual move |

### `topics`
| Column | Type |
|--------|------|
| id | UUID | PK |
| name | VARCHAR | Unique (e.g., `Earnings`, `AI`, `Geopolitics`) |

### `video_topics`
| Column | Type |
|--------|------|
| video_id | UUID | FK |
| topic_id | UUID | FK |

---

## Data Pipeline (Step-by-Step)

### Step 1: YouTube Data Ingestion
- Fetch channel metadata and video list via **YouTube Data API v3**
- Backfill last **20 videos** from Prof G Markets
- Store video metadata (title, description, publish date, duration, stats)
- **Transcript**: Use `youtube-transcript-api` to fetch auto-generated captions
- **Fallback**: If captions unavailable, download audio (yt-dlp) → transcribe with Whisper

### Step 2: LLM-Powered Content Analysis
- Split transcript into ~30-second chunks
- Send transcript to LLM (Claude/GPT-4) with structured prompt:
  - Extract all ticker symbols mentioned (validate against known ticker DB)
  - Extract explicit predictions/opinions with directional sentiment
  - Extract entities (people, companies, indices)
  - Categorize topics (Earnings, Geopolitics, Big Tech, AI, Macroeconomics, etc.)
  - Assign sentiment scores per topic/ticker
- Store results in `predictions`, `ticker_mentions`, `topics` tables

### Step 3: Embeddings for Semantic Search
- Generate vector embeddings for each transcript segment
- Model: `sentence-transformers/all-MiniLM-L6-v2` (384-dim, fast, good quality)
- Store in `transcript_segments.embedding`
- Also embed predictions for semantic prediction search

### Step 4: Market Data & Performance Tracking
- Extract all unique tickers across all processed videos
- Use `yfinance` to fetch historical price data:
  - Price on video publication date
  - Price 1 day, 1 week, 1 month after publication
- Compute returns for each window
- Compare prediction direction vs actual return → `direction_accurate`

---

## API Endpoints (FastAPI)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/search?q=&type=hybrid&channel=&ticker=` | Hybrid search (keyword + semantic) |
| GET | `/api/videos` | List processed videos (paginated) |
| GET | `/api/videos/:id` | Video detail with predictions |
| GET | `/api/predictions?ticker=X` | All predictions for a ticker |
| GET | `/api/predictions/:id/performance` | Performance data for one prediction |
| GET | `/api/channels` | List channels |
| GET | `/api/tickers` | List all tracked tickers with aggregate stats |
| POST | `/api/pipeline/process-video` | Trigger processing for a video |
| POST | `/api/pipeline/backfill` | Trigger backfill for channel |

---

## Frontend Pages (Next.js)

| Route | Page | Description |
|-------|------|-------------|
| `/` | Search | Search bar + results (transcript clips, predictions) |
| `/channels` | Channels | Browse all channels |
| `/channels/:id` | Channel Detail | All videos from channel + topic breakdown |
| `/videos/:id` | Video Detail | Full transcript, predictions, performance overlay |
| `/tickers/:ticker` | Ticker Page | All predictions for ticker, price chart with annotations |
| `/dashboard` | Dashboard | Top predictions, accuracy stats, recent activity |

---

## Visualization (Prediction vs Performance)

### Table View
| Prediction | Ticker | Direction | Price at Video | 1W Return | Accurate? |
|------------|--------|-----------|----------------|-----------|-----------|
| "NVDA will dominate AI chips" | NVDA | Bullish | $480 | +5.2% | ✅ Yes |
| "Apple demand is slowing" | AAPL | Bearish | $195 | -2.1% | ✅ Yes |

### Chart View
Line chart of ticker price with annotated markers:
- **Green arrows** = Bullish predictions made at that date
- **Red arrows** = Bearish predictions
- **Blue dots** = Neutral mentions
- Click markers to see the original prediction text + video link

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12 (FastAPI, Celery, SQLAlchemy, Alembic, Pydantic v2) |
| ML/AI | LangChain, sentence-transformers, Whisper (openai-whisper) |
| Market Data | yfinance |
| Database | PostgreSQL 16 + pgvector |
| Queue / Cache | Redis |
| Task Queue | Celery |
| Frontend | Next.js 14 (App Router), TailwindCSS, Recharts, shadcn/ui |
| Search | pgvector hybrid (`tsvector` keyword + vector cosine similarity) |
| Dev Environment | Docker Compose |
| API Client | `yt-dlp`, `google-api-python-client`, `youtube-transcript-api` |

---

## Implementation Phases

### Phase 1: Foundation — Data Pipeline (Days 1-2)
- [ ] Scaffold Python project (Poetry, pyproject.toml)
- [ ] Docker Compose: PostgreSQL + pgvector + Redis
- [ ] Database models + Alembic migrations
- [ ] YouTube fetcher → transcript extractor
- [ ] LLM analysis pipeline (transcript → predictions/tickers/topics)
- [ ] Embedding generation
- [ ] Market data fetcher + performance computation
- [ ] Store all results in DB

### Phase 2: API Layer (Day 3)
- [ ] FastAPI project structure + dependency injection
- [ ] Search endpoints (keyword via `tsvector`, semantic via pgvector, hybrid)
- [ ] CRUD endpoints for all entities
- [ ] Celery task endpoints for pipeline triggers
- [ ] API docs auto-generated (OpenAPI/Swagger)

### Phase 3: Frontend (Days 4-5)
- [ ] Scaffold Next.js project + Tailwind + shadcn/ui
- [ ] Search interface with type toggle (keyword/semantic/hybrid)
- [ ] Channel + video browsing pages
- [ ] Prediction dashboard (table)
- [ ] Price chart with prediction annotations (Recharts)
- [ ] Ticker detail page with aggregate predictions

### Phase 4: Polish & Demo Prep (Day 6)
- [ ] Backfill 20 recent Prof G Markets videos
- [ ] Run full pipeline end-to-end
- [ ] Manual QA: verify predictions, performance data, search quality
- [ ] Fix edge cases (missing captions, non-trading days, delisted tickers)
- [ ] Prepare demo walkthrough script

---

## Key Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| YouTube API rate limits | Use API keys with quotas; cache aggressively; stagger requests |
| Poor transcript quality | Fallback to Whisper; LLM prompt designed for noisy text |
| Ticker extraction false positives | Validate against known ticker list; LLM context helps disambiguate |
| Market data gaps (weekends, holidays) | Forward-fill to next trading day; clearly label trading vs calendar days |
| LLM API costs for processing | Batch segments; cache responses; use cheaper models for classification |
| Prediction accuracy is subjective | Focus on directional + return-based evaluation; human-in-loop for prototype |
| No new videos during 3-day window | Backfill solves this — we have 20 videos to work with |

---

## Future Roadmap (Post-Prototype)

1. **User Authentication** — Allow users to add their own channels
2. **Scheduled Pipeline** — Cron/webhook to auto-process new videos on publish
3. **Multi-User** — Per-user channel subscriptions, saved searches, alerts
4. **Advanced Predictions** — More granular extraction: price targets, timeframes
5. **Multiple Data Sources** — Podcasts, Twitter/X, newsletters, SEC filings
6. **Backtesting** — Aggregate prediction accuracy across channels to rank analysts
7. **Real-Time** — Push notifications when a new channel video is processed
