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

export interface SearchSegment {
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
}

export interface SegmentGroup {
  video_id: string;
  youtube_video_id?: string | null;
  video_title?: string | null;
  channel_id?: string | null;
  channel_title?: string | null;
  published_at?: string | null;
  thumbnail_url?: string | null;
  hit_count: number;
  best_rank: number;
  top_segments: SearchSegment[];
  remaining_segments: SearchSegment[];
}

export interface SearchResult {
  segments: SearchSegment[];
  groups: SegmentGroup[];
  predictions: Prediction[];
  stocks: StockDiscoveryResult[];
  themes: ThemeItem[];
  videos: Record<string, VideoItem>;
  channels: Record<string, ChannelItem>;
  total: number;
  /** More distinct video groups available beyond the current limit */
  has_more?: boolean;
  query_intent: string;
  /** stocks | etfs — which instrument class discovery results represent */
  instrument_type?: string;
}

export interface AnswerCitation {
  segment_id: string;
  video_id: string;
  start_sec: number;
  text: string;
  video_title?: string | null;
  channel_title?: string | null;
  youtube_video_id?: string | null;
}

export interface SearchAnswerResponse {
  query: string;
  summary: string;
  key_points: string[];
  citations: AnswerCitation[];
  /** False => hide the answer card entirely */
  available: boolean;
  cached?: boolean;
}

export interface WeeklyVolumePoint {
  week_start: string; // ISO date
  count: number;
}

export interface SearchCoverageResponse {
  query: string;
  total_videos: number;
  positive: number;
  neutral: number;
  negative: number;
  weekly_volume: WeeklyVolumePoint[];
  /** Null when <2 weeks of data or previous week had zero videos */
  wow_delta_pct?: number | null;
  window_days: number;
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

export const getApiBaseUrl = (): string => {
  const envUrl = process.env.NEXT_PUBLIC_API_URL;
  if (envUrl && envUrl.trim()) {
    const clean = envUrl.trim().replace(/\/$/, "");
    return clean.endsWith("/api") ? clean : `${clean}/api`;
  }
  return "/api";
};

export const API_BASE_URL = getApiBaseUrl();

/* ── Auth-aware request plumbing ─────────────────────────────────── */

import { ApiError, getAuthToken } from "@/lib/auth-client";

async function request<T>(path: string, init: RequestInit = {}, opts?: { auth?: boolean }): Promise<T> {
  const headers = new Headers(init.headers);
  const needsAuth = opts?.auth !== false; // default: attach token when available
  if (needsAuth) {
    const token = await getAuthToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(0, "network_error", "Network request failed");
  }

  if (!res.ok) {
    let code = "request_failed";
    let message = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (typeof body?.detail === "object" && body.detail?.code) {
        code = body.detail.code;
        message = body.detail.message || message;
      } else if (typeof body?.detail === "string") {
        code = res.status === 403 ? "forbidden" : code;
        message = body.detail;
      }
    } catch {
      // non-JSON body
    }
    throw new ApiError(res.status, code, message);
  }

  return res.json() as Promise<T>;
}

/** True when the error means "sign in again". */
export function isAuthError(err: unknown): err is ApiError {
  return err instanceof ApiError && (err.status === 401 || err.code === "unauthorized");
}

/** True when the account exists but has not redeemed an invite yet. */
export function isInviteRequired(err: unknown): err is ApiError {
  return err instanceof ApiError && err.code === "invite_required";
}

