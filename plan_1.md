# YT Chatter — Search Engine for Financial Market Commentary

## Problem Statement

Build a search engine for people involved in financial/stock markets that ingests YouTube channels (starting with **Prof G Markets**), processes video content to extract predictions, opinions, themes, and analysis, then maps what was said against how it actually performed in the markets. Users can search across channels, themes, topics, tickers, and people to see what was predicted vs what happened, and discover the top stocks a speaker implicitly or explicitly discusses.

**Key insight:** Most financial commentary is *thematic* ("AI is overhyped", "retail is getting crushed", "rate cuts coming") rather than ticker-specific. The engine must extract themes and map them to affected tickers.

---

## Architecture Overview

```
┌───────────────────────────────────────────────────────────┐
│                   FRONTEND (Next.js)                       │
│  Search UI  │  Video Browser  │  Prediction Dashboard     │
│  (keyword + semantic)         │  (table + chart)          │
│  Theme Explorer  │  Top Stocks Panel                      │
└────────────────────────┬──────────────────────────────────┘
                         │ REST API
┌────────────────────────▼──────────────────────────────────┐
│                API LAYER (FastAPI / Python)                │
│  Search (hybrid)  │  CRUD  │  Theme→Stocks                │
└────────────────────────┬──────────────────────────────────┘
                         │
┌────────────────────────▼──────────────────────────────────┐
│              PROCESSING PIPELINE (Python)                  │
│                                                           │
│  ┌──────────┐  ┌────────────┐  ┌───────────────────┐    │
│  │ YouTube  │→ │ Transcript │→ │  LLM Analyzer     │    │
│  │ Fetcher  │  │ Extractor  │  │  (themes,          │    │
│  │ (API v3) │  │ (YT API +  │  │   predictions,     │    │
│  │          │  │  Whisper)  │  │   tickers,         │    │
│  │          │  │            │  │   sentiment,       │    │
│  │          │  │            │  │   narratives)      │    │
│  └──────────┘  └────────────┘  └────────┬───────────┘    │
│                                          │                │
│  ┌──────────────────┐  ┌────────────┐    │                │
│  │ Theme→Ticker     │← │ Ticker     │←───┘               │
│  │ Mapping Engine   │  │ Extractor  │                    │
│  │ (curated + LLM)  │  └────────────┘                    │
│  └────────┬─────────┘                                    │
│           │                                               │
│  ┌────────▼─────────┐  ┌──────────────┐                  │
│  │ Market Data      │  │ Top Stocks   │                  │
│  │ (yfinance + FRED)│  │ Aggregator   │                  │
│  │                  │  │ (channel/vid │                  │
│  │                  │  │  /query)     │                  │
│  └────────┬─────────┘  └──────┬───────┘                  │
│           │                   │                           │
│  ┌────────▼───────────────────▼───────┐                   │
│  │   PostgreSQL + pgvector ──→ API ──→ UI                │
│  └────────────────────────────────────────────────────────┘
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

### `theme_hierarchy`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| parent_id | UUID | FK → self (null for root sectors) |
| level | VARCHAR | `sector`, `industry`, `theme`, `narrative` |
| name | VARCHAR | |
| description | TEXT | |
| created_at | TIMESTAMPTZ | |

### `theme_mentions`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| video_id | UUID | FK → videos |
| segment_id | UUID | FK → transcript_segments |
| theme_id | UUID | FK → theme_hierarchy |
| sentiment | VARCHAR | `bullish`, `bearish`, `neutral` |
| relevance_score | FLOAT | LLM-assigned (0-1) |
| mention_text | TEXT | Exact quote from transcript |
| narrative | TEXT | Free-form description of what was said about this theme |

### `theme_ticker_mappings`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| theme_id | UUID | FK → theme_hierarchy |
| ticker | VARCHAR | e.g., `NVDA` |
| relevance_score | FLOAT | How core this ticker is to the theme (0-1) |
| source | VARCHAR | `curated` or `llm` |
| notes | TEXT | Why this ticker maps to this theme |

### `predictions`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| video_id | UUID | FK → videos |
| segment_id | UUID | FK → transcript_segments |
| theme_id | UUID | FK → theme_hierarchy (null if not theme-based) |
| ticker | VARCHAR | e.g., `NVDA` (null if no explicit ticker) |
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

### `speaker_ticker_aggregation`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| channel_id | UUID | FK → channels |
| ticker | VARCHAR | |
| total_mentions | INT | Sum of explicit + implicit mentions |
| explicit_mentions | INT | Direct ticker mentions in speech |
| implicit_mentions | INT | Inferred via theme mapping |
| avg_sentiment | FLOAT | -1 (bearish) to +1 (bullish) |
| weighted_relevance | FLOAT | Aggregated relevance score across all mentions |
| last_mentioned_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

---

## Data Pipeline (Step-by-Step)

### Step 1: YouTube Data Ingestion
- Fetch channel metadata and video list via **YouTube Data API v3**
- Backfill last **20 videos** from Prof G Markets
- Store video metadata (title, description, publish date, duration, stats)
- **Transcript**: Use `youtube-transcript-api` to fetch auto-generated captions
- **Fallback**: If captions unavailable, download audio (yt-dlp) → transcribe with Whisper

### Step 2: LLM-Powered Content Analysis (Richer Extraction)
- Split transcript into ~30-second chunks
- Send each chunk to LLM (Claude/GPT-4) with structured prompt that extracts:

```json
{
  "themes": [
    {
      "sector": "Technology",
      "industry": "Semiconductors",
      "theme": "AI Chips",
      "narrative": "NVDA's dominance is facing competition from AMD's MI300 series",
      "sentiment": "bullish_on_competition",
      "confidence": 0.85
    }
  ],
  "explicit_tickers": ["NVDA", "AMD"],
  "implicit_tickers": ["AVGO", "MRVL"],
  "predictions": [
    {
      "text": "AMD's MI300 will take significant market share",
      "ticker": "AMD",
      "direction": "bullish",
      "timeframe": "12-18 months"
    }
  ],
  "entities": {
    "people": ["Scott Galloway", "Ed Elson"],
    "companies": ["Nvidia", "AMD", "Broadcom"],
    "indices": ["S&P 500", "Nasdaq"]
  }
}
```

- The LLM matches extracted themes against the hierarchical taxonomy by name/relevance
- Store themes in `theme_mentions` linked to the appropriate level in `theme_hierarchy`
- Store predictions in `predictions`
- The taxonomy is seeded from a pre-built file (`data/theme_taxonomy.json`)

### Step 3: Theme→Ticker Mapping (New Step)
After LLM analysis:
1. For each extracted theme, look up pre-curated ticker mappings in `theme_ticker_mappings` (seeded from taxonomy)
2. Run LLM enrichment pass: *"Given this specific narrative about [theme], which additional tickers are most relevant and why?"*
3. Merge curated + LLM-generated ticker lists
4. Score relevance (0-1) for each (ticker, theme, video) triple
5. Store or update in `theme_ticker_mappings`
6. **Update `speaker_ticker_aggregation`** — this is the "top stocks" source table

### Step 4: Embeddings for Semantic Search
- Generate vector embeddings for each transcript segment
- Model: `sentence-transformers/all-MiniLM-L6-v2` (384-dim, fast, good quality)
- Store in `transcript_segments.embedding`
- Also embed predictions + theme narratives for semantic search

### Step 5: Market Data & Performance Tracking
- Extract all unique tickers across all processed videos (both explicit + implicit)
- Use `yfinance` to fetch historical price data:
  - Price on video publication date
  - Price 1 day, 1 week, 1 month after publication
- Compute returns for each window
- Compare prediction direction vs actual return → `direction_accurate`

---

## Theme Taxonomy (Seed Data)

Pre-built hierarchical taxonomy stored in `data/theme_taxonomy.json`:

```
Sector: Technology
  ├── Industry: Semiconductors
  │   ├── Theme: AI Chips → NVDA, AMD, AVGO, MRVL
  │   ├── Theme: Memory/Storage → MU, WDC, STX
  │   └── Theme: Chip Manufacturing Equipment → ASML, AMAT, LRCX, KLAC
  ├── Industry: Big Tech / FAANG
  │   ├── Theme: Cloud Computing → AMZN, MSFT, GOOGL, CRM
  │   ├── Theme: Digital Advertising → META, GOOGL, SNAP, PINS
  │   ├── Theme: Consumer Hardware → AAPL
  │   └── Theme: Streaming → NFLX, DIS, WBD, SPOT
  └── Industry: Software & AI
      ├── Theme: Enterprise SaaS → CRM, NOW, WDAY, ADBE
      ├── Theme: AI/ML Platforms → MSFT, GOOGL, META, ORCL
      └── Theme: Cybersecurity → CRWD, PANW, ZS, SENT

