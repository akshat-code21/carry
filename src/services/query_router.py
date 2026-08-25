"""Query router — classifies user search queries into intents for smart routing.

Uses a lightweight LLM call to determine whether a query is:
- entity_lookup:    Asking about a specific company/event (use segment search)
- sector_discovery: Asking for top stocks in a sector/theme (use aggregated stock search)
- sentiment_check:  Asking about sentiment on a specific ticker (use aggregation data)
- factual_search:   General factual search (use segment search)
"""

import json
import logging
import time
from dataclasses import dataclass

from src.analytics.service import analytics
from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

ROUTER_SYSTEM_PROMPT = """You are a query classifier for a financial video analysis platform. \
Classify the user's search query into exactly one intent.

Intent types:
- "sector_discovery": The user wants to find top stocks, ETFs, tickers, or investment ideas \
within a sector, theme, or industry. Examples: "Semiconductors to watch?", "Best AI stocks?", \
"Top energy plays", "What are the hot tech stocks?", "Nuclear stocks?", "Defense stocks to buy?", \
"EV stocks?", "Biotech picks?", "Best semiconductor ETFs?", "AI sector ETFs", \
"Which ETF for clean energy?", "Top financial sector funds"
- "ticker_narrative": The user is asking about the narrative, outlook, predictions, analysis, \
or forward-looking view on a SPECIFIC stock, ETF, or company. They want aggregated intelligence \
— predictions, sentiment, themes — not raw transcript clips. Examples: "What was the narrative on \
Microsoft stocks for the upcoming time?", "Outlook on Nvidia?", \
"What are people saying about Tesla?", "Apple stock analysis", "MSFT predictions", \
"Google stock narrative", "What's the bull case for Amazon?", "SMH outlook", \
"What's the narrative on QQQ?"
- "entity_lookup": The user is asking about a SPECIFIC event, news item, or person's comments \
— they want the actual transcript clips. Examples: "What is the narrative on Anthropic's IPO?", \
"Nvidia earnings call analysis", "What did Cathie Wood say about Tesla?", \
"DeepSeek launch discussion"
- "sentiment_check": The user is asking about the bullish/bearish sentiment on a specific ticker \
or company. Examples: "Is Tesla bullish?", "What's the sentiment on Apple?", "Is NVDA overbought?"
- "factual_search": General search for information, clips, or segments. \
Examples: "inflation discussion", "Fed rate decision", "when was Bitcoin discussed?"

Key distinction between ticker_narrative and entity_lookup:
- ticker_narrative: User wants an OVERVIEW of what has been said about a stock \
(predictions, sentiment, themes). The focus is on the STOCK.
- entity_lookup: User wants to find specific CLIPS or EVENTS about a company or topic. \
The focus is on the CONTENT.

Also extract:
- "sector_hint": If sector_discovery, extract the sector/industry/theme keyword(s) \
the user is asking about (e.g., "semiconductors", "AI", "energy", "defense"). Null otherwise.
- "ticker_hint": If ticker_narrative, entity_lookup, or sentiment_check, extract the ticker \
symbol if identifiable (e.g., "NVDA", "TSLA", "MSFT", "AAPL", "AMZN", "GOOGL", "META", \
"SMH", "QQQ"). \
Map company names to tickers: Microsoft->MSFT, Apple->AAPL, Google/Alphabet->GOOGL, \
Amazon->AMZN, Nvidia->NVDA, Tesla->TSLA, Meta/Facebook->META, AMD->AMD, Intel->INTC. \
Null if not identifiable.
- "instrument_type": Which instrument class the user wants results for.
  - "etfs": User explicitly wants ETFs, sector funds, index funds, or passive sector exposure. \
Examples: "semiconductor ETFs", "best AI ETFs", "which ETF for defense?", "energy sector funds", \
"clean energy ETF picks"
  - "stocks": User wants individual/single-name stocks/equities, OR the query is sector discovery \
without any ETF language. Examples: "AI stocks", "semiconductors to watch", "top energy plays", \
"biotech picks", "defense stocks"
  Default to "stocks" when ambiguous.

Return ONLY valid JSON:
{"intent": "...", "sector_hint": "..." or null, "ticker_hint": "..." or null, \
"instrument_type": "stocks" or "etfs"}"""


@dataclass
class QueryIntent:
    """Classified intent for a user search query."""

    intent: str
    # Possible intents: sector_discovery | entity_lookup | sentiment_check
    #                  | factual_search | ticker_narrative
    sector_hint: str | None = None
    ticker_hint: str | None = None
    # stocks | etfs — which instrument class discovery results should return
    instrument_type: str = "stocks"