export const api = {
  async search(
    query: string,
    type: "keyword" | "semantic" | "hybrid" = "hybrid",
    sort: "relevance" | "recent" = "relevance",
    limit = 20,
  ): Promise<SearchResult> {
    return request(
      `/search?q=${encodeURIComponent(query)}&type=${type}&sort=${sort}&limit=${limit}`,
    );
  },

  async searchAnswer(query: string, segmentIds?: string[]): Promise<SearchAnswerResponse> {
    const params = new URLSearchParams({ q: query });
    if (segmentIds?.length) {
      params.set("segment_ids", segmentIds.join(","));
    }
    return request(`/search/answer?${params.toString()}`);
  },

  async searchCoverage(
    query: string,
    segmentIds?: string[],
    windowDays = 14,
  ): Promise<SearchCoverageResponse> {
    const params = new URLSearchParams({ q: query, window_days: String(windowDays) });
    if (segmentIds?.length) {
      params.set("segment_ids", segmentIds.join(","));
    }
    return request(`/search/coverage?${params.toString()}`);
  },

  async getVideos(): Promise<VideoItem[]> {
    return request("/videos");
  },

  async getVideo(id: string): Promise<VideoDetail> {
    return request(`/videos/${id}`);
  },

  async getChannels(): Promise<ChannelItem[]> {
    return request("/channels");
  },

  async getChannel(id: string): Promise<ChannelDetail> {
    const channel = await request<ChannelItem>(`/channels/${id}`);

    const [videos, top_stocks] = await Promise.all([
      request<VideoItem[]>(`/videos?channel_id=${id}`).catch(() => []),
      request<ChannelTopStock[]>(`/channels/${id}/top-stocks`).catch(() => []),
    ]);

    return { channel, videos, top_stocks };
  },

  async getTickers(): Promise<TickerItem[]> {
    return request("/tickers");
  },

  async getTopETFs(): Promise<TickerItem[]> {
    return request("/tickers/top-etfs");
  },

  async getTicker(ticker: string): Promise<TickerDetail> {
    return request(`/tickers/${ticker}`);
  },

  async getTickerSentimentTimeline(ticker: string, days = 30): Promise<TickerSentimentTimelineItem[]> {
    return request(`/tickers/${ticker}/sentiment-timeline?days=${days}`);
  },

  async getTickerPriceHistory(ticker: string, days = 30): Promise<TickerPricePoint[]> {
    return request(`/tickers/${ticker}/price-history?days=${days}`);
  },

  async getThemes(): Promise<SectorThemeNode[]> {
    return request("/themes");
  },

  async getTheme(id: string): Promise<ThemeDetail> {
    const theme = await request<ThemeItem>(`/themes/${id}`);

    const [mapped_tickers, videos] = await Promise.all([
      request<ThemeMappedTicker[]>(`/themes/${id}/tickers`).catch(() => []),
      request<ThemeVideoMention[]>(`/themes/${id}/videos`).catch(() => []),
    ]);

    return { theme, mapped_tickers, videos };
  },


  async addChannel(youtubeChannelId: string, maxVideos = 50): Promise<{ task_id: string }> {
    return request("/pipeline/backfill", {
      method: "POST",
      body: JSON.stringify({ youtube_channel_id: youtubeChannelId, max_videos: maxVideos }),
    });
  },

  async backfillChannel(youtubeChannelId: string, maxVideos = 20): Promise<{ task_id: string }> {
    return request("/pipeline/backfill", {
      method: "POST",
      body: JSON.stringify({
        youtube_channel_id: youtubeChannelId,
        max_videos: maxVideos,
      }),
    });
  },

  async ingestSingleVideo(channelDbId: string, youtubeVideoId: string): Promise<{ task_id: string }> {
    return request("/pipeline/ingest-single-video", {
      method: "POST",
      body: JSON.stringify({ channel_id: channelDbId, youtube_video_id: youtubeVideoId }),
    });
  },

  async getActivity(opts?: { limit?: number; unreadOnly?: boolean }): Promise<ActivityEvent[]> {
    const params = new URLSearchParams();
    if (opts?.limit) params.set("limit", String(opts.limit));
    if (opts?.unreadOnly) params.set("unread_only", "true");
    const qs = params.toString() ? `?${params.toString()}` : "";
    return request(`/activity${qs}`);
  },

  async getActivityUnreadCount(): Promise<{ count: number }> {
    return request("/activity/unread-count");
  },

  async markActivityRead(eventId: string): Promise<ActivityEvent> {
    return request(`/activity/${eventId}/read`, { method: "POST" });
  },

  async markAllActivityRead(): Promise<{ marked_read: number }> {
    return request("/activity/read-all", { method: "POST" });
  },

  async getTickerFlowDashboard(periodDays = 7): Promise<MCDashboardData> {
    try {
      return await request<MCDashboardData>(`/v1/tickerflow/dashboard?period_days=${periodDays}`);
    } catch (firstErr) {
      try {
        return await request<MCDashboardData>(`/v1/market-chatter/dashboard?days=${periodDays}`);
      } catch {
        // fall through to legacy alias
        void firstErr;
        return request<MCDashboardData>(`/market-chatter/dashboard?days=${periodDays}`);
      }
    }
  },

  /* ── Auth & account ──────────────────────────────────────────────── */

  async getMe(): Promise<UserProfile> {
    return request("/auth/me");
  },

  async redeemInvite(code: string): Promise<{ ok: boolean; user: UserProfile }> {
    return request("/auth/redeem-invite", {
      method: "POST",
      body: JSON.stringify({ code }),
    });
  },

  /* ── Usage analytics ─────────────────────────────────────────────── */

  async sendClientEvents(events: { type: string; data?: Record<string, unknown> }[]): Promise<void> {
    if (!events.length) return;
    await request(
      "/usage/events",
      { method: "POST", body: JSON.stringify({ events }) },
    ).catch(() => undefined); // never let tracking break the UI
  },

  async getMyUsage(days = 30): Promise<MyUsageResponse> {
    return request(`/usage/me?days=${days}`);
  },

  /* ── Admin ───────────────────────────────────────────────────────── */

  async createInvite(body: CreateInviteRequest): Promise<InviteDto> {
    return request("/admin/invites", { method: "POST", body: JSON.stringify(body) });
  },

  async listInvites(): Promise<InviteDto[]> {
    return request("/admin/invites");
  },

  async revokeInvite(inviteId: string): Promise<{ ok: boolean }> {
    return request(`/admin/invites/${inviteId}`, { method: "DELETE" });
  },

  async getPlatformOverview(days = 30): Promise<PlatformOverview> {
    return request(`/admin/metrics/overview?days=${days}`);
  },

  /* ── HFI — Investors ────────────────────────────────────────────── */

  async getHfiInvestors(): Promise<HfiInvestor[]> {
    return request("/hfi/investors");
  },

  async getHfiInvestor(investorId: string): Promise<HfiInvestor> {
    return request(`/hfi/investors/${investorId}`);
  },

  async createHfiInvestor(body: { name: string; description?: string; cik_number?: string }): Promise<HfiInvestor> {
    return request("/hfi/investors", { method: "POST", body: JSON.stringify(body) });
  },

  async updateHfiInvestor(investorId: string, body: Partial<{ name: string; description: string; cik_number: string; is_active: boolean }>): Promise<HfiInvestor> {
    return request(`/hfi/investors/${investorId}`, { method: "PATCH", body: JSON.stringify(body) });
  },

  async deleteHfiInvestor(investorId: string): Promise<void> {
    return request(`/hfi/investors/${investorId}`, { method: "DELETE" });
  },

  async getHfiInvestorStats(investorId: string): Promise<HfiInvestorStats> {
    return request(`/hfi/investors/${investorId}/stats`);
  },

  async getHfiInvestorSources(investorId: string): Promise<HfiSource[]> {
    return request(`/hfi/investors/${investorId}/sources`);
  },

  async createHfiSource(investorId: string, body: { source_type: string; url: string; label?: string; config?: Record<string, unknown> }): Promise<HfiSource> {
    return request(`/hfi/investors/${investorId}/sources`, { method: "POST", body: JSON.stringify(body) });
  },

  async deleteHfiSource(sourceId: string): Promise<void> {
    return request(`/hfi/investors/sources/${sourceId}`, { method: "DELETE" });
  },

  async getHfiInvestorContent(investorId: string, limit = 20, offset = 0): Promise<HfiContentItem[]> {
    return request(`/hfi/investors/${investorId}/content?limit=${limit}&offset=${offset}`);
  },

  async syncHfiInvestor(investorId: string): Promise<HfiSyncResponse> {
    return request(`/hfi/investors/${investorId}/sync`, { method: "POST" });
  },

  async generateHfiReport(investorId: string): Promise<HfiReport> {
    return request(`/hfi/reports/generate/${investorId}`, { method: "POST" });
  },

  /* ── HFI — Analytics ────────────────────────────────────────────── */

  async getHfiConsensus(period?: string): Promise<HfiConsensusResponse> {
    const params = period ? `?period=${encodeURIComponent(period)}` : "";
    return request(`/hfi/analytics/consensus${params}`);
  },

  async getHfiCompare(investorIds: string[], period?: string): Promise<HfiCompareResponse> {
    let params = `?investor_ids=${investorIds.join(",")}`;
    if (period) params += `&period=${encodeURIComponent(period)}`;
    return request(`/hfi/analytics/compare${params}`);
  },

  async getHfiPeriods(): Promise<string[]> {
    return request("/hfi/analytics/periods");
  },

  async getHfiPortfolio(investorId: string, period?: string): Promise<HfiPortfolioChange[]> {
    const params = period ? `?period=${encodeURIComponent(period)}` : "";
    return request(`/hfi/analytics/portfolio/${investorId}${params}`);
  },

  /* ── HFI — Reports ──────────────────────────────────────────────── */

  async getHfiReports(investorId?: string, limit = 20, offset = 0): Promise<HfiReportListItem[]> {
    let params = `?limit=${limit}&offset=${offset}`;
    if (investorId) params += `&investor_id=${investorId}`;
    return request(`/hfi/reports${params}`);
  },

  async getHfiReport(reportId: string): Promise<HfiReport> {
    return request(`/hfi/reports/${reportId}`);
  },

  /* ── HFI — Alerts ───────────────────────────────────────────────── */

  async getHfiAlerts(opts?: { investor_id?: string; severity?: string; unread_only?: boolean; limit?: number; offset?: number }): Promise<HfiAlertsResponse> {
    const params = new URLSearchParams();
    if (opts?.investor_id) params.set("investor_id", opts.investor_id);
    if (opts?.severity) params.set("severity", opts.severity);
    if (opts?.unread_only) params.set("unread_only", "true");
    if (opts?.limit) params.set("limit", String(opts.limit));
    if (opts?.offset) params.set("offset", String(opts.offset));
    const qs = params.toString();
    return request(`/hfi/alerts${qs ? `?${qs}` : ""}`);
  },

  async markHfiAlertRead(alertId: string): Promise<HfiAlert> {
    return request(`/hfi/alerts/${alertId}/read`, { method: "POST" });
  },

  async markAllHfiAlertsRead(): Promise<{ marked_read: number }> {
    return request("/hfi/alerts/read-all", { method: "POST" });
  },
};

