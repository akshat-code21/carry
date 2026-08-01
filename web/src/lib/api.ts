export interface SamplePrediction {
  text: string;
  direction?: string;
  confidence?: number;
}

export interface StockDiscoveryResult {
  ticker: string;
  composite_score: number;
  theme_relevance: number;
  themes: string[];
  mention_count: number;
  avg_sentiment: number;
  prediction_count: number;
  avg_confidence: number;
  bullish_pct: number;
  bearish_pct: number;
  sample_predictions: SamplePrediction[];
  last_mentioned_at?: string;
  is_etf?: boolean;
}

export interface SearchResult {
  segments: {
    id: string;
    video_id: string;
    video_title?: string;
    channel_title?: string;
    youtube_video_id?: string;
    thumbnail_url?: string;
    start_sec: number;
    end_sec: number;
    text: string;
    rank: number;
    search_type: string;
  }[];
  predictions: Prediction[];
  stocks: StockDiscoveryResult[];
  themes: ThemeItem[];
  videos: Record<string, VideoItem>;
  channels: Record<string, ChannelItem>;
  query_intent: string;
  /** stocks | etfs — which instrument class discovery results represent */
  instrument_type?: string;
}

export interface ActivityEvent {
  id: string;
  event_type: "video_detected" | "video_processed" | "video_failed" | string;
  channel_id: string;
  video_id?: string | null;
  youtube_video_id: string;
  title: string;
  message: string;
  payload?: Record<string, unknown> | null;
  read_at?: string | null;
  created_at: string;
}

export interface VideoItem {
  id: string;
  title: string;
  youtube_video_id: string;
  channel_id: string;
  published_at: string;
  duration_sec: number;
  created_at?: string;
}

export interface TranscriptSegment {
  id: string;
  video_id: string;
  start_sec: number;
  end_sec: number;
  text: string;
}

export interface Prediction {
  id: string;
  video_id: string;
  ticker?: string | null;
  prediction_text: string;
  direction?: string | null;
  confidence?: number | null;
  accurate?: boolean | null;
  created_at: string;
  video_title?: string | null;
  youtube_video_id?: string | null;
  published_at?: string | null;
  channel_title?: string | null;
  performance?: Record<string, unknown>;
}

export interface VideoTheme {
  id: string;
  theme_id: string;
  name: string;
  narrative: string;
}

export interface VideoDetail extends VideoItem {
  segments: TranscriptSegment[];
  predictions: Prediction[];
  themes: VideoTheme[];
}

export interface ChannelItem {
  id: string;
  title: string;
  description: string;
  youtube_channel_id: string;
  created_at?: string;
}

export interface ChannelTopStock {
  ticker: string;
  weighted_relevance: number;
  total_mentions: number;
  avg_sentiment: number;
}

export interface ChannelDetail {
  channel: ChannelItem;
  videos: VideoItem[];
  top_stocks: ChannelTopStock[];
}

export interface TickerItem {
  ticker: string;
  is_etf: boolean;
  total_mentions: number;
  themes?: string[];
}

export interface TickerSentimentTimelineItem {
  date: string;
  bullish_count: number;
  bearish_count: number;
  total_count: number;
}

export interface TickerPricePoint {
  date: string;
  close: number;
  open?: number;
  high?: number;
  low?: number;
  volume?: number;
}

export interface TickerDetail {
  ticker: string;
  is_etf: boolean;
  predictions: Prediction[];
  themes: ThemeItem[];
  performance?: {
    prediction_id: string;
    price_at_video: number;
    price_1w?: number;
    created_at?: string;
  }[];
}

export interface ThemeTickerInfo {
  ticker: string;
  relevance_score: number;
  source: string;
}

export interface SubThemeNode {
  id: string;
  name: string;
  description?: string | null;
  level: "theme";
  tickers?: ThemeTickerInfo[];
}

export interface IndustryThemeNode {
  id: string;
  name: string;
  description?: string | null;
  level: "industry";
  themes: SubThemeNode[];
}

