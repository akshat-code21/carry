"""Pydantic schemas for API request/response models."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# --- Channel schemas ---


class ChannelResponse(BaseModel):
    id: UUID
    youtube_channel_id: str
    title: str
    description: str | None = None
    thumbnail_url: str | None = None
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

    model_config = {"from_attributes": True}


class TickerDetailResponse(TickerResponse):
    predictions: list[PredictionWithPerformance] = []
    themes: list[ThemeResponse] = []


class TickerSentimentDailyPoint(BaseModel):
    """Bullish/bearish/neutral mention counts for a ticker on a single day."""

    date: str
    bullish_count: int = 0
    bearish_count: int = 0
    neutral_count: int = 0
    total_count: int = 0


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


class SearchResponse(BaseModel):
    segments: list[SearchSegmentResult] = []
    predictions: list[SearchPredictionResult] = []
    videos: dict[str, dict] = {}
    channels: dict[str, dict] = {}
    total: int = 0


class StockSearchResult(BaseModel):
    ticker: str
    total_relevance: float
    themes: list[str] = []


# --- Pipeline schemas ---


class ProcessVideoRequest(BaseModel):
    video_id: UUID


class BackfillRequest(BaseModel):
    youtube_channel_id: str
    max_videos: int = Field(default=20, ge=1, le=500)


class PipelineStatusResponse(BaseModel):
    task_id: str
    status: str


# Resolve forward references
VideoDetailResponse.model_rebuild()
PredictionWithPerformance.model_rebuild()
ThemeHierarchyResponse.model_rebuild()