/* ── Auth / usage / admin types ──────────────────────────────────── */

export interface UserProfile {
  id: string;
  clerk_user_id: string;
  email: string;
  full_name?: string | null;
  image_url?: string | null;
  role: "admin" | "user";
  status: "active" | "pending_invite" | "deactivated";
  created_at: string;
  last_seen_at: string;
}

export interface InviteDto {
  id: string;
  code: string;
  invited_email: string | null;
  max_uses: number;
  uses_count: number;
  expires_at: string | null;
  revoked_at: string | null;
  created_at: string;
}

export interface CreateInviteRequest {
  invited_email?: string | null;
  max_uses: number;
  expires_in_days?: number | null;
}

export interface UsageDailyPoint {
  day: string;
  api_calls: number;
  searches: number;
  search_zero_results: number;
  page_views: number;
  video_views: number;
  channel_views: number;
  theme_views: number;
  ticker_views: number;
  expensive_ops: number;
  llm_input_tokens: number;
  llm_output_tokens: number;
}

export interface MyUsageResponse {
  totals: Record<string, number | string | null>;
  daily: UsageDailyPoint[];
  top_queries: { query: string; count: number }[];
  recent_events: { type: string; payload: Record<string, unknown>; created_at: string }[];
}

export interface PlatformOverview {
  users: { total: number; active: number; pending_invite: number; dau: number; wau: number; mau: number };
  activity: { window_days: number; api_calls: number; expensive_ops: number };
  searches: { total: number; zero_results: number; zero_result_rate: number };
  llm: { input_tokens: number; output_tokens: number };
  daily_active: { day: string; users: number; searches: number }[];
  top_users: { id: string; email: string; full_name: string | null; api_calls: number; searches: number; last_active: string | null }[];
  top_queries: { query: string; count: number }[];
  top_features: { route: string; views: number }[];
}

