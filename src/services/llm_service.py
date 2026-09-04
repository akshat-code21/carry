"""LLM service - Anthropic Claude implementation (swappable via interface)."""

import json
import logging

from src.config import get_settings
from src.services.interfaces import (
    AnalysisResult,
    ExtractedEntities,
    ExtractedPrediction,
    ExtractedTheme,
    LLMProvider,
    TickerMapping,
    TranscriptSegmentDTO,
)

logger = logging.getLogger(__name__)
settings = get_settings()

# System prompt for transcript analysis (cached across calls)
ANALYSIS_SYSTEM_PROMPT = """You are an expert financial analyst extracting structured data \
from YouTube financial commentary transcripts.

For the given transcript chunk, extract ALL of the following:

1. **Themes**: Market themes being discussed. For each theme provide:
   - sector: The broad sector (e.g., "Technology", "Financials", "Healthcare")
   - industry: The specific industry (e.g., "Semiconductors", "Big Tech / FAANG")
   - theme: The specific theme (e.g., "AI Chips", "Rate Cuts", "Retail")
   - narrative: A one-sentence description of what was said about this theme
   - sentiment: "bullish", "bearish", or "neutral"
   - confidence: 0.0 to 1.0 - how confident the speaker seemed

2. **Explicit Tickers**: Stock tickers explicitly mentioned by name or company name by \
the speaker (e.g., speaker says "Nvidia" or "NVDA"). Do NOT include competitor tickers \
here unless they were explicitly named by the speaker.

3. **Implicit Tickers**: Stock tickers implicitly relevant based on the general sector \
topic discussed (e.g., discussing "AI chips" implies NVDA, AMD, etc.). These are background \
sector context only.

4. **Predictions**: Concrete, testable predictions or calls. For each:
   - text: What was predicted, in plain English
   - ticker: The stock ticker symbol (e.g. "NVDA", "AAPL", "MSFT", "TSLA", "AMZN", \
"GOOGL", "XOM") corresponding ONLY to the specific company being predicted. If a company \
name (e.g. "Apple", "Nvidia") is mentioned in relation to the prediction, convert it to its \
official stock ticker symbol. If a private company backed by a major public company is \
mentioned (e.g. "OpenAI" -> "MSFT", "Anthropic" -> "AMZN"), use the primary public ticker \
symbol. Use null for macro calls or when no specific company was target of the call.
   - direction: "bullish", "bearish", or "neutral"
   - timeframe: The timeframe if mentioned (e.g., "by end of year", "next quarter")
   - confidence: 0.0 to 1.0

5. **Entities**: Named entities mentioned:
   - people: Names of individuals
   - companies: Company names
   - indices: Market indices (S&P 500, Nasdaq, etc.)

Return ONLY valid JSON matching this exact schema:
{
  "themes": [...],
  "explicit_tickers": [...],
  "implicit_tickers": [...],
  "predictions": [...],
  "entities": {"people": [...], "companies": [...], "indices": [...]}
}

Rules:
- Skip generic banter, intros, ads, and non-financial discussion
- Be conservative with predictions - only extract clear, testable calls
- Never assign a competitor stock ticker to a prediction unless that company was specifically \
discussed for that prediction call
- Never invent tickers or timeframes not mentioned in the transcript
- If a chunk has no financial content, return empty arrays
"""

THEME_TICKER_ENRICHMENT_PROMPT = """You are a financial market expert. Given a theme and \
its narrative context from a financial commentary, suggest additional single-name stock \
(equity) tickers that are most relevant to this theme.

For each ticker, provide:
- ticker: The stock symbol of a public company (NOT an ETF, index fund, or bond fund)
- relevance_score: 0.0 to 1.0 (how core and directly relevant this ticker is to the theme - \
assign >= 0.85 only for essential core tickers)
- reason: A brief explanation of why this ticker maps to this theme

Return ONLY valid JSON as an array:
[{"ticker": "SYMBOL", "relevance_score": 0.85, "reason": "..."}]

Rules:
- Only suggest individual company equities (e.g. NVDA, JPM, XOM).
- Do NOT suggest ETFs or funds (e.g. no QQQ, SPY, SMH, XLK, XLF, HYG, IWM, ARKK, ICLN, GLD, TLT).
- Quality over quantity - 2-3 highly core tickers is better than loosely related ones.
"""


