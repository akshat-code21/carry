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
  predictions: any[];
  stocks: StockDiscoveryResult[];
  themes: any[];
  videos: Record<string, any>;
  channels: Record<string, any>;
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

export const api = {
  async search(query: string, type: "keyword" | "semantic" | "hybrid" = "hybrid"): Promise<SearchResult> {
    const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&type=${type}`);
    if (!res.ok) throw new Error("Search failed");
    return res.json();
  },

  async getVideos() {
    const res = await fetch("/api/videos");
    if (!res.ok) throw new Error("Failed to fetch videos");
    return res.json();
  },

  async getVideo(id: string) {
    const res = await fetch(`/api/videos/${id}`);
    if (!res.ok) throw new Error("Failed to fetch video");
    return res.json();
  },

  async getChannels() {
    const res = await fetch("/api/channels");
    if (!res.ok) throw new Error("Failed to fetch channels");
    return res.json();
  },

  async getChannel(id: string) {
    const [channelRes, videosRes, stocksRes] = await Promise.all([
      fetch(`/api/channels/${id}`),
      fetch(`/api/videos?channel_id=${id}`),
      fetch(`/api/channels/${id}/top-stocks`)
    ]);

    if (!channelRes.ok) throw new Error("Failed to fetch channel");

    const channel = await channelRes.json();
    const videos = videosRes.ok ? await videosRes.json() : [];
    const top_stocks = stocksRes.ok ? await stocksRes.json() : [];

    return { channel, videos, top_stocks };
  },

  async getTickers() {
    const res = await fetch("/api/tickers");
    if (!res.ok) throw new Error("Failed to fetch tickers");
    return res.json();
  },

  async getTopETFs() {
    const res = await fetch("/api/tickers/top-etfs");
    if (!res.ok) throw new Error("Failed to fetch top ETFs");
    return res.json();
  },

  async getTicker(ticker: string) {
    const res = await fetch(`/api/tickers/${ticker}`);
    if (!res.ok) throw new Error("Failed to fetch ticker");
    return res.json();
  },

  async getTickerSentimentTimeline(ticker: string, days?: number) {
    const qs = days ? `?days=${days}` : "";
    const res = await fetch(`/api/tickers/${ticker}/sentiment-timeline${qs}`);
    if (!res.ok) throw new Error("Failed to fetch ticker sentiment timeline");
    return res.json();
  },

  async getTickerPriceHistory(ticker: string, days?: number) {
    const qs = days ? `?days=${days}` : "";
    const res = await fetch(`/api/tickers/${ticker}/price-history${qs}`);
    if (!res.ok) throw new Error("Failed to fetch ticker price history");
    return res.json();
  },
  async getThemes() {
    const res = await fetch("/api/themes");
    if (!res.ok) throw new Error("Failed to fetch themes");
    return res.json();
  },

  async getTheme(id: string) {
    const res = await fetch(`/api/themes/${id}`);
    if (!res.ok) throw new Error("Failed to fetch theme");
    return res.json();
  },

  async backfillChannel(youtubeChannelId: string, maxVideos: number = 20) {
    const res = await fetch("/api/pipeline/backfill", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        youtube_channel_id: youtubeChannelId,
        max_videos: maxVideos,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to trigger backfill");
    }
    return res.json();
  },

  async ingestSingleVideo(channelId: string, youtubeVideoId: string) {
    const res = await fetch("/api/pipeline/ingest-single-video", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        channel_id: channelId,
        youtube_video_id: youtubeVideoId,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to trigger video ingestion");
    }
    return res.json();
  },

  async getActivity(opts?: { limit?: number; unreadOnly?: boolean; offset?: number }) {
    const params = new URLSearchParams();
    if (opts?.limit) params.set("limit", String(opts.limit));
    if (opts?.offset) params.set("offset", String(opts.offset));
    if (opts?.unreadOnly) params.set("unread_only", "true");
    const qs = params.toString();
    const res = await fetch(`/api/activity${qs ? `?${qs}` : ""}`);
    if (!res.ok) throw new Error("Failed to fetch activity");
    return res.json() as Promise<ActivityEvent[]>;
  },

  async getActivityUnreadCount() {
    const res = await fetch("/api/activity/unread-count");
    if (!res.ok) throw new Error("Failed to fetch unread count");
    return res.json() as Promise<{ count: number }>;
  },

  async markActivityRead(eventId: string) {
    const res = await fetch(`/api/activity/${eventId}/read`, { method: "POST" });
    if (!res.ok) throw new Error("Failed to mark activity read");
    return res.json() as Promise<ActivityEvent>;
  },

  async markAllActivityRead() {
    const res = await fetch("/api/activity/read-all", { method: "POST" });
    if (!res.ok) throw new Error("Failed to mark all activity read");
    return res.json() as Promise<{ marked_read: number }>;
  },

  async getTickerFlowDashboard(periodDays = 7) {
    const res = await fetch(`/api/v1/tickerflow/dashboard?period_days=${periodDays}`);
    if (!res.ok) throw new Error("Failed to fetch TickerFlow dashboard");
    return res.json() as Promise<MCDashboardData>;
  },
};

export interface MCDashboardSummary {
  total_mentions: number;
  tracked_tickers: number;
  tracked_stocks: number;
  tracked_etfs: number;
  avg_market_sentiment: number;
  overall_bullish_pct: number;
}

export interface MCDashboardTickerItem {
  symbol: string;
  company_name?: string | null;
  is_etf: boolean;
  mentions: number;
  buzz_score: number;
  sentiment_score: number;
  bullish_pct: number;
  trend: string;
  top_catalyst?: string | null;
  last_updated?: string | null;
}

export interface MCPlatformBreakdown {
  reddit_mentions: number;
  x_mentions: number;
  news_mentions: number;
  stocktwits_mentions: number;
  total_mentions: number;
}

export interface MCDashboardData {
  as_of: string;
  period_days: number;
  summary: MCDashboardSummary;
  top_stocks: MCDashboardTickerItem[];
  top_etfs: MCDashboardTickerItem[];
  bullish_leaders: MCDashboardTickerItem[];
  bearish_laggards: MCDashboardTickerItem[];
  platform_breakdown: MCPlatformBreakdown;
  driver_cards: any[];
}