Sector: Financials
  ├── Theme: Rate Cuts → XLF, JPM, GS, BAC, regional bank ETFs
  ├── Theme: Consumer Credit → PYPL, SQ, AFRM, COF
  ├── Theme: Asset Management → BLK, BK, STT
  ├── Theme: Insurance → BRK.B, MET, PRU, ALL
  └── Theme: Fintech → SQ, SHOP, MELI, SOFI

Sector: Consumer
  ├── Theme: Retail → AMZN, WMT, TGT, COST, HD, LOW
  ├── Theme: Consumer Spending → DIS, MCD, SBUX, NKE, LULU
  ├── Theme: Luxury → LVMUY, HERMES, TPR, CPRI
  └── Theme: Travel & Hospitality → EXPE, BKNG, ABNB, MAR, HLN

Sector: Healthcare
  ├── Theme: Pharma → PFE, MRK, ABBV, LLY, UNH
  ├── Theme: Biotech → AMGN, GILD, REGN, VRTX
  ├── Theme: MedTech → ISRG, SYK, BSX, MDT
  └── Theme: Healthcare AI → TDOC, CVS, UNH, HUM

Sector: Geopolitics / Macro
  ├── Theme: Defense → LMT, NOC, RTX, GD, LHX
  ├── Theme: Energy Crisis → XOM, CVX, COP, OXY, XLE
  ├── Theme: China/Taiwan Tensions → TSM, AAPL, NVDA, AMD
  ├── Theme: Inflation → TIPS, GLD, commodities
  └── Theme: Recession Fears → defensive stocks, utilities, consumer staples