export interface SectorThemeNode {
  id: string;
  name: string;
  description?: string | null;
  level: "sector" | "narrative";
  industries?: IndustryThemeNode[];
}

export interface ThemeItem {
  id: string;
  name: string;
  level: "sector" | "industry" | "theme" | "narrative";
  description?: string | null;
  parent_id?: string | null;
}

export interface ThemeMappedTicker {
  ticker: string;
  source: string;
  relevance_score: number;
}

export interface ThemeVideoMention {
  id: string;
  title: string;
  mention_text: string;
  published_at: string;
  sentiment: string;
}

export interface ThemeDetail {
  theme: ThemeItem;
  mapped_tickers: ThemeMappedTicker[];
  videos: ThemeVideoMention[];
}


/* ── Market Chatter Types (TickerFlow) ────────────────────────── */

export interface MCDashboardSummary {
  total_mentions: number;
  tracked_tickers: number;
  tracked_stocks: number;
  tracked_etfs: number;
  overall_bullish_pct: number;
}

export interface MCPlatformBreakdown {
  reddit_mentions: number;
  x_mentions: number;
  news_mentions: number;
  stocktwits_mentions: number;
  total_mentions: number;
}

export interface MCDashboardTickerItem {
  symbol: string;
  company_name: string;
  is_etf: boolean;
  mentions: number;
  bullish_pct: number;
}

export interface MCDashboardData {
  summary: MCDashboardSummary;
  platform_breakdown: MCPlatformBreakdown;
  top_stocks: MCDashboardTickerItem[];
  top_etfs: MCDashboardTickerItem[];
  bullish_leaders: MCDashboardTickerItem[];
  bearish_laggards: MCDashboardTickerItem[];
}

