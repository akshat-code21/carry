# Carry - Product Deep Dive (PM Perspective)

> Companion to `carry_high_level_summary.md` (what the product is) and `carry_deep_dive.md` (how it's built). This document looks at Carry the way a product manager would: who it serves, what jobs it does, where the experience shines, where it's thin, and what to build next.
>
> No code required to read this - every technical concept is translated into product terms. (An internal-term glossary is at the end.)

---

## 1. TL;DR

Carry answers three questions no existing consumer tool answers well:

1. **"What is the market actually saying about X right now?"** - with receipts (who said it, when, down to the second).
2. **"Who should I actually listen to?"** - because every public prediction is graded against what the market later did.
3. **"What are the smartest investors I follow doing?"** - tracked continuously, summarized automatically.

The product's wedge is **accountability**: commentary without a track record is noise, and Carry is the only place where the noise becomes a measurable, searchable, citable signal. It is live in invite-only beta across YouTube commentary, social sentiment (Reddit/X/StockTwits/news), and smart-money tracking.

## 2. Who It Serves & The Jobs They Hire It For

### Persona 1 - The Self-Directed Retail Investor
**Profile:** Holds a personal portfolio, consumes finfluencer content daily, has no Bloomberg terminal.
**Jobs to be done:**
- *"When I hear a bullish take on NVDA, tell me who else said it, when, and whether calls like that have worked out."*
- *"Alert me to what the market narrative is this week without me watching 40 videos."*
**Why they'd stay:** Carry converts hours of passive video-watching into minutes of verified reading.

### Persona 2 - The Equity Research / Buy-Side Analyst
**Profile:** Needs primary-source evidence and audit trails; professionally accountable for calls.
**Jobs to be done:**
- *"I need to cite exactly what CNBC or Meet Kevin said on March 3 about rate cuts - timestamped."*
- *"Rank the commentators my sector actually moves on - separate signal from audience size."*
**Why they'd pay:** Source-of-truth search with citation + a searchable prediction ledger is analyst-grade tooling at consumer price.

### Persona 3 - The Finance Content Professional
**Profile:** Newsletter writers, media teams, creator-economy operators.
**Jobs to be done:**
- *"What themes are emerging before they're obvious?"* (narrative maps)
- *"Which voices are gaining accuracy and traction in my beat?"*
**Why they'd stay:** Themes and channel analytics are content-strategy gold.

**Observation from the current build:** the experience is strongest for Personas 1–2. Persona 3 tooling exists implicitly (themes, channels) but isn't yet packaged as a workflow.

## 3. Product Principles (visible in the build)

1. **Provenance or it didn't happen.** Every AI-generated claim carries channel attribution and a clip citation. This is the anti-hallucination stance that makes the product *trustable* rather than just *impressive* - and it's enforced at the model-prompt level, not bolted on in the UI.
2. **Grade the call, not the confidence.** Predictions are scored against realized 1-day/1-week/1-month price moves. Confidence is displayed but never substituted for outcomes.
3. **Transparent scores.** Sentiment scores are formulas over disclosed inputs (model + engagement weighting), not black-box vendor feeds - a trust feature and a marketing asset.
4. **Fresh beats comprehensive.** Near-real-time ingestion (push-based, zero marginal quota cost) is prioritized over exhaustive archive backfill.
5. **Cheap to run, priced to scale.** Architecture choices (nano-tier LLMs, local models, free data sources) keep unit costs near zero - an intentional product decision that keeps future pricing flexible.

## 4. Feature-by-Feature Deep Dive

*Format per feature: what the user gets → how it works (plain language) → PM assessment (strengths / gaps).*

### 4.1 Search & AI Answers - *the flagship*

**What the user gets:** Type anything - "rate cuts", "NVDA", "best semiconductor stocks". Get: an AI-written summary of what finance creators actually said, with each claim attributed to a named channel; up to 4 key points; clickable clip citations that jump to the exact second; plus raw results (video clips, predictions, ticker cards, channels) filterable by keyword/semantic mode, time period, and channel.

**How it works:** A lightweight AI router first figures out *what kind of question* this is (a specific ticker's sentiment? sector stock-picks? a factual lookup?) and routes it to the right search strategy. Keyword and semantic search run in parallel and are merged. The top ~12 clips feed a summarization model that is *forbidden* from using outside knowledge and *required* to name the channel behind every claim. Answers are cached for 24 hours so repeat searches are instant and free.

**PM assessment:**
- ✅ The attribution requirement is a genuine differentiator vs. generic AI chat - it turns "AI summary" into "evidence with sources."
- ✅ Smart caching means the marginal cost of a search is fractions of a cent - pricing-friendly.
- ⚠️ **Gap:** answers are capped at what the ~12 retrieved clips support. If coverage of a niche query is thin, users hit "channels haven't discussed this" - correct behavior, but a dead-end moment. A "watch this query" / notify-when-covered loop would convert that dead end into retention.
- ⚠️ **Gap:** answer quality is only as good as channel coverage. The channel list is the product's diet - there's no user-facing way to request new channels.

### 4.2 Predictions, Verified - *the moat*

**What the user gets:** Every prediction extracted from commentary is a ledger entry: who, what, direction, confidence, when. Once the horizon passes, it's graded against the actual market move. Users can see per-channel accuracy and per-ticker prediction history.

**How it works:** The extraction step treats predictions as first-class objects with direction, confidence, and horizon. A daily job matches each matured prediction to real price data and marks it right or wrong.

**PM assessment:**
- ✅ This is the retention engine: "who's actually right?" is a reason to come back weekly, not a one-time novelty.
- ✅ Defensible data asset - an accumulated track-record database can't be cloned by a fast follower, even one with the same extraction approach.
- ⚠️ **Gap:** grading is currently return-based at fixed horizons (1d/1w/1m). Vague predictions ("NVDA looks good long-term") and conditional calls are hard to grade - there will be an accuracy-perception gap if grading feels arbitrary. Publishing the grading methodology in-product would preempt "your accuracy scores are bogus" pushback.
- ⚠️ **Gap:** no user-facing leaderboard of commentators yet - the data exists; the surface doesn't.

### 4.3 Tickerflow (Social Sentiment) - *the breadth play*

**What the user gets:** For any S&P 100 ticker: a bull/bear score normalized across Reddit, X, StockTwits, and news; mention-volume trend vs. its 30-day norm; the catalyst themes driving the score with representative quotes; sentiment-over-price overlay.

**How it works:** Collectors pull raw chatter per source; spam/duplicates are filtered; a finance-specific model scores sentiment locally; a small AI pass extracts the *why* (catalyst themes) from the highest-engagement posts. The score blends sentiment quality (weighted by engagement) with unusual mention volume.

**PM assessment:**
- ✅ Four sources, one comparable number - this is the "check the mood before I check the price" habit loop.
- ✅ Local/open models + free APIs = near-zero marginal cost per ticker.
- ⚠️ **Gap:** universe limited to S&P 100 - mid-caps and other high-retail-interest names are absent. This is a deliberate cost decision; it should be framed in-product as "large caps today, more soon" rather than discovered as a 404.
- ⚠️ **Gap:** X data flows through an unofficial library - a continuity risk that needs a fallback plan (the paid-gateway integration is already built but switched off, which is exactly that fallback).

### 4.4 Themes (Narrative Maps) - *the discovery surface*

**What the user gets:** A visual hierarchy of market narratives - Sector → Industry → Theme → Ticker - with an interactive circle-pack exploration view and theme detail pages showing the commentary behind each node.

**How it works:** A seeded taxonomy organizes all extracted commentary; implicit ticker mentions are mapped to themes; ETFs are resolved as theme proxies where relevant.

**PM assessment:**
- ✅ Best "I don't know what to search" surface - solves the cold-start problem that pure search can't.
- ⚠️ **Gap:** narrative *momentum* (is this theme heating up or fading?) is the killer question and is only partially visible today. Emerging-narrative alerts would be the natural v2.

### 4.5 Investors & Smart Money Consensus (HFI) - *the premium wedge*

**What the user gets:** Track any investor or fund: their published content (letters, websites, filings) is ingested, their theses extracted, portfolio changes logged. Auto-generated reports summarize each investor; alerts fire on notable signals; the Consensus page aggregates positions across all tracked investors.

**How it works:** Per-user investor records (with SEC identity where applicable) + configured content sources → content ingested and deduplicated → AI extracts entities, theses, and portfolio changes → LLM-written reports and threshold alerts run on a schedule; a private search index powers "what has this investor said about X."

**PM assessment:**
- ✅ Highest willingness-to-pay audience (Persona 2) and a natural premium tier: "track more investors, get alerts."
- ✅ Cross-investor consensus is a unique aggregate no single-source tool can offer.
- ⚠️ **Gap:** this is the most manually-configured surface (users create investors + sources themselves). A curated starter library of well-known investors would collapse onboarding friction - likely the single highest-leverage onboarding fix in the product.

### 4.6 Supporting Surfaces

| Surface | User value | PM notes |
|---|---|---|
| **Overview (dashboard)** | One glance: market mood, trending tickers, sentiment, chatter | The daily-habit entry point; worth instrumenting as the "return visit" anchor |
| **Channels** | Browse monitored creators + per-channel stats | Currently admin-curated; user channel requests are an obvious demand signal to capture |
| **Activity feed** | Live "new video detected → processed" notifications | Makes the product feel alive; underleveraged as a push-notification surface |
| **Usage / Admin** | Personal usage analytics; invite & platform management | Invite-only gating is a growth control today, scarcity/word-of-mouth asset at launch |
| **⌘K Command palette** | Keyboard-fast navigation | Signals pro-user intent; consistent with Persona 2 |
| **Compare page** | Side-by-side comparison | Built but hidden from navigation - either finish it or remove it; limbo features erode trust in internal roadmaps |

## 5. The Core User Journey (today's happy path)

1. **Invite** → user receives a single-use code (scarcity + friction = intentional).
2. **First search** → lands on Search; the AI answer with named-channel attribution is the "wow" moment. *This is the activation moment - it must happen within 60 seconds of signup.*
3. **Exploration loop** → search → clip citation → video breakdown → related ticker/theme → another search. The internal link graph is strong.
4. **Habit loop** → Overview dashboard (daily mood check) + Activity feed (new content from followed channels) + Tickerflow checks around market events.
5. **Depth loop (power users)** → Investors tracking, Consensus, prediction track records.

**Where users currently fall out:** (a) niche query with no coverage → dead end (fix: query-watch); (b) HFI setup friction (fix: curated starter library); (c) no reason to return on a quiet market day (fix: daily/weekly digest, email or in-app).

## 6. Metrics Framework (what I'd instrument next)

| Layer | North-star candidate | Supporting metrics |
|---|---|---|
| Engagement | **Weekly searches per active user** | Answer click-through on citations, clip plays, time-to-first-search |
| Retention | **W4 retention of invited users** | Return-visit cadence, Overview/Tickerflow visit frequency |
| Quality (trust) | **% answers with ≥3 distinct attributed channels** | Citation click rate (proxy for perceived rigor), grading-dispute rate |
| Growth | **Invite conversion rate & K-factor** | Invite code redemption, viral invites per user |
| Value (moat) | **# predictions graded / month** | Track-record coverage per channel, accuracy-delta between top and bottom commentators |

The usage-analytics infrastructure (per-request event tracking, token spend, latency) already exists - the gap is defining and dashboarding the *product* metrics above rather than ops metrics.

## 7. Competitive Positioning (PM lens)

| Compete against | Their gap Carry exploits |
|---|---|
| Generic AI chat (ChatGPT/Perplexity) | No source-of-truth finance corpus, no second-level timestamps, no outcome grading |
| ApeWisdom / Swaggy Stocks | Mentions without sentiment quality; no attribution, no verification |
| Prospero.ai / Danelfin | Black-box scores; Carry shows the clips behind every number |
| StockTwits / LunarCrush | Single-platform; Carry synthesizes video + social + smart money |
| Bloomberg / RavenPack | $20k+/year; same *class* of signal at consumer price |

**The one-line pitch that survives diligence:** *"Everyone sells sentiment. Carry sells commentary with receipts - every claim attributed, every prediction graded."*

**Positioning risk:** the competitive analysis in `docs/competitve_analysis.md` correctly warns that the *sentiment score itself* is commoditized. The moat is the accumulated verified track record + multi-source provenance - so product decisions should always protect and showcase those two assets (e.g., never hide citations, always show grading).

## 8. Top Risks & Open Product Questions

1. **Data-source continuity** - unofficial X and yfinance paths could break without notice. *Mitigations exist (paid fallbacks built/inactive); needs a runbook + budget trigger.*
2. **Trust events** - one visibly wrong citation or unfair accuracy grade can undermine the entire trust positioning. *Needs: in-product feedback ("was this citation useful?"), a methodology page, and a correction mechanism.*
3. **Content-liability surface** - grading real people's predictions publicly invites creator pushback ("your extraction misread me"). *Needs an editorial policy, a dispute flow, and careful framing (information, not investment advice - the in-app disclosure pattern is already planned in the implementation docs).*
4. **Cold-start per niche** - thin coverage moments are the most likely churn trigger. *Needs query-watch + channel-expansion pipeline tied to demand signals.*
5. **The invite gate is doing double duty** - growth control *and* beta quality screen. Decide when it stops being an asset and starts being a ceiling.
6. **Feature limbo** - the hidden Compare page pattern should be a one-time event, not a habit.

## 9. Roadmap Suggestions (prioritized by leverage)

1. **Commentator leaderboard** (data exists, surface missing) - cheapest moat-showcase; strong shareable artifact.
2. **Curated investor starter library** - removes HFI onboarding friction; unlocks the premium wedge.
3. **Query-watch / coverage alerts** - converts the #1 dead end into a retention loop.
4. **Emerging-narrative alerts** (themes momentum) - the "before it's obvious" promise, made real.
5. **Digest (daily/weekly)** - a quiet-market-day reason to return; cheap given existing aggregation.
6. **Public methodology page** (grading + scoring formulas) - trust moat, marketing asset, preempts disputes.
7. **Channel-request flow** - user-curated coverage pipeline; demand signal for expansion.
8. **Pricing experiments on HFI/alerts** - the natural paid tier; cost base supports aggressive consumer pricing.

## 10. Glossary (internal term → product meaning)

| Internal term | What it means in product terms |
|---|---|
| **yt-chatter** | The original repo name; the YouTube commentary engine |
| **Market Chatter / TickerFlow** | The social sentiment feature (Reddit/X/StockTwits/news scores) |
| **HFI** | "Hedge Fund Intelligence" - the Investors/Consensus smart-money feature |
| **RISS / SMS / OCS** | The three published sentiment formulas: quality-weighted sentiment, mention-volume-vs-baseline, and their 70/30 blend |
| **WebSub** | The push mechanism that makes new YouTube videos appear in near real time |
| **OCS v0.1 / scoring versions** | The commitment to versioned, explainable score formulas |
| **Invite gate** | The invite-code requirement at signup (Clerk auth + single-use codes) |



