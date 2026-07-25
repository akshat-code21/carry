"""Abstract interfaces for all external service integrations.

These ABCs define clean contracts so implementations can be swapped
(e.g., switch from Anthropic to OpenAI, or from yfinance to a paid provider)
without touching any business logic.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date


# --- Data transfer objects ---


@dataclass
class TranscriptSegmentDTO:
    """A single timestamped segment of a transcript."""

    start_sec: float
    end_sec: float
    text: str


@dataclass
class ExtractedTheme:
    """A theme extracted by the LLM from a transcript chunk."""

    sector: str
    industry: str
    theme: str
    narrative: str
    sentiment: str  # bullish | bearish | neutral (overridden by FinBERT)
    confidence: float  # 0-1
    llm_sentiment: str | None = None  # Original LLM output (set by pipeline)
    finbert_confidence: float | None = None  # FinBERT max(P) (set by pipeline)


@dataclass
class ExtractedPrediction:
    """A prediction extracted by the LLM from a transcript chunk."""

    text: str
    ticker: str | None = None
    direction: str | None = None  # bullish | bearish | neutral (overridden by FinBERT)
    timeframe: str | None = None
    confidence: float | None = None
    llm_direction: str | None = None  # Original LLM output (set by pipeline)
    finbert_confidence: float | None = None  # FinBERT max(P) (set by pipeline)


@dataclass
class ExtractedEntities:
    """Named entities extracted from transcript."""

    people: list[str] = field(default_factory=list)
    companies: list[str] = field(default_factory=list)
    indices: list[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    """Full result of LLM analysis on a transcript chunk."""

    themes: list[ExtractedTheme] = field(default_factory=list)
    explicit_tickers: list[str] = field(default_factory=list)
    implicit_tickers: list[str] = field(default_factory=list)
    predictions: list[ExtractedPrediction] = field(default_factory=list)
    entities: ExtractedEntities = field(default_factory=ExtractedEntities)


@dataclass
class TickerMapping:
    """A ticker mapping suggested by the LLM for a theme."""

    ticker: str
    relevance_score: float  # 0-1
    reason: str


@dataclass
class FinBertResult:
    """Result of FinBERT sentiment classification on a text."""

    sentiment: str  # bullish | bearish | neutral
    confidence: float  # max(softmax probabilities), 0.0-1.0
    probabilities: dict  # {"positive": 0.85, "negative": 0.10, "neutral": 0.05}


@dataclass
class PricePoint:
    """A single day's price data."""

    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class VideoMetadata:
    """Metadata for a YouTube video."""

    video_id: str
    title: str
    description: str
    published_at: str  # ISO format
    duration_sec: int
    thumbnail_url: str
    view_count: int


@dataclass
class ChannelMetadata:
    """Metadata for a YouTube channel."""

    channel_id: str
    title: str
    description: str
    thumbnail_url: str


# --- Service interfaces ---


class YouTubeService(ABC):
    """Interface for YouTube data fetching."""

    @abstractmethod
    async def get_channel_info(self, channel_id: str) -> ChannelMetadata:
        """Fetch channel metadata."""

    @abstractmethod
    async def list_channel_videos(
        self, channel_id: str, max_results: int = 20
    ) -> list[VideoMetadata]:
        """List videos from a channel, most recent first."""

    @abstractmethod
    async def get_video_info(self, video_id: str) -> VideoMetadata:
        """Fetch metadata for a single video."""


class TranscriptSource(ABC):
    """Interface for fetching video transcripts."""

    @abstractmethod
    async def fetch_transcript(self, video_id: str) -> list[TranscriptSegmentDTO]:
        """Fetch transcript segments for a YouTube video."""


class LLMProvider(ABC):
    """Interface for LLM-based content analysis."""

    @abstractmethod
    async def analyze_transcript_chunk(
        self, segments: list[TranscriptSegmentDTO], video_title: str
    ) -> AnalysisResult:
        """Analyze a chunk of transcript segments and extract themes, predictions, etc."""

    @abstractmethod
    async def enrich_theme_tickers(
        self, theme_name: str, narrative: str
    ) -> list[TickerMapping]:
        """Given a theme and its narrative, suggest additional relevant tickers."""


class EmbeddingProvider(ABC):
    """Interface for generating text embeddings."""

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts. Returns list of vectors."""

    @abstractmethod
    def dimensions(self) -> int:
        """Return the dimensionality of the embedding vectors."""


class MarketDataSource(ABC):
    """Interface for stock/ETF market data."""

    @abstractmethod
    async def get_price_history(
        self, ticker: str, start: date, end: date
    ) -> list[PricePoint]:
        """Fetch daily price history for a ticker over a date range."""

    @abstractmethod
    async def get_price_at_date(self, ticker: str, target_date: date) -> float | None:
        """Get the close price on or near a specific date (forward-fills to next trading day)."""


class EconDataSource(ABC):
    """Interface for economic/macro data (FRED)."""

    @abstractmethod
    async def get_series(
        self, series_id: str, start: date, end: date
    ) -> list[tuple[date, float]]:
        """Fetch a FRED data series (e.g., FEDFUNDS, CPIAUCSL)."""