class AnthropicLLMService(LLMProvider):
    """LLM service using Anthropic Claude API."""

    def __init__(self, model: str | None = None) -> None:
        self._api_key = settings.anthropic_api_key
        self._model = model or settings.anthropic_model
        self._client = None

    def _get_client(self):
        """Lazily initialize the Anthropic client."""
        if self._client is None:
            if not self._api_key:
                raise ValueError("ANTHROPIC_API_KEY is not set. Please set it in your .env file.")
            import anthropic

            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    async def analyze_transcript_chunk(
        self, segments: list[TranscriptSegmentDTO], video_title: str
    ) -> AnalysisResult:
        """Analyze a chunk of transcript segments using Claude."""
        client = self._get_client()

        # Format segments into a readable transcript block
        transcript_text = "\n".join(
            f"[{seg.start_sec:.0f}s - {seg.end_sec:.0f}s] {seg.text}" for seg in segments
        )

        user_prompt = f"""Video Title: "{video_title}"

Transcript Chunk:
{transcript_text}

Extract all themes, tickers, predictions, and entities from this transcript chunk."""

        try:
            response = client.messages.create(
                model=self._model,
                max_tokens=4096,
                system=ANALYSIS_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )

            # Parse the response
            content = response.content[0].text
            data = json.loads(content)

            return AnalysisResult(
                themes=[
                    ExtractedTheme(
                        sector=t.get("sector", ""),
                        industry=t.get("industry", ""),
                        theme=t.get("theme", ""),
                        narrative=t.get("narrative", ""),
                        sentiment=t.get("sentiment", "neutral"),
                        confidence=float(t.get("confidence", 0.5)),
                    )
                    for t in data.get("themes", [])
                ],
                explicit_tickers=data.get("explicit_tickers", []),
                implicit_tickers=data.get("implicit_tickers", []),
                predictions=[
                    ExtractedPrediction(
                        text=p.get("text", ""),
                        ticker=p.get("ticker"),
                        direction=p.get("direction"),
                        timeframe=p.get("timeframe"),
                        confidence=p.get("confidence"),
                    )
                    for p in data.get("predictions", [])
                ],
                entities=ExtractedEntities(
                    people=data.get("entities", {}).get("people", []),
                    companies=data.get("entities", {}).get("companies", []),
                    indices=data.get("entities", {}).get("indices", []),
                ),
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return AnalysisResult()
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            raise

    async def enrich_theme_tickers(self, theme_name: str, narrative: str) -> list[TickerMapping]:
        """Ask Claude to suggest additional tickers for a theme."""
        client = self._get_client()

        user_prompt = f"""Theme: "{theme_name}"
Narrative: "{narrative}"

What additional stock tickers are most relevant to this theme and narrative?"""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                system=THEME_TICKER_ENRICHMENT_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )

            content = response.content[0].text
            data = json.loads(content)

            return [
                TickerMapping(
                    ticker=item.get("ticker", ""),
                    relevance_score=float(item.get("relevance_score", 0.5)),
                    reason=item.get("reason", ""),
                )
                for item in data
            ]
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse ticker enrichment response: {e}")
            return []
        except Exception as e:
            logger.error(f"Ticker enrichment failed: {e}")
            raise


class OpenAILLMService(LLMProvider):
    """LLM service using OpenAI API (GPT-4o, GPT-4.1, etc.)."""

    def __init__(self, model: str | None = None) -> None:
        self._api_key = settings.openai_api_key
        self._model = model or settings.openai_model or "gpt-5.4-nano"
        self._client = None

    def _get_client(self):
        """Lazily initialize the OpenAI client."""
        if self._client is None:
            if not self._api_key:
                raise ValueError("OPENAI_API_KEY is not set. Please set it in your .env file.")
            from openai import OpenAI

            self._client = OpenAI(api_key=self._api_key)
        return self._client

    async def analyze_transcript_chunk(
        self, segments: list[TranscriptSegmentDTO], video_title: str
    ) -> AnalysisResult:
        """Analyze a chunk of transcript segments using OpenAI."""
        client = self._get_client()

        transcript_text = "\n".join(
            f"[{seg.start_sec:.0f}s - {seg.end_sec:.0f}s] {seg.text}" for seg in segments
        )

        user_prompt = f"""Video Title: "{video_title}"

Transcript Chunk:
{transcript_text}

Extract all themes, tickers, predictions, and entities from this transcript chunk."""

        token_param = {}
        if "gpt-5" in self._model.lower() or self._model.lower().startswith("o1"):
            token_param["max_completion_tokens"] = 4096
        else:
            token_param["max_tokens"] = 4096

        try:
            response = client.chat.completions.create(
                model=self._model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                **token_param,
            )

            content = response.choices[0].message.content
            data = json.loads(content)

            return AnalysisResult(
                themes=[
                    ExtractedTheme(
                        sector=t.get("sector", ""),
                        industry=t.get("industry", ""),
                        theme=t.get("theme", ""),
                        narrative=t.get("narrative", ""),
                        sentiment=t.get("sentiment", "neutral"),
                        confidence=float(t.get("confidence", 0.5)),
                    )
                    for t in data.get("themes", [])
                ],
                explicit_tickers=data.get("explicit_tickers", []),
                implicit_tickers=data.get("implicit_tickers", []),
                predictions=[
                    ExtractedPrediction(
                        text=p.get("text", ""),
                        ticker=p.get("ticker"),
                        direction=p.get("direction"),
                        timeframe=p.get("timeframe"),
                        confidence=p.get("confidence"),
                    )
                    for p in data.get("predictions", [])
                ],
                entities=ExtractedEntities(
                    people=data.get("entities", {}).get("people", []),
                    companies=data.get("entities", {}).get("companies", []),
                    indices=data.get("entities", {}).get("indices", []),
                ),
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            return AnalysisResult()
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            raise

    async def enrich_theme_tickers(self, theme_name: str, narrative: str) -> list[TickerMapping]:
        """Ask OpenAI to suggest additional tickers for a theme."""
        client = self._get_client()

        user_prompt = f"""Theme: "{theme_name}"
Narrative: "{narrative}"

What additional stock tickers are most relevant to this theme and narrative?"""

        token_param = {}
        if "gpt-5" in self._model.lower() or self._model.lower().startswith("o1"):
            token_param["max_completion_tokens"] = 2048
        else:
            token_param["max_tokens"] = 2048

        try:
            response = client.chat.completions.create(
                model=self._model,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": THEME_TICKER_ENRICHMENT_PROMPT
                        + '\n\nWrap your response in a JSON object: {"tickers": [...]}',
                    },
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                **token_param,
            )

            content = response.choices[0].message.content
            data = json.loads(content)

            # Handle both {"tickers": [...]} and bare [...] formats
            items = data.get("tickers", data) if isinstance(data, dict) else data

            return [
                TickerMapping(
                    ticker=item.get("ticker", ""),
                    relevance_score=float(item.get("relevance_score", 0.5)),
                    reason=item.get("reason", ""),
                )
                for item in items
            ]
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI ticker enrichment response: {e}")
            return []
        except Exception as e:
            logger.error(f"OpenAI ticker enrichment failed: {e}")
            raise
