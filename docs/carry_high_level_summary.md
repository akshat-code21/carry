# Carry - High-Level Product Summary

> **Hear what the market is saying.**
>
> Carry ingests thousands of hours of finance commentary from YouTube, Reddit, X, and news - then extracts the tickers, predictions, and sentiment that actually matter, timestamped to the second.
>
> *Product: Carry (`carry-fin.vercel.app` · API: `carry-api.akshat21.me`) - internally the repo is named "yt-chatter", which reflects its YouTube-first origin.*

---

## 1. The Problem

Financial market commentary is produced at enormous scale and velocity - thousands of YouTube channels, Substack writers, Reddit threads, X posts, and news wires every day. But this signal is:

- **Unsearchable** - commentary lives inside hours of video audio and social feeds that no search engine indexes at the *sentence* level.
- **Unverified** - pundits make confident calls with no systematic record of whether they were right.
- **Unsynthesized** - retail investors must manually stitch together what "the market is saying" across dozens of sources, while institutional investors pay $20k+/year (Bloomberg, RavenPack) for exactly this kind of intelligence.

Carry closes this gap for individual investors and analysts: it turns raw market commentary into a **searchable, structured, and outcome-verified** intelligence layer.

## 2. What Carry Does

Carry continuously ingests financial commentary, uses LLMs and NLP to structure it, and holds it accountable against real market outcomes.

### Core pillars

**1. Commentary Intelligence Engine (YouTube-first)**
- Monitors a curated set of finance YouTube channels and detects new uploads in near real time (WebSub push, no API quota burn).
- Transcripts every video (with multi-tier fallbacks: YouTube captions → Supadata → local Whisper ASR).
- An LLM pipeline extracts the **tickers, predictions, sentiment, confidence, and themes** from every transcript segment - each claim timestamped to the second.
- Commentary is mapped to a hierarchical taxonomy: **Sector → Industry → Theme → Ticker** (e.g., Tech → Semiconductors → AI Chips → NVDA, AMD).

**2. Search & Answers**
- Hybrid search engine (keyword + semantic) across millions of words of transcript - jump to the exact second an expert made a call.
- Query intent routing (stock picks vs. sentiment checks vs. factual questions vs. ETF discovery).
- AI-generated answer summaries with **mandatory channel attribution** - every synthesized claim names the creator who said it, with clickable clip citations.

**3. Predictions, Verified**
- Every prediction is logged the moment it's made, then scored against what the market actually did (1-day / 1-week / 1-month returns from real price data).
- Users can see **who's consistently right - not just who's loud**.

**4. Social Sentiment Signal (TickerFlow / Market Chatter)**
- Ingests Reddit, X, StockTwits, and news (GDELT) for the S&P 100 universe.
- Scores chatter with a locally-hosted FinBERT model plus LLM narrative extraction, producing transparent, formula-driven scores (RISS, SMS, composite OCS) - normalized across sources into one comparable bullish/bearish number.

**5. Smart Money Tracking (Hedge Fund Intelligence)**
- Track individual investors/funds, ingest their published content (websites, letters, SEC filings), extract their theses and portfolio changes.
- Generates investor reports, alerts, and a cross-investor **Smart Money Consensus** view.

**6. Narrative Maps**
- Watch themes emerge, spread across sectors, and shift over time via a hierarchical theme explorer (circle-pack + grid visualizations).

## 3. Who It's For

- **Retail investors** who want institutional-grade sentiment and commentary intelligence without the terminal price tag.
- **Equity research analysts** who need to search, cite, and audit what commentators actually said, and track their accuracy.
- **Finance content teams** monitoring the commentary landscape for emerging narratives.

## 4. Product Surface (What the User Sees)

| Surface | What it gives the user |
|---|---|
| **Search** | Hybrid keyword/semantic search with AI answers, clip citations, filters (period, channel, sort) |
| **Overview (Dashboard)** | At-a-glance market mood: trending tickers, sentiment, social chatter |
| **Channels** | Browse monitored creators; per-channel stats and latest breakdowns |
| **Themes** | Narrative taxonomy explorer - sector/industry/theme drill-downs |
| **Tickerflow** | Per-ticker social sentiment across Reddit / X / StockTwits / news, with mention volume and price overlay |
| **Investors** | Tracked funds/investors with sources, theses, reports, and alerts |
| **Consensus** | Smart-money consensus across tracked investors |
| **Activity** | Live feed of newly detected/processed videos |
| **Usage / Admin** | Personal usage analytics; admin invite & platform metrics management |

Access is **invite-only** (single-use invite codes at signup, powered by Clerk authentication).

## 5. Why It's Different

1. **Sentence-level provenance** - nothing is summarized without attribution and a jump-to-second citation.
2. **Verified track records** - predictions are graded against actual outcomes, turning commentary from noise into measurable signal.
3. **Transparent scoring** - sentiment scores come from published formulas over local models (FinBERT + LLM), not black-box vendor feeds.
4. **Multi-source synthesis in one place** - YouTube, Reddit, X, StockTwits, news, and smart-money filings unified under one searchable data model.

## 6. Current Status

- **Live, invite-only beta**: full stack deployed (Next.js on Vercel, FastAPI + Celery + Postgres/pgvector on GCP, Redis via Aiven).
- **Operating cost**: ~$625–790/month, overwhelmingly infrastructure (Cloud SQL) - AI costs are <$0.01 per fully analyzed video and ~$0.001–0.005 per search.
- The product evolved from a YouTube-only prototype ("YT Chatter") through a formalized platform blueprint and competitive analysis into the current multi-source Carry positioning.

## 7. Roadmap Direction (inferred from docs & code)

- Broader ticker coverage beyond the S&P 100 social-sentiment universe.
- Deeper smart-money automation (SEC/13F ingestion, alert rules).
- Public launch beyond the invite gate (Clerk Pro, billing tiers considered in implementation plans).
- Methodology publishing (publicly audited scoring / information-coefficient validation) as the trust moat.

