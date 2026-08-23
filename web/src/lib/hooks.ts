"use client";

import { useQuery, useMutation, useQueryClient, keepPreviousData } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ApiError } from "@/lib/auth-client";

export function useVideos() {
  return useQuery({
    queryKey: ["videos"],
    queryFn: () => api.getVideos(),
  });
}

export function useVideo(id: string) {
  return useQuery({
    queryKey: ["video", id],
    queryFn: () => api.getVideo(id),
    enabled: !!id,
  });
}

export function useChannels() {
  return useQuery({
    queryKey: ["channels"],
    queryFn: () => api.getChannels(),
  });
}

export function useChannel(id: string) {
  return useQuery({
    queryKey: ["channel", id],
    queryFn: () => api.getChannel(id),
    enabled: !!id,
  });
}

export function useTickers() {
  return useQuery({
    queryKey: ["tickers"],
    queryFn: () => api.getTickers(),
  });
}

export function useTopETFs() {
  return useQuery({
    queryKey: ["topETFs"],
    queryFn: () => api.getTopETFs(),
  });
}

export function useTicker(ticker: string) {
  return useQuery({
    queryKey: ["ticker", ticker],
    queryFn: () => api.getTicker(ticker),
    enabled: !!ticker,
  });
}

export function useTickerSentiment(ticker: string, days = 30) {
  return useQuery({
    queryKey: ["tickerSentiment", ticker, days],
    queryFn: () => api.getTickerSentimentTimeline(ticker, days),
    enabled: !!ticker,
    placeholderData: keepPreviousData,
  });
}

export function useTickerPriceHistory(ticker: string, days = 30) {
  return useQuery({
    queryKey: ["tickerPriceHistory", ticker, days],
    queryFn: () => api.getTickerPriceHistory(ticker, days),
    enabled: !!ticker,
    placeholderData: keepPreviousData,
  });
}

export function useThemes() {
  return useQuery({
    queryKey: ["themes"],
    queryFn: () => api.getThemes(),
  });
}

export function useTheme(id: string) {
  return useQuery({
    queryKey: ["theme", id],
    queryFn: () => api.getTheme(id),
    enabled: !!id,
  });
}

export function useActivity(opts?: { limit?: number; unreadOnly?: boolean }) {
  return useQuery({
    queryKey: ["activity", opts?.limit, opts?.unreadOnly],
    queryFn: () => api.getActivity(opts),
  });
}

export function useUnreadCount() {
  return useQuery({
    queryKey: ["unreadCount"],
    queryFn: () => api.getActivityUnreadCount(),
    refetchInterval: 30_000,
  });
}

export function useDashboardData() {
  const videos = useVideos();
  const channels = useChannels();
  const themes = useThemes();
  const tickers = useTickers();
  const etfs = useTopETFs();

  const isLoading =
    videos.isLoading ||
    channels.isLoading ||
    themes.isLoading ||
    tickers.isLoading ||
    etfs.isLoading;

  const isError =
    videos.isError ||
    channels.isError ||
    themes.isError ||
    tickers.isError ||
    etfs.isError;

  return {
    isLoading,
    isError,
    data: {
      videos: videos.data || [],
      channels: channels.data || [],
      themes: themes.data || [],
      tickers: tickers.data || [],
      etfs: etfs.data || [],
    },
    refetch: () => {
      videos.refetch();
      channels.refetch();
      themes.refetch();
      tickers.refetch();
      etfs.refetch();
    },
  };
}

export function useSearch(query: string, type: "keyword" | "semantic" | "hybrid" = "hybrid") {
  return useQuery({
    queryKey: ["search", query, type],
    queryFn: () => api.search(query, type),
    enabled: !!query.trim(),
  });
}

export function useTickerFlowDashboard(periodDays = 7) {
  return useQuery({
    queryKey: ["tickerflowDashboard", periodDays],
    queryFn: () => api.getTickerFlowDashboard(periodDays),
  });
}

export function useBackfillChannel() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ youtubeChannelId, maxVideos }: { youtubeChannelId: string; maxVideos?: number }) =>
      api.backfillChannel(youtubeChannelId, maxVideos),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["channels"] });
    },
  });
}

export function useIngestVideo() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ channelDbId, youtubeVideoId }: { channelDbId: string; youtubeVideoId: string }) =>
      api.ingestSingleVideo(channelDbId, youtubeVideoId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["channel", variables.channelDbId] });
      queryClient.invalidateQueries({ queryKey: ["videos"] });
    },
  });
}

/* ── Auth & usage hooks ─────────────────────────────────────────── */

export function useMe() {
  const query = useQuery({
    queryKey: ["me"],
    queryFn: () => api.getMe(),
    retry: false,
    staleTime: 60_000,
  });

  // Surface semantic flags for gating UI (invite gate, admin controls).
  const error = query.error;
  const inviteRequired = error instanceof ApiError && error.code === "invite_required";
  const unauthorized =
    error instanceof ApiError &&
    (error.status === 401 || error.code === "unauthorized" || error.status === 0);

  return { ...query, user: query.data, isAdmin: query.data?.role === "admin", inviteRequired, unauthorized };
}

export function useRedeemInvite() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (code: string) => api.redeemInvite(code),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["me"] });
    },
  });
}

export function useMyUsage(days = 30) {
  return useQuery({
    queryKey: ["myUsage", days],
    queryFn: () => api.getMyUsage(days),
  });
}