class QueryRouter:
    """Classifies search queries into intents using a lightweight LLM call."""

    def __init__(self) -> None:
        self._client = None

    def _get_client(self):
        """Lazily initialize the OpenAI client for fast/cheap classification."""
        if self._client is None:
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY is not set.")
            from openai import OpenAI

            self._client = OpenAI(api_key=settings.openai_api_key)
        return self._client

    async def classify(self, query: str) -> QueryIntent:
        """Classify a search query into an intent.

        Uses GPT-4o-mini for fast, cheap classification.
        Falls back to 'factual_search' if classification fails.
        """
        # Fast heuristic shortcuts to avoid LLM calls for obvious cases
        fast_result = self._heuristic_classify(query)
        if fast_result:
            logger.debug(f"Query '{query}' classified by heuristic: {fast_result.intent}")
            return fast_result

        # LLM classification
        started = time.perf_counter()
        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model="gpt-5.4-nano",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                    {"role": "user", "content": query},
                ],
                temperature=0.0,
                max_completion_tokens=100,
            )

            usage = getattr(response, "usage", None)
            analytics.record_llm_usage(
                provider="openai",
                model="gpt-5.4-nano",
                purpose="search_classify",
                input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                output_tokens=getattr(usage, "completion_tokens", 0) or 0,
                duration_ms=(time.perf_counter() - started) * 1000.0,
            )

            content = response.choices[0].message.content
            data = json.loads(content)

            instrument_type = QueryRouter._normalize_instrument_type(data.get("instrument_type"))
            # Prefer deterministic keyword signal when present — more reliable than LLM.
            heuristic_instrument = QueryRouter.detect_instrument_type(query)
            if heuristic_instrument:
                instrument_type = heuristic_instrument

            intent = QueryIntent(
                intent=data.get("intent", "factual_search"),
                sector_hint=data.get("sector_hint"),
                ticker_hint=data.get("ticker_hint"),
                instrument_type=instrument_type,
            )
            logger.info(
                f"Query '{query}' classified as: {intent.intent} "
                f"(sector={intent.sector_hint}, ticker={intent.ticker_hint}, "
                f"instrument={intent.instrument_type})"
            )
            return intent

        except Exception as e:
            logger.warning(f"Query classification failed, falling back to factual_search: {e}")
            analytics.record_llm_usage(
                provider="openai",
                model="gpt-5.4-nano",
                purpose="search_classify",
                success=False,
                error_summary=str(e),
                duration_ms=(time.perf_counter() - started) * 1000.0,
            )
            return QueryIntent(
                intent="factual_search",
                instrument_type=QueryRouter.detect_instrument_type(query) or "stocks",
            )

    @staticmethod
    def _normalize_instrument_type(value: str | None) -> str:
        """Normalize instrument_type to 'stocks' or 'etfs'."""
        if not value:
            return "stocks"
        v = value.strip().lower()
        if v in ("etf", "etfs", "fund", "funds", "index"):
            return "etfs"
        return "stocks"

    @staticmethod
    def detect_instrument_type(query: str) -> str | None:
        """Detect whether the query is asking for stocks or ETFs.

        Returns 'stocks', 'etfs', or None if no strong instrument signal
        (caller should default to 'stocks' for global discovery).
        """
        q = query.lower().strip().rstrip("?").rstrip(".")

        etf_signals = [
            "etfs",
            "etf",
            "sector fund",
            "sector funds",
            "index fund",
            "index funds",
            "exchange traded",
            "exchange-traded",
        ]
        stock_signals = [
            "stocks",
            "stock",
            "equities",
            "equity",
            "single name",
            "single-name",
            "individual names",
            "companies to",
            "company picks",
        ]

        has_etf = any(sig in q for sig in etf_signals)
        has_stock = any(sig in q for sig in stock_signals)

        if has_etf and not has_stock:
            return "etfs"
        if has_stock and not has_etf:
            return "stocks"
        if has_etf and has_stock:
            # "stocks and etfs" / mixed — prefer explicit ETF wording order:
            # if 'etf' appears before 'stock', treat as etfs, else stocks.
            etf_pos = min(
                (q.find(sig) for sig in etf_signals if sig in q),
                default=len(q),
            )
            stock_pos = min(
                (q.find(sig) for sig in stock_signals if sig in q),
                default=len(q),
            )
            return "etfs" if etf_pos < stock_pos else "stocks"
        return None

    @staticmethod
    def _heuristic_classify(query: str) -> QueryIntent | None:
        """Fast regex/keyword heuristics to avoid LLM calls for obvious patterns.

        Returns None if no heuristic matched (falls through to LLM).
        """
        q = query.lower().strip().rstrip("?").rstrip(".")
        instrument_type = QueryRouter.detect_instrument_type(query) or "stocks"

        # Sector discovery patterns: "X stocks to watch", "best X stocks", "top X plays"
        sector_keywords = [
            "semiconductor",
            "ai ",
            "artificial intelligence",
            "tech",
            "energy",
            "defense",
            "biotech",
            "pharma",
            "ev ",
            "electric vehicle",
            "nuclear",
            "crypto",
            "blockchain",
            "fintech",
            "saas",
            "cloud",
            "cybersecurity",
            "healthcare",
            "real estate",
            "reit",
            "oil",
            "gas",
            "mining",
            "solar",
            "wind",
            "renewable",
            "chip",
            "autonomous",
            "space",
            "quantum",
            "robotics",
            "drone",
            "clean energy",
            "inflation",
            "recession",
            "banking",
            "financial",
        ]

        discovery_suffixes = [
            "to watch",
            "to buy",
            "stocks",
            "etfs",
            "etf",
            "picks",
            "plays",
            "tickers",
            "ideas",
            "names",
            "opportunities",
            "funds",
        ]

        discovery_prefixes = [
            "best",
            "top",
            "hottest",
            "most discussed",
            "trending",
            "popular",
            "favorite",
            "recommended",
            "which",
        ]

        # Prefer the longest matching sector phrase (e.g. "clean energy" over "energy")
        matched_sectors = [s for s in sector_keywords if s in q]
        best_sector = (
            max(matched_sectors, key=lambda s: len(s.strip())).strip() if matched_sectors else None
        )

        if best_sector:
            for suffix in discovery_suffixes:
                if suffix in q:
                    return QueryIntent(
                        intent="sector_discovery",
                        sector_hint=best_sector,
                        instrument_type=instrument_type,
                    )
            for prefix in discovery_prefixes:
                if q.startswith(prefix):
                    return QueryIntent(
                        intent="sector_discovery",
                        sector_hint=best_sector,
                        instrument_type=instrument_type,
                    )

        # Bare ETF discovery: "best ETFs?", "top ETFs to buy"
        if instrument_type == "etfs" and any(
            p in q for p in ("best", "top", "which", "to buy", "to watch", "picks")
        ):
            return QueryIntent(
                intent="sector_discovery",
                sector_hint=best_sector,
                instrument_type="etfs",
            )

        # Check for bare sector queries like just "semiconductors?" or "AI stocks?"
        for sector in sector_keywords:
            stripped = q.strip()
            if stripped == sector.strip() or stripped == f"{sector.strip()}s":
                return QueryIntent(
                    intent="sector_discovery",
                    sector_hint=sector.strip(),
                    instrument_type=instrument_type,
                )

        # Sentiment check heuristic — e.g. "What is the sentiment on NVDA?", "Is TSLA bullish?"
        sentiment_signals = [
            "sentiment",
            "bullish",
            "bearish",
            "bull case",
            "bear case",
            "overbought",
            "oversold",
        ]
        if any(sig in q for sig in sentiment_signals):
            ticker = QueryRouter._extract_ticker_heuristic(query)
            if ticker:
                return QueryIntent(
                    intent="sentiment_check",
                    ticker_hint=ticker,
                    instrument_type=instrument_type,
                )

        # Ticker narrative heuristic — e.g. "Outlook on Nvidia?",
        # "What are people saying about Tesla?"
        narrative_signals = [
            "narrative",
            "outlook",
            "what are people saying",
            "what is the narrative",
            "what's the narrative",
            "stock analysis",
            "bull case for",
            "bear case for",
        ]
        if any(sig in q for sig in narrative_signals):
            ticker = QueryRouter._extract_ticker_heuristic(query)
            if ticker:
                return QueryIntent(
                    intent="ticker_narrative",
                    ticker_hint=ticker,
                    instrument_type=instrument_type,
                )

        return None

    @staticmethod
    def _extract_ticker_heuristic(query: str) -> str | None:
        """Try to pull a ticker symbol from the raw query without an LLM.

        Maps common company names → tickers, and falls back to any uppercase
        1-5 letter token that looks like a ticker.
        """
        import re

        lowered = query.lower()
        name_map = {
            "nvidia": "NVDA",
            "nvda": "NVDA",
            "tesla": "TSLA",
            "tsla": "TSLA",
            "apple": "AAPL",
            "aapl": "AAPL",
            "microsoft": "MSFT",
            "msft": "MSFT",
            "google": "GOOGL",
            "alphabet": "GOOGL",
            "googl": "GOOGL",
            "goog": "GOOGL",
            "amazon": "AMZN",
            "amzn": "AMZN",
            "meta": "META",
            "facebook": "META",
            "amd": "AMD",
            "intel": "INTC",
            "intc": "INTC",
            "palantir": "PLTR",
            "pltr": "PLTR",
            "netflix": "NFLX",
            "nflx": "NFLX",
        }
        for name, ticker in name_map.items():
            if re.search(rf"\b{re.escape(name)}\b", lowered):
                return ticker
        # Fallback: any standalone uppercase ticker-like token (2-5 caps) in original query
        m = re.search(r"\b([A-Z]{2,5})\b", query)
        if m:
            cand = m.group(1).upper()
            # Avoid common English words that look like tickers
            if cand not in {"WHAT", "WHEN", "THIS", "THAT", "SENTIMENT", "BULLISH", "BEARISH"}:
                return cand
        return None
