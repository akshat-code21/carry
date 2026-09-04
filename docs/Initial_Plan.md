# SentimentAI: AI-Powered Stock Sentiment & Market Intelligence Platform
## Complete Project Blueprint - VC-Ready Technical Due Diligence Package

> **Document Version:** 2.0.0  
> **Classification:** Confidential - For Investor & Technical Review  
> **Prepared By:** Principal AI Architect & Quantitative Research Team  
> **Date:** June 2026  
> **Status:** Final Draft

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Product Requirements Document (PRD)](#product-requirements-document)
3. [Functional Requirements](#functional-requirements)
4. [Non-Functional Requirements](#non-functional-requirements)
5. [High-Level Architecture](#high-level-architecture)
6. [Detailed System Architecture](#detailed-system-architecture)
7. [Agent Architecture](#agent-architecture)
8. [Data Collection Layer](#data-collection-layer)
9. [Data Processing Layer](#data-processing-layer)
10. [Vector Search Architecture](#vector-search-architecture)
11. [LLM Analysis Pipeline](#llm-analysis-pipeline)
12. [Quantitative Scoring Engine](#quantitative-scoring-engine)
13. [Database Design](#database-design)
14. [API Design](#api-design)
15. [Event-Driven Architecture](#event-driven-architecture)
16. [Real-Time Processing Pipeline](#real-time-processing-pipeline)
17. [Backtesting Framework](#backtesting-framework)
18. [Monitoring & Observability](#monitoring--observability)
19. [Infrastructure Design](#infrastructure-design)
20. [Security Considerations](#security-considerations)
21. [Regulatory & Compliance Considerations](#regulatory--compliance-considerations)
22. [Cost Analysis](#cost-analysis)
23. [Technology Recommendations](#technology-recommendations)
24. [MVP Design](#mvp-design)
25. [Phase 1–6 Implementation Plans](#phase-1-implementation-plan)
26. [Risks and Mitigations](#risks-and-mitigations)
27. [Future Enhancements](#future-enhancements)
28. [Final Build Recommendation](#final-build-recommendation)

---

# Executive Summary

## The Opportunity

Retail investors - numbering over **170 million globally** and controlling approximately **$38 trillion in assets** - lack access to the same real-time sentiment intelligence infrastructure that institutional investors have used for decades. Bloomberg Terminal subscriptions cost $24,000/year. Refinitiv's Eikon runs $22,000/year. Sophisticated alternative data feeds are priced exclusively for hedge funds.

Meanwhile, the signal is hiding in plain sight: Twitter/X, Reddit, Substack, and financial blogs collectively generate over **2.5 million stock-related posts per day**, carrying predictive information about price movements that academic research has repeatedly validated - yet no product synthesizes this signal into actionable, quantitatively rigorous intelligence accessible to retail investors at scale.

**SentimentAI** closes this gap.

## What We Are Building

SentimentAI is a **multi-agent AI platform** that ingests near-real-time financial social media content, news, and public market commentary for any publicly traded stock ticker, processes it through a 10-agent LangGraph pipeline powered by LLMs, and produces seven distinct quantitative sentiment scores with explainable confidence intervals - delivered through a consumer-grade interface and a developer-facing API.

## Market Sizing

| Market | Size (2026) | CAGR | Our Relevance |
|--------|------------|------|---------------|
| Global Retail Investing | $38T AUM | 7.2% | Primary user base |
| Alternative Data Market | $9.8B | 31.4% | Core product category |
| NLP/Sentiment Analytics | $4.1B | 22.6% | Core technology |
| Financial SaaS for Retail | $6.3B | 18.9% | Go-to-market |

- **TAM:** $4.1B (global sentiment analytics market)
- **SAM:** $1.2B (English-language retail investor tooling, accessible via API/SaaS)
- **SOM (Year 3):** $48M ARR at 0.5% SAM penetration

## Competitive Moat

SentimentAI's durable competitive advantages compound over time:

1. **Proprietary Multi-Source Fusion** - No existing product aggregates all 10+ sources into a single normalized scoring engine
2. **Author Credibility Network** - A persistent author reputation database grows more accurate and defensible with every data point processed
3. **Backtested Signal Validation** - Correlating predictions against actual returns creates a trust signal competitors cannot purchase
4. **Narrative Intelligence Layer** - LLM-powered theme detection identifies investment narratives, not just sentiment polarity
5. **Data Flywheel** - More users → more feedback data → better calibration → better product → more users

## Business Model

| Tier | Price | Features | Target |
|------|-------|----------|--------|
| Starter (Free) | $0/mo | 3 tickers, 15-min delay, 24h history | Acquisition |
| Pro | $39/mo | Unlimited tickers, near real-time, 90-day history, all 7 scores | Retail investors |
| Trader | $99/mo | API access, alerts, portfolio dashboard, 2-year history | Active traders |
| Enterprise | $799+/mo | White-label, bulk API, custom agents, SLA | RIAs, fintechs |

## Key Metrics (Target - Year 2)

- 50,000 Pro+ subscribers → $23.4M ARR
- API: 200 enterprise accounts → $19.2M ARR  
- LTV:CAC ratio > 4:1
- Monthly churn < 3%
- Data freshness: < 5 minutes end-to-end latency (Pro tier)

## Funding Ask Context

A **Seed round of $3.5M** funds Phase 1–2 (18 months), covering team (8 FTEs), infrastructure, data licensing, and go-to-market. Expected outcome: 5,000 paying subscribers, Series A readiness with $2M+ ARR and validated signal-to-performance correlation.

---

# Product Requirements Document

## Problem Statement

### Primary Problem
Retail investors making multi-thousand dollar investment decisions rely on manual browsing of Reddit threads, Twitter feeds, and financial blogs - a process that is:
- **Incomplete:** No single person can monitor 10+ platforms simultaneously
- **Biased:** Manual curation introduces recency and confirmation bias
- **Unquantified:** There is no systematic way to measure sentiment strength or credibility
- **Unvalidated:** No feedback loop connects past sentiment to actual outcomes

### Secondary Problem
The financial content ecosystem is polluted with bots, paid promoters, misinformation campaigns, and coordinated pump-and-dump schemes. Retail investors have no tools to detect or filter this noise at scale.

### Market Validation
- Academic research (Da et al., 2011; Chen et al., 2014; Bollen et al., 2011) demonstrates that social media sentiment Granger-causes stock returns with statistical significance
- Reddit's r/WallStreetBets GME episode demonstrated that retail social sentiment can move markets - yet no product systematically monitors this
- 73% of retail investors surveyed (Schwab 2024) report using social media as a primary research input

## Goals

### Business Goals
- Build the leading AI-powered sentiment intelligence platform for retail investors
- Achieve product-market fit at 5,000 paying subscribers within 18 months
- Establish data and signal quality as defensible IP through backtesting publication
- Create API revenue stream as a B2B2C distribution channel

### Product Goals
- Reduce research time for retail investors from hours to minutes
- Provide quantitatively rigorous sentiment scores with explainable confidence
- Detect emerging narratives and unusual activity before they reach mainstream coverage
- Build a trusted brand through transparent methodology and backtested accuracy

### Technical Goals
- Achieve < 5-minute end-to-end latency for Pro tier
- Process > 100,000 content items per day per major ticker
- Maintain 99.5% platform uptime
- Support horizontal scaling to 10,000 concurrent API requests

## Non-Goals (v1.0)

- **Not a trading platform:** We provide intelligence, not execution (regulatory boundary)
- **Not a financial advisor:** All outputs are informational, not investment advice
- **Not a prediction engine:** We score sentiment, not predict price targets
- **Not a news aggregator:** We augment, not replace, primary news consumption
- **Not a portfolio manager:** We analyze, not allocate
- **Not real-time options/derivatives analysis:** Out of scope for Phase 1–2

> ⚠️ **Compliance Note (Beginner-Friendly):** The distinction between "informational sentiment scores" and "investment advice" is legally critical. Scores must always be presented with disclosures, and the platform must never make directional buy/sell recommendations tied to specific price targets. Consult a securities attorney before launch. In the United States, the Investment Advisers Act of 1940 governs this boundary.

## User Personas

### Persona 1: The Active Retail Trader - "Alex"
- **Demographics:** 32 years old, software engineer, trades 10–20 hours/week
- **Portfolio:** $50K–$200K, primarily individual stocks + ETFs
- **Behavior:** Monitors Reddit, Twitter, Discord daily; uses TradingView for charts
- **Pain Points:** Spends 2–3 hours/day reading posts; no way to quantify what he's reading; fears missing sentiment shifts while sleeping
- **Jobs to Be Done:** "Know what the crowd is feeling about a stock before I enter a position"
- **Willingness to Pay:** $50–100/month for a reliable signal

### Persona 2: The Long-Term Growth Investor - "Sarah"
- **Demographics:** 45 years old, marketing director, invests 3–5 hours/week
- **Portfolio:** $150K–$500K, concentrated in 15–25 stocks, 3–5 year horizon
- **Behavior:** Reads Seeking Alpha, WSJ; follows select analysts on Substack
- **Pain Points:** Wants to know if the narrative around a stock is changing before quarterly earnings; concerned about missing early signs of reputational risk
- **Jobs to Be Done:** "Track how the investment thesis for my holdings is evolving across public discourse"
- **Willingness to Pay:** $30–50/month

### Persona 3: The Investment Researcher - "Marcus"
- **Demographics:** 28 years old, works at a family office; runs independent research on the side
- **Portfolio/Role:** Conducts due diligence on 40–60 stocks per quarter
- **Behavior:** Uses Bloomberg for fundamentals; needs a sentiment layer; writes Substack newsletter
- **Pain Points:** No programmatic way to run sentiment analysis across a watchlist; manual processes don't scale
- **Jobs to Be Done:** "Get API access to sentiment scores I can incorporate into my models and reports"
- **Willingness to Pay:** $100–200/month for API access

### Persona 4: The Fintech Builder - "Priya"
- **Demographics:** 35 years old, co-founder of a retail investment app
- **Company:** 50K DAU mobile investing app
- **Behavior:** Looking for white-labeled sentiment data to embed in their product
- **Pain Points:** Building sentiment in-house is cost-prohibitive; needs reliable, real-time data
- **Jobs to Be Done:** "Embed SentimentAI scores natively in our app UI via API"
- **Willingness to Pay:** $800–2,000/month enterprise

## User Stories

### Core User Stories

**US-001:** As Alex (active trader), I want to see a real-time composite sentiment score for TSLA so that I can gauge crowd conviction before entering a trade.

**US-002:** As Sarah (long-term investor), I want to see the dominant narrative themes being discussed about AAPL over the past 90 days so that I can identify if the investment thesis is changing.

**US-003:** As Marcus (researcher), I want API access to all 7 sentiment scores for a list of 50 tickers so that I can build a custom watchlist dashboard.

**US-004:** As Alex, I want to receive an alert when social momentum for NVDA spikes significantly above its 30-day baseline so that I can investigate before the crowd.

**US-005:** As any user, I want to see which sources and author types are driving a stock's sentiment score so that I can judge the credibility of the signal.

**US-006:** As Sarah, I want to see a sentiment history chart for MSFT over the past 6 months correlated with price performance so that I can assess the signal's historical predictive value.

**US-007:** As Priya (enterprise), I want webhook delivery of sentiment score updates so that I can update our app in near real-time without polling.

**US-008:** As Alex, I want the platform to flag unusual bot activity or coordinated posting campaigns targeting a stock so that I can discount manipulated signals.

**US-009:** As Marcus, I want to export raw scored data to CSV so that I can run my own quantitative analysis.

**US-010:** As any user, I want to understand *why* a score changed in plain English so that I can learn from the signal, not just consume it.

## Success Metrics

### Product Metrics (North Star: Weekly Active Users making data-driven decisions)

| Metric | Phase 1 Target | Phase 2 Target | Phase 3 Target |
|--------|---------------|---------------|---------------|
| Paying Subscribers | 500 | 5,000 | 25,000 |
| DAU/MAU Ratio | > 25% | > 35% | > 40% |
| API Calls/Day (Pro+) | 50K | 500K | 5M |
| Score Freshness (Pro) | < 10 min | < 5 min | < 2 min |
| Data Sources Active | 5 | 10 | 15+ |
| Tickers Supported | Top 500 | All US equities | Global equities |
| NPS Score | > 35 | > 50 | > 65 |

### Technical Quality Metrics

| Metric | Target |
|--------|--------|
| Platform Uptime | 99.5% (Phase 1), 99.9% (Phase 3+) |
| End-to-End Latency (p95) | < 10 min (Phase 1), < 5 min (Phase 2) |
| Bot Detection Accuracy | > 90% precision @ 85% recall |
| Sentiment Classification Accuracy | > 82% vs. human labels |
| Signal Backtesting (IC) | > 0.05 Information Coefficient over 5-day horizon |
| False Narrative Alert Rate | < 5% |

### Business Metrics

| Metric | Target |
|--------|--------|
| Monthly Recurring Revenue | $500K (Month 18) |
| MRR Growth Rate | > 15% MoM (Phase 1–2) |
| CAC (blended) | < $120 |
| LTV (Pro) | > $600 (18-month LTV) |
| Gross Margin | > 65% (Phase 2+) |
| Churn Rate (Monthly) | < 4% (Phase 1), < 2.5% (Phase 3) |

---

# Functional Requirements

## FR-01: Data Ingestion
- **FR-01.1:** System SHALL collect data from minimum 10 distinct sources per ticker analysis request
- **FR-01.2:** System SHALL support near-real-time ingestion with < 3-minute source-to-queue latency
- **FR-01.3:** System SHALL handle API rate limits gracefully without data loss using queue buffering
- **FR-01.4:** System SHALL deduplicate content across sources using content fingerprinting
- **FR-01.5:** System SHALL store raw content immutably for audit and reprocessing

## FR-02: Content Processing
- **FR-02.1:** System SHALL classify each item as Bullish / Bearish / Neutral with confidence probability
- **FR-02.2:** System SHALL detect and flag bot-generated content with probability score
- **FR-02.3:** System SHALL extract named entities (company names, tickers, people) from content
- **FR-02.4:** System SHALL detect misinformation patterns using LLM verification
- **FR-02.5:** System SHALL assess stock-specific relevance (0–1) for each content item
- **FR-02.6:** System SHALL extract queues and themes using LLM-based classification
- **FR-02.7:** System SHALL assign source trust and author credibility scores

## FR-03: Scoring Engine
- **FR-03.1:** System SHALL produce 7 distinct scores per ticker: RISS, STSS, LTCS, MNSS, SMS, CS, OCS
- **FR-03.2:** System SHALL provide 95% confidence intervals for each score
- **FR-03.3:** System SHALL explain score drivers in natural language (top 3 factors)
- **FR-03.4:** System SHALL apply time-decay weighting with configurable decay constants
- **FR-03.5:** System SHALL update scores within 5 minutes of new content ingestion (Pro tier)
- **FR-03.6:** System SHALL maintain historical score records with timestamp precision

## FR-04: Narrative Intelligence
- **FR-04.1:** System SHALL identify top 3–5 dominant narratives per ticker using embedding clustering
- **FR-04.2:** System SHALL track narrative momentum (rising, stable, declining)
- **FR-04.3:** System SHALL detect emerging narratives with < 2-hour detection lag
- **FR-04.4:** System SHALL detect cross-stock narrative correlation (sector themes)

## FR-05: Agent Orchestration
- **FR-05.1:** System SHALL operate a 10-agent LangGraph pipeline for each analysis workflow
- **FR-05.2:** System SHALL support parallel agent execution where dependencies allow
- **FR-05.3:** System SHALL implement retry logic with exponential backoff for failed agents
- **FR-05.4:** System SHALL provide human-in-the-loop escalation for low-confidence outputs

## FR-06: API & Delivery
- **FR-06.1:** System SHALL expose a RESTful API (OpenAPI 3.1 compliant) for all score types
- **FR-06.2:** System SHALL support WebSocket streaming for real-time score updates
- **FR-06.3:** System SHALL support webhook callbacks for score threshold alerts
- **FR-06.4:** System SHALL deliver email/push notifications for configured alerts

## FR-07: Backtesting
- **FR-07.1:** System SHALL store all historical scores with timestamps for backtesting
- **FR-07.2:** System SHALL calculate signal performance metrics (IC, Sharpe of signal, hit rate)
- **FR-07.3:** System SHALL visualize sentiment-price correlation over selectable time periods

---

# Non-Functional Requirements

## NFR-01: Performance
- API response time (score retrieval): p50 < 200ms, p95 < 800ms, p99 < 2s
- Score update latency (Pro tier): < 5 minutes from content publication to score update
- Websocket delivery: < 500ms from score change to client delivery
- Batch processing (historical): > 10,000 items/minute throughput

## NFR-02: Scalability
- Render handles service scaling automatically; no infrastructure management required.
- Data pipeline must scale to 1M+ items/day without architectural changes
- Vector database must support 50M+ embeddings with < 50ms query time (p95)
- Database reads must support 10,000 QPS per ticker

## NFR-03: Reliability & Availability
- System uptime: 99.5% (Phase 1), 99.9% (Phase 3), 99.95% (Enterprise SLA)
- RTO (Recovery Time Objective): < 1 hour
- RPO (Recovery Point Objective): < 15 minutes
- Zero data loss during component failures using Redis Queue persistence

## NFR-04: Security
- All data in transit: TLS 1.3
- All data at rest: AES-256 encryption
- API authentication: JWT + API key with rate limiting
- No storage of PII beyond platform authentication
- SOC 2 Type II compliance target (Phase 3)

## NFR-05: Observability
- Distributed tracing across all agent steps (OpenTelemetry)
- Structured logging with correlation IDs
- Real-time alerting on latency, error rate, queue depth
- Business metric dashboards (Grafana)

## NFR-06: Compliance
- GDPR-compatible data handling (right to erasure for user accounts)
- All outputs include investment disclaimer
- Content scraped in compliance with platform Terms of Service
- Data licensing agreements in place before commercial launch

> ⚠️ **Data Licensing Note (Beginner-Friendly):** Most social media platforms (Twitter/X, Reddit, etc.) have explicit Terms of Service that restrict or require licensing for commercial data use. X's API now requires paid access for any commercial application. Reddit's Data API is also paid. Budget $5,000–30,000/month for legitimate data access licenses before launch. Using scraping tools to bypass these APIs violates ToS and creates legal and operational risk. Always use official, licensed APIs.

---

# High-Level Architecture

```
╔══════════════════════════════════════════════════════════════════╗
║                    DATA SOURCES (External)                       ║
║  Twitter/X  Reddit  StockTwits  Reuters  WSJ  SeekingAlpha      ║
║  Substack   Yahoo Finance  Financial Blogs  StockTwits  EDGAR    ║
╚══════════════════════╤═══════════════════════════════════════════╝
                       │ Licensed APIs / Webhooks / RSS
╔══════════════════════▼═══════════════════════════════════════════╗
║              DATA INGESTION LAYER (Python Collectors)            ║
║   Rate-Limited API Clients → Content Normalizer → Deduplicator  ║
╚══════════════════════╤═══════════════════════════════════════════╝
                       │ Redis Queue Topics (raw.content.{source})
╔══════════════════════▼═══════════════════════════════════════════╗
║              MULTI-AGENT PROCESSING PIPELINE                     ║
║  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────────┐   ║
║  │Validator│→│  Cleaner │→│LLM Agent │→│ Sentiment Agent   │   ║
║  └─────────┘ └──────────┘ └──────────┘ └───────────────────┘   ║
║  ┌──────────────┐ ┌───────────┐ ┌─────────┐ ┌─────────────┐   ║
║  │Narrative Agent│→│Credibility│→│ Quant   │→│  Aggregator │   ║
║  └──────────────┘ └───────────┘ └─────────┘ └─────────────┘   ║
║                    Orchestrated by LangGraph                      ║
╚══════════════════════╤═══════════════════════════════════════════╝
                       │
         ┌─────────────┴───────────────┐
         │                             │
╔════════▼════════╗          ╔════════▼════════╗
║  STORAGE LAYER  ║          ║  VECTOR LAYER   ║
║  PostgreSQL      ║          ║  Qdrant (Embed) ║
║  Redis Cache     ║          ║  Semantic Search║
║  S3 (Raw/Audit) ║          ║  Clustering     ║
╚════════╤════════╝          ╚════════╤════════╝
         └─────────────┬─────────────┘
╔════════════════════▼══════════════════════════╗
║              SCORING ENGINE                    ║
║  RISS  STSS  LTCS  MNSS  SMS  CS  OCS        ║
║  Time-Decay  Confidence Intervals  Calibration ║
╚════════════════════╤══════════════════════════╝
                     │
╔════════════════════▼══════════════════════════╗
║           API / DELIVERY LAYER                 ║
║  FastAPI REST  WebSocket  Webhooks  GraphQL    ║
╚════════════════════╤══════════════════════════╝
                     │
╔════════════════════▼══════════════════════════╗
║              FRONTEND LAYER                    ║
║  Next.js Dashboard  Mobile (React Native)     ║
║  Real-Time Charts  Score Explanations         ║
╚═══════════════════════════════════════════════╝
```

---

# Detailed System Architecture

## Component Breakdown

### 1. Data Ingestion Service
- **Language:** Python 3.12
- **Framework:** FastAPI for health/control endpoints; asyncio for concurrent collection
- **Deployment:** 1 service per source family (social, news, discussion boards)
- **Output:** Normalized `RawContent` objects pushed to Redis Queue

### 2. Agent Orchestration Service
- **Framework:** LangGraph (primary), CrewAI (specialized sub-tasks)
- **LLM Providers:** OpenAI GPT-4o (primary), Anthropic Claude 3.7 (fallback/quality checks)
- **Embedding Models:** OpenAI `text-embedding-3-large` (3072d), with Cohere as fallback
- **Deployment:** Render Background Worker connected directly to the GitHub repository

### 3. Scoring Engine Service
- **Language:** Python (NumPy, SciPy, Pandas)
- **Scheduling:** Score recalculation triggered by Redis Queue events AND scheduled refresh every 5 minutes
- **Output:** Score objects pushed to PostgreSQL and Redis cache

### 4. API Gateway
- **Framework:** FastAPI + Uvicorn (ASGI)
- **Auth:** Supabase Auth (JWT) + API key management
- **Rate Limiting:** Redis-backed sliding window
- **Documentation:** Auto-generated OpenAPI 3.1

### 5. Frontend
- **Framework:** Next.js 15 (App Router) + TypeScript
- **Charts:** Recharts (open source), Lightweight Charts (TradingView) for price overlays
- **Real-time:** Socket.IO client + SWR for cache-while-revalidate
- **Deployment:** Vercel Edge Network

### 6. Infrastructure
- **Cloud:** Render (primary backend platform) with managed services
- **Deployment Model:** Render Web Services + Background Workers
- **Queue System:** Upstash Redis Queue / Confluent Cloud Redis Queue
- **CI/CD:** GitHub Actions → Render Auto Deploy

---

# Agent Architecture

## Overview

The agent architecture uses **LangGraph** as the primary orchestration framework, implementing a **directed acyclic graph (DAG) with conditional branching** and **persistent state management**. For complex sub-workflows (e.g., competitive analysis across multiple tickers), **CrewAI** crews operate as specialized sub-processes that LangGraph can invoke.

## LangGraph State Definition

```python
from typing import TypedDict, Annotated, List, Dict, Optional
from langgraph.graph import StateGraph, END
import operator

class ContentItem(TypedDict):
    id: str
    source: str
    text: str
    author_id: str
    timestamp: str
    metadata: Dict

class AgentState(TypedDict):
    # Input
    ticker: str
    analysis_id: str
    lookback_hours: int
    
    # Progressive data enrichment
    raw_items: List[ContentItem]
    validated_items: List[ContentItem]
    cleaned_items: List[ContentItem]
    analyzed_items: List[ContentItem]        # LLM analysis output
    sentiment_results: List[Dict]
    narrative_clusters: List[Dict]
    credibility_assessed: List[Dict]
    
    # Scores
    quant_scores: Dict[str, float]
    confidence_intervals: Dict[str, tuple]
    score_explanations: Dict[str, str]
    
    # Control flow
    errors: Annotated[List[str], operator.add]  # Accumulate errors
    retry_count: int
    human_escalation_required: bool
    pipeline_stage: str
    
    # Output
    final_report: Optional[Dict]
```

## Agent Specifications

### Agent 1: Data Collection Agent
**Responsibility:** Fetches raw content from all configured sources for a given ticker.

```
Inputs:  ticker, lookback_hours, source_configs
Outputs: raw_items (List[ContentItem])
Tools:   TwitterAPIClient, RedditAPIClient, RSSFeedParser, StockTwitsClient, SeekingAlphaClient
```

**Implementation Notes:**
- Uses `asyncio.gather()` for parallel source fetching
- Per-source rate limiting via Redis token bucket
- Implements exponential backoff (1s, 2s, 4s, 8s) on rate limit errors
- Content fingerprinting (SHA-256 of normalized text) for deduplication
- Targets < 60 seconds total collection time for top-tier sources

**Failure Handling:**
- If a source returns < 10 results, mark as `source_degraded` but continue
- If all sources fail for a ticker, emit `collection_failure` event and escalate
- Partial collection (>= 3 sources) proceeds with confidence penalty

### Agent 2: Data Validation Agent
**Responsibility:** Validates raw items for integrity, format compliance, and basic quality checks.

```
Inputs:  raw_items
Outputs: validated_items, validation_report
Checks:  Schema validation, encoding normalization, duplicate detection, 
         language detection (English filter), minimum content length,
         timestamp sanity checks, ticker mention verification
```

**Filters Applied:**
- Minimum post length: 15 characters
- Maximum post length: 50,000 characters (long-form articles)
- Language: English only (Phase 1–2); multilingual in Phase 4
- Ticker relevance: Must contain ticker symbol OR company name
- Timestamp: Must be within lookback window

**Expected Throughput:** 50,000 items/minute (CPU-bound, parallelized with `concurrent.futures`)

### Agent 3: Content Cleaning Agent
**Responsibility:** Normalizes text for downstream LLM processing.

```
Inputs:  validated_items
Outputs: cleaned_items
Steps:   URL removal → Emoji normalization → Hashtag extraction → 
         Cashtag extraction → Mention anonymization → HTML stripping →
         Boilerplate detection → Duplicate paragraph removal
```

**Technical Notes:**
- Custom regex pipeline + `ftfy` for encoding normalization
- Preserves market-specific tokens (`$TSLA`, `#earnings`, emoji sentiment signals)
- For long articles: extracts most relevant paragraphs using TF-IDF scoring against ticker context

### Agent 4: LLM Analysis Agent
**Responsibility:** Sends cleaned content to LLM for deep semantic understanding.

```
LLM:    Primary: Claude claude-sonnet-4-6 (best cost/quality for bulk)
        Premium: GPT-4o for ambiguous/high-stakes content
Batch:  Groups up to 20 items per LLM call to reduce latency/cost
```

**Prompt Engineering (Structured Output):**

```python
ANALYSIS_PROMPT = """
You are a financial content analyst. Analyze the following social media post/article
about {ticker} ({company_name}).

Content: {content}

Respond in JSON with exactly these fields:
{
  "sentiment": "bullish" | "bearish" | "neutral",
  "sentiment_confidence": float (0.0-1.0),
  "relevance_score": float (0.0-1.0, how relevant to {ticker} specifically),
  "queues": list of strings (max 5, from: earnings|technical_analysis|management|
             product|competition|regulation|macro|short_interest|options|insider),
  "key_claims": list of strings (specific factual or opinion claims made, max 3),
  "narrative_tags": list of strings (max 3 narrative themes),
  "quality_score": float (0.0-1.0, based on substance and specificity),
  "misinformation_flags": list of strings (specific suspicious claims, empty if none),
  "contains_price_target": boolean,
  "price_target": float or null,
  "time_horizon": "intraday" | "short_term" | "long_term" | "unspecified"
}
"""
```

**Cost Optimization:**
- Tier 1 (< 100 chars): Skip LLM; use FinBERT only (saves 80% of LLM calls)
- Tier 2 (100–500 chars): Claude Haiku / GPT-4o mini
- Tier 3 (> 500 chars, high-engagement, or news): Claude Sonnet / GPT-4o

**Caching:** LLM responses cached in Redis with 6-hour TTL using content hash as key. Reduces repeat processing of viral content by ~40%.

### Agent 5: Sentiment Agent
**Responsibility:** Combines LLM semantic sentiment with statistical NLP signals.

```
Inputs:  cleaned_items, llm_analysis_results
Models:  FinBERT (domain-specific financial sentiment)
         VADER (rule-based baseline)
         Custom fine-tuned RoBERTa (Phase 3, trained on financial corpus)
         LLM output (from Agent 4)
Ensemble: Weighted average:
         FinBERT: 0.35, LLM: 0.45, VADER: 0.10, Custom: 0.10 (Phase 3)
         FinBERT: 0.45, LLM: 0.45, VADER: 0.10 (Phase 1-2)
```

**Output per item:**
```json
{
  "item_id": "...",
  "sentiment_vector": [P_bullish, P_bearish, P_neutral],
  "sentiment_score": float (-1.0 to 1.0),
  "sentiment_confidence": float (0.0 to 1.0),
  "model_agreement": float (0.0 to 1.0, disagreement → lower confidence)
}
```

### Agent 6: Narrative Detection Agent
**Responsibility:** Identifies dominant themes and emerging narratives using embedding clustering.

```
Process:
1. Generate 3072-dim embeddings for all items (OpenAI text-embedding-3-large)
2. Store in Qdrant for this analysis session
3. Run HDBSCAN clustering (handles noise; no pre-defined cluster count)
4. Characterize each cluster using LLM summarization of 5 representative items
5. Calculate narrative metrics: size, coherence, momentum, sentiment
6. Cross-reference with historical narrative fingerprints
```

**Narrative Output:**
```json
{
  "narrative_id": "...",
  "theme_label": "AI Data Center Growth Story",
  "item_count": 847,
  "cluster_coherence": 0.73,
  "dominant_sentiment": "bullish",
  "sentiment_score": 0.72,
  "momentum": "rising",
  "momentum_velocity": 0.15,
  "first_detected": "2024-01-15T09:23:00Z",
  "key_sources": ["seeking_alpha", "twitter"],
  "summary": "Growing consensus that NVDA's data center segment..."
}
```

**Performance:** HDBSCAN on 10,000 items with 3072-dim embeddings reduced via PCA/UMAP to 128-dim: ~8 seconds

### Agent 7: Credibility Agent
**Responsibility:** Assesses author credibility, bot probability, and source trust.

```
Author Features:
- Verified status (boolean)
- Follower count (log-normalized)
- Account age (normalized to 5-year cap)
- Historical credibility EMA (from author_credibility table)
- Historical prediction accuracy (measured against price moves)
- Posting frequency (anomaly detection vs. personal baseline)
- Content diversity score (low diversity → bot signal)

Bot Detection Model:
- Features: posting_rate, template_similarity_score, follower/following_ratio,
  account_age, cashtag_frequency, content_uniqueness, engagement_pattern
- Model: XGBoost classifier trained on labeled bot/human dataset
- Threshold: P(bot) > 0.7 → exclude from scoring
- P(bot) 0.3–0.7 → partial weight reduction: w_bot = 1 - P(bot)
```

**Misinformation Detection:**
```python
# LLM-based fact-check for flagged claims
FACT_CHECK_PROMPT = """
The following financial claim was made about {ticker}: "{claim}"

Assess the following:
1. Is this claim verifiable? (yes/no/partially)
2. Does it contradict known public information? (yes/no/unknown)
3. Does it show hallmarks of pump-and-dump language? (yes/no)
4. Reliability assessment: "high" | "medium" | "low" | "suspicious"

Response in JSON only.
"""
```

### Agent 8: Quantitative Scoring Agent
**Responsibility:** Applies the mathematical scoring framework to produce all 7 scores.

This agent implements the full scoring model defined in the Quantitative Scoring Engine section. It receives enriched items and produces the final score objects.

### Agent 9: Signal Aggregation Agent
**Responsibility:** Aggregates individual item scores into ticker-level signals.

```
Functions:
- Weighted averaging with time-decay
- Outlier detection (IQR method) and Winsorization
- Confidence interval calculation (bootstrap resampling, n=1000)
- Signal change detection (vs. previous score)
- Alert threshold evaluation
- Cross-ticker sector signal aggregation
```

### Agent 10: Reporting Agent
**Responsibility:** Generates human-readable explanations and structured report objects.

```
Outputs:
- Natural language score explanation (3–5 sentences per score)
- Top-5 most influential content items (with excerpts)
- Top-3 dominant narratives with summaries
- Notable anomalies (bot clusters, misinformation, unusual engagement)
- Recommended reading (highest-quality bullish and bearish content)
- Data quality summary (coverage, source diversity, confidence)
```

**Output Format:**
```json
{
  "ticker": "NVDA",
  "analysis_id": "uuid",
  "generated_at": "ISO8601",
  "lookback_hours": 24,
  "data_coverage": {
    "total_items": 14782,
    "post_filtering": 11203,
    "source_breakdown": {...},
    "bot_exclusions": 1247,
    "spam_exclusions": 332
  },
  "scores": {
    "retail_sentiment": {"score": 72.4, "ci_95": [68.1, 76.7], "direction": "bullish"},
    "short_term_signal": {"score": 61.2, "ci_95": [56.8, 65.6], "direction": "bullish"},
    ...
  },
  "narratives": [...],
  "score_drivers": {...},
  "alerts": [...],
  "disclaimer": "..."
}
```

## LangGraph Workflow Definition

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.redis import RedisSaver
from typing import TypedDict, List, Dict, Optional, Literal, Annotated
import operator

# ─────────────────────────────────────────────────────────────────
# STATE DEFINITION - extended to support loop control
# ─────────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    # Input
    ticker:             str
    analysis_id:        str
    lookback_hours:     int

    # Progressive enrichment through pipeline
    raw_items:          List[Dict]
    validated_items:    List[Dict]
    cleaned_items:      List[Dict]

    # Parallel branch outputs - kept SEPARATE until merge node
    llm_results:        List[Dict]   # from analyze node (LLM)
    sentiment_results:  List[Dict]   # from sentiment node (FinBERT)

    # Post-merge
    merged_results:     List[Dict]   # combined, disagreement-annotated items
    disagreement_score: float        # mean disagreement across all items

    # Loop control - NEW, was completely missing before
    retry_count:        int          # 0 = never retried, 1 = retried once (max)
    llm_tier:           str          # "haiku" | "sonnet" - escalates on retry

    # Downstream
    narrative_clusters:     List[Dict]
    credibility_assessed:   List[Dict]
    quant_scores:           Dict
    signals:                Dict

    # Control flow
    human_escalation_required: bool
    errors: Annotated[List[str], operator.add]  # accumulates, never overwrites
    pipeline_stage: str

    # Final output
    final_report: Optional[Dict]


# ─────────────────────────────────────────────────────────────────
# NODE IMPLEMENTATIONS - the three missing ones
# ─────────────────────────────────────────────────────────────────

def merge_and_check(state: AgentState) -> AgentState:
    """
    NEW NODE - was completely absent in original code.

    1. Zips LLM results with FinBERT results item by item
    2. Computes per-item disagreement score
    3. Adjusts confidence proportional to disagreement
    4. Computes aggregate disagreement_score for routing decision
    """
    llm_results      = state["llm_results"]
    finbert_results  = state["sentiment_results"]

    merged = []
    total_disagreement = 0.0

    for llm_item, finbert_item in zip(llm_results, finbert_results):
        llm_score     = llm_item["sentiment_score"]       # -1.0 to +1.0
        finbert_score = finbert_item["sentiment_score"]   # -1.0 to +1.0

        # Disagreement: max possible = 2.0 (one says +1, other says -1)
        disagreement = abs(llm_score - finbert_score)

        # Confidence drops as disagreement rises
        # At disagreement=0:   confidence unchanged
        # At disagreement=1.0: confidence halved
        # At disagreement=2.0: confidence zeroed
        base_confidence   = (llm_item["sentiment_confidence"] +
                             finbert_item["sentiment_confidence"]) / 2
        adjusted_confidence = base_confidence * max(0.0, 1.0 - (disagreement / 2.0))

        merged.append({
            **llm_item,                                      # LLM output as base
            "finbert_score":        finbert_score,
            "disagreement":         round(disagreement, 4),
            "sentiment_confidence": round(adjusted_confidence, 4),
            "weight_in_scoring":    1.0,                     # may be reduced in apply_penalty
        })
        total_disagreement += disagreement

    avg_disagreement = total_disagreement / len(merged) if merged else 0.0

    return {
        **state,
        "merged_results":     merged,
        "disagreement_score": round(avg_disagreement, 4),
        "pipeline_stage":     "merge_complete",
    }


def escalation_prep(state: AgentState) -> AgentState:
    """
    NEW NODE - prepares state for LLM retry with a stronger model.

    Only runs when merge detects high disagreement on first pass.
    Upgrades llm_tier to 'sonnet' so analyze node uses the right model.
    Increments retry_count so we never loop more than once.
    Clears llm_results so analyze reruns cleanly on the same cleaned_items.
    """
    return {
        **state,
        "llm_tier":        "sonnet",         # upgrade from haiku → sonnet
        "retry_count":     state["retry_count"] + 1,
        "llm_results":     [],               # clear stale results; analyze will repopulate
        "pipeline_stage":  "escalation_prep",
    }


def apply_confidence_penalty(state: AgentState) -> AgentState:
    """
    NEW NODE - runs when disagreement is high but we've exhausted retries.

    Items with high disagreement still proceed to narrative clustering
    (Agent 6 can still place them in thematic clusters) but carry
    very low weight in the scoring engine.

    Disagreement buckets:
      > 0.8  → effectively dropped (weight = 0.0); flagged in report
      > 0.4  → heavy penalty    (weight = 0.3, confidence *= 0.4)
      <= 0.4 → no penalty       (should not reach here, but safe default)
    """
    penalized = []
    for item in state["merged_results"]:
        item = item.copy()
        d = item.get("disagreement", 0.0)

        if d > 0.8:
            item["weight_in_scoring"]    = 0.0
            item["sentiment_confidence"] = 0.0
            item["dropped_reason"]       = "high_model_disagreement"

        elif d > 0.4:
            item["weight_in_scoring"]    = 0.3
            item["sentiment_confidence"] = item["sentiment_confidence"] * 0.4
            item["dropped_reason"]       = "penalized_model_disagreement"

        penalized.append(item)

    return {
        **state,
        "merged_results":  penalized,
        "pipeline_stage":  "penalty_applied",
    }


# ─────────────────────────────────────────────────────────────────
# ROUTING FUNCTIONS
# ─────────────────────────────────────────────────────────────────

def route_after_merge(
    state: AgentState,
) -> Literal["escalation_prep", "apply_penalty", "narrative"]:
    """
    Decision point after every merge (both initial and post-retry pass).

    First pass  (retry_count == 0):
      - Low disagreement  → proceed to narrative normally
      - High disagreement → escalation_prep → analyze (retry with Sonnet)

    Second pass (retry_count == 1, after Sonnet retry):
      - Low disagreement  → proceed to narrative normally  ← Sonnet fixed it
      - High disagreement → apply_penalty → narrative      ← give up, discount items
    """
    disagreement = state["disagreement_score"]
    retry_count  = state["retry_count"]

    if disagreement < 0.4:
        # Agreement is acceptable - proceed regardless of retry_count
        return "narrative"

    if retry_count == 0:
        # First disagreement, haven't retried yet → escalate to Sonnet
        return "escalation_prep"

    # retry_count >= 1: already retried with Sonnet, still disagreeing → give up
    return "apply_penalty"


def route_after_aggregate(
    state: AgentState,
) -> Literal["escalate", "report"]:
    """Unchanged from original - human escalation for low overall confidence."""
    if state["human_escalation_required"]:
        return "escalate"
    return "report"


# ─────────────────────────────────────────────────────────────────
# GRAPH CONSTRUCTION - corrected
# ─────────────────────────────────────────────────────────────────

workflow = StateGraph(AgentState)

# ── Register all nodes (existing + three new ones) ──────────────
workflow.add_node("collect",          data_collection_agent)
workflow.add_node("validate",         data_validation_agent)
workflow.add_node("clean",            content_cleaning_agent)
workflow.add_node("analyze",          llm_analysis_agent)       # reads state["llm_tier"]
workflow.add_node("sentiment",        sentiment_agent)           # FinBERT, unchanged
workflow.add_node("merge",            merge_and_check)           # NEW
workflow.add_node("escalation_prep",  escalation_prep)           # NEW
workflow.add_node("apply_penalty",    apply_confidence_penalty)  # NEW
workflow.add_node("narrative",        narrative_detection_agent)
workflow.add_node("credibility",      credibility_agent)
workflow.add_node("quant_score",      quantitative_scoring_agent)
workflow.add_node("aggregate",        signal_aggregation_agent)
workflow.add_node("escalate",         human_escalation_handler)
workflow.add_node("report",           reporting_agent)

# ── Linear backbone ─────────────────────────────────────────────
workflow.set_entry_point("collect")
workflow.add_edge("collect",  "validate")
workflow.add_edge("validate", "clean")

# ── Parallel fan-out from clean ─────────────────────────────────
# Both branches start simultaneously after cleaning.
# LangGraph will wait for BOTH to complete before merge runs.
workflow.add_edge("clean", "analyze")     # → llm_results
workflow.add_edge("clean", "sentiment")   # → sentiment_results

# ── Fan-in: both branches converge at merge ──────────────────────
# FIXED: was "analyze → narrative" and "sentiment → credibility" before.
# Both now correctly flow into merge.
workflow.add_edge("analyze",   "merge")
workflow.add_edge("sentiment", "merge")

# ── Conditional routing after merge (handles the loop) ──────────
workflow.add_conditional_edges(
    "merge",
    route_after_merge,
    {
        "escalation_prep": "escalation_prep",  # high disagreement, first pass
        "apply_penalty":   "apply_penalty",    # high disagreement, post-retry
        "narrative":       "narrative",         # good agreement, proceed
    }
)

# ── THE LOOP ────────────────────────────────────────────────────
# escalation_prep upgrades llm_tier to "sonnet" + increments retry_count
# then routes back to analyze, which re-runs with the stronger model.
# analyze writes new llm_results to state.
# then goes back to merge, which re-evaluates disagreement.
# retry_count is now 1, so even if still disagreeing → apply_penalty (no infinite loop).
workflow.add_edge("escalation_prep", "analyze")   # ← THE LOOP

# ── apply_penalty rejoins the main path ─────────────────────────
# Penalized items still go through narrative clustering and credibility.
# They just carry near-zero weight in the scoring engine.
workflow.add_edge("apply_penalty", "narrative")

# ── Sequential final stages (unchanged) ─────────────────────────
workflow.add_edge("narrative",   "credibility")
workflow.add_edge("credibility", "quant_score")
workflow.add_edge("quant_score", "aggregate")

# ── Human escalation conditional (unchanged) ────────────────────
workflow.add_conditional_edges(
    "aggregate",
    route_after_aggregate,
    {
        "escalate": "escalate",
        "report":   "report",
    }
)
workflow.add_edge("escalate", "report")
workflow.add_edge("report",   END)

# ── Compile with Redis checkpointing ────────────────────────────
checkpointer = RedisSaver(redis_url=REDIS_URL)
app = workflow.compile(checkpointer=checkpointer)
```

## Memory Management

**Short-term memory (within run):** LangGraph state object (in-memory, Redis-backed checkpoint)

**Cross-run memory (author reputation):** PostgreSQL `author_credibility` table - persists and improves author scores across all analyses

**Semantic memory (narrative fingerprints):** Qdrant collection `narrative_fingerprints` - stores cluster centroids for historical narrative matching

**Episodic memory (analysis cache):** Redis - caches completed analyses for 30 minutes; prevents redundant processing for same ticker/window

## CrewAI Integration

CrewAI is used for **competitive analysis sub-workflows** invoked by the Reporting Agent:

```python
from crewai import Agent, Task, Crew

sector_analyst = Agent(
    role="Sector Sentiment Analyst",
    goal="Compare {ticker} sentiment against sector peers",
    tools=[SentimentDatabaseTool, VectorSearchTool]
)

competitive_researcher = Agent(
    role="Competitive Intelligence Agent", 
    goal="Identify sector-wide narrative shifts affecting {ticker}",
    tools=[NewsSearchTool, EmbeddingSearchTool]
)

sector_analysis_crew = Crew(
    agents=[sector_analyst, competitive_researcher],
    tasks=[sector_comparison_task, narrative_shift_task],
    process=Process.sequential
)
```

---

# Data Collection Layer

## Source Configuration

| Source | Type | Latency | Auth | Rate Limit | License Cost |
|--------|------|---------|------|------------|-------------|
| X/Twitter | Social | 1–3 min | Bearer OAuth2 | 500K tweets/month (Basic) | $100/mo+ |
| Reddit | Discussion | 1–5 min | OAuth2 | 60 requests/min | $0.24/1K requests |
| StockTwits | Financial Social | 1–2 min | API Key | 400 req/min | Free tier |
| Reuters RSS | News | 5–15 min | RSS/Paid API | Unlimited RSS | $0 (RSS), Paid API |
| Yahoo Finance | Discussion | 5–10 min | Unofficial/RapidAPI | Limited | RapidAPI tiers |
| Seeking Alpha | Financial | 15–30 min | Official API | Commercial License | $200–2000/mo |
| Google News | News aggregation | 5–15 min | SerpAPI | Per call | $50–500/mo |
| Substack | Newsletter | Manual/RSS | RSS | Unlimited | $0 |
| Financial blogs | News | 15–60 min | RSS | Unlimited | $0 |
| EDGAR | Regulatory | 15–60 min | Free API | 10 req/sec | $0 |

> ⚠️ **API Access Note (Beginner-Friendly):** Reddit charged $0.24 per 1,000 API requests after its API policy change in 2023. For a platform analyzing 100 stocks at 10,000 items/stock/day, that's 1M API calls/day → ~$240/day or ~$7,200/month in Reddit API costs alone. Budget carefully and consider tiered analysis (not all stocks need all sources at the same frequency). Always agree to and follow each platform's Developer Agreement before building commercial products on top of their data.

## Content Normalization Schema

```python
@dataclass
class RawContent:
    id: str                    # UUID
    source: str                # "twitter" | "reddit" | etc.
    source_item_id: str        # Native ID in source system
    ticker: str                # "$NVDA" normalized
    text: str                  # Original raw text
    author_id: str             # Internal author UUID
    author_source_id: str      # Platform-native author ID
    author_display_name: str
    author_follower_count: int
    author_verified: bool
    author_account_created: datetime
    engagement: Dict           # {likes, reposts, comments, saves, views}
    published_at: datetime
    collected_at: datetime
    url: str
    language: str              # ISO 639-1
    content_type: str          # "post" | "comment" | "article" | "reply"
    parent_id: Optional[str]   # For threaded discussions
    media_urls: List[str]
    hashtags: List[str]
    cashtags: List[str]        # e.g. ["$NVDA", "$AMD"]
    fingerprint: str           # SHA-256 of normalized text
```

## Deduplication Strategy

```python
# Content fingerprint: SHA-256 of lowercased, stripped text
def compute_fingerprint(text: str) -> str:
    normalized = " ".join(text.lower().split())
    return hashlib.sha256(normalized.encode()).hexdigest()

# Near-duplicate detection using MinHash LSH
# Detects reposts/paraphrases that aren't exact duplicates
from datasketch import MinHash, MinHashLSH

lsh = MinHashLSH(threshold=0.85, num_perm=128)
# Items with Jaccard similarity > 0.85 considered near-duplicates
# Keeps highest-engagement version; discards rest
```

---

# Data Processing Layer

## Processing Pipeline Stages

```
Raw Redis Queue Message
      │
      ▼
┌─────────────────┐
│ Schema Validator │  ← Pydantic model validation
└────────┬────────┘
         │
┌────────▼────────┐
│ Language Filter  │  ← fastText language detection (98% accuracy)
└────────┬────────┘
         │
┌────────▼────────┐
│ Deduplicator     │  ← Exact (fingerprint) + Near-dup (MinHash LSH)
└────────┬────────┘
         │
┌────────▼────────┐
│ Text Cleaner     │  ← URLs, HTML, encoding normalization
└────────┬────────┘
         │
┌────────▼────────┐
│ Relevance Filter │  ← Ticker mention + semantic relevance check
└────────┬────────┘
         │
┌────────▼────────┐    ┌─────────────────────┐
│ LLM Tier Router  │───▶│ Tier-appropriate LLM │
└────────┬────────┘    └──────────┬──────────┘
         │                        │
┌────────▼────────────────────────▼──────────┐
│           Enriched Content Item              │
│  sentiment + queues + entities + quality    │
└──────────────────────┬──────────────────────┘
                       │
              ┌────────┴────────┐
              │                 │
        ┌─────▼─────┐   ┌───────▼──────┐
        │  Postgres  │   │    Qdrant     │
        │ (metadata) │   │ (embeddings) │
        └───────────┘   └─────────────┘
```

## LLM Tier Routing Logic

```python
def route_to_llm_tier(item: ContentItem) -> str:
    char_count = len(item.text)
    is_high_engagement = item.engagement.get('total', 0) > 100
    is_news_source = item.source in ["reuters", "wsj", "seeking_alpha"]
    
    if char_count < 100 and not is_high_engagement:
        return "finbert_only"          # No LLM cost
    elif char_count < 500 and not is_news_source:
        return "claude_haiku"          # $0.00025/1K tokens
    elif is_news_source or is_high_engagement:
        return "claude_sonnet"         # $0.003/1K tokens
    else:
        return "claude_haiku"
```

## Processing Throughput Design

| Stage | Target Throughput | Parallelism Strategy |
|-------|------------------|---------------------|
| Ingestion | 100K items/hour | 20 async workers per source |
| Validation | 200K items/hour | ThreadPoolExecutor (CPU-bound) |
| LLM Tier 1 (FinBERT) | 50K items/hour | 8 GPU workers |
| LLM Tier 2 (Haiku) | 10K items/hour | 50 async API calls |
| LLM Tier 3 (Sonnet) | 2K items/hour | 20 async API calls |
| Embedding | 20K items/hour | Batch OpenAI calls (100 items/batch) |
| Scoring | 500K items/hour | NumPy vectorized operations |

---

# Vector Search Architecture

## Vector Database Comparison

| Criterion | Pinecone | Weaviate | Qdrant | Chroma |
|-----------|----------|----------|--------|--------|
| Managed SaaS | ✅ Excellent | ✅ Good | ✅ Good | ❌ Dev-only |
| Performance (QPS) | High | High | Very High | Low |
| Hybrid Search | ✅ | ✅ Excellent | ✅ | ❌ |
| Self-Hosted Option | ❌ SaaS only | ✅ | ✅ | ✅ |
| Cost (50M vectors) | $700+/mo | $400+/mo | $200+/mo (self) | N/A prod |
| Metadata Filtering | ✅ | ✅ | ✅ Excellent | Limited |
| Payload Storage | Limited | ✅ | ✅ | ✅ |
| Geo-distributed | ✅ | ✅ | Planned | ❌ |
| Ecosystem Maturity | Excellent | Very Good | Good | Early |
| Phase 1–2 Fit | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |

### Recommendation: **Qdrant**

**Rationale:**
- Best performance per dollar for managed deployment compatible with Render-based infrastructure
- Native Rust implementation: 4x throughput vs. Python-based alternatives
- Excellent filtering on metadata (ticker, timestamp, source, sentiment) without vector search penalty
- Payload storage: keeps item metadata collocated with vector, reducing DB round trips
- Strong LangChain integration out of the box
- Migration path: Qdrant Cloud (managed) available when self-hosting becomes operationally burdensome at scale

**Collection Design:**

```python
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, HnswConfigDiff

client.create_collection(
    collection_name="content_embeddings",
    vectors_config=VectorParams(
        size=3072,              # OpenAI text-embedding-3-large dimension
        distance=Distance.COSINE,
        hnsw_config=HnswConfigDiff(
            m=16,               # Graph connectivity
            ef_construct=200,   # Build-time accuracy
        )
    ),
    optimizers_config=OptimizersConfig(
        indexing_threshold=20000  # Build index after 20K points
    )
)

# Payload schema (stored alongside each vector)
payload_schema = {
    "item_id": "keyword",
    "ticker": "keyword",       # Filter: ticker == "NVDA"
    "source": "keyword",       # Filter: source in ["reuters", "wsj"]
    "sentiment_score": "float",# Filter: sentiment_score > 0.5
    "published_at": "datetime",# Filter: published_at > (now - 24h)
    "author_credibility": "float",
    "bot_probability": "float",
    "relevance_score": "float"
}
```

**Collections:**
- `content_embeddings`: All processed content (200M+ vectors at scale)
- `narrative_fingerprints`: Cluster centroids for narrative matching (50K vectors)
- `author_profiles`: Author writing style fingerprints (5M vectors)

**Query Patterns:**
```python
# Semantic search: "What are people saying about NVDA's AI strategy?"
results = client.search(
    collection_name="content_embeddings",
    query_vector=embed("NVDA artificial intelligence data center strategy"),
    query_filter=Filter(must=[
        FieldCondition(key="ticker", match=MatchValue(value="NVDA")),
        FieldCondition(key="published_at", range=DatetimeRange(gte=cutoff_time)),
        FieldCondition(key="bot_probability", range=Range(lte=0.3))
    ]),
    limit=50,
    with_payload=True
)

# Narrative clustering: find similar narratives to current cluster centroid
results = client.search(
    collection_name="narrative_fingerprints",
    query_vector=current_cluster_centroid,
    limit=5
)
```

---

# LLM Analysis Pipeline

## Model Strategy

### Model Selection Matrix

| Use Case | Phase 1–2 | Phase 3+ | Fallback |
|----------|-----------|---------|---------|
| Deep analysis (articles, long posts) | Claude claude-sonnet-4-6 | Claude Opus / GPT-4o | Claude Haiku |
| Bulk sentiment (short posts) | Claude Haiku / GPT-4o mini | Fine-tuned OSS | FinBERT |
| Fact-checking / misinformation | GPT-4o | Claude Opus | GPT-4o mini |
| Narrative summarization | Claude claude-sonnet-4-6 | Claude claude-sonnet-4-6 | GPT-4o |
| Report generation | Claude claude-sonnet-4-6 | Claude Opus | GPT-4o |
| Embeddings | OpenAI text-embedding-3-large | Same | Cohere embed-v3 |

### Open Source Alternatives (Phase 3 Cost Optimization)

For bulk processing (Tier 1/2), self-hosted models can reduce LLM costs by 70–80%:
- **FinBERT** (ProsusAI): Financial domain-specific sentiment, deployable on A100 GPU
- **Llama 3.1 70B** (Meta): General analysis quality competitive with GPT-4o mini at zero per-call cost
- **Mistral 7B** (fine-tuned on financial corpus): Fastest inference for bulk tasks
- **Deployment:** managed GPU providers (Modal, Runservice instance, Together, etc.) or on-prem A100 cluster; break-even vs. API at ~5M calls/month

### LLM Cost Optimization Techniques

1. **Intelligent caching:** SHA-256 fingerprint → Redis cached response (6-hour TTL). Viral content processed once despite 10,000+ encounters.
2. **Tier routing:** Only 15% of content items require full LLM analysis (Tier 3); 55% use Haiku; 30% use FinBERT only.
3. **Prompt compression:** Use DSPy-style prompt optimization to reduce average token count by 30%.
4. **Batch processing:** Group 20–50 items per LLM API call using structured output.
5. **Asynchronous queuing:** LLM calls dispatched asynchronously; no blocking.

### Context Window Management

For long articles (up to 50,000 characters):
1. Extract first and last paragraphs (always informative for conclusions/thesis)
2. TF-IDF sentence scoring against ticker context: select top N sentences
3. Rolling window processing for articles exceeding 8K tokens: chunk with 20% overlap
4. Hierarchical summarization: chunks → intermediate summary → final analysis

---

# Quantitative Scoring Engine

## Mathematical Framework

> **Design Principle:** Every score must be interpretable, reproducible, backtestable, and auditable. No black-box aggregations.

### Notation

Let:
- **D** = {d₁, d₂, ..., dₙ} - the set of all processed content items for ticker **T** over time window **W**
- For each item **dᵢ**: a feature vector **fᵢ** = (fᵢᵃ, fᵢᶜ, fᵢᵉ, fᵢᵇ, fᵢᵗ, fᵢˢ, fᵢᵐ)
  where superscripts denote: **a**=author, **c**=content, **e**=engagement, **b**=behavior, **t**=time, **s**=source, **m**=market

---

## Feature Engineering

### 1. Author Score - A(dᵢ)

$$A(d_i) = \alpha_1 \cdot \text{log\_norm}(F_i) + \alpha_2 \cdot V_i + \alpha_3 \cdot \text{age\_score}(a_i) + \alpha_4 \cdot \text{EMA}(C_i) + \alpha_5 \cdot \text{acc\_score}(i)$$

Where:
- **log\_norm(Fᵢ)** = log(1 + follower\_count) / log(1 + max\_follower\_count) ∈ [0, 1]
- **Vᵢ** = 1 if verified else 0
- **age\_score(aᵢ)** = min(account\_age\_years / 5, 1.0) - capped at 5 years
- **EMA(Cᵢ)** = exponential moving average of historical credibility ratings ∈ [0, 1]
- **acc\_score(i)** = historical directional accuracy: TP / (TP + FP) from tracked predictions

**Default weights:** α⃗ = [0.20, 0.25, 0.10, 0.25, 0.20] (sum to 1.0, empirically calibrated)

**Source-type adjustments:**
- Institutional accounts (verified news organizations): A(dᵢ) multiplied by 1.3 (capped at 1.0)
- Anonymous accounts (no verifiable identity): A(dᵢ) multiplied by 0.7

### 2. Sentiment Score - S(dᵢ)

Raw directional sentiment derived from ensemble model:

$$S(d_i) = P(\text{bullish}|d_i) - P(\text{bearish}|d_i) \in [-1, 1]$$

**Ensemble composition (Phase 2):**
$$P(\text{bullish}|d_i)_{\text{ensemble}} = 0.45 \cdot P_{\text{LLM}} + 0.40 \cdot P_{\text{FinBERT}} + 0.15 \cdot P_{\text{VADER}}$$

**Sentiment confidence:**
$$\text{conf}(d_i) = \max(P(\text{bullish}), P(\text{bearish}), P(\text{neutral})) \cdot (1 - \sigma_{\text{models}})$$

where σ_models is the standard deviation of sentiment probabilities across models (disagreement penalty).

### 3. Bot Probability - P_bot(dᵢ)

$$P_{\text{bot}}(d_i) = \sigma\left(\mathbf{w}_{\text{bot}}^T \mathbf{x}_{\text{bot}}(d_i) + b\right)$$

**Features xbot:**

| Feature | Description | Signal |
|---------|-------------|--------|
| posting\_rate\_24h | Posts per hour in last 24h | High → bot |
| template\_similarity | Cosine sim to known bot templates | High → bot |
| follower\_following\_ratio | Followers / Following | Near 0 or > 100 → anomaly |
| account\_age\_days | Days since account creation | < 30 → suspicious |
| content\_uniqueness | Distinct vocabulary ratio | Low → bot |
| cashtag\_density | Cashtags per post | Very high → spam |
| engagement\_irregularity | Engagement pattern vs. organic baseline | High → inauthentic |
| posting\_time\_regularity | Clock regularity of posts | Perfect intervals → bot |

**Model:** XGBoost classifier trained on labeled dataset (human-annotated + known bot accounts).

**Application:**
- P_bot(dᵢ) > 0.70 → exclude item from all scoring
- P_bot(dᵢ) ∈ [0.30, 0.70] → partial weight: w_bot(dᵢ) = 1 - P_bot(dᵢ)
- P_bot(dᵢ) < 0.30 → full weight: w_bot(dᵢ) = 1.0

### 4. Time Decay - w_t(dᵢ)

Standard exponential decay:
$$w_t(d_i) = e^{-\lambda \cdot \Delta t_i}$$

where Δtᵢ = (now − published\_at) in hours.

**Decay constants by context:**

| Context | λ (per hour) | Half-life |
|---------|-------------|----------|
| Short-term signal (STSS) | 0.50 | 1.4 hours |
| Standard (RISS, OCS) | 0.10 | 6.9 hours |
| Medium-term (MNSS) | 0.03 | 23 hours |
| Long-term conviction (LTCS) | 0.005 | 5.8 days |
| Breaking news boost | −0.20 (inverse) | Amplifies recency |

**Burst Detection:** During high-activity periods (mention volume > 3σ above 30-day baseline), the STSS decay is further accelerated (λ → 0.75) to emphasize the most recent signals.

### 5. Engagement Quality Score - E(dᵢ)

$$E(d_i) = \sum_j \gamma_j \cdot \text{norm}(e_{ij}) + \delta \cdot \text{EV\_norm}(d_i)$$

Where engagement types j ∈ {likes, reposts/retweets, comments, saves/bookmarks}:

| Type | Weight γⱼ | Rationale |
|------|----------|-----------|
| Likes | 0.15 | Low-friction, weak signal |
| Reposts/Retweets | 0.30 | Active content sharing |
| Comments | 0.35 | Highest intent, most meaningful |
| Saves/Bookmarks | 0.20 | Private endorsement |

**Engagement Velocity (EV):**
$$\text{EV}(d_i) = \frac{\Delta e_i}{\Delta t} \quad [\text{engagements per minute}]$$

$$\text{EV\_norm}(d_i) = \min\left(\frac{\text{EV}(d_i)}{\text{EV}_{p95}}, 1.0\right)$$

**Normalization:** Each engagement type normalized using log-normalization against the 95th percentile for that source (different platforms have vastly different engagement scales).

$$\text{norm}(e_{ij}) = \frac{\log(1 + e_{ij})}{\log(1 + e_{p95,j})}$$

**Engagement Quality vs. Quantity Distinction:**
A post with 10 substantive comments > a post with 1,000 bot-generated likes. The model accounts for this by:
- Applying bot probability to engagement attribution (high-bot-probability engagers discounted)
- Flagging engagement anomalies (sudden spike > 5σ in 1 hour without news catalyst)

### 6. Source Trust Score - T(dᵢ)

Static baseline (updated quarterly via editorial review):

| Source | T(dᵢ) | Rationale |
|--------|--------|-----------|
| Reuters, Bloomberg, AP | 0.95 | Professional editorial, high accountability |
| Wall Street Journal, FT | 0.90 | Premium financial journalism |
| Seeking Alpha (verified) | 0.75 | Edited financial research |
| CNBC, Yahoo Finance News | 0.70 | Reputable but speed-driven |
| Twitter/X (verified accounts) | 0.65 | Identity verified, variable quality |
| Substack (established authors) | 0.60 | Self-published, audience-validated |
| Reddit r/investing | 0.55 | Community-moderated, retail perspective |
| StockTwits | 0.50 | Financial community, unfiltered |
| Twitter/X (unverified) | 0.45 | Anonymous, higher noise |
| Reddit r/WallStreetBets | 0.40 | Retail sentiment with higher meme risk |
| Unknown blogs | 0.30 | Unverifiable, lowest trust |

**Dynamic adjustment:** Source trust updated based on:
- Historical accuracy of content from that source (±0.05 per quarter)
- Misinformation incident history (−0.15 per confirmed incident)
- Peer review signal (content from this source engaged with by high-credibility authors: +0.03)

### 7. Content Quality Score - Q(dᵢ)

LLM-assigned quality score from analysis prompt, normalized ∈ [0, 1].

Factors assessed:
- Specificity (concrete data vs. vague opinion)
- Originality (new analysis vs. repost/reaction)
- Substance (evidence-backed vs. assertion-only)
- Relevance to investment thesis
- Absence of manipulation language

---

## Composite Raw Sentiment Score

The core aggregation formula (ticker-level):

$$\boxed{S_{\text{raw}}(T) = \frac{\displaystyle\sum_{i \in D} w_t(d_i) \cdot w_{\text{bot}}(d_i) \cdot A(d_i) \cdot T(d_i) \cdot Q(d_i) \cdot E_{\text{norm}}(d_i) \cdot S(d_i)}{\displaystyle\sum_{i \in D} w_t(d_i) \cdot w_{\text{bot}}(d_i) \cdot A(d_i) \cdot T(d_i) \cdot Q(d_i) \cdot E_{\text{norm}}(d_i)}}$$

This is a **quality-weighted average** of item-level sentiment scores, where the weight of each item is a product of all quality factors.

**Final normalized score (−100 to +100):**

$$S_{\text{final}}(T) = 100 \cdot \tanh\left(k \cdot S_{\text{raw}}(T)\right)$$

where **k = 2.0** is a calibration constant that produces a natural distribution centered around 0 with soft saturation at extremes. The hyperbolic tangent prevents extreme scores from dominating and provides a sigmoid-shaped response to strong signals.

---

## Individual Score Definitions

### Score 1: Retail Investor Sentiment Score (RISS)
**Purpose:** Pure retail crowd sentiment, excluding institutional/professional noise.

**Modifications from base formula:**
- Source filter: Excludes Reuters, WSJ, Bloomberg, Seeking Alpha
- Account filter: Excludes accounts with > 500K followers or verified-institution status
- Language filter: Weights conversational financial language (first-person, informal) more
- Time window: 24 hours, standard λ = 0.10
- RISS-specific weight boost: `retail_language_score` ∈ [0,1] (LLM-assessed)

### Score 2: Short-Term Trading Signal Score (STSS)
**Purpose:** 24-hour momentum signal for tactical positioning.

**Modifications:**
- Time window: 24 hours only
- Decay constant: λ = 0.50 (aggressive; half-life = 1.4 hours)
- Weight boost: Engagement velocity (3× standard weight)
- Include: Options mentions, specific price targets, short interest references, technical level discussions
- STSS direction: Score > 0 ≡ bullish signal; < 0 ≡ bearish signal

### Score 3: Long-Term Conviction Score (LTCS)
**Purpose:** Structural narrative strength for position building decisions.

**Modifications:**
- Time window: 90 days
- Decay constant: λ = 0.005 (slow; half-life = 5.8 days)
- Source weight boost: Institutional analysis (+1.5×), Substack long-form (+1.3×)
- Content filter: Minimum quality score Q(dᵢ) > 0.6 (removes noise)
- Includes: Fundamental analysis mentions, business model discussions, competitive positioning

### Score 4: Market Narrative Strength Score (MNSS)
**Purpose:** Measures narrative coherence and dominance across discourse.

**Algorithm:**
1. Generate embedding for all items (vector dimension: 3072)
2. HDBSCAN clustering in reduced 128-dim space (UMAP)
3. For each cluster k: compute metrics
4. MNSS = Σₖ (cluster_weight_k × coherence_k × sentiment_k × momentum_k)

$$\text{MNSS} = 100 \cdot \tanh\left(\sum_k \frac{n_k}{N} \cdot \rho_k \cdot S_k \cdot m_k\right)$$

Where:
- nₖ / N = cluster size fraction
- ρₖ = cluster coherence (mean pairwise cosine similarity within cluster)
- Sₖ = mean sentiment of cluster
- mₖ = narrative momentum (slope of cluster size over time)

### Score 5: Social Momentum Score (SMS)
**Purpose:** Rate of change in social attention - identifies acceleration before price moves.

$$\text{SMS}(T) = 100 \cdot \tanh\left(\frac{V_{24h} - \bar{V}_{30d}}{\sigma_{30d}}\right)$$

Where:
- V₂₄ₕ = mention volume in last 24 hours
- V̄₃₀d = 30-day rolling mean of daily mention volume
- σ₃₀d = 30-day rolling standard deviation

This is essentially a Z-score of current activity vs. historical baseline, normalized via tanh.

**Burst Detection Supplement:**
CUSUM algorithm monitors for sudden regime changes:
$$C_t = \max(0, C_{t-1} + V_t - \bar{V} - k\sigma)$$

Alert triggered when Cₜ > threshold h. This catches coordinated campaigns and news-driven spikes.

### Score 6: Confidence Score (CS)

$$\text{CS} = \min\left(\frac{n}{n_{\text{target}}}, 1.0\right) \times \left(1 - \sigma_S\right) \times \text{Div} \times 100$$

Where:
- n = number of valid items after filtering; n_target = 500 (saturation point)
- σ_S = standard deviation of individual item sentiment scores (consistency penalty; ranges 0–1)
- Div = source diversity ratio: unique_sources_with_data / total_configured_sources

**Interpretation:**
- CS > 80: High confidence - large volume, consistent signal, diverse sources
- CS 50–80: Moderate confidence - usable signal, interpret with caution
- CS < 50: Low confidence - small stock or news gap; score less reliable

### Score 7: Overall Composite Score (OCS)

$$\text{OCS} = w_{\text{RISS}} \cdot \text{RISS} + w_{\text{STSS}} \cdot \text{STSS} + w_{\text{LTCS}} \cdot \text{LTCS} + w_{\text{MNSS}} \cdot \text{MNSS} + w_{\text{SMS}} \cdot \text{SMS}$$

**Default weights:** w⃗ = [0.25, 0.20, 0.25, 0.15, 0.15]

**Dynamic reweighting based on user profile:**
- "Trader" profile: STSS weight → 0.40, LTCS weight → 0.10
- "Investor" profile: LTCS weight → 0.40, STSS weight → 0.05
- "Researcher" profile: MNSS weight → 0.30, equal other weights

---

## Confidence Intervals

All scores reported with bootstrapped 95% confidence intervals:

```python
def bootstrap_ci(scores: np.ndarray, n_bootstrap: int = 1000, ci: float = 0.95) -> tuple:
    """
    Bootstrap confidence interval for weighted mean sentiment score.
    """
    boot_means = []
    n = len(scores)
    for _ in range(n_bootstrap):
        sample = np.random.choice(scores, size=n, replace=True)
        boot_means.append(np.mean(sample))
    
    lower = np.percentile(boot_means, (1 - ci) / 2 * 100)
    upper = np.percentile(boot_means, (1 + ci) / 2 * 100)
    return (round(lower, 2), round(upper, 2))
```

---

## Calibration Process

**Initial calibration:** Train calibration model on 6-month historical dataset:
- Sentiment scores at time T → actual 5-day stock return
- Platt scaling (logistic regression) to calibrate probability estimates
- Isotonic regression for non-parametric calibration

**Ongoing calibration:** Monthly recalibration using:
- Continuous feedback loop: Compare past scores against realized returns
- Reliability diagrams to detect systematic over/under-confidence
- Temperature scaling adjustment for neural model outputs

---

# Database Design

## Schema Overview

### PostgreSQL Schema (Core Relational Data)

```sql
-- Tickers reference table
CREATE TABLE tickers (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol      VARCHAR(10) UNIQUE NOT NULL,     -- "NVDA"
    company_name TEXT NOT NULL,
    sector      VARCHAR(100),
    industry    VARCHAR(100),
    market_cap  BIGINT,
    exchange    VARCHAR(20),                      -- "NASDAQ"
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Data sources configuration
CREATE TABLE data_sources (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100) UNIQUE NOT NULL,  -- "twitter"
    display_name    VARCHAR(100),                   -- "X / Twitter"
    source_type     VARCHAR(50),                    -- "social"|"news"|"discussion"
    base_trust_score DECIMAL(4,3) DEFAULT 0.5,     -- 0.000 to 1.000
    is_active       BOOLEAN DEFAULT TRUE,
    rate_limit_rpm  INTEGER,                        -- requests per minute
    api_key_required BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Author profiles (cross-source)
CREATE TABLE authors (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id               UUID REFERENCES data_sources(id),
    platform_user_id        VARCHAR(255),           -- native ID on platform
    username                VARCHAR(255),
    display_name            VARCHAR(500),
    is_verified             BOOLEAN DEFAULT FALSE,
    follower_count          BIGINT DEFAULT 0,
    following_count         BIGINT DEFAULT 0,
    account_created_at      TIMESTAMPTZ,
    account_age_score       DECIMAL(4,3),           -- computed, 0-1
    historical_credibility  DECIMAL(4,3) DEFAULT 0.5, -- EMA, 0-1
    prediction_accuracy     DECIMAL(4,3),            -- vs price moves
    bot_probability         DECIMAL(4,3) DEFAULT 0.0, -- 0-1
    posts_analyzed          INTEGER DEFAULT 0,
    last_analyzed_at        TIMESTAMPTZ,
    reputation_score        DECIMAL(4,3) DEFAULT 0.5, -- composite 0-1
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source_id, platform_user_id)
);

-- Raw content (immutable, append-only)
CREATE TABLE raw_content (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker_id           UUID REFERENCES tickers(id),
    source_id           UUID REFERENCES data_sources(id),
    author_id           UUID REFERENCES authors(id),
    platform_item_id    VARCHAR(500),               -- native ID
    content_fingerprint VARCHAR(64) UNIQUE NOT NULL, -- SHA-256
    raw_text            TEXT NOT NULL,
    content_type        VARCHAR(50),                 -- "post"|"article"|"comment"
    parent_item_id      UUID REFERENCES raw_content(id), -- for threads
    url                 TEXT,
    language            CHAR(5) DEFAULT 'en',
    char_count          INTEGER,
    published_at        TIMESTAMPTZ NOT NULL,
    collected_at        TIMESTAMPTZ DEFAULT NOW(),
    -- Engagement snapshot at collection time
    engagement_likes    BIGINT DEFAULT 0,
    engagement_reposts  BIGINT DEFAULT 0,
    engagement_comments BIGINT DEFAULT 0,
    engagement_saves    BIGINT DEFAULT 0,
    engagement_views    BIGINT DEFAULT 0,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Processed content (enriched)
CREATE TABLE processed_content (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_content_id      UUID REFERENCES raw_content(id) UNIQUE,
    processing_version  VARCHAR(20) NOT NULL,       -- "1.0.0" (schema version)
    clean_text          TEXT,
    
    -- Sentiment outputs
    sentiment           VARCHAR(10),                -- "bullish"|"bearish"|"neutral"
    sentiment_score     DECIMAL(6,4),               -- -1.0000 to 1.0000
    sentiment_confidence DECIMAL(4,3),
    finbert_score       DECIMAL(6,4),
    llm_score           DECIMAL(6,4),
    vader_score         DECIMAL(6,4),
    
    -- LLM Analysis
    relevance_score     DECIMAL(4,3),
    quality_score       DECIMAL(4,3),
    queues              JSONB,                      -- ["earnings","AI","competition"]
    key_claims          JSONB,
    narrative_tags      JSONB,
    contains_price_target BOOLEAN DEFAULT FALSE,
    price_target        DECIMAL(10,2),
    time_horizon        VARCHAR(20),
    
    -- Author/Content assessment
    bot_probability     DECIMAL(4,3),
    misinformation_flags JSONB,
    engagement_quality_score DECIMAL(4,3),
    engagement_velocity DECIMAL(10,4),             -- engagements/minute
    author_score        DECIMAL(4,3),
    source_trust_score  DECIMAL(4,3),
    
    -- Embedding reference
    qdrant_point_id     VARCHAR(100),               -- ID in Qdrant
    embedding_model     VARCHAR(100),
    
    processed_at        TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Ticker-level sentiment scores (time series)
CREATE TABLE ticker_scores (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker_id       UUID REFERENCES tickers(id),
    score_version   VARCHAR(20) DEFAULT '1.0.0',    -- scoring engine version
    
    -- Lookback window
    window_hours    INTEGER NOT NULL,               -- 24, 72, 168, 720, 2160
    calculated_at   TIMESTAMPTZ NOT NULL,
    
    -- Item counts
    items_collected  INTEGER,
    items_after_filter INTEGER,
    items_excluded_bot INTEGER,
    
    -- Seven scores (-100 to +100)
    riss            DECIMAL(6,2),                   -- Retail Investor Sentiment Score
    riss_ci_lower   DECIMAL(6,2),
    riss_ci_upper   DECIMAL(6,2),
    
    stss            DECIMAL(6,2),                   -- Short-Term Trading Signal
    stss_ci_lower   DECIMAL(6,2),
    stss_ci_upper   DECIMAL(6,2),
    
    ltcs            DECIMAL(6,2),                   -- Long-Term Conviction
    ltcs_ci_lower   DECIMAL(6,2),
    ltcs_ci_upper   DECIMAL(6,2),
    
    mnss            DECIMAL(6,2),                   -- Market Narrative Strength
    mnss_ci_lower   DECIMAL(6,2),
    mnss_ci_upper   DECIMAL(6,2),
    
    sms             DECIMAL(6,2),                   -- Social Momentum
    sms_ci_lower    DECIMAL(6,2),
    sms_ci_upper    DECIMAL(6,2),
    
    confidence_score DECIMAL(6,2),
    
    ocs             DECIMAL(6,2),                   -- Overall Composite
    ocs_ci_lower    DECIMAL(6,2),
    ocs_ci_upper    DECIMAL(6,2),
    
    -- Explainability
    score_drivers   JSONB,                          -- top factors
    data_quality    JSONB,                          -- source breakdown
    
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Narratives detected per ticker
CREATE TABLE narratives (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker_id       UUID REFERENCES tickers(id),
    narrative_key   VARCHAR(100),                   -- stable key for tracking
    theme_label     TEXT NOT NULL,
    summary         TEXT,
    dominant_sentiment VARCHAR(10),
    sentiment_score DECIMAL(6,4),
    item_count      INTEGER,
    cluster_coherence DECIMAL(4,3),
    momentum_direction VARCHAR(20),                 -- "rising"|"stable"|"declining"
    momentum_velocity DECIMAL(8,4),
    first_detected_at TIMESTAMPTZ,
    last_updated_at   TIMESTAMPTZ DEFAULT NOW(),
    qdrant_centroid_id VARCHAR(100),
    is_active         BOOLEAN DEFAULT TRUE,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

-- Alerts configuration and history
CREATE TABLE alert_configs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID,                               -- foreign key to auth.users
    ticker_id   UUID REFERENCES tickers(id),
    alert_type  VARCHAR(50),                        -- "score_threshold"|"sms_spike"|"bot_cluster"
    condition   JSONB,                              -- {"score": "ocs", "op": "gt", "value": 70}
    delivery    VARCHAR(50),                        -- "email"|"push"|"webhook"
    webhook_url TEXT,
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Backtesting results
CREATE TABLE backtest_results (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker_id           UUID REFERENCES tickers(id),
    score_type          VARCHAR(20),                -- "stss"|"ltcs"|"ocs"
    lookback_period     VARCHAR(20),                -- "24h"|"7d"|"30d"
    forward_period      VARCHAR(20),                -- "1d"|"5d"|"21d"
    evaluation_date     DATE NOT NULL,
    
    -- Score at evaluation date
    sentiment_score     DECIMAL(6,2),
    
    -- Actual market outcome
    actual_return_pct   DECIMAL(8,4),              -- % return over forward_period
    market_return_pct   DECIMAL(8,4),              -- benchmark return
    excess_return_pct   DECIMAL(8,4),              -- alpha
    
    -- Signal metrics
    signal_direction    VARCHAR(10),                -- "bullish"|"bearish"
    was_correct         BOOLEAN,
    
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_raw_content_ticker_published ON raw_content(ticker_id, published_at DESC);
CREATE INDEX idx_processed_content_ticker ON processed_content(raw_content_id);
CREATE INDEX idx_ticker_scores_ticker_window ON ticker_scores(ticker_id, window_hours, calculated_at DESC);
CREATE INDEX idx_narratives_ticker_active ON narratives(ticker_id, is_active, last_updated_at DESC);
CREATE INDEX idx_backtest_ticker_score ON backtest_results(ticker_id, score_type, evaluation_date);

-- TimescaleDB hypertable for score time series (for efficient time-range queries)
-- SELECT create_hypertable('ticker_scores', 'calculated_at');
-- SELECT create_hypertable('raw_content', 'published_at');
```

### Redis Cache Schema

```
# Score cache (refreshed every 5 minutes)
scores:{ticker}:{window_hours}          TTL: 10 min    → JSON score object
scores:{ticker}:latest                   TTL: 5 min     → latest OCS + 24h scores

# Author cache
author:{source}:{platform_id}           TTL: 1 hour    → author profile JSON
author:bot_prob:{platform_id}           TTL: 24 hours  → cached bot probability

# LLM response cache
llm:fingerprint:{sha256}               TTL: 6 hours   → LLM analysis JSON

# Rate limiting
ratelimit:user:{user_id}               TTL: rolling    → request counter
ratelimit:source:{source_name}         TTL: rolling    → API call counter

# Session/websocket state
ws:session:{session_id}                TTL: 1 hour    → active subscription config

# Analysis job tracking
job:{analysis_id}                      TTL: 1 hour    → current pipeline stage, progress
```

### S3 Storage (Object Storage)

```
s3://sentimentai-{env}-raw/
├── raw/{source}/{year}/{month}/{day}/{hour}/
│   └── {content_id}.json.gz           # Compressed raw JSON objects
│
s3://sentimentai-{env}-processed/
├── embeddings/batch/{date}/
│   └── {batch_id}.parquet             # Embedding batch exports
│
s3://sentimentai-{env}-exports/
├── user-exports/{user_id}/
│   └── {ticker}_{date}.csv
│
s3://sentimentai-{env}-models/
├── bot-classifier/latest/             # Model artifacts
├── sentiment-custom/latest/
└── calibration/latest/
```

---

# API Design

## Base URL & Versioning

```
Production:  https://api.sentimentai.io/v1
Staging:     https://api.staging.sentimentai.io/v1
```

All endpoints return `application/json`. Versioning is URL-path based. Breaking changes require a new major version.

## Authentication

```
# API Key (for programmatic access)
Authorization: Bearer sk-sat-{user_id}_{random_64_char}

# JWT (for frontend sessions via Supabase)
Authorization: Bearer {supabase_jwt_token}
```

## Core Endpoints

### GET /tickers/{symbol}/scores
Returns all 7 sentiment scores for a ticker.

**Path Parameters:**
- `symbol` (string, required): Stock ticker symbol (e.g., `NVDA`)

**Query Parameters:**
- `window_hours` (int, optional): Lookback window. Options: 24, 72, 168, 720. Default: 24
- `include_ci` (bool, optional): Include confidence intervals. Default: true
- `include_drivers` (bool, optional): Include score driver explanations. Default: false

**Response:**
```json
{
  "ticker": "NVDA",
  "symbol": "NVDA",
  "company_name": "NVIDIA Corporation",
  "analysis_id": "018f5e3d-7a2b-7c3d-8e9f-0a1b2c3d4e5f",
  "window_hours": 24,
  "calculated_at": "2026-06-12T14:30:00Z",
  "data_coverage": {
    "items_collected": 18473,
    "items_analyzed": 14892,
    "items_excluded_bot": 2318,
    "sources_active": 9,
    "sources_configured": 10
  },
  "scores": {
    "retail_sentiment": {
      "score": 72.4,
      "direction": "bullish",
      "ci_lower": 68.1,
      "ci_upper": 76.7,
      "label": "Strongly Bullish"
    },
    "short_term_signal": {
      "score": 61.2,
      "direction": "bullish",
      "ci_lower": 56.8,
      "ci_upper": 65.6,
      "label": "Moderately Bullish"
    },
    "long_term_conviction": {
      "score": 68.7,
      "direction": "bullish",
      "ci_lower": 64.2,
      "ci_upper": 73.2,
      "label": "Strongly Bullish"
    },
    "narrative_strength": {
      "score": 55.1,
      "direction": "bullish",
      "ci_lower": 49.8,
      "ci_upper": 60.4,
      "label": "Moderately Bullish"
    },
    "social_momentum": {
      "score": 83.2,
      "direction": "bullish",
      "ci_lower": 79.1,
      "ci_upper": 87.3,
      "label": "Strong Bullish Momentum"
    },
    "confidence": {
      "score": 87.3,
      "label": "High Confidence"
    },
    "composite": {
      "score": 68.2,
      "direction": "bullish",
      "ci_lower": 63.4,
      "ci_upper": 73.0,
      "label": "Strongly Bullish"
    }
  },
  "top_narratives": [
    {
      "theme": "AI Data Center Demand",
      "sentiment": "bullish",
      "strength": 0.83,
      "momentum": "rising",
      "item_count": 4231
    }
  ],
  "alerts": [],
  "disclaimer": "These scores represent aggregated public sentiment data and are provided for informational purposes only. They do not constitute investment advice..."
}
```

**HTTP Status Codes:** 200 OK | 400 Bad Request | 401 Unauthorized | 404 Ticker Not Found | 429 Rate Limited | 500 Internal Error

---

### GET /tickers/{symbol}/narratives
Returns detected narrative clusters for a ticker.

### GET /tickers/{symbol}/history
Returns historical score time series.

**Query Parameters:**
- `score_type`: `riss|stss|ltcs|mnss|sms|cs|ocs`. Default: `ocs`
- `start_date`: ISO 8601 date
- `end_date`: ISO 8601 date
- `window_hours`: Lookback window for each historical score point

### GET /tickers/{symbol}/content
Returns top-ranked content items driving the score.

**Query Parameters:**
- `sentiment_filter`: `bullish|bearish|neutral|all`
- `source_filter`: comma-separated sources
- `min_quality`: 0.0–1.0 quality threshold
- `limit`: Max items to return (1–100)
- `offset`: Pagination offset

### GET /tickers/{symbol}/authors
Returns most influential authors for a ticker.

### GET /watchlist/scores
Bulk score retrieval for a list of tickers (Pro+ tier).

**Query Parameters:**
- `symbols`: comma-separated list (max 50 for Pro, 500 for Enterprise)
- `score_type`: which scores to include
- `window_hours`: lookback window

### POST /alerts
Create a new alert for score threshold or anomaly detection.

### WebSocket: /ws/tickers/{symbol}/live
Real-time score streaming. Sends updated score objects whenever a score recalculation occurs.

```json
// Subscription message (client → server)
{"action": "subscribe", "ticker": "NVDA", "score_types": ["ocs", "sms"]}

// Score update (server → client)
{
  "event": "score_update",
  "ticker": "NVDA",
  "score_type": "ocs",
  "score": 71.4,
  "delta": +3.2,
  "timestamp": "2026-06-12T14:35:00Z"
}
```

### POST /v1/analysis/trigger
Force a fresh analysis run for a ticker (Enterprise tier only, rate limited).

---

# Event-Driven Architecture

## Redis Queue Topology

### Cluster Configuration
- **Platform:** Render Managed Redis Queue (Managed Streaming for Apache Redis Queue)
- **Version:** Redis Queue 3.6
- **Brokers:** 3 brokers (m6i.2xlarge), Multi-AZ
- **Retention:** 7 days (raw queues), 30 days (processed queues)
- **Replication factor:** 3 (all queues)

### Topic Definitions

```yaml
queues:
  # Ingestion tier
  raw.content.twitter:
    partitions: 12
    retention: 7d
    cleanup: delete
    
  raw.content.reddit:
    partitions: 8
    retention: 7d
    
  raw.content.news:
    partitions: 6
    retention: 7d
    
  raw.content.all:               # Fanout aggregated queue
    partitions: 24
    retention: 7d

  # Processing tier
  processing.validated:
    partitions: 24
    retention: 3d
    
  processing.cleaned:
    partitions: 24
    retention: 3d
    
  processing.llm-analysis:
    partitions: 24
    retention: 3d
    
  processing.sentiment:
    partitions: 24
    retention: 3d
    
  processing.credibility:
    partitions: 24
    retention: 3d

  # Scoring tier
  scores.computed.ticker:        # Keyed by ticker symbol
    partitions: 48
    retention: 30d
    compaction: enabled          # Keep latest per ticker
    
  scores.alerts:                 # Alert events
    partitions: 12
    retention: 7d

  # Control tier
  control.analysis.requests:     # Trigger analysis jobs
    partitions: 12
    retention: 1d
    
  control.dead-letter:          # Failed messages for investigation
    partitions: 6
    retention: 30d
```

### Event Schema (Avro)

```json
{
  "namespace": "io.sentimentai.events",
  "type": "record",
  "name": "RawContentEvent",
  "fields": [
    {"name": "event_id", "type": "string"},
    {"name": "event_version", "type": "string"},
    {"name": "event_time", "type": "long", "logicalType": "timestamp-millis"},
    {"name": "source", "type": "string"},
    {"name": "ticker", "type": "string"},
    {"name": "content", "type": "RawContent"},
    {"name": "metadata", "type": {"type": "map", "values": "string"}}
  ]
}
```

### Consumer Groups

```
cg-validator          → raw.content.all → processing.validated
cg-cleaner            → processing.validated → processing.cleaned
cg-llm-analyzer       → processing.cleaned → processing.llm-analysis
cg-sentiment          → processing.cleaned → processing.sentiment
cg-credibility        → processing.sentiment → processing.credibility
cg-scorer             → processing.credibility → scores.computed.ticker
cg-alert-evaluator    → scores.computed.ticker → scores.alerts
cg-db-writer          → processing.credibility → PostgreSQL (batch writes)
cg-qdrant-writer      → processing.llm-analysis → Qdrant (embedding writes)
cg-notification       → scores.alerts → delivery (email/push/webhook)
```

---

# Real-Time Processing Pipeline

## Pipeline Flow with Latency Budget

```
Data Source Publication
        │
   [0–30s] Source API polling / webhook
        │
   Redis Queue: raw.content.{source}
        │
   [30–60s] Validation + Cleaning
        │
   Redis Queue: processing.cleaned
        │
   [60–180s] LLM Analysis (batched)
             FinBERT Inference (parallel)
        │
   Redis Queue: processing.llm-analysis
        │
   [30–60s] Credibility Assessment
        │
   Redis Queue: processing.credibility
        │
   [10–30s] Score Recalculation
        │
   Redis + PostgreSQL write
        │
   [< 500ms] WebSocket push to clients
        │
Total end-to-end target: < 5 minutes (Pro tier)
```

## Score Recalculation Strategy

**Trigger-based recalculation (Pro/Trader tier):**
- Any new credibility-assessed item consumed → incremental score update
- Incremental update: Add new item(s) to running weighted sum; no full recompute needed
- Full recompute: Every 15 minutes (for drift correction) and on demand

**Scheduled refresh (Starter/Free tier):**
- Full recalculation every 30 minutes for active tickers
- Active ticker definition: ≥ 1 user active session or alert configured

**Score versioning:**
Each score record carries a `score_version` field tracking the scoring engine version, enabling safe reruns with updated methodology.

---

# Backtesting Framework

## Design Philosophy

The backtesting framework serves dual purposes: **product validation** (proving signal quality to users) and **model improvement** (identifying calibration gaps).

> ⚠️ **Financial Regulation Note (Beginner-Friendly):** Backtested results must always be prominently disclosed as such, must include standard disclosures ("past performance does not guarantee future results"), and must not be presented as predictions of future returns. In many jurisdictions, publishing performance track records is regulated. Consult a securities attorney before publishing any backtested signal performance in marketing materials.

## Historical Data Collection

```python
# Backtest data pipeline
class BacktestDataCollector:
    """
    For each historical date T in backtest range:
    1. Pull ticker_scores at timestamp T (already stored)
    2. Pull actual price data from Alpaca/Polygon historical API
    3. Calculate returns over [T, T+1d], [T, T+5d], [T, T+21d]
    4. Store in backtest_results table
    """
    
    def calculate_forward_return(
        self, ticker: str, score_date: date, forward_days: int
    ) -> float:
        price_at_score = self.price_api.get_close(ticker, score_date)
        price_at_forward = self.price_api.get_close(ticker, score_date + timedelta(forward_days))
        return (price_at_forward - price_at_score) / price_at_score
```

## Signal Quality Metrics

### 1. Information Coefficient (IC)

The IC measures the rank correlation between predicted sentiment and actual returns:

$$IC = \text{Spearman Rank Correlation}(S_{\text{score}}, R_{\text{forward}})$$

**Target:** IC > 0.05 over 5-day forward returns (considered a useful signal in academic literature)

### 2. Hit Rate (Directional Accuracy)

$$\text{Hit Rate} = \frac{\text{Number of correct directional predictions}}{\text{Total predictions}}$$

**Calculation:**
- Score > +20 → bullish prediction; hit if forward return > 0
- Score < −20 → bearish prediction; hit if forward return < 0
- |Score| < 20 → neutral, excluded from hit rate calculation

**Target:** Hit rate > 54% (statistically significant above chance with p < 0.05)

### 3. Sharpe Ratio of Signal (Signal Sharpe)

Construct a hypothetical long/short portfolio based on score thresholds:

$$\text{Signal Sharpe} = \frac{E[R_{\text{signal}}] - R_f}{\sigma(R_{\text{signal}})}$$

**Target:** Signal Sharpe > 0.5 on 5-day forward windows

### 4. Information Ratio

$$IR = \frac{\text{IC}}{\sigma(\text{IC})} = \frac{\bar{IC}_{monthly}}{\sigma_{monthly}(IC)}$$

**Target:** IR > 0.3 (indicates stability of signal quality over time)

### 5. Correlation Analysis

Plot and calculate:
- Pearson correlation: S(t) vs. R(t+Δ) for Δ ∈ {1, 3, 5, 10, 21} days
- Granger causality test: Does sentiment at time t predict price at t+Δ, controlling for lagged price?
- Cross-autocorrelation function (CCF) plot

### Backtesting Dashboard Features

- Interactive IC chart over time (monthly rolling IC)
- Hit rate heatmap by stock sector and market cap decile
- Sentiment-to-return scatter plot with regression line and R²
- Best/worst prediction case studies (qualitative explanation)
- Score calibration plot (binned score vs. average realized return)
- Statistical significance tests (t-test on IC distribution)

---

# Monitoring & Observability

## Three Pillars

### 1. Metrics (Prometheus + Grafana)

**Pipeline metrics:**
```
sentimentai_items_ingested_total{source, ticker}
sentimentai_items_processed_total{stage}
sentimentai_items_failed_total{stage, error_type}
sentimentai_processing_latency_seconds{stage, quantile}
sentimentai_llm_latency_seconds{model, tier}
sentimentai_llm_tokens_used_total{model}
sentimentai_kafka_consumer_lag{consumer_group, queue, partition}
sentimentai_score_recalculation_latency_seconds{ticker}
```

**Business metrics:**
```
sentimentai_scores_computed_total{ticker, window_hours}
sentimentai_api_requests_total{endpoint, status_code}
sentimentai_api_latency_seconds{endpoint, quantile}
sentimentai_active_websocket_connections
sentimentai_alerts_triggered_total{alert_type}
sentimentai_bot_items_excluded_total
```

**Alerting rules:**
- Redis Queue consumer lag > 10,000 messages → PagerDuty P1
- LLM API error rate > 5% for 5 minutes → PagerDuty P2
- Score freshness > 15 minutes (Pro tier) → PagerDuty P2
- API p99 latency > 5 seconds → PagerDuty P3
- Database connection pool > 80% → PagerDuty P3

### 2. Tracing (OpenTelemetry → Jaeger)

Every analysis run gets a trace:
- Trace ID = analysis_id
- Spans: collect → validate → clean → llm_analyze → sentiment → credibility → score → aggregate → report
- Each span includes: ticker, item_count, latency, error flags
- LLM calls include: model, token_count, cost_estimate, cache_hit

### 3. Logging (Structured JSON → CloudWatch Logs → OpenSearch)

```json
{
  "timestamp": "2026-06-12T14:30:00.123Z",
  "level": "INFO",
  "service": "scoring-engine",
  "trace_id": "018f5e3d-...",
  "span_id": "7a2b...",
  "ticker": "NVDA",
  "analysis_id": "...",
  "stage": "quantitative_scoring",
  "items_processed": 14892,
  "score_ocs": 68.2,
  "duration_ms": 342,
  "message": "Scoring complete"
}
```

## Data Quality Monitoring

Automated checks run after each analysis cycle:
- **Coverage check:** If source coverage < 50% of expected, emit warning
- **Score drift check:** If OCS changes > 20 points between cycles without news catalyst, flag for review
- **Distribution check:** If > 80% of items from single source, flag source concentration
- **Bot cluster detection:** If bot exclusion rate > 30%, trigger fraud investigation alert

---

# Infrastructure Design

> This version has been adapted for a lean startup architecture using Render serverless-style services and managed cloud components instead of AWS-native infrastructure and Kubernetes operations.

## Cloud Provider Comparison

| Criterion | Render | GCP | Azure |
|-----------|-----|-----|-------|
| Redis Queue (Managed) | Managed Redis Queue ⭐⭐⭐ | PubSub (different paradigm) | Event Hubs |
| Render Worker Architecture | Render ⭐⭐⭐ | GKE ⭐⭐⭐ | AKS ⭐⭐ |
| ML/AI Services | SageMaker ⭐⭐ | Vertex AI ⭐⭐⭐ | Azure ML ⭐⭐ |
| Managed PostgreSQL | RDS/Aurora ⭐⭐⭐ | Cloud SQL ⭐⭐ | Azure DB ⭐⭐ |
| Vector DB Support | External | External | External |
| Global CDN | CloudFront ⭐⭐⭐ | Cloud CDN ⭐⭐⭐ | Azure CDN ⭐⭐ |
| Developer Ecosystem | Largest ⭐⭐⭐ | Very large ⭐⭐⭐ | Enterprise focus ⭐⭐ |
| Cost at Seed scale | Moderate | Moderate | Moderate |
| Startup Credits | $5K–100K | $200K+ | $120K+ |

### Recommendation: **Render (Primary)**

**Rationale:**
- Largest ecosystem and talent pool - easier hiring
- Managed Redis Queue (Managed Redis Queue) is best-in-class managed Redis Queue
- Aurora PostgreSQL Serverless v2 perfect for variable load at seed stage
- GitHub Actions → Container Registry → Render → Render Deployments: industry-standard MLOps pipeline
- GCP secondary consideration for Phase 3+ ML training workloads (Vertex AI)

## Render Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Render Production Architecture                  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    VPC (us-east-1)                        │   │
│  │                                                           │   │
│  │   Public Subnets (3 AZs)                                 │   │
│  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │   │
│  │   │  ALB (API)  │  │  ALB (WS)   │  │  NAT GW     │    │   │
│  │   └──────┬──────┘  └──────┬──────┘  └─────────────┘    │   │
│  │          │                 │                              │   │
│  │   Private Subnets (3 AZs)                                │   │
│  │   ┌────────────────────────────────────────────────┐    │   │
│  │   │              Render Cluster                        │    │   │
│  │   │   ┌──────────┐  ┌──────────┐  ┌──────────┐   │    │   │
│  │   │   │ FastAPI  │  │ Scoring  │  │ Agents   │   │    │   │
│  │   │   │ Pods (8) │  │ Pods (4) │  │ Pods(16) │   │    │   │
│  │   │   └──────────┘  └──────────┘  └──────────┘   │    │   │
│  │   │   ┌──────────┐  ┌──────────┐  ┌──────────┐   │    │   │
│  │   │   │ Ingestor │  │ Qdrant   │  │ Workers  │   │    │   │
│  │   │   │ Pods (8) │  │ (StatefulSet│ │ Pods(12) │   │    │   │
│  │   │   └──────────┘  └──────────┘  └──────────┘   │    │   │
│  │   └────────────────────────────────────────────────┘    │   │
│  │                                                           │   │
│  │   Data Tier (Isolated Subnets)                           │   │
│  │   ┌─────────────┐  ┌─────────────┐  ┌───────────────┐  │   │
│  │   │Aurora PG    │  │ Managed Redis Queue Redis Queue   │  │ ElastiCache   │  │   │
│  │   │ Multi-AZ    │  │ 3-broker    │  │ Redis Cluster │  │   │
│  │   └─────────────┘  └─────────────┘  └───────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Global Services:                                                │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐  ┌────────────────┐  │
│  │CloudFront│  │Route 53 │  │   S3     │  │  CloudWatch    │  │
│  │  (CDN)  │  │  (DNS)  │  │ Storage  │  │  + Grafana     │  │
│  └─────────┘  └─────────┘  └──────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Render Worker Architecture Node Groups

| Node Group | Instance Type | Count (Phase 1) | Count (Phase 3) | Purpose |
|-----------|--------------|----------------|----------------|---------|
| api-nodes | c6i.2xlarge | 3–6 | 8–20 | FastAPI service instances |
| agent-nodes | c6i.4xlarge | 4–8 | 12–30 | LangGraph agents |
| scoring-nodes | c6i.2xlarge | 2–4 | 6–12 | Scoring engine |
| gpu-nodes | g5.2xlarge | 0–2 | 2–6 | FinBERT inference |
| qdrant-nodes | r6i.4xlarge | 3 | 6 | Vector database |
| worker-nodes | c6i.2xlarge | 4–8 | 10–20 | Redis Queue consumers |

## Autoscaling Strategy

- **HPA (Horizontal Pod Autoscaler):** Scale API service instances on CPU > 60% and queue depth metrics from KEDA
- **KEDA (Render Worker Architecture Event-Driven Autoscaling):** Scale agent/worker service instances based on Redis Queue consumer lag
- **Cluster Autoscaler:** Add/remove EC2 instances based on service instance pending state
- **Spot Instances:** Use for agent and worker node groups (70% cost reduction; tolerate interruptions via checkpoint)

---

# Security Considerations

## Authentication & Authorization

```python
# API key format: sk-sat-{user_id_prefix}_{random_64_chars}
# Stored: bcrypt hash of key
# Rate limiting: Redis sliding window per key

# JWT: RS256 signed, 1-hour expiry, refresh token (7 days)
# Scopes: read:scores, read:history, write:alerts, admin

# RBAC tiers:
# free → read:scores (3 tickers, delayed)
# pro → read:scores (unlimited), read:history, write:alerts  
# trader → pro + api:access + webhook:write
# enterprise → trader + admin:bulk + api:unlimited
```

## Data Security

- **Encryption in transit:** TLS 1.3 everywhere (API, internal service mesh via Istio)
- **Encryption at rest:** Render KMS-managed keys; S3 SSE-KMS; RDS encryption enabled
- **Secrets management:** Render Secrets Manager for API keys, database credentials; no secrets in code or environment variables
- **Network:** All inter-service communication within VPC; no public service exposure except ALB
- **WAF:** Render WAF on ALBs; rules for: SQLi, XSS, rate limiting by IP, known bad actors

## Privacy

- **No PII storage:** User accounts store email + hashed password only; no financial data
- **Content data:** Social media posts are public; no attempt to de-anonymize users
- **Author profiles:** Aggregated behavioral data only; no storage of private communications
- **GDPR compliance:** User account deletion cascades to all user-specific data within 30 days

## Threat Model

| Threat | Likelihood | Impact | Mitigation |
|--------|-----------|--------|-----------|
| API key theft | Medium | High | Key rotation, anomaly detection |
| Prompt injection via content | Medium | Medium | Input sanitization, sandboxed LLM calls |
| Data source IP ban | High | High | Residential proxy rotation, multiple accounts |
| Competitor scraping our scores | Medium | Low | API rate limiting, CAPTCHA on frontend |
| LLM hallucination in reports | High | Medium | Confidence scoring, human review for alerts |
| Redis Queue queue poisoning | Low | High | Schema registry + Avro validation |
| Database injection | Low | Critical | Parameterized queries, RLS in PostgreSQL |

---

# Regulatory & Compliance Considerations

> ⚠️ **Critical Section - Consult Legal Counsel Before Launch**

## US Securities Regulations

**Investment Advisers Act of 1940:**
- Platforms providing "investment advice" for compensation must register as Investment Advisers (IA) with the SEC
- **Mitigation:** Sentinel signals are framed as "informational sentiment scores," never as investment advice, buy/sell recommendations, or price predictions. All outputs include mandated disclaimers.
- A no-action letter or legal opinion from securities counsel is strongly recommended before launch

**Regulation FD (Fair Disclosure):**
- Ensures no selective disclosure of material non-public information
- **Mitigation:** Platform uses only publicly available information; no insider data ingested

**Market Manipulation (Section 9, 10(b) of Securities Exchange Act):**
- Artificially influencing stock prices is illegal
- **Mitigation:** Platform displays information; makes no recommendations; clear disclaimers; report suspected manipulation to FINRA

## Data Licensing

> ⚠️ **This is a Day-1 budget and legal requirement, not an afterthought.**

| Source | Commercial License Required | Estimated Cost |
|--------|---------------------------|---------------|
| X/Twitter API | Yes (Basic/Pro tier) | $100–$5,000/mo |
| Reddit Data API | Yes | $0.24/1K requests |
| Seeking Alpha | Yes (commercial license) | $200–$2,000/mo |
| Reuters | Yes (commercial news feed) | $500–$5,000/mo |
| StockTwits | Yes (commercial tier) | $200–$1,000/mo |
| Yahoo Finance | Unofficial - avoid for commercial | Risk |
| Bloomberg | Yes (B-PIPE) | $2,000–$10,000/mo |
| AlphaVantage (price data) | Freemium | $50–$500/mo |

**Total estimated data licensing cost at MVP:** $2,000–$8,000/month

## Copyright & Fair Use

- Social media posts: Copyright owned by authors; commercial aggregation for analysis may qualify as transformative use, but this is legally untested territory
- News articles: Reproduction is illegal; extraction of sentiment/queues from licensed feeds is generally permissible
- Recommendation: Display only metadata and snippets (< 150 characters) with source attribution; never reproduce full articles

## GDPR / International Data Regulations

- EU users' public social media content is processed; no PII stored beyond user accounts
- Privacy policy must disclose data sources and processing methodology
- Data Processing Agreement (DPA) required with all sub-processors (Render, OpenAI, etc.)
- OpenAI's API: Ensure enterprise data processing agreement that disables training on your data

---

# Cost Analysis

## Monthly Infrastructure Cost (Render)

### Phase 1 - MVP (Months 1–6)

| Component | Spec | Monthly Cost |
|-----------|------|-------------|
| Render Cluster | 10 nodes (mixed types) | $2,100 |
| Aurora PostgreSQL | db.r6g.large, Multi-AZ | $480 |
| Managed Redis Queue Redis Queue | kafka.m5.large, 3 brokers | $520 |
| ElastiCache Redis | cache.r6g.large, 2 nodes | $280 |
| Qdrant (self-hosted on EC2) | r6i.2xlarge × 3 | $720 |
| S3 Storage | 5TB | $115 |
| ALB + Data Transfer | - | $300 |
| CloudWatch, Route53, misc | - | $200 |
| **Infrastructure Subtotal** | | **$4,715/mo** |

| LLM Costs | Volume | Monthly Cost |
|-----------|--------|-------------|
| OpenAI Embedding | 5M items/mo × 3072d | $1,500 |
| Claude Haiku (Tier 2) | 1M calls × avg 500 tokens | $375 |
| Claude Sonnet (Tier 3) | 150K calls × avg 2K tokens | $1,800 |
| **LLM Subtotal** | | **$3,675/mo** |

| Data Licensing | | Monthly Cost |
|---------------|---|-------------|
| X/Twitter API | Basic | $100 |
| Reddit API | ~1M calls | $240 |
| StockTwits | Basic commercial | $200 |
| AlphaVantage | Premium | $200 |
| News RSS + SerpAPI | - | $150 |
| **Data Subtotal** | | **$890/mo** |

**Total Phase 1 Monthly Cost: ~$9,280/month**

**Gross Margin at 500 Pro subscribers ($39/mo) = $19,500 revenue → GM = 52.5%**

### Phase 3 - Growth (Month 18+, 5,000 subscribers)

| Component | Monthly Cost |
|-----------|-------------|
| Infrastructure (scaled Render) | $18,000 |
| LLM costs (optimized with self-hosted) | $12,000 |
| Data licensing (expanded) | $6,000 |
| Observability (Grafana, Datadog) | $2,000 |
| **Total** | **$38,000/mo** |

**Revenue at 5,000 Pro + 500 Trader subscribers:**
- Pro: 5,000 × $39 = $195,000
- Trader: 500 × $99 = $49,500
- API: 50 Enterprise × $799 = $39,950
- **Total MRR: $284,450**
- **Gross Margin: ~87% (after COGS of $38K)**

## LLM Cost Optimization Roadmap

| Phase | Strategy | LLM Cost per 1M items |
|-------|---------|----------------------|
| 1 | API-only (Claude + OpenAI) | $120–$150 |
| 2 | Aggressive caching + tier routing | $80–$100 |
| 3 | Self-hosted Llama/Mistral for bulk | $25–$40 |
| 4 | Fine-tuned domain-specific model | $10–$20 |

---

# Technology Recommendations

## Final Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Agent Orchestration** | LangGraph (primary) | Best state machine control for complex agent workflows |
| **Sub-task Crews** | CrewAI | Best for specialized multi-agent research tasks |
| **Backend API** | FastAPI + Python 3.12 | Async, performant, excellent ML ecosystem |
| **Frontend** | Next.js 15 + TypeScript | Best React framework for production SaaS |
| **Vector DB** | Qdrant | Best performance/cost; excellent metadata filtering |
| **Relational DB** | Aurora PostgreSQL + TimescaleDB | Scale + time-series optimization |
| **Cache** | ElastiCache Redis | Industry standard; LangGraph checkpointing support |
| **Queue System** | Managed Redis Queue (Redis Queue) | Best durability; LangChain-compatible |
| **Primary LLM** | Claude claude-sonnet-4-6 | Best quality/cost for long-form analysis |
| **Bulk LLM** | Claude Haiku + FinBERT | Cost optimization for high-volume processing |
| **Embeddings** | OpenAI text-embedding-3-large | Best quality; 3072d; strong financial domain performance |
| **Cloud** | Render | Ecosystem, talent, managed services |
| **Containers** | Render (Render Worker Architecture) | Standard; portability; KEDA for event-driven scaling |
| **Auth** | Supabase | Best managed auth; PostgreSQL native |
| **Monitoring** | Prometheus + Grafana + OTel | Industry standard observability stack |
| **CI/CD** | GitHub Actions + Render Deployments | Best GitOps pipeline |
| **IaC** | Terraform + Helm | Reproducible infrastructure |

---

# MVP Design

## MVP Scope (Phase 1, Months 1–6)

The MVP focuses on **validating the core value proposition** (sentiment scores that retail investors find useful) with the **minimum infrastructure required** to handle real traffic reliably.

### MVP Features (In Scope)
- Top 100 US stocks by market cap (S&P 100)
- 5 data sources: Twitter/X, Reddit, StockTwits, Google News RSS, Yahoo Finance discussions
- 3 scores: RISS, SMS, OCS (simplified; STSS, LTCS, MNSS in Phase 2)
- 24-hour lookback window only
- Simple web dashboard: score display, directional trend, top 5 influencing posts
- Email alerts for OCS threshold crossings
- Starter tier (free) + Pro tier ($39/month)
- REST API (rate-limited) for Pro subscribers
- Score refresh every 15 minutes (no real-time WebSocket in MVP)

### MVP Architecture (Simplified)

```
5 Data Collectors (async Python) →  
   [Redis Queue: raw.content] →  
   [Single processing service: validate + clean + FinBERT sentiment] →  
   [PostgreSQL: enriched items] →  
   [Scoring Engine: RISS + SMS + OCS] →  
   [Redis: score cache] →  
   [FastAPI: REST endpoints] →  
   [Next.js dashboard]
```

**No LangGraph in MVP:** Simpler sequential pipeline for faster time-to-market. LangGraph introduced in Phase 2.

### MVP Engineering Headcount

| Role | Count |
|------|-------|
| Backend Engineer (Python) | 2 |
| ML Engineer | 1 |
| Frontend Engineer (Next.js) | 1 |
| DevOps/Platform Engineer | 1 |
| Product Manager | 1 |
| **Total** | **6 FTEs** |

### MVP Success Criteria (Phase 1 Gate)
- 200+ paying Pro subscribers by Month 6
- NPS > 30 from at least 50 survey responses
- System processes > 50,000 content items/day reliably
- Backtesting shows RISS IC > 0.03 over 5-day window (minimum threshold for signal existence)
- Zero critical security incidents

---

# Phase 1 Implementation Plan - Foundation & MVP
**Timeline: Months 1–6 | Budget: ~$600K**

## Objectives
Build and validate the core data pipeline, scoring engine, and consumer-facing product.

## Month 1–2: Infrastructure & Data Layer

**Week 1–2:**
- Render account setup, VPC, IAM policies, Terraform base modules
- GitHub organization, branching strategy, CI/CD skeleton (GitHub Actions)
- Render cluster (minimal): 3 nodes, Redis Queue (single broker dev), PostgreSQL RDS

**Week 3–4:**
- Implement RawContent data model + schema registry (Avro)
- Twitter/X collector (async, rate-limited)
- Reddit collector (PRAW-based)
- StockTwits collector
- Deduplication + fingerprinting

**Week 5–6:**
- Validation agent (Pydantic schemas)
- Content cleaning pipeline
- FinBERT deployment (managed GPU providers (Modal, Runservice instance, Together, etc.) endpoint)
- Basic sentiment scoring (RISS only)

**Week 7–8:**
- PostgreSQL schema finalized and migrated (Alembic)
- Redis cache integration
- Score calculation engine (RISS + SMS + OCS v0.1)
- Internal testing with live data: 10 tickers

## Month 3–4: API & Frontend

**Week 9–10:**
- FastAPI REST API: /scores, /history, /content endpoints
- Supabase Auth integration (sign-up, API key generation)
- Rate limiting middleware (Redis-backed)

**Week 11–12:**
- Next.js frontend scaffolding
- Score dashboard (score display, direction indicator, source breakdown)
- Historical score chart (90-day sparkline)
- Top influencing posts display

**Week 13–14:**
- Pro tier gating (Stripe integration)
- Email alert system (Render SES)
- Expand to 100 tickers

**Week 15–16:**
- Beta launch to waitlist (target: 100 beta users)
- Bug fixes, performance optimization
- Monitoring setup (Grafana dashboards, PagerDuty alerts)

## Month 5–6: Launch & Validate

**Week 17–18:**
- Public launch (Product Hunt, tech communities, fintech Twitter)
- User onboarding flow
- First NPS survey
- Backtesting infrastructure: pull 6 months historical data, calculate initial IC

**Week 19–20:**
- Respond to user feedback
- Score calibration based on first backtest results
- Google News RSS + Yahoo Finance collector (sources 4–5)

**Week 21–24:**
- Iterate on dashboard based on user behavior data
- Add 2 more sources: Substack RSS, StockTwits expanded
- Phase 1 completion assessment vs. success criteria

## Deliverables
- ✅ 5 operational data collectors
- ✅ RISS, SMS, OCS scores for 100 tickers
- ✅ Web dashboard + REST API
- ✅ Pro tier with Stripe billing
- ✅ 200+ paying subscribers
- ✅ First backtesting report

## Team Requirements
6 FTEs: 2 Backend, 1 ML, 1 Frontend, 1 DevOps, 1 PM

## Risks
- X/Twitter API policy changes → Mitigation: build Reddit/StockTwits as primary sources; X as bonus
- LLM API costs exceed budget → Mitigation: FinBERT-first routing cap; cost alerting at $500/day
- Regulatory challenge on "investment advice" framing → Mitigation: legal review in Month 1

## Dependencies
- X/Twitter Developer Agreement approved
- Reddit API commercial access granted
- Securities attorney review completed
- OpenAI/Anthropic enterprise agreements signed

---

# Phase 2 Implementation Plan - Advanced Sentiment Intelligence
**Timeline: Months 7–12 | Budget: ~$800K**

## Objectives
Introduce LangGraph multi-agent pipeline, expand scores to all 7, add narrative intelligence, near-real-time updates.

## Key Deliverables

**Month 7–8: LangGraph Migration**
- Refactor processing pipeline to LangGraph StateGraph
- Implement all 10 agents (Agents 1–10 as specified)
- Redis-based checkpointing for pipeline durability
- Parallel processing: FinBERT + LLM in parallel (reduce latency 40%)

**Month 8–9: Full Scoring Suite**
- Implement STSS and LTCS (time-decay variants)
- Implement MNSS (narrative clustering with Qdrant/HDBSCAN)
- Implement full Confidence Score
- OCS v2.0 with dynamic weighting
- 95% confidence intervals via bootstrap

**Month 9–10: Narrative Intelligence**
- Qdrant collection: `narrative_fingerprints`
- HDBSCAN narrative clustering pipeline
- LLM narrative labeling and summarization
- Narrative momentum tracking
- Emerging narrative detection (< 2-hour lag)
- Dashboard: narrative timeline and theme viewer

**Month 10–11: Real-Time Layer**
- WebSocket server (Socket.IO on FastAPI)
- Near-real-time score updates (< 5 min latency, Pro tier)
- Push notifications (Firebase Cloud Messaging for mobile)
- Webhook delivery system for Enterprise

**Month 11–12: Expansion & Credibility**
- Author credibility database (full implementation)
- Bot detection XGBoost model (trained on labeled dataset)
- Misinformation flagging (LLM-based fact-check)
- Expand to All US equities (5,000+ tickers; only active tickers scored)
- 3 additional sources: Seeking Alpha, Reuters feed, financial Substack newsletters

## Phase 2 Gate Criteria
- All 7 scores live and documented
- Score refresh latency < 5 min (Pro tier)
- NPS > 40
- 2,000+ paying subscribers
- Backtesting IC > 0.04 (STSS, 5-day)

## Team Delta (Phase 2 additions)
- +1 Senior ML Engineer (narrative clustering, bot detection)
- +1 Backend Engineer (WebSocket, webhook infrastructure)
- +1 Data Engineer (pipeline optimization, Redis Queue tuning)

---

# Phase 3 Implementation Plan - Multi-Agent Automation
**Timeline: Months 13–18 | Budget: ~$1.2M**

## Objectives
Full multi-agent automation with CrewAI crews, cross-ticker intelligence, mobile app, and Enterprise API launch.

## Key Deliverables

**Month 13–14: CrewAI Integration**
- Sector analysis crews (compare ticker against sector peers)
- Competitive intelligence crew (identify sector narrative shifts)
- Earnings intelligence crew (pre/post earnings sentiment tracking)
- Integration with LangGraph as sub-workflow nodes

**Month 15–16: Cross-Ticker Intelligence**
- Sector sentiment dashboard (e.g., "Semiconductor Sector Sentiment")
- Correlation detection: which stocks move together in social discourse
- Macro narrative detection (Fed, inflation, rates sentiment)
- Competitor sentiment comparison UI

**Month 16–17: Mobile App**
- React Native app (iOS + Android)
- Push notifications for alerts
- Score widgets for iOS home screen
- Watchlist management with Swipe-to-compare

**Month 17–18: Enterprise Layer**
- Enterprise API portal with self-service onboarding
- Webhook management UI
- Bulk API endpoints (500 tickers at once)
- White-label configuration system
- Enterprise SLA (99.9% uptime commitment)
- First enterprise pilot customers (target: 5 accounts)

## Phase 3 Gate Criteria
- 5,000+ Pro/Trader subscribers
- 5 Enterprise accounts signed
- Mobile app 4+ App Store rating
- $500K+ MRR
- Series A metrics met (if fundraising)

---

# Phase 4 Implementation Plan - Advanced Quantitative Scoring
**Timeline: Months 19–24 | Budget: ~$1.5M**

## Objectives
Fine-tuned models, calibrated scoring, options sentiment, advanced quantitative features.

## Key Deliverables

- **Fine-tuned sentiment model:** Train domain-specific RoBERTa/Llama on financial social media corpus (10M+ labeled examples from backtesting feedback loop). Target: 5% accuracy improvement over FinBERT baseline.
- **Options sentiment detection:** Parse and score mentions of options activity (calls/puts, unusual options activity, IV discussion)
- **Earnings prediction score:** Composite score 30 days before earnings using LTCS + narrative trends
- **Author prediction accuracy tracking:** Close-loop system matching past author predictions to price outcomes; update `prediction_accuracy` field
- **Multi-language support:** Spanish, Portuguese, French language processing (expand TAM to LatAm, Europe)
- **Institutional flow detection:** Detect institutional-style language in content (differentiates retail vs. professional discourse)
- **Portfolio-level sentiment:** Aggregate scores across a portfolio; weighted by position size

---

# Phase 5 Implementation Plan - Backtesting & Validation
**Timeline: Months 25–30 | Budget: ~$1.0M**

## Objectives
Public signal performance disclosure, third-party validation, research publication.

## Key Deliverables

- **Historical backtest database:** 2+ years of historical scores for S&P 500 matched against daily returns
- **Signal Performance Dashboard:** Public-facing IC charts, hit rate displays, monthly signal report card
- **Third-party audit:** Commission independent quant research firm to validate signal methodology and backtest results
- **Academic paper:** Submit research paper on social sentiment signal predictability to SSRN/Journal of Finance
- **Signal alerts for institutional users:** Implement FINRA-compliant disclosure framework for publishing signal statistics
- **Calibration engine v2:** Fully automated monthly recalibration using realized-return feedback

---

# Phase 6 Implementation Plan - Production Scaling
**Timeline: Months 31–36 | Budget: ~$2.0M**

## Objectives
Global scale, international expansion, platform ecosystem, strategic partnerships.

## Key Deliverables

- **Global multi-region deployment:** US (us-east-1) + EU (eu-west-1) + APAC (ap-southeast-1)
- **International equities:** LSE, TSX, ASX, NSE/BSE (India), Nikkei
- **Platform API ecosystem:** Developer marketplace; third-party integrations (brokerage apps, portfolio trackers)
- **99.95% SLA infrastructure:** Active-active multi-region; <30-second failover
- **Data partnership program:** Revenue-share API distribution through brokerage platforms
- **ML platform:** Internal MLOps platform for model versioning, A/B testing, automated retraining
- **Compliance expansion:** SOC 2 Type II certification; FCA registration (UK); MAS licensing (Singapore)

---

# Risks and Mitigations

| Risk | Category | Likelihood | Impact | Mitigation |
|------|----------|-----------|--------|-----------|
| X/Twitter API ban or cost spike | Data | High | High | Multi-source redundancy; Reddit/StockTwits as primary; negotiate directly with X |
| LLM API cost exceeds budget | Technical | Medium | High | Tier routing; self-hosted models in Phase 3; monthly cost cap alerts |
| Score quality insufficient for PMF | Product | Medium | Critical | Rigorous backtesting before launch; user feedback loop; IC threshold gate |
| Regulatory action ("investment advice") | Legal | Medium | Critical | Legal review Day 1; disclaimers everywhere; no directional recommendations |
| Data licensing dispute | Legal | Medium | High | Formal agreements signed before commercial launch; budget line item |
| Bot/manipulation detection bypass | Technical | Medium | Medium | Continuous model update; ensemble approach; red team exercises |
| LLM hallucination in public reports | Technical | High | Medium | Confidence gating; human review for alerts; factual claim citation system |
| Competitor (Bloomberg, Refinitiv) enters | Market | Low | High | Move fast on retail brand; data moat (historical database); niche focus |
| Redis Queue/infrastructure outage | Technical | Low | High | Multi-AZ; DLQ; automatic recovery; RTO < 1 hour tested quarterly |
| Talent acquisition challenges | Operational | Medium | Medium | Competitive equity grants; remote-first; clear technical career path |
| Security breach / API key leak | Security | Low | Critical | Regular pen tests; automatic key rotation; anomaly detection; SOC 2 roadmap |
| OpenAI/Anthropic model deprecation | Technical | Medium | Medium | Multi-model architecture; no single-model dependency; abstraction layer |

---

# Future Enhancements

## Post-Phase 6 Roadmap

### Year 3–4 Vision

**Predictive Analytics Layer**
- Integrate fundamental data (earnings, insider trading, short interest) with sentiment signals
- Composite "investment grade" scores combining sentiment + fundamentals
- Temporal pattern recognition: "What happened the last 3 times NVDA had this sentiment profile before earnings?"

**Social Graph Analysis**
- Map influence networks: who follows whom among high-credibility accounts
- Information propagation modeling: detect signal origination and spread
- Identify "smart money" retail accounts with above-average prediction history

**AI Research Assistant**
- Natural language queries: "Why is TSLA sentiment negative this week?"
- Conversational interface over the entire indexed content corpus
- Auto-generated research briefs combining sentiment + news + price action

**Community Features**
- Verified analyst leaderboard (track-record based, not self-reported)
- Community-annotated narratives
- User prediction markets (gamified, non-financial)

**Institutional Product**
- Factor model: Package sentiment as a quantitative factor for institutional use
- Risk monitoring: High-velocity negative sentiment as a portfolio risk indicator
- ESG sentiment: Track environmental and governance sentiment separately

**Platform Integrations**
- Broker integrations: Score overlays in TD Ameritrade/Webull/Robinhood
- TradingView indicator: Publish SentimentAI indicators as TradingView Pine Script
- Bloomberg B-PIPE: Distribute scores via Bloomberg data terminal

---

# Final Build Recommendation

## What to Build First

**Months 1–3: Build the data moat, not the product.**

The most defensible long-term asset in SentimentAI is not the frontend or the scoring algorithm - it is the **accumulated historical database** of scored content items matched against price outcomes. Start collecting and storing data on Day 1, even before the product is usable, because every day of historical data has compounding value for backtesting and calibration that can never be recovered retroactively.

**Specific Recommendation:**
1. Stand up the Redis Queue pipeline and 3 primary collectors (Twitter, Reddit, StockTwits) in Week 1
2. Store everything in S3 (raw) and PostgreSQL (metadata) from Day 1
3. Run FinBERT-based scoring from Week 3 (even without LangGraph)
4. Build the front-end after you have 30 days of real data to validate

## Architecture Philosophy

**Start simple, build for replacement, not for scale.**

The MVP architecture intentionally avoids LangGraph, CrewAI, and multi-model ensembles. This is deliberate: simpler systems fail in simpler, more debuggable ways. Add complexity only when a specific need arises:
- LangGraph → when agent failures need stateful recovery (Phase 2)
- CrewAI → when multi-agent research workflows exceed single-agent scope (Phase 3)
- Self-hosted LLMs → when LLM cost exceeds 20% of COGS (Phase 3)

**Use interfaces, not implementations.** Abstract the vector database, LLM, and embedding model behind Python protocol classes from Day 1. This makes the Phase 3 migrations (Qdrant → Pinecone, Claude → Llama) a configuration change, not a rewrite.

## Hiring Sequence

1. **First hire:** Senior ML Engineer with NLP background and production experience. This person owns the scoring engine and model quality - the core product.
2. **Second hire:** Senior Backend Engineer with distributed systems and Redis Queue experience. This person owns the pipeline reliability.
3. **Third hire:** Full-stack Engineer with TypeScript/Next.js and some backend capability. This person ships the product users actually see.
4. **Fourth hire:** Data Engineer. The data moat is everything; this person ensures the pipeline never loses data.
5. **Fifth hire:** DevOps/SRE. Reliability at scale; bring on before launch, not after the first outage.

## Critical Success Factors

| Factor | Why Critical | How to Achieve |
|--------|-------------|---------------|
| Signal quality | Users won't pay for noise | Rigorous backtesting before launch; IC > 0.05 gate |
| Data source reliability | No signal without data | Diversify sources; never depend on single API; budget for licensing |
| Explainability | Users need to understand, not just consume | Every score change has a natural language explanation |
| Trust through transparency | Fintech trust is earned, not bought | Publish methodology; open backtesting dashboard; academic validation |
| Speed to Pro | Free users cost money | Aggressive conversion funnel; clear value demo within 5 minutes of signup |

## The Single Most Important Metric

**Track the IC (Information Coefficient) monthly, publicly.**

If the signal has predictive power, the IC will show it. Publish it on the website. This is the most differentiated trust signal in the market: no competitor publishes validated signal performance for retail investors. If IC is positive and improving, marketing writes itself. If IC is declining, you know which model component to fix before users churn.

A platform with a validated IC of 0.08 over 5-day windows is a **fundamentally different product** than one with an IC of 0.02 - and users sophisticated enough to care about data quality (your Pro/Trader buyers) will recognize this immediately.

## Summary Investment Thesis

SentimentAI is built on three compounding advantages:

1. **Data flywheel:** Every processed item makes the author credibility database more accurate, which improves scoring, which generates better product outcomes, which attracts more users, which justifies more data investment.

2. **Backtested trust:** In a market saturated with unvalidated "AI signals," a platform that publicly publishes IC, hit rate, and signal Sharpe - and continuously improves them - builds a trust moat that price cannot erode.

3. **Distribution via API:** The Enterprise/API business model makes every fintech app that embeds SentimentAI a distribution channel. At scale, the embedded API business generates higher-margin revenue than direct consumer subscriptions while requiring no incremental marketing spend.

The market is large, the problem is real, the technical path is clear, and the timing - with LLMs making agent architectures economically viable for the first time - is exactly right.

---

## Document End

**Prepared by:** Principal AI Architect | Quantitative Research Team  
**Version:** 2.0.0 | June 2026  
**Next Review:** Phase 1 Completion Assessment (Month 6)

---

*All financial projections, cost estimates, and technical performance targets in this document are forward-looking estimates based on current market conditions and technology capabilities. They are subject to change based on execution, market conditions, and regulatory developments. This document does not constitute a prospectus or offering document.*
