"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  StockDiscoveryResult,
  SearchAnswerResponse,
  AnswerCitation,
  SearchCoverageResponse,
  Prediction,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/Skeleton";
import { PageHeader } from "@/components/PageHeader";
import {
  Search,
  Loader2,
  ExternalLink,
  X,
  Tv,
  TrendingUp,
  TrendingDown,
  BarChart3,
  MessageSquare,
  PanelRightClose,
  PanelRightOpen,
  ChevronDown,
  ChevronUp,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import { useSearch, useSearchAnswer, useSearchCoverage, useTicker, useTickerSentiment } from "@/lib/hooks";
import { SocialSourceBadges } from "@/components/SocialSourceBadges";
import { SocialSentimentPanel } from "@/components/SocialSentimentPanel";
import { motion, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils";

interface PlaybackModalState {
  videoId: string;
  youtubeVideoId?: string;
  title: string;
  channelTitle?: string;
  startSec: number;
  text: string;
}

const containerVariants = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.04, delayChildren: 0.05 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 8 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: "easeOut" as const } },
};

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
};

const formatDate = (value?: string | null) => {
  if (!value) return null;
  return new Date(value).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
};

// Sanitize leaked citations in LLM answers
const UUID_BRACKET_RE = /\[\s*([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|\d+)\s*\]/gi;
const RAW_UUID_RE = /\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b/gi;

function sanitizeCitations(text: string, ..._args: unknown[]): string {
  if (!text) return text;
  let out = text.replace(UUID_BRACKET_RE, "");
  out = out.replace(RAW_UUID_RE, "");
  out = out.replace(/\(\s*,\s*/g, "(");
  out = out.replace(/,\s*\)/g, ")");
  out = out.replace(/\(\s*\)/g, "");
  out = out.replace(/\[\s*\]/g, "");
  out = out.replace(/,\s*,/g, ",");
  out = out.replace(/\s{2,}/g, " ");
  out = out.replace(/\s+([.,;:)])/g, "$1");
  return out.trim();
}