/* ── HFI (Hedge Fund Intelligence) types ─────────────────────────── */

export interface HfiInvestor {
  id: string;
  name: string;
  description: string | null;
  cik_number: string | null;
  is_active: boolean;
  last_synced_at: string | null;
  sources_count: number;
  created_at: string;
  updated_at: string;
}

export interface HfiInvestorStats {
  content_items: number;
  reports: number;
  unread_alerts: number;
}

export interface HfiSource {
  id: string;
  source_type: string;
  url: string;
  label: string | null;
  is_active: boolean;
  last_checked_at: string | null;
  last_successful_at: string | null;
  consecutive_failures: number;
  check_frequency_hours: number;
  created_at: string;
}

export interface HfiContentItem {
  id: string;
  content_type: string;
  title: string | null;
  url: string | null;
  processing_status: string;
  published_at: string | null;
  created_at: string;
}

export interface HfiPortfolioChange {
  id: string;
  ticker_symbol: string | null;
  company_name: string | null;
  cusip: string | null;
  change_type: string;
  shares_previous: number;
  shares_current: number;
  value_usd: number | null;
  percent_of_portfolio: number | null;
  filing_period: string;
  report_date: string | null;
  created_at: string;
}

export interface HfiReport {
  id: string;
  investor_id: string | null;
  report_type: string;
  title: string;
  summary: string | null;
  content_markdown: string;
  is_read: boolean;
  period_start: string | null;
  period_end: string | null;
  generated_at: string;
  created_at: string;
}

