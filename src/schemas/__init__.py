"""Pydantic schemas for API request/response models."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.schemas.market_chatter import MCTickerResponse, SignalSummary, SourceCard

# --- Channel schemas ---


class ChannelResponse(BaseModel):
    id: UUID
    youtube_channel_id: str
    title: str
    description: str | None = None
    thumbnail_url: str | None = None
    channel_type: str = "individual"  # individual | institutional
    video_count: int | None = None
    last_checked_at: datetime | None = None
    websub_subscribed_at: datetime | None = None
    websub_lease_expires_at: datetime | None = None
    websub_status: str = "pending"
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Video schemas ---


class VideoResponse(BaseModel):
    id: UUID
    channel_id: UUID
    youtube_video_id: str
    title: str
    description: str | None = None
    published_at: datetime | None = None
    duration_sec: int | None = None
    thumbnail_url: str | None = None
    view_count: int | None = None
    transcript_status: str
    processed: bool
    ingest_status: str = "discovered"
    transcript_attempts: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class VideoDetailResponse(VideoResponse):
    predictions: list["PredictionResponse"] = []
    theme_mentions: list["ThemeMentionResponse"] = []


# --- Prediction schemas ---


class PredictionResponse(BaseModel):
    id: UUID
    video_id: UUID
    ticker: str | None = None
    prediction_text: str
    direction: str | None = None
    confidence: float | None = None
    timeframe_hint: str | None = None
    extracted_by: str | None = None
    accurate: bool | None = None
    created_at: datetime
    video_title: str | None = None
    youtube_video_id: str | None = None
    published_at: datetime | None = None
    channel_title: str | None = None

    model_config = {"from_attributes": True}


class PredictionWithPerformance(PredictionResponse):
    performance: "PerformanceResponse | None" = None


# --- Performance schemas ---


class PerformanceResponse(BaseModel):
    id: UUID
    ticker: str
    price_at_video: float | None = None
    price_1d: float | None = None
    price_1w: float | None = None
    price_1m: float | None = None
    return_1d: float | None = None
    return_1w: float | None = None
    return_1m: float | None = None
    direction_accurate: bool | None = None

    model_config = {"from_attributes": True}


# --- Theme schemas ---


class ThemeResponse(BaseModel):
    id: UUID
    parent_id: UUID | None = None
    level: str
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}


class ThemeMentionResponse(BaseModel):
    id: UUID
    theme_id: UUID
    sentiment: str | None = None
    relevance_score: float | None = None
    mention_text: str | None = None
    narrative: str | None = None

    model_config = {"from_attributes": True}


class ThemeTickerMappingResponse(BaseModel):
    ticker: str
    relevance_score: float | None = None
    source: str

    model_config = {"from_attributes": True}


class ThemeHierarchyResponse(BaseModel):
    """Hierarchical theme tree response."""

    id: str
    name: str
    description: str | None = None
    level: str
    industries: list["IndustryNode"] | None = None
    themes: list["ThemeNode"] | None = None


class IndustryNode(BaseModel):
    id: str
    name: str
    description: str | None = None
    level: str
    themes: list["ThemeNode"] = []


class ThemeNode(BaseModel):
    id: str
    name: str
    description: str | None = None
    level: str
    tickers: list[ThemeTickerMappingResponse] = []


# --- Ticker schemas ---


class TickerResponse(BaseModel):
    ticker: str
    total_mentions: int = 0
    explicit_mentions: int = 0
    implicit_mentions: int = 0
    avg_sentiment: float | None = None
    weighted_relevance: float | None = None
    last_mentioned_at: datetime | None = None
    is_etf: bool = False

    model_config = {"from_attributes": True}


class TickerDetailResponse(TickerResponse):
    predictions: list[PredictionWithPerformance] = []
    themes: list[ThemeResponse] = []
    # TickerFlow social-sentiment bundle (signal, source cards, chart); None when unavailable
    social: MCTickerResponse | None = None
    # Blended YouTube + social sentiment (-1..1); falls back to avg_sentiment
    combined_avg_sentiment: float | None = None
    # Mentions collected from TickerFlow social sources (Reddit/X/News)
    social_mentions: int | None = None


class TickerSentimentDailyPoint(BaseModel):
    """Bullish/bearish/neutral mention counts for a ticker on a single day."""

    date: str
    bullish_count: int = 0
    bearish_count: int = 0
    neutral_count: int = 0
    total_count: int = 0


class PricePointResponse(BaseModel):
    """A single day's OHLCV price data for a ticker."""

    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