export const api = {
  async search(query: string, type: "keyword" | "semantic" | "hybrid" = "hybrid"): Promise<SearchResult> {
    const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&type=${type}`);
    if (!res.ok) throw new Error("Search failed");
    return res.json();
  },

  async getVideos(): Promise<VideoItem[]> {
    const res = await fetch("/api/videos");
    if (!res.ok) throw new Error("Failed to fetch videos");
    return res.json();
  },

  async getVideo(id: string): Promise<VideoDetail> {
    const res = await fetch(`/api/videos/${id}`);
    if (!res.ok) throw new Error("Failed to fetch video");
    return res.json();
  },

  async getChannels(): Promise<ChannelItem[]> {
    const res = await fetch("/api/channels");
    if (!res.ok) throw new Error("Failed to fetch channels");
    return res.json();
  },

  async getChannel(id: string): Promise<ChannelDetail> {
    const res = await fetch(`/api/channels/${id}`);
    if (!res.ok) throw new Error("Failed to fetch channel");
    const channel = await res.json();

    const [videosRes, stocksRes] = await Promise.all([
      fetch(`/api/videos?channel_id=${id}`),
      fetch(`/api/channels/${id}/top-stocks`),
    ]);

    const videos = videosRes.ok ? await videosRes.json() : [];
    const top_stocks = stocksRes.ok ? await stocksRes.json() : [];

    return { channel, videos, top_stocks };
  },

  async getTickers(): Promise<TickerItem[]> {
    const res = await fetch("/api/tickers");
    if (!res.ok) throw new Error("Failed to fetch tickers");
    return res.json();
  },

  async getTopETFs(): Promise<TickerItem[]> {
    const res = await fetch("/api/tickers/top-etfs");
    if (!res.ok) throw new Error("Failed to fetch top ETFs");
    return res.json();
  },

  async getTicker(ticker: string): Promise<TickerDetail> {
    const res = await fetch(`/api/tickers/${ticker}`);
    if (!res.ok) throw new Error("Failed to fetch ticker");
    return res.json();
  },

  async getTickerSentimentTimeline(ticker: string, days = 30): Promise<TickerSentimentTimelineItem[]> {
    const res = await fetch(`/api/tickers/${ticker}/sentiment-timeline?days=${days}`);
    if (!res.ok) throw new Error("Failed to fetch sentiment timeline");
    return res.json();
  },

  async getTickerPriceHistory(ticker: string, days = 30): Promise<TickerPricePoint[]> {
    const res = await fetch(`/api/tickers/${ticker}/price-history?days=${days}`);
    if (!res.ok) throw new Error("Failed to fetch price history");
    return res.json();
  },

  async getThemes(): Promise<SectorThemeNode[]> {
    const res = await fetch("/api/themes");
    if (!res.ok) throw new Error("Failed to fetch themes");
    return res.json();
  },

  async getTheme(id: string): Promise<ThemeDetail> {
    const res = await fetch(`/api/themes/${id}`);
    if (!res.ok) throw new Error("Failed to fetch theme");
    const theme = await res.json();

    const [tickersRes, videosRes] = await Promise.all([
      fetch(`/api/themes/${id}/tickers`),
      fetch(`/api/themes/${id}/videos`),
    ]);

    const mapped_tickers = tickersRes.ok ? await tickersRes.json() : [];
    const videos = videosRes.ok ? await videosRes.json() : [];

    return { theme, mapped_tickers, videos };
  },


  async addChannel(youtubeChannelId: string, maxVideos = 50): Promise<{ task_id: string }> {
    const res = await fetch("/api/channels", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ youtube_channel_id: youtubeChannelId, max_videos: maxVideos }),
    });
    if (!res.ok) throw new Error("Failed to add channel");
    return res.json();
  },

  async backfillChannel(youtubeChannelId: string, maxVideos = 20): Promise<{ task_id: string }> {
    const res = await fetch("/api/channels/backfill", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        youtube_channel_id: youtubeChannelId,
        max_videos: maxVideos,
      }),
    });
    if (!res.ok) throw new Error("Failed to trigger backfill");
    return res.json();
  },

  async ingestSingleVideo(channelDbId: string, youtubeVideoId: string): Promise<{ task_id: string }> {
    const res = await fetch(`/api/channels/${channelDbId}/ingest-video`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ youtube_video_id: youtubeVideoId }),
    });
    if (!res.ok) throw new Error("Failed to trigger video ingestion");
    return res.json();
  },

  async getActivity(opts?: { limit?: number; unreadOnly?: boolean }): Promise<ActivityEvent[]> {
    const params = new URLSearchParams();
    if (opts?.limit) params.set("limit", String(opts.limit));
    if (opts?.unreadOnly) params.set("unread_only", "true");
    const qs = params.toString() ? `?${params.toString()}` : "";
    const res = await fetch(`/api/activity${qs}`);
    if (!res.ok) throw new Error("Failed to fetch activity");
    return res.json();
  },

  async getActivityUnreadCount(): Promise<{ count: number }> {
    const res = await fetch("/api/activity/unread-count");
    if (!res.ok) throw new Error("Failed to fetch unread count");
    return res.json();
  },

  async markActivityRead(eventId: string): Promise<ActivityEvent> {
    const res = await fetch(`/api/activity/${eventId}/read`, { method: "POST" });
    if (!res.ok) throw new Error("Failed to mark activity read");
    return res.json();
  },

  async markAllActivityRead(): Promise<{ marked_read: number }> {
    const res = await fetch("/api/activity/read-all", { method: "POST" });
    if (!res.ok) throw new Error("Failed to mark all activity read");
    return res.json();
  },

  async getTickerFlowDashboard(periodDays = 7): Promise<MCDashboardData> {
    let res = await fetch(`/api/v1/tickerflow/dashboard?period_days=${periodDays}`);
    if (!res.ok) {
      res = await fetch(`/api/v1/market-chatter/dashboard?days=${periodDays}`);
    }
    if (!res.ok) {
      res = await fetch(`/api/market-chatter/dashboard?days=${periodDays}`);
    }
    if (!res.ok) throw new Error("Failed to fetch market chatter dashboard");
    return res.json();
  },
};
