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
  themes: any[];
  videos: Record<string, any>;
  channels: Record<string, any>;
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

  async getTicker(ticker: string) {
    const res = await fetch(`/api/tickers/${ticker}`);
    if (!res.ok) throw new Error("Failed to fetch ticker");
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
};
