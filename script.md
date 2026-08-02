# Carry — 1-Minute Elevator Pitch Script

> **Format:** Presenter on camera / voiceover with product demo cuts  
> **Total Duration:** 60 seconds  
> **Pacing note:** ~150 words = 60 seconds at a natural speaking pace

---

## The Script

**[0:00 – 0:08] THE HOOK** *(energetic, direct to camera)*

> Every day, millions of stock opinions flood YouTube, Reddit, and X. But here's the problem — nobody's tracking whether any of them are actually right.

**[0:08 – 0:18] THE PROBLEM** *(slight pause, then build)*

> Retail investors are drowning in financial noise — a YouTube creator says buy Nvidia, Reddit's buzzing about Tesla, X is bearish on Apple — and there's no way to see the full picture, verify these calls against real market data, or know who to actually trust.

**[0:18 – 0:35] THE SOLUTION** *(cut to product demo — search UI, TickerFlow dashboard, ticker pages)*

> Carry fixes this. We ingest YouTube channels, Reddit threads, and X posts — then use AI to extract every stock prediction, theme, and market call. Our TickerFlow engine scores real-time social sentiment across platforms — buzz scores, bullish-bearish ratios, buy and sell signals — while our prediction tracker matches every claim against actual price movements: 1-day, 1-week, and 1-month returns.

**[0:35 – 0:48] THE MAGIC / DIFFERENTIATION** *(cut to TickerFlow ticker view, signal chart with buy/sell markers, sentiment dashboard)*

> Search "AI semiconductor stocks" and Carry tells you which tickers creators are talking about, what Reddit's sentiment is, and whether the market agreed. It's not just a search engine — it's a cross-platform intelligence layer that turns scattered financial opinions into actionable, verified signals.

**[0:48 – 0:60] VISION + CTA** *(back to camera, confident tone)*

> Today we cover YouTube, Reddit, and X. Tomorrow — podcasts, earnings calls, StockTwits. Our vision is to become the accountability layer for all financial commentary on the internet. We're building the Bloomberg Terminal for social-driven market intelligence.

---

## Speaker Notes

| Timestamp | What's on screen | Key demo moment |
|---|---|---|
| 0:00–0:08 | Speaker on camera, bold text overlay: *"Who's actually tracking financial opinions?"* | — |
| 0:08–0:18 | Quick montage: YouTube finance thumbnails → Reddit WSB posts → X/Twitter stock takes | Convey the multi-platform noise |
| 0:18–0:25 | Demo: typing "AI semiconductor stocks" into Carry search bar | Show hybrid search in action |
| 0:25–0:30 | Demo: TickerFlow dashboard — top stocks, ETFs, bullish leaders, platform breakdown | Show the social sentiment aggregation |
| 0:30–0:35 | Demo: TickerFlow ticker view (e.g., NVDA) — signal score, buzz chart, buy/sell markers | Show cross-platform signal computation |
| 0:35–0:42 | Demo: search results — stock discovery cards + transcript segments with predictions | Show LLM extraction + smart query routing |
| 0:42–0:48 | Demo: ticker detail page — prediction table, 1d/1w/1m performance charts | The "scorecard" moment |
| 0:48–0:55 | Speaker on camera with TickerFlow dashboard briefly visible behind | Vision framing |
| 0:55–0:60 | Logo + tagline: *"The accountability layer for financial commentary"* | Strong close |

---

## Alternate Taglines (pick one)

1. *"The accountability layer for financial commentary"*
2. *"Cross-platform intelligence for market conviction"*
3. *"Know who's right, not just who's loud"*
4. *"Bloomberg Terminal for social-driven market intelligence"*

---

## Key Product Capabilities Referenced

These are the real features from the codebase that the script references:

**YouTube Analysis Pipeline:**
- **Hybrid search** (keyword + semantic + intent-classified routing via LLM query router)
- **LLM-powered claim extraction** (Claude/OpenAI structured analysis of transcripts)
- **Theme taxonomy** (Sector → Industry → Theme → Ticker hierarchy)
- **Performance scoring** (1-day, 1-week, 1-month returns via yfinance)
- **ETF mapping for institutional channels** (auto-classified channel types)
- **WebSub real-time channel monitoring** (new uploads auto-ingested)

**TickerFlow / Market Chatter:**
- **Multi-source social sentiment** (Reddit, X, news — weighted 45/30/25)
- **Buzz scores & bullish/bearish ratios** per ticker, per source
- **Signal computation** (composite score from sentiment + attention + confidence)
- **Buy/sell signal markers** on price + mentions overlay charts
- **TickerFlow Dashboard** (top stocks, top ETFs, bullish leaders, bearish laggards, platform breakdown)
- **Daily trend tracking** (mentions, buzz, sentiment over time per ticker)

> [!TIP]
> The script intentionally avoids technical jargon (no mention of pgvector, Celery, FastAPI, Adanos API, etc.). Investors and users care about *what it does*, not *how it's built*. Save the tech stack for a deep-dive or technical demo.
