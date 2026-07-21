# YT Chatter 📈

> **Search Engine for Financial Market Commentary from YouTube**

YT Chatter is an end-to-end platform that ingests YouTube financial commentary, processes transcripts with LLMs to extract predictions, themes, and ticker mentions, and maps what was said against how stock prices actually performed in real market data.

---

## 🌟 Key Features

- **Automated Video & Transcript Ingestion**: Ingests YouTube channels, extracts captions via YouTube Data API v3 / `youtube-transcript-api`, with `yt-dlp` + Whisper fallback.
- **LLM Structured Analysis**: Extracts claims, predictions, sentiment, explicit ticker mentions, and implicit thematic ties using Anthropic Claude & OpenAI models.
- **Hierarchical Theme Taxonomy & Ticker Mapping**: Organizes market commentary by Sector → Industry → Theme → Ticker (e.g., Tech → Semiconductors → AI Chips → NVDA, AMD).
- **Hybrid Search Engine**: Combines PostgreSQL full-text keyword search (`tsvector`) with semantic vector search (`pgvector` 384-dim embeddings).
- **Market Performance Evaluation**: Matches video release dates against historical stock price movements using `yfinance` (1-day, 1-week, 1-month returns) to evaluate prediction accuracy.
- **Interactive Next.js Dashboard**: Search interface, video breakdowns, prediction accuracy tracking, ticker performance charts (Recharts), and theme explorers.

---

## 🏗️ Architecture Overview

```
┌───────────────────────────────────────────────────────────┐
│                   FRONTEND (Next.js 16)                   │
│  Search UI  │  Video Browser  │  Prediction Dashboard     │
│  (Keyword + Semantic)         │  (Table + Recharts)       │
└────────────────────────┬──────────────────────────────────┘
                         │ REST API (FastAPI)
┌────────────────────────▼──────────────────────────────────┐
│                   BACKEND (Python 3.12)                   │
│  FastAPI Endpoints  │  Celery Task Worker  │  SQLAlchemy  │
└────────────────────────┬──────────────────────────────────┘
                         │
┌────────────────────────▼──────────────────────────────────┐
│                 PROCESSING PIPELINE                       │
│  ┌────────────┐   ┌─────────────┐   ┌──────────────────┐  │
│  │ YT Fetcher │ → │ Transcript  │ → │ LLM Analyzer     │  │
│  └────────────┘   └─────────────┘   └────────┬─────────┘  │
│                                              │            │
│  ┌─────────────┐   ┌────────────┐   ┌────────▼─────────┐  │
│  │ yfinance /  │ ← │ Embeddings │ ← │ Theme-Ticker     │  │
│  │ Market Data │   │ (pgvector) │   │ Mapping Engine   │  │
│  └──────┬──────┘   └────────────┘   └──────────────────┘  │
└─────────┼─────────────────────────────────────────────────┘
          │
┌─────────▼─────────────────────────────────────────────────┐
│              STORAGE (PostgreSQL 16 + Redis)              │
│  - pgvector (Vector embeddings)                           │
│  - Relational Schema (Videos, Predictions, Themes)        │
│  - Redis 7 (Celery broker & Cache)                        │
└───────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technologies |
|---|---|
| **Backend Framework** | Python 3.12, FastAPI, Uvicorn, Pydantic v2 |
| **Task Queue & Async** | Celery, Redis 7, `asyncio` |
| **Database & ORM** | PostgreSQL 16 with `pgvector`, SQLAlchemy 2.0 (Async), AsyncPG, Alembic |
| **Backend Package Manager** | `uv` (Fast Python package resolver and installer) |
| **AI / LLM / NLP** | Anthropic API (`claude-sonnet`), OpenAI API (`gpt-4o`, `text-embedding-3-small`) |
| **Data Scraping & APIs** | `youtube-transcript-api`, `google-api-python-client`, `yt-dlp`, `yfinance`, `fredapi` |
| **Frontend Framework** | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, Recharts, Lucide Icons |
| **Frontend Runtime & Package Manager** | `bun` |
| **Dev Tooling** | Docker, Docker Compose, `Makefile`, `ruff` (linter/formatter), `pytest` |

---

## 📋 Prerequisites

Ensure you have the following installed on your local system before getting started:

1. **Python**: `3.12` or higher
2. **`uv`**: High-performance Python package manager ([Installation Guide](https://docs.astral.sh/uv/getting-started/installation/))
3. **`bun`**: All-in-one JavaScript runtime & package manager ([Installation Guide](https://bun.sh/))
4. **Docker & Docker Compose**: For running PostgreSQL (`pgvector`) and Redis containers

---

## 🚀 Quick Start Guide (Local Development)

Follow these steps to set up the project locally for development and contributions.

### 1. Clone the Repository & Configure Environment

```bash
# Clone the repository
git clone https://github.com/your-org/yt-chatter.git
cd yt-chatter

