**TickerFlow → Insight**

A curated GitHub toolkit for multi-source stock sentiment

The space breaks into a three-stage pipeline: collect chatter per source (Twitter/X, Reddit, podcasts, news) → score it with sentiment / NLP → synthesize into a signal or digest. The repositories below are organized along that pipeline. Star counts (as of July 2026\) are a rough quality signal; “active” marks repos still updated in 2026\.

# **1  ·  Start here - full-stack frameworks (collect → decide)**

*These already handle the “mix multiple sources into an insight” step, so treat them as architecture foundations rather than something to rebuild.*

[**OpenBB-finance/OpenBB**](https://github.com/OpenBB-finance/OpenBB)  \~70k ★ · active

The serious backbone. An open data platform built for analysts, quants and AI agents, with connectors to news, fundamentals and social data - pull data through this rather than writing fifteen scrapers. Pair with agents-for-openbb for the agent layer.

[**TauricResearch/TradingAgents**](https://github.com/TauricResearch/TradingAgents)  \~91k ★ · active

The multi-agent LLM framework. Analyst agents (news, sentiment, fundamentals) debate and produce a buy/sell/hold call - the best reference for the synthesis layer. Note the active forks: \-CN, \-AShare, \-astock, and \-MCPmode (wires it to Model Context Protocol tools).

[**kbhujbal/AlphaAnalyst**](https://github.com/kbhujbal/AlphaAnalyst-open-source-autonomous-equity-research-agent)  \~44 ★ · active

Enter a ticker, get an analyst-style memo with news sentiment and earnings-call tone analysis. Small, but the closest match to a “Morning Pulse” output format.

[**jason8745/llm-agent-trader**](https://github.com/jason8745/llm-agent-trader)  \~377 ★

LLM decision analysis plus backtesting, with a FastAPI backend and Next.js frontend - useful for seeing the full application skeleton end to end.

# **2  ·  Per-source collectors (the plumbing)**

**Reddit / WallStreetBets**

[**Idanzinner/reddit-finance-scraper**](https://github.com/Idanzinner/reddit-finance-scraper)  · PRAW

Clean PRAW scraper with nested-comment support and multiple export formats. A good starting point for the ingestion layer.

[**Steffanic/redditTraders**](https://github.com/Steffanic/redditTraders)

Plots ticker mentions per day against price. Simple, but exactly the right idea for a mention-volume signal.

[**junhuplim/Stocks-Sentiments**](https://github.com/junhuplim/Stocks-Sentiments)

PRAW scraping plus sentiment scoring, wired end to end as a compact reference.

**Twitter / X & StockTwits**

[**shirosaidev/stocksight**](https://github.com/shirosaidev/stocksight)  \~2.5k ★

Most-starred in this niche: Twitter \+ news headlines → Elasticsearch → NLP sentiment. Dated (2023) but a solid blueprint.

[**StephanAkkerman/fintwit-bot**](https://github.com/StephanAkkerman/fintwit-bot)  \~155 ★ · active

Pulls Twitter, Reddit and Binance into one Discord bot - one of the few maintained multi-platform collectors.

[**gregyjames/stocktwits-sentiment**](https://github.com/gregyjames/stocktwits-sentiment)

StockTwits-specific sentiment with Keras / TensorFlow.

**News (Yahoo Finance etc.)**

[**janlukasschroeder/realtime-newsapi**](https://github.com/janlukasschroeder/realtime-newsapi)  \~362 ★

Real-time financial news aggregator with a query API - the most useful news repo here.

[**yfinance (standard library)**](https://github.com/ranaroussi/yfinance)

Gives Yahoo news \+ prices out of the box. Most small “Yahoo scraper” repos are just thin wrappers around this, so start here.

**Podcasts - honest gap**

There is no good finance-specific podcast-sentiment repo. The realistic path is DIY: yt-dlp or an RSS feed → OpenAI Whisper (or mlx-whisper) for transcription → feed transcripts into the same FinBERT / LLM scoring as your text sources.

[**wuyuyang001-oss/podcast-deepread**](https://github.com/wuyuyang001-oss/podcast-deepread)

Shows the transcription-to-structured-text half (local Whisper → chaptered HTML), which you can adapt for the ingestion side.

# **3  ·  The sentiment brain**

[**ProsusAI/finBERT**](https://github.com/ProsusAI/finBERT)  \~2.2k ★

The standard financial-sentiment model - what most of the tools above plug into for scoring.

[**LikithMeruvu/FinBert-Finetuning-for-Stock-Sentiment**](https://github.com/LikithMeruvu/FinBert-Finetuning-for-Stock-Sentiment)

A fine-tune of FinBERT on \~4.9k news headlines (\~81–82% accuracy) - a template if you want a customized scorer.

# **4  ·  Reference multi-source pipelines**

*Low-star, mostly recent hobby builds - but the architecture is exactly the Chatter Radar pattern, so they are worth a skim for design, not production use.*

[**high-altitude-ai/alpha-agent**](https://github.com/high-altitude-ai/alpha-agent)

A three-agent Collector → Analyst → Decider pipeline over live news and social sentiment. The cleanest expression of the pattern.

[**justinj8/ai\_agentic\_stock\_prediction**](https://github.com/justinj8/ai_agentic_stock_prediction)

Market overview \+ news/social sentiment \+ technicals → a final “Trader” recommendation.

[**Mynk724/financial-news-sentimental-analysis**](https://github.com/Mynk724/financial-news-sentimental-analysis)

News \+ Reddit \+ Twitter/X \+ FinBERT combined in one place.

# **Practical notes**

**Quality filter.**  Most sub-10-star repos are course or vibe-coded projects; treat them as design references, not production code. Build your foundation on OpenBB \+ FinBERT and borrow collectors from the maintained ones (fintwit-bot, realtime-newsapi).

**Your differentiator.**  None of these carry SEBI-style compliance framing - that is genuinely the layer to build on top. Worth stressing that these tools output signals, not investment recommendations to act on directly.

*Compiled July 2026 · star counts approximate and subject to change*