Sector: Industrials
  ├── Theme: Infrastructure → CAT, DE, URI, PWR
  ├── Theme: Aerospace → BA, RTX, GE, SPR
  ├── Theme: Clean Energy → ENPH, SEDG, NEE, ICLN, TAN
  └── Theme: EVs → TSLA, RIVN, LCID, F, GM, NIO
```

---

## "Top Stocks" Derivation

### Channel-Level
- Aggregate `speaker_ticker_aggregation` across all videos
- Rank by `weighted_relevance × total_mentions × |avg_sentiment|`
- Return top 20 stocks with sentiment indicators

### Per-Video
- Scope aggregation to a single video's `theme_mentions`
- Look up `theme_ticker_mappings` for the matched themes
- Rank by relevance_score × mention frequency within video

### Per-Query (Dynamic)
- Search matches videos/segments by theme or keyword
- Collect all matched themes across results
- Aggregate top tickers for those themes
- Return as "Stocks mentioned/implied by this topic"
- Query example: *"What did Scott say about AI?"* → finds AI-themed segments → surfaces top AI stocks (NVDA, AMD, MSFT, GOOGL, META) with what was said about each

---

## API Endpoints (FastAPI)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/search?q=&type=hybrid&channel=&ticker=` | Hybrid search (keyword + semantic) with theme matching |
| GET | `/api/videos` | List processed videos (paginated) |
| GET | `/api/videos/:id` | Video detail with predictions and themes |
| GET | `/api/videos/:id/stocks` | Top stocks discussed in a video |
| GET | `/api/predictions?ticker=X` | All predictions for a ticker |
| GET | `/api/predictions?theme=X` | All predictions for a theme |
| GET | `/api/predictions/:id/performance` | Performance data for one prediction |
| GET | `/api/channels` | List channels |
| GET | `/api/channels/:id/top-stocks` | Top stocks for a channel |
| GET | `/api/tickers` | List all tracked tickers with aggregate stats |
| GET | `/api/tickers/:ticker` | Detail for a ticker: predictions, themes, performance |
| GET | `/api/themes` | List all themes in taxonomy (hierarchical) |
| GET | `/api/themes/:id/tickers` | Tickers mapped to a theme |
| GET | `/api/themes/:id/videos` | Videos discussing a theme |
| GET | `/api/search/stocks?q=` | Search → relevant stocks for the query |
| POST | `/api/pipeline/process-video` | Trigger processing for a video |
| POST | `/api/pipeline/backfill` | Trigger backfill for channel |

---

## Frontend Pages (Next.js)

| Route | Page | Description |
|-------|------|-------------|
| `/` | Search | Search bar + results (transcript clips, predictions, themes) |
| `/` | — | **"Stocks Mentioned" sidebar** — tickers relevant to search query |
| `/channels` | Channels | Browse all channels |
| `/channels/:id` | Channel Detail | All videos + **"Top Stocks This Channel Talks About"** panel (ranked with sentiment) + theme/topic breakdown |
| `/videos/:id` | Video Detail | Full transcript predictions, performance overlay, **"Stocks Discussed"** panel |
| `/videos/:id` | — | Timeline showing which themes were discussed at which timestamps |
| `/tickers/:ticker` | Ticker Page | All predictions for ticker, price chart with annotations, all themes mentioning this ticker |
| `/themes/:id` | Theme Page | All videos discussing this theme, mapped tickers, aggregate sentiment |
| `/themes` | Theme Explorer | Hierarchical navigation: Sector → Industry → Theme → Videos + Stocks |
| `/dashboard` | Dashboard | Top predictions, accuracy stats, recent activity, trending themes |

