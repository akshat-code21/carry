"""Query router — classifies user search queries into intents for smart routing.

Uses a lightweight LLM call to determine whether a query is:
- entity_lookup:    Asking about a specific company/event (use segment search)
- sector_discovery: Asking for top stocks in a sector/theme (use aggregated stock search)
- sentiment_check:  Asking about sentiment on a specific ticker (use aggregation data)
- factual_search:   General factual search (use segment search)
"""

import json
import logging

from dataclasses import dataclass

from src.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

ROUTER_SYSTEM_PROMPT = """You are a query classifier for a financial video analysis platform. Classify the user's search query into exactly one intent.

Intent types:
- "sector_discovery": The user wants to find top stocks, tickers, or investment ideas within a sector, theme, or industry. Examples: "Semiconductors to watch?", "Best AI stocks?", "Top energy plays", "What are the hot tech stocks?", "Nuclear stocks?", "Defense stocks to buy?", "EV stocks?", "Biotech picks?"
- "ticker_narrative": The user is asking about the narrative, outlook, predictions, analysis, or forward-looking view on a SPECIFIC stock or company. They want aggregated intelligence — predictions, sentiment, themes — not raw transcript clips. Examples: "What was the narrative on Microsoft stocks for the upcoming time?", "Outlook on Nvidia?", "What are people saying about Tesla?", "Apple stock analysis", "MSFT predictions", "Google stock narrative", "What's the bull case for Amazon?"
- "entity_lookup": The user is asking about a SPECIFIC event, news item, or person's comments — they want the actual transcript clips. Examples: "What is the narrative on Anthropic's IPO?", "Nvidia earnings call analysis", "What did Cathie Wood say about Tesla?", "DeepSeek launch discussion"
- "sentiment_check": The user is asking about the bullish/bearish sentiment on a specific ticker or company. Examples: "Is Tesla bullish?", "What's the sentiment on Apple?", "Is NVDA overbought?"
- "factual_search": General search for information, clips, or segments. Examples: "inflation discussion", "Fed rate decision", "when was Bitcoin discussed?"

Key distinction between ticker_narrative and entity_lookup:
- ticker_narrative: User wants an OVERVIEW of what has been said about a stock (predictions, sentiment, themes). The focus is on the STOCK.
- entity_lookup: User wants to find specific CLIPS or EVENTS about a company or topic. The focus is on the CONTENT.

Also extract:
- "sector_hint": If sector_discovery, extract the sector/industry/theme keyword(s) the user is asking about (e.g., "semiconductors", "AI", "energy", "defense"). Null otherwise.
- "ticker_hint": If ticker_narrative, entity_lookup, or sentiment_check, extract the ticker symbol if identifiable (e.g., "NVDA", "TSLA", "MSFT", "AAPL", "AMZN", "GOOGL", "META"). Map company names to tickers: Microsoft→MSFT, Apple→AAPL, Google/Alphabet→GOOGL, Amazon→AMZN, Nvidia→NVDA, Tesla→TSLA, Meta/Facebook→META, AMD→AMD, Intel→INTC. Null if not identifiable.

Return ONLY valid JSON:
{"intent": "...", "sector_hint": "..." or null, "ticker_hint": "..." or null}"""


@dataclass
class QueryIntent:
    """Classified intent for a user search query."""

    intent: str  # sector_discovery | entity_lookup | sentiment_check | factual_search
    sector_hint: str | None = None
    ticker_hint: str | None = None


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
        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                    {"role": "user", "content": query},
                ],
                temperature=0.0,
                max_tokens=100,
            )

            content = response.choices[0].message.content
            data = json.loads(content)

            intent = QueryIntent(
                intent=data.get("intent", "factual_search"),
                sector_hint=data.get("sector_hint"),
                ticker_hint=data.get("ticker_hint"),
            )
            logger.info(f"Query '{query}' classified as: {intent.intent} (sector={intent.sector_hint}, ticker={intent.ticker_hint})")
            return intent

        except Exception as e:
            logger.warning(f"Query classification failed, falling back to factual_search: {e}")
            return QueryIntent(intent="factual_search")

    @staticmethod
    def _heuristic_classify(query: str) -> QueryIntent | None:
        """Fast regex/keyword heuristics to avoid LLM calls for obvious patterns.

        Returns None if no heuristic matched (falls through to LLM).
        """
        q = query.lower().strip().rstrip("?").rstrip(".")

        # Sector discovery patterns: "X stocks to watch", "best X stocks", "top X plays"
        sector_keywords = [
            "semiconductor", "ai ", "artificial intelligence", "tech", "energy",
            "defense", "biotech", "pharma", "ev ", "electric vehicle", "nuclear",
            "crypto", "blockchain", "fintech", "saas", "cloud", "cybersecurity",
            "healthcare", "real estate", "reit", "oil", "gas", "mining",
            "solar", "wind", "renewable", "chip", "autonomous", "space",
            "quantum", "robotics", "drone",
        ]

        discovery_suffixes = [
            "to watch", "to buy", "stocks", "picks", "plays", "tickers",
            "ideas", "names", "opportunities",
        ]

        discovery_prefixes = [
            "best", "top", "hottest", "most discussed", "trending",
            "popular", "favorite", "recommended",
        ]

        # Check for "[sector] stocks?" / "[sector] to watch?" patterns
        for sector in sector_keywords:
            if sector in q:
                for suffix in discovery_suffixes:
                    if suffix in q:
                        return QueryIntent(
                            intent="sector_discovery",
                            sector_hint=sector.strip(),
                        )
                for prefix in discovery_prefixes:
                    if q.startswith(prefix):
                        return QueryIntent(
                            intent="sector_discovery",
                            sector_hint=sector.strip(),
                        )

        # Check for bare sector queries like just "semiconductors?" or "AI stocks?"
        for sector in sector_keywords:
            stripped = q.strip()
            if stripped == sector.strip() or stripped == f"{sector.strip()}s":
                return QueryIntent(
                    intent="sector_discovery",
                    sector_hint=sector.strip(),
                )

        return None
