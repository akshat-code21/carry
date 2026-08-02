"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { StockDiscoveryResult } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/PageHeader";
import {
  Search,
  Loader2,
  Play,
  ExternalLink,
  X,
  Tv,
  TrendingUp,
  TrendingDown,
  BarChart3,
  MessageSquare,
  PanelRightClose,
  PanelRightOpen,
} from "lucide-react";
import Link from "next/link";
import { useSearch } from "@/lib/hooks";
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

function SearchPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const reducedMotion = useReducedMotion();

  const activeQuery = searchParams.get("q") || "";
  const activeType = (searchParams.get("type") as "keyword" | "semantic" | "hybrid") || "hybrid";

  const [query, setQuery] = useState(activeQuery);
  const [type, setType] = useState<"keyword" | "semantic" | "hybrid">(activeType);
  const [playbackModal, setPlaybackModal] = useState<PlaybackModalState | null>(null);
  const [railOpen, setRailOpen] = useState(true);

  const { data: results, isLoading: loading } = useSearch(activeQuery, activeType);

  useEffect(() => {
    setQuery(activeQuery);
    setType(activeType);
  }, [activeQuery, activeType]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    router.push(`/search?q=${encodeURIComponent(query.trim())}&type=${type}`);
  };

  const handleTypeChange = (newType: "keyword" | "semantic" | "hybrid") => {
    setType(newType);
    if (query.trim()) {
      router.push(`/search?q=${encodeURIComponent(query.trim())}&type=${newType}`);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const revealAnim = reducedMotion ? {} : containerVariants;
  const itemAnim = reducedMotion ? {} : itemVariants;

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
              <Button type="submit" disabled={loading}>
                {loading && <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />}
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
                    size="sm"
                    className={cn("h-7 capitalize", `${type === t ? "text-black h-7 capitalize" : " text-white h-7 capitalize"}`)}
                    onClick={() => handleTypeChange(t)}
                  >
                    {t}
                  </Button>
                ))}
              </div>
            </div>
          </form>
        </div>

        {results && (
          <motion.div
            className="flex flex-col gap-4 pb-10"
            variants={revealAnim}
            initial={reducedMotion ? false : "hidden"}
            animate="show"
          >
            {/* Stock / ETF Discovery Cards — shown prominently for exploratory queries */}
            {results.stocks && results.stocks.length > 0 && (
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
                  <Badge variant="outline" className="border-signal/30 bg-signal/10 text-micro text-signal">
                    AI-Powered Discovery
                  </Badge>
                </div>

                <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                  {results.stocks.map((stock: StockDiscoveryResult, idx: number) => {
                    const sentimentColor =
                      stock.avg_sentiment > 0.2 ? "text-bullish" :
                        stock.avg_sentiment < -0.2 ? "text-bearish" : "text-ink-secondary";
                    const sentimentLabel =
                      stock.avg_sentiment > 0.2 ? "Bullish" :
                        stock.avg_sentiment < -0.2 ? "Bearish" : "Neutral";
                    const SentimentIcon = stock.avg_sentiment > 0.2 ? TrendingUp : stock.avg_sentiment < -0.2 ? TrendingDown : BarChart3;

                    return (
                      <motion.div key={stock.ticker} variants={itemAnim}>
                        <Card className="h-full transition-colors hover:border-signal/40">
                          <CardContent className="flex flex-col gap-3 p-4">
                            {/* Ticker + Score Row */}
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2.5">
                                <span className="w-5 font-mono text-micro font-semibold text-ink-faint">#{idx + 1}</span>
                                <Link href={`/tickers/${stock.ticker}`} className="transition-colors hover:text-signal">
                                  <span className="font-mono text-title font-semibold tracking-tight text-ink">${stock.ticker}</span>
                                </Link>
                                {stock.is_etf && (
                                  <Badge variant="outline" className="border-warning/30 bg-warning/10 px-1.5 py-0 text-micro text-warning">
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

                            {/* Stats Row */}
                            <div className="flex items-center gap-4 font-mono text-small text-ink-secondary">
                              <div className="flex items-center gap-1">
                                <MessageSquare className="h-3 w-3" />
                                <span>{stock.mention_count} mentions</span>
                              </div>
                              <div className="flex items-center gap-1">
                                <BarChart3 className="h-3 w-3" />
                                <span>{stock.prediction_count} predictions</span>
                              </div>
                              {stock.avg_confidence > 0 && (
                                <span>{(stock.avg_confidence * 100).toFixed(0)}% conf</span>
                              )}
                            </div>

                            {/* Themes */}
                            {stock.themes.length > 0 && (
                              <div className="flex flex-wrap gap-1.5">
                                {stock.themes.slice(0, 3).map((theme) => (
                                  <Badge key={theme} variant="outline" className="border-signal/20 bg-signal/5 px-2 py-0 text-micro text-signal">
                                    {theme}
                                  </Badge>
                                ))}
                                {stock.themes.length > 3 && (
                                  <Badge variant="outline" className="border-line px-2 py-0 text-micro text-ink-faint">
                                    +{stock.themes.length - 3} more
                                  </Badge>
                                )}
                              </div>
                            )}

                            {/* Sample Prediction */}
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
            )}

            {/* Transcript Segments Header */}
            <div className="flex items-center justify-between">
              <h2 className="font-display text-heading font-semibold text-ink">
                {results.stocks && results.stocks.length > 0 ? "Related Segments" : "Results"} ({results.segments?.length || 0})
              </h2>
              {query && (
                <span className="font-mono text-micro text-ink-faint">
                  matching &quot;{query}&quot;
                </span>
              )}
            </div>

            <div className="grid gap-3">
              {results.segments?.map((seg) => {
                const video = results.videos?.[seg.video_id];
                const channel = results.channels?.[video?.channel_id] || (seg.channel_title ? { title: seg.channel_title } : null);

                const videoTitle = seg.video_title || video?.title || `Video Segment (${seg.video_id.slice(0, 8)}...)`;
                const channelTitle = seg.channel_title || channel?.title;
                const youtubeVideoId = seg.youtube_video_id || video?.youtube_video_id;

                return (
                  <motion.div key={seg.id} variants={itemAnim}>
                    <Card className="transition-colors hover:border-line-strong">
                      <CardHeader className="pb-3">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex flex-1 flex-col gap-1.5">
                            {channelTitle && (
                              <div className="flex items-center gap-1.5 text-small text-ink-secondary">
                                <Tv className="h-3.5 w-3.5 text-signal" />
                                <span className="font-medium">{channelTitle}</span>
                              </div>
                            )}
                            <Link href={`/videos/${seg.video_id}?t=${Math.floor(seg.start_sec)}`} className="group">
                              <CardTitle className="leading-snug text-title font-semibold transition-colors group-hover:text-signal">
                                {videoTitle}
                              </CardTitle>
                            </Link>
                          </div>
                          <div className="flex shrink-0 items-center gap-2">
                            <Badge variant="outline" className="border-bullish/30 bg-bullish/10 font-mono text-micro text-bullish">
                              {(seg.rank * 100).toFixed(1)}% match
                            </Badge>
                            <Badge variant="outline" className="font-mono text-micro capitalize text-ink-secondary">
                              {seg.search_type}
                            </Badge>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent className="flex flex-col gap-3">
                        {/* Evidence block quote */}
                        <div className="rounded-r-md border-l-2 border-signal bg-panel-raised px-4 py-3">
                          <p className="text-body italic leading-relaxed text-ink">
                            &quot;{seg.text}&quot;
                          </p>
                        </div>
                        <div className="flex items-center gap-3">
                          <Link href={`/videos/${seg.video_id}?t=${Math.floor(seg.start_sec)}`}>
                            <Button variant="outline" size="sm" className="gap-1.5">
                              <Play className="h-3.5 w-3.5" />
                              Play @ {formatTime(seg.start_sec)}
                            </Button>
                          </Link>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                );
              })}

              {(!results.segments || results.segments.length === 0) && (
                <div className="rounded-lg border border-dashed border-line px-6 py-10 text-center">
                  <p className="text-body font-medium text-ink">No transcript segments found</p>
                  <p className="mt-1 text-small text-ink-secondary">
                    Try a broader keyword, or switch to semantic search for concept matching.
                  </p>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </div>

      {/* Right Rail - Dynamic Top Stocks / ETFs */}
      {railOpen ? (
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
            {/* Show discovered stocks/ETFs if sector_discovery, else show predictions */}
            {results && results.stocks && results.stocks.length > 0 ? (
              <div className="flex flex-col gap-3">
                {results.stocks.slice(0, 8).map((stock: StockDiscoveryResult, i: number) => (
                  <div key={i} className="flex items-center justify-between border-b border-line pb-2.5 last:border-0 last:pb-0">
                    <div className="flex max-w-[160px] flex-col gap-0.5">
                      <div className="flex items-center gap-1.5">
                        <Link href={`/tickers/${stock.ticker}`} className="font-mono text-small font-semibold text-ink hover:text-signal hover:underline">
                          ${stock.ticker}
                        </Link>
                        {stock.is_etf && (
                          <Badge variant="outline" className="border-warning/30 bg-warning/10 px-1 py-0 text-micro text-warning">
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
                  .filter((p: any) => p.ticker)
                  .map((p: any, i: number) => (
                    <div key={i} className="flex items-center justify-between border-b border-line pb-2.5 last:border-0 last:pb-0">
                      <div className="flex max-w-[160px] flex-col gap-0.5">
                        <Link href={`/tickers/${p.ticker}`} className="font-mono text-small font-semibold text-ink hover:text-signal hover:underline">
                          ${p.ticker}
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
      )}

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