function SearchAnswerCard({
  answer,
  skeleton,
}: {
  answer?: SearchAnswerResponse;
  skeleton: boolean;
}) {
  return (
    <div className="rounded-lg border border-signal/30 bg-panel p-4">
      <div className="mb-2.5 flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-signal" />
        <span className="label-overline text-signal">Summary</span>
        {/* {answer?.cached && (
          <Badge
            variant="outline"
            className="border-line px-1.5 py-0 font-mono text-micro text-ink-faint"
          >
            cached
          </Badge>
        )} */}
      </div>

      {skeleton ? (
        <div className="space-y-2.5">
          <Skeleton className="h-3.5 w-full" />
          <Skeleton className="h-3.5 w-11/12" />
          <Skeleton className="h-3.5 w-8/12" />
        </div>
      ) : answer ? (
        <>
          <p className="text-body leading-relaxed text-ink">
            {sanitizeCitations(answer.summary, answer.citations)}
          </p>

          {answer.key_points.length > 0 && (
            <ul className="mt-3 flex flex-col gap-1.5">
              {answer.key_points.map((point, i) => {
                const clean = sanitizeCitations(point, answer.citations);
                if (!clean) return null;
                return (
                  <li key={i} className="flex items-start gap-2 text-small text-ink-secondary">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-signal" />
                    {clean}
                  </li>
                );
              })}
            </ul>
          )}

          {/* TickerFlow social-sentiment strip (Reddit/X/News) for tickers in the query */}
          {(answer.social_context ?? []).length > 0 && (
            <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 border-t border-line/60 pt-2.5">
              <span className="label-overline text-ink-faint">Social</span>
              {answer.social_context!.map((snap) => (
                <div key={snap.symbol} className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-micro font-semibold text-ink">
                    {snap.symbol}
                  </span>
                  <span className="font-mono text-micro text-ink-secondary">
                    {snap.total_mentions ?? 0} mentions
                  </span>
                  {snap.sentiment_score != null && (
                    <span
                      className={cn(
                        "font-mono text-micro font-semibold",
                        snap.sentiment_score > 0.05
                          ? "text-bullish"
                          : snap.sentiment_score < -0.05
                            ? "text-bearish"
                            : "text-ink-secondary",
                      )}
                    >
                      {snap.sentiment_score > 0 ? "+" : ""}
                      {snap.sentiment_score.toFixed(2)}
                    </span>
                  )}
                  {snap.bullish_pct != null && (
                    <span className="font-mono text-micro text-bullish/70">
                      {snap.bullish_pct.toFixed(0)}% bull
                    </span>
                  )}
                  {snap.bearish_pct != null && (
                    <span className="font-mono text-micro text-bearish/70">
                      {snap.bearish_pct.toFixed(0)}% bear
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* {answer.citations.length > 0 && (
            <div className="mt-3 flex items-center gap-1.5">
              {answer.citations.map((c, i) => (
                <button
                  key={c.segment_id}
                  type="button"
                  onClick={() => onCitationClick(c)}
                  title={`Play clip: ${c.video_title ?? ""}`}
                  className="flex h-6 min-w-6 items-center justify-center rounded border border-signal/30 bg-signal/10 px-1.5 font-mono text-micro font-semibold text-signal transition-colors hover:bg-signal/20"
                >
                  [{i + 1}]
                </button>
              ))}
              <span className="ml-1 text-micro text-ink-faint">play cited clip</span>
            </div>
          )} */}

          {/* <p className="mt-3 text-micro text-ink-faint">
            AI-generated from transcript clips — verify against the sources.
          </p> */}
        </>
      ) : null}
    </div>
  );
}

function CoverageSnapshotCard({ coverage }: { coverage: SearchCoverageResponse }) {
  const total = coverage.total_videos;
  if (total === 0) return null;

  const widthPct = (n: number) => `${(n / total) * 100}%`;
  const maxCount = Math.max(1, ...coverage.weekly_volume.map((w) => w.count));
  const wow = coverage.wow_delta_pct;

  const stances = [
    { label: "Positive", count: coverage.positive, color: "bg-bullish" },
    { label: "Neutral", count: coverage.neutral, color: "bg-ink-faint/60" },
    { label: "Negative", count: coverage.negative, color: "bg-bearish" },
  ];

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-line bg-panel p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-signal" />
          <span className="label-overline text-signal">Coverage</span>
        </div>
        <Badge
          variant="outline"
          className="border-line px-1.5 py-0 font-mono text-micro text-ink-faint"
        >
          {coverage.window_days}d
        </Badge>
      </div>

      <div className="flex items-baseline gap-2">
        <span className="font-display text-heading font-semibold text-ink">{total}</span>
        <span className="text-small text-ink-secondary">
          videos · last {coverage.window_days} days
        </span>
      </div>

      {/* Stacked stance bar */}
      <div className="flex h-2 w-full overflow-hidden rounded-full bg-panel-raised">
        {stances.map(
          (s) =>
            s.count > 0 && (
              <div
                key={s.label}
                className={s.color}
                style={{ width: widthPct(s.count) }}
                title={`${s.label}: ${s.count}`}
              />
            ),
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
        {stances.map((s) => (
          <div key={s.label} className="flex items-center gap-1.5 text-small text-ink-secondary">
            <span className={cn("h-2 w-2 rounded-full", s.color)} />
            {s.label}
            <span className="font-mono font-semibold text-ink">{s.count}</span>
          </div>
        ))}
      </div>

      {/* TickerFlow social mentions (Reddit/X/News) for the resolved ticker */}
      {coverage.social?.available && (
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-line/60 pt-2.5">
          <span className="label-overline text-ink-faint">
            Social · {coverage.social.symbol}
          </span>
          <span className="font-mono text-small text-ink-secondary">
            {coverage.social.mentions} mentions
          </span>
          {coverage.social.bullish_pct != null && (
            <span className="font-mono text-micro text-bullish">
              {coverage.social.bullish_pct.toFixed(0)}% bull
            </span>
          )}
          {coverage.social.bearish_pct != null && (
            <span className="font-mono text-micro text-bearish">
              {coverage.social.bearish_pct.toFixed(0)}% bear
            </span>
          )}
        </div>
      )}

      {/* Weekly volume + WoW momentum */}
      {coverage.weekly_volume.length > 1 && (
        <div className="mt-1 flex flex-col gap-1.5">
          <div className="flex items-center justify-between">
            <span className="label-overline">Weekly volume</span>
            {wow !== null && wow !== undefined && (
              <Badge
                variant="outline"
                className={cn(
                  "gap-0.5 border px-1.5 py-0 font-mono text-micro",
                  wow >= 0
                    ? "border-bullish/30 bg-bullish/10 text-bullish"
                    : "border-bearish/30 bg-bearish/10 text-bearish",
                )}
              >
                {wow >= 0 ? "▲" : "▼"} {Math.abs(wow)}% WoW
              </Badge>
            )}
          </div>
          <div className="flex h-12 items-stretch gap-2">
            {coverage.weekly_volume.map((w) => (
              <div key={w.week_start} className="flex min-w-0 flex-1 flex-col items-center gap-1">
                <div className="flex w-full flex-1 items-end">
                  <div
                    className={cn("w-full rounded-t-sm", w.count > 0 ? "bg-signal/60" : "bg-line")}
                    style={{ height: `${Math.max((w.count / maxCount) * 100, 6)}%` }}
                    title={`${w.count} videos`}
                  />
                </div>
                <span className="font-mono text-micro text-ink-faint">
                  {new Date(`${w.week_start}T00:00:00`).toLocaleDateString(undefined, {
                    month: "numeric",
                    day: "numeric",
                  })}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

type DateRange = "all" | "7d" | "30d" | "90d";
type SortMode = "relevance" | "recent";

const RESULT_LIMIT_STEP = 20;

const DATE_RANGE_DAYS: Record<Exclude<DateRange, "all">, number> = {
  "7d": 7,
  "30d": 30,
  "90d": 90,
};

interface DateRangeFilter {
  key: DateRange;
  /** Epoch ms below which groups are excluded; null = no bound */
  cutoffMs: number | null;
}

// Module scope so the impure clock read stays out of the component render path
function resolveCutoff(key: Exclude<DateRange, "all">): number {
  return Date.now() - DATE_RANGE_DAYS[key] * 86_400_000;
};

function SearchPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const reducedMotion = useReducedMotion();

  const activeQuery = searchParams.get("q") || "";
  const activeType = (searchParams.get("type") as "keyword" | "semantic" | "hybrid") || "hybrid";
  const activeSort: SortMode = searchParams.get("sort") === "recent" ? "recent" : "relevance";

  const [query, setQuery] = useState(activeQuery);
  const [type, setType] = useState<"keyword" | "semantic" | "hybrid">(activeType);
  const [playbackModal, setPlaybackModal] = useState<PlaybackModalState | null>(null);
  const [railOpen, setRailOpen] = useState(true);
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const [resultLimit, setResultLimit] = useState(RESULT_LIMIT_STEP);
  const [dateFilter, setDateFilter] = useState<DateRangeFilter>({ key: "all", cutoffMs: null });
  const [channelFilter, setChannelFilter] = useState<string | null>(null);
  const [showAllVideos, setShowAllVideos] = useState(false);

  const {
    data: results,
    isLoading: loading,
    isFetching: resultsFetching,
    isPlaceholderData,
    refetch,
  } = useSearch(activeQuery, activeType, activeSort, resultLimit);

  const isSearching = loading || resultsFetching;

  // Reset view-local state whenever the search parameters change
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setResultLimit(RESULT_LIMIT_STEP);
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setDateFilter({ key: "all", cutoffMs: null });
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setChannelFilter(null);
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setExpandedGroups(new Set());
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setShowAllVideos(false);
  }, [activeQuery, activeType, activeSort]);

  const toggleGroup = (videoId: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(videoId)) {
        next.delete(videoId);
      } else {
        next.add(videoId);
      }
      return next;
    });
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setQuery(activeQuery);
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setType(activeType);
  }, [activeQuery, activeType]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;
    const targetUrl = `/search?q=${encodeURIComponent(trimmed)}&type=${type}&sort=${activeSort}`;
    router.push(targetUrl);
    if (trimmed === activeQuery && type === activeType) {
      refetch();
    }
  };

  const handleTypeChange = (newType: "keyword" | "semantic" | "hybrid") => {
    setType(newType);
    if (query.trim()) {
      router.push(
        `/search?q=${encodeURIComponent(query.trim())}&type=${newType}&sort=${activeSort}`,
      );
    }
  };

  const handleSortChange = (newSort: SortMode) => {
    if (newSort === activeSort) return;
    router.push(`/search?q=${encodeURIComponent(activeQuery)}&type=${activeType}&sort=${newSort}`);
  };

  const revealAnim = reducedMotion ? {} : containerVariants;
  const itemAnim = reducedMotion ? {} : itemVariants;

  const groups = results?.groups && results.groups.length > 0 ? results.groups : null;

  // Channel facets derived from the returned groups (no extra endpoint needed)
  const channelFacets = useMemo(() => {
    const map = new Map<string, { key: string; title: string; count: number }>();
    for (const g of results?.groups ?? []) {
      const key = g.channel_id || g.channel_title || "";
      if (!key) continue;
      const entry = map.get(key);
      if (entry) {
        entry.count += g.hit_count;
      } else {
        map.set(key, { key, title: g.channel_title || key, count: g.hit_count });
      }
    }
    return [...map.values()].sort((a, b) => b.count - a.count);
  }, [results]);

  const visibleGroups = useMemo(() => {
    let gs = results?.groups ?? [];
    if (channelFilter) {
      gs = gs.filter((g) => (g.channel_id || g.channel_title || "") === channelFilter);
    }
    if (dateFilter.cutoffMs !== null) {
      gs = gs.filter(
        (g) => g.published_at && new Date(g.published_at).getTime() >= dateFilter.cutoffMs!,
      );
    }
    return gs;
  }, [results, channelFilter, dateFilter]);

  const activeDateRange = dateFilter.key;
  const hasActiveFilters = channelFilter !== null || activeDateRange !== "all";

  // Resolve the cutoff at click time so rendering stays pure
  const handleDateRangeChange = (r: DateRange) => {
    setDateFilter({ key: r, cutoffMs: r === "all" ? null : resolveCutoff(r) });
  };

  const clearFilters = () => {
    setDateFilter({ key: "all", cutoffMs: null });
    setChannelFilter(null);
  };

  // ── AI answer — synthesized from the top fused-rank segments ──────────
  // Avoid the keepPreviousData race: while a new query is fetching, results
  // still holds the previous query's groups. Sending those stale ids with the
  // new query poisons the answer cache (MSFT query + NVDA ids → "don't mention MSFT").
  const answerSegmentIds = useMemo(() => {
    if (isPlaceholderData || resultsFetching) return [];
    return (results?.groups ?? [])
      .flatMap((g) => [...g.top_segments, ...g.remaining_segments])
      .map((s) => s.id)
      .slice(0, 12);
  }, [results, isPlaceholderData, resultsFetching]);
  const { data: answer, isFetching: answerFetching } = useSearchAnswer(
    activeQuery,
    answerSegmentIds,
  );
  const { data: coverage } = useSearchCoverage(activeQuery, answerSegmentIds);
  const showAnswerSkeleton =
    !!activeQuery && !answer && answerSegmentIds.length >= 3 && answerFetching;
  const showCoverage = !!coverage && coverage.total_videos > 0;

  // ── Selected / resolved ticker for live Social Sentiment Panel ─────────
  const [selectedTickerState, setSelectedTickerState] = useState<{ query: string; ticker: string | null }>({
    query: "",
    ticker: null,
  });
  const selectedTicker = selectedTickerState.query === activeQuery ? selectedTickerState.ticker : null;
  const setSelectedTicker = (ticker: string | null) => {
    setSelectedTickerState({ query: activeQuery, ticker });
  };

  const activeTicker = useMemo(() => {
    if (selectedTicker) return selectedTicker;
    if (results?.stocks && results.stocks.length > 0) {
      return results.stocks[0].ticker;
    }
    if (coverage?.social?.symbol) {
      return coverage.social.symbol;
    }
    if (answer?.social_context && answer.social_context.length > 0) {
      return answer.social_context[0].symbol;
    }
    const cleanQuery = activeQuery.trim().toUpperCase().replace(/^\$/, "");
    if (/^[A-Z]{1,5}$/.test(cleanQuery)) {
      return cleanQuery;
    }
    return null;
  }, [selectedTicker, results?.stocks, coverage?.social?.symbol, answer?.social_context, activeQuery]);

  const { data: tickerDetail } = useTicker(activeTicker ?? "");
  const { data: sentimentTimeline = [] } = useTickerSentiment(activeTicker ?? "");

  return (
    <div className="flex h-full flex-col gap-6 lg:flex-row">
      {/* Main Search Area */}
      <div className="flex flex-1 flex-col gap-6">
        <PageHeader
          title="Search"
          description="Search transcripts, predictions, and themes across all channels."
        />

        {/* Search Container Box */}
        <div className="rounded-lg border border-line bg-panel p-4">
          <form onSubmit={handleSearchSubmit} className="flex flex-col gap-3">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-2.5 z-10 h-4 w-4 text-ink-faint" />
                <Input
                  type="text"
                  placeholder="Search for 'AI chips', 'inflation', 'Nvidia'..."
                  className="pl-9"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
              </div>
              <Button type="submit" size={"lg"} disabled={isSearching} className="text-base!">
                {isSearching && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />}
                Search
              </Button>
            </div>

            <div className="flex items-center gap-3 pt-1">
              <span className="label-overline">Search type</span>
              <div className="flex gap-0.5 rounded-md border border-line bg-panel p-0.5">
                {(["keyword", "semantic", "hybrid"] as const).map((t) => (
                  <Button
                    key={t}
                    type="button"
                    variant={type === t ? "default" : "ghost"}
                    size="lg"
                    className="h-7 capitalize text-base!"
                    // className={cn("h-7 capitalize", `${type === t ? "text-white h-7 capitalize" : " text-black h-7 capitalize"}`)}
                    onClick={() => handleTypeChange(t)}
                  >
                    {t}
                  </Button>
                ))}
              </div>
            </div>
          </form>
        </div>

        {/* AI Answer + Coverage Snapshot — lazy-loaded after segments render */}
        {(showAnswerSkeleton || answer?.available || showCoverage) && (
          <div
            className={cn(
              "grid gap-4",
              showCoverage && (showAnswerSkeleton || answer?.available)
                ? "lg:grid-cols-2"
                : "grid-cols-1",
            )}
          >
            {(showAnswerSkeleton || answer?.available) && (
              <SearchAnswerCard
                answer={answer}
                skeleton={showAnswerSkeleton}
              />
            )}
            {/* {showCoverage && <CoverageSnapshotCard coverage={coverage} />} */}
          </div>
        )}

        {results && (
          <motion.div
            className={cn(
              "flex flex-col gap-4 pb-10 transition-opacity duration-200",
              (isSearching || isPlaceholderData) && "opacity-60 pointer-events-none",
            )}
            variants={revealAnim}
            initial={reducedMotion ? false : "hidden"}
            animate="show"
          >
            {/* Stock / ETF Discovery Cards — shown prominently for exploratory queries */}
            {/* {results.stocks && results.stocks.length > 0 && (
              <div className="flex flex-col gap-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <BarChart3 className="h-4 w-4 text-signal" />
                    <h2 className="font-display text-heading font-semibold text-ink">
                      {results.instrument_type === "etfs" || results.stocks.every((s) => s.is_etf)
                        ? `Top ETFs (${results.stocks.length})`
                        : `Top Stocks (${results.stocks.length})`}
                    </h2>
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                  {results.stocks.map((stock: StockDiscoveryResult, idx: number) => {
                    const isSelected = activeTicker === stock.ticker;
                    const sentimentColor =
                      stock.avg_sentiment > 0.2 ? "text-bullish" :
                        stock.avg_sentiment < -0.2 ? "text-bearish" : "text-ink-secondary";
                    const sentimentLabel =
                      stock.avg_sentiment > 0.2 ? "Bullish" :
                        stock.avg_sentiment < -0.2 ? "Bearish" : "Neutral";
                    const SentimentIcon = stock.avg_sentiment > 0.2 ? TrendingUp : stock.avg_sentiment < -0.2 ? TrendingDown : BarChart3;

                    return (
                      <motion.div key={stock.ticker} variants={itemAnim} className="min-w-0">
                        <Card
                          onClick={() => setSelectedTicker(stock.ticker)}
                          className={cn(
                            "h-full min-w-0 cursor-pointer overflow-hidden transition-all",
                            isSelected
                              ? "border-signal shadow-xs ring-1 ring-signal/30"
                              : "hover:border-signal/40",
                          )}
                        >
                          <CardContent className="flex min-w-0 flex-col gap-3 overflow-hidden p-4">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2.5">
                                <span className="w-5 font-mono text-micro font-semibold text-ink-faint">#{idx + 1}</span>
                                <Link
                                  href={`/tickers/${stock.ticker}`}
                                  onClick={(e) => e.stopPropagation()}
                                  className="transition-colors hover:text-signal"
                                >
                                  <span className="font-mono text-title font-semibold tracking-tight text-ink">{stock.ticker}</span>
                                </Link>
                                {stock.is_etf && (
                                  <Badge variant="outline" className="border-info/30 bg-info/10 px-1.5 py-0 text-micro text-info">
                                    ETF
                                  </Badge>
                                )}
                              </div>
                              <div className="flex items-center gap-2">
                                <div className={`flex items-center gap-1 ${sentimentColor}`}>
                                  <SentimentIcon className="h-3.5 w-3.5" />
                                  <span className="font-mono text-small font-semibold">{sentimentLabel}</span>
                                </div>
                                {stock.bullish_pct > 0 && (
                                  <span className="font-mono text-micro text-bullish/70">{stock.bullish_pct}% bull</span>
                                )}
                              </div>
                            </div>

                            <div className="flex items-center gap-4 font-mono text-small text-ink-secondary">
                              <div className="flex items-center gap-1">
                                <MessageSquare className="h-3 w-3" />
                                <span>{stock.mention_count} mentions</span>
                              </div>
                              <div className="flex items-center gap-1">
                                <BarChart3 className="h-3 w-3" />
                                <span>{stock.prediction_count} predictions</span>
                              </div>
                            </div>

                            <SocialSourceBadges social={stock.social} />

                            {stock.sample_predictions.length > 0 && (
                              <div className="border-l-2 border-line-strong py-0.5 pl-3">
                                <p className="line-clamp-2 text-small italic text-ink-secondary">
                                  &quot;{stock.sample_predictions[0].text}&quot;
                                </p>
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      </motion.div>
                    );
                  })}
                </div>
              </div>
            )} */}

            {/* Live Social & Video Sentiment Chart with TradingView Dual-Pane Price + Chatter */}
            {tickerDetail?.social && (
              <div className="flex flex-col gap-2">
                <SocialSentimentPanel
                  social={tickerDetail.social}
                  predictions={tickerDetail.predictions}
                  sentimentTimeline={sentimentTimeline}
                  youtubeMentions={tickerDetail.total_mentions}
                  youtubeAvgSentiment={tickerDetail.avg_sentiment}
                />
              </div>
            )}

            {/* Filter bar — only meaningful for grouped results */}
            {groups && groups.length > 0 && (
              <div className="flex flex-wrap items-center gap-x-5 gap-y-2 rounded-lg border border-line bg-panel p-3">
                {/* Sort */}
                <div className="flex items-center gap-2">
                  <span className="label-overline">Sort</span>
                  <div className="flex gap-0.5 rounded-md border border-line bg-panel p-0.5">
                    {(["relevance", "recent"] as const).map((s) => (
                      <Button
                        key={s}
                        type="button"
                        variant={activeSort === s ? "default" : "ghost"}
                        size="lg"
                        disabled={loading}
                        className="h-7 capitalize text-base!"
                        onClick={() => handleSortChange(s)}
                      >
                        {s === "recent" ? "Newest" : "Relevance"}
                      </Button>
                    ))}
                  </div>
                </div>

                {/* Date range */}
                <div className="flex items-center gap-2">
                  <span className="label-overline">Period</span>
                  <div className="flex gap-0.5 rounded-md border border-line bg-panel p-0.5">
                    {(["all", "7d", "30d", "90d"] as const).map((r) => (
                      <Button
                        key={r}
                        type="button"
                        variant={activeDateRange === r ? "default" : "ghost"}
                        size="lg"
                        className="h-7 text-base!"
                        onClick={() => handleDateRangeChange(r)}
                      >
                        {r === "all" ? "All time" : r}
                      </Button>
                    ))}
                  </div>
                </div>

                {/* Channel facet */}
                {channelFacets.length > 1 && (
                  <div className="flex items-center gap-2">
                    <span className="label-overline">Channel</span>
                    <select
                      value={channelFilter ?? ""}
                      onChange={(e) => setChannelFilter(e.target.value || null)}
                      className="h-8 rounded-md border border-line bg-panel px-2 text-small text-ink outline-none transition-colors focus:border-signal"
                    >
                      <option value="">All channels</option>
                      {channelFacets.map((c) => (
                        <option key={c.key} value={c.key}>
                          {c.title} ({c.count})
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {hasActiveFilters && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="ml-auto gap-1 text-ink-secondary hover:text-ink"
                    onClick={clearFilters}
                  >
                    <X className="h-3.5 w-3.5" />
                    Clear filters
                  </Button>
                )}
              </div>
            )}

            {/* Transcript Segments Header */}
            <div className="flex items-center justify-between">
              <h2 className="font-display text-heading font-semibold text-ink">
                {results.stocks && results.stocks.length > 0 ? "Related Segments" : "Results"}{" "}
                {groups
                  ? hasActiveFilters && visibleGroups.length !== results.groups.length
                    ? `(${visibleGroups.length} of ${results.groups.length})`
                    : `(${results.groups.length})`
                  : `(${results.segments?.length || 0})`}
              </h2>
              {query && (
                <span className="font-mono text-micro text-ink-faint">
                  matching &quot;{query}&quot;
                </span>
              )}
            </div>

            {groups ? (
              /* ── Consolidated: broad side-by-side card grid (3-column layout) ── */
              visibleGroups.length > 0 ? (
                <div className="flex flex-col gap-5">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 items-stretch">
                    {(showAllVideos ? visibleGroups : visibleGroups.slice(0, 6)).map((group) => {
                      const isExpanded = expandedGroups.has(group.video_id);
                      const videoTitle =
                        group.video_title || `Video (${group.video_id.slice(0, 8)}...)`;
                      const dateLabel = formatDate(group.published_at);
                      const bestMatch = group.top_segments[0]?.rank ?? group.best_rank;
                      const extraCount = group.remaining_segments.length;
                      const thumbUrl =
                        group.thumbnail_url ||
                        (group.youtube_video_id
                          ? `https://img.youtube.com/vi/${group.youtube_video_id}/hqdefault.jpg`
                          : null);

                      return (
                        <motion.div key={group.video_id} variants={itemAnim} className="flex flex-col h-full">
                          <Card className="flex flex-col h-full overflow-hidden transition-all duration-200 hover:border-signal/40 hover:shadow-xl bg-panel group">
                            {/* Card Thumbnail Area with Overlaid Badges */}
                            <div className="relative aspect-video w-full overflow-hidden bg-panel-raised border-b border-line">
                              {thumbUrl ? (
                                // eslint-disable-next-line @next/next/no-img-element
                                <img
                                  src={thumbUrl}
                                  alt=""
                                  className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                                />
                              ) : (
                                <div className="flex h-full w-full items-center justify-center bg-panel-raised text-ink-faint">
                                  <Tv className="h-8 w-8 opacity-40" />
                                </div>
                              )}

                              {/* Gradient Vignette for Legibility */}
                              <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/20 to-black/60 pointer-events-none" />

                              {/* Top Floating Channel & Date */}
                              <div className="absolute top-3 left-3 right-3 flex items-center justify-between gap-2 pointer-events-none">
                                {group.channel_title && (
                                  <div className="flex items-center gap-1.5 rounded-md bg-black/80 backdrop-blur-md px-2.5 py-1 text-small font-medium text-white border border-white/10 truncate max-w-[65%]">
                                    <Tv className="h-3.5 w-3.5 shrink-0 text-signal" />
                                    <span className="truncate">{group.channel_title}</span>
                                  </div>
                                )}
                                {dateLabel && (
                                  <div className="rounded-md bg-black/80 backdrop-blur-md px-2.5 py-1 text-micro font-mono text-slate-300 border border-white/10 shrink-0">
                                    {dateLabel}
                                  </div>
                                )}
                              </div>

                              {/* Bottom Floating Match & Mentions Badges */}
                              <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between pointer-events-none">
                                <Badge
                                  variant="outline"
                                  className="border-signal/40 bg-black/80 backdrop-blur-md font-mono text-micro px-2.5 py-0.5 text-signal"
                                >
                                  {group.hit_count} mention{group.hit_count === 1 ? "" : "s"}
                                </Badge>
                                <Badge
                                  variant="outline"
                                  className="border-bullish/40 bg-black/80 backdrop-blur-md font-mono text-micro px-2.5 py-0.5 text-bullish"
                                >
                                  {(bestMatch * 100).toFixed(0)}% match
                                </Badge>
                              </div>
                            </div>

                            {/* Card Header: Title */}
                            <CardHeader className="p-5 pb-2">
                              <Link href={`/videos/${group.video_id}`} className="group/title">
                                <CardTitle className="line-clamp-2 text-title font-semibold text-ink leading-snug group-hover/title:text-signal transition-colors">
                                  {videoTitle}
                                </CardTitle>
                              </Link>
                            </CardHeader>

                            {/* Card Content: Primary Excerpt & Extra Clips Accordion */}
                            <CardContent className="p-5 pt-1 flex-1 flex flex-col justify-between gap-3.5">
                              {group.top_segments.length > 0 && (
                                <div className="rounded-r-md border-l-2 border-signal bg-panel-raised/70 p-3 text-body italic text-ink-secondary leading-relaxed line-clamp-3">
                                  &quot;{group.top_segments[0].text}&quot;
                                </div>
                              )}

                              {extraCount > 0 && (
                                <div className="pt-1 mt-auto">
                                  <Button
                                    type="button"
                                    variant="ghost"
                                    size="sm"
                                    className="w-full justify-between h-8 px-3 text-small text-ink-secondary hover:text-ink hover:bg-panel-raised"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      toggleGroup(group.video_id);
                                    }}
                                  >
                                    <span className="font-mono">
                                      {isExpanded
                                        ? "Hide extra clips"
                                        : `+${extraCount} more clip${extraCount === 1 ? "" : "s"} in this video`}
                                    </span>
                                    {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                                  </Button>

                                  {isExpanded && (
                                    <div className="mt-2 divide-y divide-line rounded-md border border-line bg-panel-raised/40 max-h-44 overflow-y-auto">
                                      {group.remaining_segments.map((seg) => (
                                        <Link
                                          key={seg.id}
                                          href={`/videos/${seg.video_id}?t=${Math.floor(seg.start_sec)}`}
                                          className="flex items-start gap-2.5 p-2.5 text-small transition-colors hover:bg-panel"
                                        >
                                          <span className="shrink-0 font-mono font-semibold text-signal">
                                            {formatTime(seg.start_sec)}
                                          </span>
                                          <span className="line-clamp-2 text-ink-secondary">
                                            {seg.text}
                                          </span>
                                        </Link>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              )}
                            </CardContent>
                          </Card>
                        </motion.div>
                      );
                    })}
                  </div>

                  {visibleGroups.length > 6 && (
                    <div className="flex justify-center pt-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowAllVideos(!showAllVideos)}
                        className="font-mono text-small gap-1.5 hover:border-signal/40 hover:text-signal"
                      >
                        {showAllVideos ? (
                          <>
                            <ChevronUp className="h-3.5 w-3.5" />
                            Show Top 6 Videos
                          </>
                        ) : (
                          <>
                            <ChevronDown className="h-3.5 w-3.5" />
                            Show All {visibleGroups.length} Videos
                          </>
                        )}
                      </Button>
                    </div>
                  )}
                </div>
              ) : (
                <div className="rounded-lg border border-dashed border-line px-6 py-10 text-center">
                  <p className="text-body font-medium text-ink">No videos match your filters</p>
                  <p className="mt-1 text-small text-ink-secondary">
                    Try widening the period or clearing the channel filter.
                  </p>
                  <Button variant="outline" size="sm" className="mt-3" onClick={clearFilters}>
                    Clear filters
                  </Button>
                </div>
              )
            ) : (
              /* ── Fallback: flat segment grid (legacy response shape) ── */
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {results.segments?.map((seg) => {
                  const video = results.videos?.[seg.video_id];
                  const channel =
                    results.channels?.[video?.channel_id] ||
                    (seg.channel_title ? { title: seg.channel_title } : null);

                  const videoTitle = seg.video_title || video?.title || `Video Segment (${seg.video_id.slice(0, 8)}...)`;
                  const channelTitle = seg.channel_title || channel?.title;

                  return (
                    <motion.div key={seg.id} variants={itemAnim} className="flex flex-col h-full">
                      <Card className="flex flex-col h-full overflow-hidden transition-all duration-200 hover:border-signal/40 bg-panel group">
                        <CardHeader className="p-4 pb-2">
                          <div className="flex flex-col gap-1.5">
                            {channelTitle && (
                              <div className="flex items-center gap-1.5 text-micro font-medium text-ink-secondary">
                                <Tv className="h-3 w-3 text-signal shrink-0" />
                                <span className="truncate">{channelTitle}</span>
                              </div>
                            )}
                            <Link href={`/videos/${seg.video_id}?t=${Math.floor(seg.start_sec)}`} className="group/title">
                              <CardTitle className="line-clamp-2 text-title font-semibold text-ink leading-snug group-hover/title:text-signal transition-colors">
                                {videoTitle}
                              </CardTitle>
                            </Link>
                          </div>
                        </CardHeader>
                        <CardContent className="p-4 pt-1 flex-1 flex flex-col justify-between gap-3">
                          <div className="rounded-r-md border-l-2 border-signal bg-panel-raised/60 p-2.5 text-small italic text-ink-secondary leading-relaxed line-clamp-3">
                            &quot;{seg.text}&quot;
                          </div>
                          <div className="flex items-center justify-between pt-1 font-mono text-micro text-ink-faint border-t border-line">
                            <span className="text-signal font-semibold">{formatTime(seg.start_sec)}</span>
                            <Badge variant="outline" className="border-bullish/30 bg-bullish/10 text-bullish text-[10px]">
                              {(seg.rank * 100).toFixed(0)}% match
                            </Badge>
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>
                  );
                })}
              </div>
            )}

            {(!results.segments || results.segments.length === 0) && (
              <div className="rounded-lg border border-dashed border-line px-6 py-10 text-center">
                <p className="text-body font-medium text-ink">No transcript segments found</p>
                <p className="mt-1 text-small text-ink-secondary">
                  Try a broader keyword, or switch to semantic search for concept matching.
                </p>
              </div>
            )}

            {/* Load more — fetches a larger result set; hidden while filters narrow the view */}
            {groups && results.has_more && !hasActiveFilters && (
              <Button
                variant="outline"
                className="self-center"
                disabled={loading}
                onClick={() => setResultLimit((l) => l + RESULT_LIMIT_STEP)}
              >
                {loading && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />}
                Load more videos
              </Button>
            )}
          </motion.div>
        )}
      </div>

      {/* Right Rail - Dynamic Top Stocks / ETFs */}
      {/* {railOpen ? (
        <Card className="h-fit w-full shrink-0 lg:w-72 lg:sticky lg:top-4">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between gap-2">
              <div>
                <CardTitle className="text-title font-semibold">
                  {results?.stocks && results.stocks.length > 0
                    ? results.instrument_type === "etfs" || results.stocks.every((s) => s.is_etf)
                      ? "Discovered ETFs"
                      : "Discovered Stocks"
                    : "Stocks Mentioned"}
                </CardTitle>
                <CardDescription className="text-small">
                  {results?.stocks && results.stocks.length > 0
                    ? results.instrument_type === "etfs" || results.stocks.every((s) => s.is_etf)
                      ? "Top ETFs matching your query"
                      : "Top stocks matching your query"
                    : "Relevant to your search query"}
                </CardDescription>
              </div>
              <Button variant="ghost" size="icon-sm" onClick={() => setRailOpen(false)} aria-label="Collapse rail">
                <PanelRightClose className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {results && results.stocks && results.stocks.length > 0 ? (
              <div className="flex flex-col gap-3">
                {results.stocks.slice(0, 8).map((stock: StockDiscoveryResult, i: number) => (
                  <div key={i} className="flex items-center justify-between border-b border-line pb-2.5 last:border-0 last:pb-0">
                    <div className="flex max-w-[160px] flex-col gap-0.5">
                      <div className="flex items-center gap-1.5">
                        <Link href={`/tickers/${stock.ticker}`} className="font-mono text-small font-semibold text-ink hover:text-signal hover:underline">
                          {stock.ticker}
                        </Link>
                        {stock.is_etf && (
                          <Badge variant="outline" className="border-info/30 bg-info/10 px-1 py-0 text-micro text-info">
                            ETF
                          </Badge>
                        )}
                      </div>
                      <span className="line-clamp-1 text-small text-ink-secondary">
                        {stock.themes.slice(0, 2).join(", ") || "—"}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="font-mono text-micro text-ink-faint">{stock.mention_count}×</span>
                      <Badge
                        variant={stock.avg_sentiment > 0.2 ? "default" : stock.avg_sentiment < -0.2 ? "destructive" : "secondary"}
                        className="px-2 py-0 font-mono text-micro font-semibold uppercase tracking-wider"
                      >
                        {stock.avg_sentiment > 0.2 ? "bullish" : stock.avg_sentiment < -0.2 ? "bearish" : "neutral"}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            ) : results && results.predictions?.length > 0 ? (
              <div className="flex flex-col gap-3">
                {results.predictions
                  .filter((p: Prediction) => p.ticker)
                  .map((p: Prediction, i: number) => (
                    <div key={i} className="flex items-center justify-between border-b border-line pb-2.5 last:border-0 last:pb-0">
                      <div className="flex max-w-[160px] flex-col gap-0.5">
                        <Link href={`/tickers/${p.ticker}`} className="font-mono text-small font-semibold text-ink hover:text-signal hover:underline">
                          {p.ticker}
                        </Link>
                        <span className="line-clamp-1 text-small text-ink-secondary">
                          {p.prediction_text}
                        </span>
                      </div>
                      <Badge
                        variant={p.direction === "bullish" ? "default" : p.direction === "bearish" ? "destructive" : "secondary"}
                        className="px-2 py-0 font-mono text-micro font-semibold uppercase tracking-wider"
                      >
                        {p.direction}
                      </Badge>
                    </div>
                  ))}
              </div>
            ) : (
              <p className="text-small text-ink-secondary">
                No explicit stocks found in these search results.
              </p>
            )}
          </CardContent>
        </Card>
      ) : (
        <Button
          variant="outline"
          size="sm"
          onClick={() => setRailOpen(true)}
          className="fixed bottom-4 right-4 z-40 gap-1.5 lg:sticky lg:top-4 lg:self-start"
          aria-label="Expand rail"
        >
          <PanelRightOpen className="h-4 w-4" />
          Discover
        </Button>
      )} */}

      {/* Timestamp Playback Modal */}
      {playbackModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-scrim p-4 backdrop-blur-sm animate-in fade-in duration-150">
          <div className="relative flex w-full max-w-3xl flex-col gap-4 rounded-lg border border-line bg-panel p-6 shadow-2xl">
            {/* Modal Header */}
            <div className="flex items-start justify-between gap-4">
              <div className="flex flex-col gap-1 pr-6">
                {playbackModal.channelTitle && (
                  <span className="font-mono text-micro font-semibold uppercase tracking-[0.1em] text-signal">
                    {playbackModal.channelTitle}
                  </span>
                )}
                <h2 className="leading-snug text-heading font-semibold text-ink">
                  {playbackModal.title}
                </h2>
                <div className="mt-0.5 flex items-center gap-2">
                  <span className="rounded border border-bullish/20 bg-bullish/10 px-2 py-0.5 font-mono text-micro text-bullish">
                    Playing @ {formatTime(playbackModal.startSec)}
                  </span>
                </div>
              </div>
              <button
                onClick={() => setPlaybackModal(null)}
                className="rounded-md p-1.5 text-ink-faint transition-colors hover:bg-panel-raised hover:text-ink"
                aria-label="Close modal"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Video Player Embed */}
            {playbackModal.youtubeVideoId ? (
              <div className="aspect-video w-full overflow-hidden rounded-lg border border-line bg-black shadow-lg">
                <iframe
                  width="100%"
                  height="100%"
                  src={`https://www.youtube.com/embed/${playbackModal.youtubeVideoId}?start=${Math.floor(playbackModal.startSec)}&autoplay=1`}
                  title={playbackModal.title}
                  frameBorder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                ></iframe>
              </div>
            ) : (
              <div className="flex aspect-video w-full flex-col items-center justify-center gap-2 rounded-lg border border-line bg-panel-raised text-small text-ink-secondary">
                <p>YouTube ID not found for this video segment.</p>
                <Link href={`/videos/${playbackModal.videoId}`}>
                  <Button variant="secondary" size="sm">Go to Video Page</Button>
                </Link>
              </div>
            )}

            {/* Transcript Snippet & Direct Link */}
            <div className="flex items-center justify-between gap-4 rounded-md border border-line bg-panel-raised p-3.5">
              <p className="line-clamp-2 flex-1 text-small italic text-ink-secondary">
                &quot;{playbackModal.text}&quot;
              </p>
              <Link href={`/videos/${playbackModal.videoId}?t=${Math.floor(playbackModal.startSec)}`}>
                <Button variant="outline" size="sm" className="whitespace-nowrap gap-1">
                  <ExternalLink className="h-3.5 w-3.5" /> Full Video Page
                </Button>
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={
      <div className="flex h-full items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin text-ink-faint" />
      </div>
    }>
      <SearchPageContent />
    </Suspense>
  );
}