export interface HfiReportListItem {
  id: string;
  investor_id: string | null;
  report_type: string;
  title: string;
  summary: string | null;
  is_read: boolean;
  generated_at: string;
}

export interface HfiAlert {
  id: string;
  investor_id: string | null;
  alert_type: string;
  title: string;
  summary: string | null;
  severity: string;
  score: number;
  is_read: boolean;
  created_at: string;
}

export interface HfiAlertsResponse {
  alerts: HfiAlert[];
  total: number;
  unread_count: number;
}

export interface HfiFundHoldingDetail {
  investor_id: string;
  investor_name: string;
  change_type: string;
  shares_current: number;
  shares_previous: number;
  value_usd: number | null;
  percent_of_portfolio: number | null;
}

export interface HfiConsensusHolding {
  ticker_symbol: string | null;
  company_name: string | null;
  total_funds_holding: number;
  funds_buying: number;
  funds_selling: number;
  total_value_usd: number | null;
  funds: HfiFundHoldingDetail[];
}

export interface HfiConsensusResponse {
  filing_period: string;
  available_periods: string[];
  total_funds_analyzed: number;
  holdings: HfiConsensusHolding[];
}

export interface HfiCompareCell {
  ticker_symbol: string | null;
  company_name: string | null;
  shares: number;
  value_usd: number | null;
  percent_of_portfolio: number | null;
  change_type: string;
}

export interface HfiCompareInvestor {
  investor_id: string;
  investor_name: string;
  holdings: HfiCompareCell[];
}

export interface HfiCompareResponse {
  period: string;
  all_tickers: string[];
  investors: HfiCompareInvestor[];
}

export interface HfiSyncResponse {
  investor_id: string;
  status: string;
  processed: number;
  failed: number;
  skipped: number;
}