# --- Search schemas ---


class SearchRequest(BaseModel):
    q: str = Field(..., min_length=1, description="Search query")
    type: str = Field(default="hybrid", description="Search type: keyword, semantic, hybrid")
    channel: UUID | None = None
    ticker: str | None = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class SearchSegmentResult(BaseModel):
    id: str
    video_id: str
    start_sec: float
    end_sec: float
    text: str
    rank: float
    search_type: str
    video_title: str | None = None
    channel_title: str | None = None
    youtube_video_id: str | None = None
    thumbnail_url: str | None = None


class SearchPredictionResult(BaseModel):
    id: str
    video_id: str
    prediction_text: str
    ticker: str | None = None
    direction: str | None = None
    confidence: float | None = None
    accurate: bool | None = None
    rank: float
    search_type: str
    video_title: str | None = None
    channel_title: str | None = None
    youtube_video_id: str | None = None


class SamplePrediction(BaseModel):
    text: str
    direction: str | None = None
    confidence: float | None = None


class SocialTickerSnapshot(BaseModel):
    """Compact TickerFlow social-sentiment snapshot (Reddit/X/News) used on
    search result cards. Derived from a full MCTickerResponse without the
    per-day chart to keep payloads small."""

    symbol: str
    data_status: str | None = None
    as_of: datetime | None = None
    signal: SignalSummary | None = None
    sources: list[SourceCard] = []
    total_mentions: int | None = None
    buzz_score: float | None = None
    sentiment_score: float | None = None
    bullish_pct: float | None = None
    bearish_pct: float | None = None


class SocialCoverageStats(BaseModel):
    """Aggregated TickerFlow social mentions for the coverage window."""

    symbol: str
    mentions: int = 0
    bullish_pct: float | None = None
    bearish_pct: float | None = None
    sentiment_score: float | None = None
    by_source: dict[str, int] = {}
    available: bool = False


class StockDiscoveryResult(BaseModel):
    """Rich stock discovery result with multi-signal scoring."""

    ticker: str
    composite_score: float = 0.0
    theme_relevance: float = 0.0
    themes: list[str] = []
    mention_count: int = 0
    avg_sentiment: float = 0.0
    prediction_count: int = 0
    avg_confidence: float = 0.0
    bullish_pct: float = 0.0
    bearish_pct: float = 0.0
    sample_predictions: list[SamplePrediction] = []
    last_mentioned_at: str | None = None
    is_etf: bool = False
    # TickerFlow social-sentiment context (Reddit/X/News); None when unavailable
    social: SocialTickerSnapshot | None = None


class SegmentGroup(BaseModel):
    """Transcript segments consolidated per video for grouped search display."""

    video_id: str
    youtube_video_id: str | None = None
    video_title: str | None = None
    channel_id: str | None = None
    channel_title: str | None = None
    published_at: str | None = None
    thumbnail_url: str | None = None
    hit_count: int = 0
    best_rank: float = 0.0
    top_segments: list[SearchSegmentResult] = []
    remaining_segments: list[SearchSegmentResult] = []


class SearchResponse(BaseModel):
    segments: list[SearchSegmentResult] = []
    groups: list[SegmentGroup] = []
    predictions: list[SearchPredictionResult] = []
    stocks: list[StockDiscoveryResult] = []
    videos: dict[str, dict] = {}
    channels: dict[str, dict] = {}
    total: int = 0
    # More distinct video groups available beyond the current limit
    has_more: bool = False
    query_intent: str = "factual_search"
    # stocks | etfs — instrument class inferred for discovery results
    instrument_type: str = "stocks"


# Legacy alias for the /api/search/stocks endpoint
class StockSearchResult(BaseModel):
    ticker: str
    total_relevance: float = 0.0
    themes: list[str] = []