# Create environment configuration file from template
cp .env.example .env
```

Open `.env` and fill in your API keys:
- `YOUTUBE_API_KEY`: YouTube Data API v3 key
- `OPENAI_API_KEY`: OpenAI API Key (used for vector embeddings and chat)
- `ANTHROPIC_API_KEY`: Anthropic Claude API Key (used for structured LLM claim extraction)
- `FRED_API_KEY`: *(Optional)* Federal Reserve Economic Data API key

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

## 🐳 Alternative: Full Stack Docker Setup

If you prefer running the entire stack (API, Worker, Postgres, Redis) in Docker containers:

```bash
# Build and launch all services in detached mode
make up

# Stop all services
make down
```

---

## 🛠️ Developer Command Reference (`Makefile`)

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
| `make test` | Run test suite via `pytest` |
| `make lint` | Run code quality & formatting checks via `ruff` |
| `make format` | Automatically fix formatting issues via `ruff format` |
| `make process-video id=<ID>` | Process a single YouTube video ID through the ingestion pipeline |
| `make backfill channel=<ID>` | Trigger backfill pipeline for a channel ID |

---

## 📂 Project Structure

```text
yt-chatter/
├── alembic/                  # Database migration scripts & configuration
│   └── versions/             # Migration files
├── data/                     # Seed datasets & taxonomy configuration
│   └── theme_taxonomy.json   # Sector -> Industry -> Theme hierarchy
├── src/                      # Core backend Python package
│   ├── api/                  # FastAPI routers (search, videos, predictions, themes, etc.)
│   ├── models/               # SQLAlchemy ORM models (Video, Prediction, Theme, etc.)
│   ├── pipeline/             # Data ingestion, LLM analysis, embeddings, market tracking
│   ├── schemas/              # Pydantic validation schemas
│   ├── services/             # Core business logic & integrations (YouTube, LLM, Market Data)
│   ├── tasks/                # Celery background tasks
│   ├── config.py             # App environment variables & pydantic-settings
│   ├── database.py           # Async SQLAlchemy engine & session factory
│   └── main.py               # FastAPI application entrypoint
├── tests/                    # Backend unit and integration test suite
├── web/                      # Frontend Next.js application
│   ├── src/
│   │   ├── app/              # Next.js App Router pages (channels, themes, tickers, videos)
│   │   ├── components/       # React components & UI primitives (shadcn/ui)
│   │   └── lib/              # API client & utility functions
│   ├── bun.lock              # Bun lockfile
│   └── package.json          # Node dependencies & scripts
├── docker-compose.yml        # Multi-container orchestrator (Postgres, Redis, API, Worker)
├── Dockerfile                # Production Dockerfile for Python app
├── Makefile                  # Developer shortcut commands
├── pyproject.toml            # Python dependencies and tool configs (ruff, pytest)
└── README.md                 # Project documentation
```

---

## ⚡ Data Pipeline Workflow

When a video is processed by the pipeline:

1. **Ingestion (`src/pipeline/ingestion.py`)**: Fetches metadata via YouTube Data API v3 and retrieves transcript segments with timestamps.
2. **Analysis (`src/pipeline/analysis.py`)**: Batches transcripts and sends them to Claude / OpenAI to extract structured themes, predictions, sentiment, and ticker mentions.
3. **Theme & Ticker Mapping (`src/pipeline/theme_mapping.py`)**: Links extracted claims to the hierarchical theme taxonomy and maps implicit stock tickers.
4. **Embedding Generation (`src/pipeline/embeddings.py`)**: Embeds text segments into 384-dimensional vectors stored in PostgreSQL `pgvector`.
5. **Market Tracking (`src/pipeline/market_tracking.py`)**: Queries `yfinance` for historical prices post-publish date to evaluate return accuracy.

---

## 🧪 Testing & Code Quality

Before opening a pull request, please run the test suite and verify code quality checks:

```bash
# Run backend test suite
make test

# Check linting and formatting
make lint

# Auto-format Python code
make format

# Check frontend linting
cd web && bun run lint
```

---