---

## Visualization

### Prediction vs Performance (Table + Chart)

**Table View**
| Prediction | Theme | Ticker | Direction | Price at Video | 1W Return | Accurate? |
|------------|-------|--------|-----------|----------------|-----------|-----------|
| "NVDA will dominate AI chips" | AI Chips | NVDA | Bullish | $480 | +5.2% | ✅ Yes |
| "retail is getting crushed" | Retail | AMZN, WMT, TGT | Bearish | — | — | See chart |

**Chart View**
- Line chart of ticker price with annotated markers:
  - **Green arrows** = Bullish predictions
  - **Red arrows** = Bearish predictions
  - **Blue dots** = Neutral mentions / thematic discussions
  - Click markers to see the original prediction text + video link

### Top Stocks Display
- **Pill/badge UI**: Ticker symbol + sentiment color + mini sparkline
- **Hover/reveal**: "Why this stock? Discussed via [theme names]"
- **Aggregate**: "This channel mentions NVDA most frequently (X times, 70% bullish)"

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
| Frontend | Next.js 16 (App Router), TailwindCSS, Recharts, shadcn/ui |
| Search | pgvector hybrid (`tsvector` keyword + vector cosine similarity) |
| Dev Environment | Docker Compose |
| API Client | `yt-dlp`, `google-api-python-client`, `youtube-transcript-api` |

---

## Implementation Phases

### Phase 0: Seed Data & Taxonomy (Day 0)
- [ ] Build `data/theme_taxonomy.json` with hierarchical theme→ticker mappings
- [ ] Create database migration for new tables (theme_hierarchy, theme_mentions, theme_ticker_mappings, speaker_ticker_aggregation)

### Phase 1: Foundation — Data Pipeline (Days 1-2)
- [ ] Scaffold Python project (Poetry, pyproject.toml)
- [ ] Docker Compose: PostgreSQL + pgvector + Redis
- [ ] Database models + Alembic migrations (all tables)
- [ ] YouTube fetcher → transcript extractor
- [ ] LLM analysis pipeline (transcript → themes + predictions + tickers + narratives)
- [ ] Theme→Ticker mapping engine (curated lookup + LLM enrichment)
- [ ] Embedding generation
- [ ] Market data fetcher + performance computation
- [ ] Speaker ticker aggregation computation
- [ ] Store all results in DB

### Phase 2: API Layer (Day 3)
- [ ] FastAPI project structure + dependency injection
- [ ] Search endpoints (keyword via `tsvector`, semantic via pgvector, hybrid)
- [ ] Theme endpoints (hierarchy, videos, tickers)
- [ ] Top stocks endpoints (channel-level, per-video, per-query)
- [ ] CRUD endpoints for all entities
- [ ] Celery task endpoints for pipeline triggers
- [ ] API docs auto-generated (OpenAPI/Swagger)

### Phase 3: Frontend (Days 4-5)
- [ ] Scaffold Next.js project + Tailwind + shadcn/ui
- [ ] Search interface with type toggle (keyword/semantic/hybrid)
- [ ] Theme explorer (hierarchical navigation)
- [ ] Channel + video browsing pages with top stocks panels
- [ ] Ticker detail page with prediction annotations
- [ ] Prediction dashboard (table + chart)
- [ ] Price chart with prediction annotations (Recharts)
- [ ] Ticker detail page with aggregate predictions

### Phase 4: Polish & Demo Prep (Day 6)
- [ ] Backfill 20 recent Prof G Markets videos
- [ ] Run full pipeline end-to-end
- [ ] Manual QA: verify theme extraction, ticker mapping, prediction accuracy
- [ ] Fix edge cases (missing captions, non-trading days, ambiguous themes)
- [ ] Prepare demo walkthrough script

---

## Key Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| YouTube API rate limits | Use API keys with quotas; cache aggressively; stagger requests |
| Poor transcript quality | Fallback to Whisper; LLM prompt designed for noisy text |
| Ticker extraction false positives | Validate against known ticker list; LLM context + theme mapping helps disambiguate |
| **Theme→Ticker mapping accuracy** | Curated seed data + LLM enrichment with human review queue; start with 50-100 well-known themes |
| Theme extraction too vague/incorrect | Hierarchical taxonomy constrains the LLM; if theme doesn't match taxonomy, store as narrative-level free-text |
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
8. **Community Curation** — Users can suggest theme→ticker mappings, vote on accuracy