class AnswerCitation(BaseModel):
    """A transcript segment cited by a synthesized search answer."""

    segment_id: str
    video_id: str
    start_sec: float
    text: str
    video_title: str | None = None
    channel_title: str | None = None
    youtube_video_id: str | None = None


class SearchAnswerResponse(BaseModel):
    """LLM-synthesized answer for a search query, with clip citations."""

    query: str
    summary: str = ""
    key_points: list[str] = []
    citations: list[AnswerCitation] = []
    # False => client should hide the answer card entirely
    available: bool = False
    cached: bool = False
    # TickerFlow social-sentiment snapshots for tickers detected in the query
    social_context: list[SocialTickerSnapshot] = []


class WeeklyVolumePoint(BaseModel):
    """Video count for one 7-day slice of the coverage window."""

    week_start: str  # ISO date
    count: int


class SearchCoverageResponse(BaseModel):
    """Coverage intelligence: how much content discusses a query topic."""

    query: str
    total_videos: int = 0
    positive: int = 0
    neutral: int = 0
    negative: int = 0
    weekly_volume: list[WeeklyVolumePoint] = []
    # Null when <2 weeks of data or previous week had zero videos
    wow_delta_pct: float | None = None
    window_days: int = 14
    # TickerFlow social-sentiment stats for the resolved ticker, if any
    social: SocialCoverageStats | None = None


# --- Pipeline schemas ---


class ProcessVideoRequest(BaseModel):
    video_id: UUID


class IngestSingleVideoRequest(BaseModel):
    channel_id: UUID = Field(..., description="Database Channel UUID")
    youtube_video_id: str = Field(..., description="YouTube Video ID (e.g. _RXAoo-V9Nw)")


class BackfillRequest(BaseModel):
    youtube_channel_id: str
    max_videos: int = Field(default=20, ge=1, le=500)


class PipelineStatusResponse(BaseModel):
    task_id: str
    status: str


class SimulateWebSubRequest(BaseModel):
    """Fake a YouTube WebSub push for local testing (no real channel upload)."""

    youtube_channel_id: str | None = Field(
        default=None,
        description="YouTube channel id (UC...). Provide this or channel_id.",
    )
    channel_id: UUID | None = Field(
        default=None,
        description="Internal channel UUID. Provide this or youtube_channel_id.",
    )
    youtube_video_id: str = Field(
        ...,
        description=(
            "YouTube video id to pretend was just uploaded. "
            "Use a real video id not yet in the DB for full ingest, "
            "or any unused id to only test detection."
        ),
    )
    title: str = Field(
        default="Simulated new upload",
        description="Title shown in the Atom payload / activity feed",
    )
    mode: str = Field(
        default="full",
        description=(
            "'full' = discovery + auto-ingest/process (like a real push). "
            "'discovery_only' = create video + video_detected only (no LLM)."
        ),
    )


class SimulateWebSubResponse(BaseModel):
    task_id: str
    status: str
    mode: str
    youtube_channel_id: str
    youtube_video_id: str
    title: str
    message: str


# --- Activity schemas ---


class ActivityEventResponse(BaseModel):
    id: UUID
    event_type: str
    channel_id: UUID
    video_id: UUID | None = None
    youtube_video_id: str
    title: str
    message: str
    payload: dict | None = None
    read_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ActivityUnreadCountResponse(BaseModel):
    count: int


# --- Auth / user schemas ---


class UserProfileResponse(BaseModel):
    """Current-user profile returned by GET /api/auth/me."""

    id: UUID
    clerk_user_id: str
    email: str
    full_name: str | None = None
    image_url: str | None = None
    role: str  # admin | user
    status: str  # active | pending_invite | deactivated
    created_at: datetime
    last_seen_at: datetime

    model_config = {"from_attributes": True}


class RedeemInviteRequest(BaseModel):
    code: str = Field(min_length=1, max_length=64)


class RedeemInviteResponse(BaseModel):
    ok: bool
    user: UserProfileResponse


# Resolve forward references
VideoDetailResponse.model_rebuild()
PredictionWithPerformance.model_rebuild()
ThemeHierarchyResponse.model_rebuild()
