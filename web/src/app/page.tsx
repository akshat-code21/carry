"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api, SearchResult, StockDiscoveryResult } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Search, Loader2, Play, ExternalLink, X, Tv, TrendingUp, TrendingDown, BarChart3, MessageSquare } from "lucide-react";
import Link from "next/link";

interface PlaybackModalState {
  videoId: string;
  youtubeVideoId?: string;
  title: string;
  channelTitle?: string;
  startSec: number;
  text: string;
}

function SearchPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const initialQuery = searchParams.get("q") || "";
  const initialType = (searchParams.get("type") as "keyword" | "semantic" | "hybrid") || "hybrid";

  const [query, setQuery] = useState(initialQuery);
  const [type, setType] = useState<"keyword" | "semantic" | "hybrid">(initialType);
  const [results, setResults] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [playbackModal, setPlaybackModal] = useState<PlaybackModalState | null>(null);

  // Sync state with URL params & execute search when q is present
  useEffect(() => {
    const qParam = searchParams.get("q") || "";
    const typeParam = (searchParams.get("type") as "keyword" | "semantic" | "hybrid") || "hybrid";

    setQuery(qParam);
    setType(typeParam);

    if (qParam.trim()) {
      executeSearch(qParam, typeParam);
    }
  }, [searchParams]);

  const executeSearch = async (searchQuery: string, searchType: "keyword" | "semantic" | "hybrid") => {
    setLoading(true);
    try {
      const data = await api.search(searchQuery, searchType);
      setResults(data);
    } catch (err) {
      console.error("Search failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    router.push(`/?q=${encodeURIComponent(query.trim())}&type=${type}`);
  };

  const handleTypeChange = (newType: "keyword" | "semantic" | "hybrid") => {
    setType(newType);
    if (query.trim()) {
      router.push(`/?q=${encodeURIComponent(query.trim())}&type=${newType}`);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="flex h-full gap-6">
      {/* Main Search Area */}
      <div className="flex-1 flex flex-col gap-6">
        <div className="flex flex-col gap-2">
          <h1 className="text-3xl font-bold tracking-tight">Search</h1>
          <p className="text-muted-foreground">
            Search transcripts, predictions, and themes across all channels.
          </p>
        </div>

        {/* Search Container Box */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5 shadow-sm">
          <form onSubmit={handleSearchSubmit} className="flex flex-col gap-4">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3.5 top-3.5 h-4 w-4 text-zinc-400 z-10" />
                <input
                  type="text"
                  placeholder="Search for 'AI chips', 'inflation', 'Nvidia'..."
                  className="flex h-11 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 pl-10 text-sm text-white placeholder:text-zinc-500 focus:border-zinc-400 focus:outline-none"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
              </div>
              <Button type="submit" disabled={loading} className="h-11 px-6 font-semibold bg-indigo-600 hover:bg-indigo-500 text-white">
                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Search
              </Button>
            </div>

            <div className="flex items-center gap-3 pt-1">
              <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Search Type:</span>
              <div className="flex gap-1 bg-zinc-950 p-1 rounded-md border border-zinc-800">
                {(["keyword", "semantic", "hybrid"] as const).map((t) => (
                  <Button
                    key={t}
                    type="button"
                    variant={type === t ? "default" : "ghost"}
                    size="sm"
                    className="capitalize h-7 text-xs font-medium"
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
          <div className="flex flex-col gap-4 pb-10">
            {/* Stock Discovery Cards — shown prominently for exploratory queries */}
            {results.stocks && results.stocks.length > 0 && (
              <div className="flex flex-col gap-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5 text-indigo-400" />
                    <h2 className="text-xl font-semibold text-zinc-100">
                      Top Stocks ({results.stocks.length})
                    </h2>
                  </div>
                  <Badge variant="secondary" className="bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 text-xs">
                    AI-Powered Discovery
                  </Badge>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {results.stocks.map((stock: StockDiscoveryResult, idx: number) => {
                    const sentimentColor =
                      stock.avg_sentiment > 0.2 ? "text-emerald-400" :
                      stock.avg_sentiment < -0.2 ? "text-red-400" : "text-zinc-400";
                    const sentimentLabel =
                      stock.avg_sentiment > 0.2 ? "Bullish" :
                      stock.avg_sentiment < -0.2 ? "Bearish" : "Neutral";
                    const SentimentIcon = stock.avg_sentiment > 0.2 ? TrendingUp : stock.avg_sentiment < -0.2 ? TrendingDown : BarChart3;

                    return (
                      <Card key={stock.ticker} className="border-zinc-800/80 bg-zinc-900/60 hover:border-indigo-500/40 transition-all duration-200 hover:shadow-lg hover:shadow-indigo-500/5">
                        <CardContent className="p-4 flex flex-col gap-3">
                          {/* Ticker + Score Row */}
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2.5">
                              <span className="text-xs font-bold text-zinc-500 w-5">#{idx + 1}</span>
                              <Link href={`/tickers/${stock.ticker}`} className="hover:text-indigo-400 transition-colors">
                                <span className="text-lg font-bold text-white tracking-tight">${stock.ticker}</span>
                              </Link>
                            </div>
                            <div className="flex items-center gap-2">
                              <div className={`flex items-center gap-1 ${sentimentColor}`}>
                                <SentimentIcon className="h-3.5 w-3.5" />
                                <span className="text-xs font-semibold">{sentimentLabel}</span>
                              </div>
                              {stock.bullish_pct > 0 && (
                                <span className="text-[10px] text-emerald-400/70 font-mono">{stock.bullish_pct}% bull</span>
                              )}
                            </div>
                          </div>

                          {/* Stats Row */}
                          <div className="flex items-center gap-4 text-xs text-zinc-400">
                            <div className="flex items-center gap-1">
                              <MessageSquare className="h-3 w-3" />
                              <span>{stock.mention_count} mentions</span>
                            </div>
                            <div className="flex items-center gap-1">
                              <BarChart3 className="h-3 w-3" />
                              <span>{stock.prediction_count} predictions</span>
                            </div>
                            {stock.avg_confidence > 0 && (
                              <span className="font-mono text-zinc-500">
                                {(stock.avg_confidence * 100).toFixed(0)}% conf
                              </span>
                            )}
                          </div>

                          {/* Themes */}
                          {stock.themes.length > 0 && (
                            <div className="flex flex-wrap gap-1.5">
                              {stock.themes.slice(0, 3).map((theme) => (
                                <Badge key={theme} variant="outline" className="text-[10px] text-indigo-300/80 border-indigo-500/20 bg-indigo-500/5 px-2 py-0">
                                  {theme}
                                </Badge>
                              ))}
                              {stock.themes.length > 3 && (
                                <Badge variant="outline" className="text-[10px] text-zinc-500 border-zinc-700 px-2 py-0">
                                  +{stock.themes.length - 3} more
                                </Badge>
                              )}
                            </div>
                          )}

                          {/* Sample Prediction */}
                          {stock.sample_predictions.length > 0 && (
                            <div className="border-l-2 border-zinc-700 pl-3 py-1">
                              <p className="text-xs text-zinc-400 italic line-clamp-2">
                                "{stock.sample_predictions[0].text}"
                              </p>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Transcript Segments Header */}
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-zinc-100">
                {results.stocks && results.stocks.length > 0 ? "Related Segments" : "Results"} ({results.segments?.length || 0})
              </h2>
              {query && (
                <span className="text-xs text-zinc-400">
                  Showing matches for &quot;{query}&quot;
                </span>
              )}
            </div>

            <div className="grid gap-4">
              {results.segments?.map((seg) => {
                const video = results.videos?.[seg.video_id];
                const channel = results.channels?.[video?.channel_id] || (seg.channel_title ? { title: seg.channel_title } : null);

                const videoTitle = seg.video_title || video?.title || `Video Segment (${seg.video_id.slice(0, 8)}...)`;
                const channelTitle = seg.channel_title || channel?.title;
                const youtubeVideoId = seg.youtube_video_id || video?.youtube_video_id;

                return (
                  <Card key={seg.id} className="border-zinc-800/80 bg-zinc-900/40 hover:border-zinc-700 transition-all duration-150">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex flex-col gap-1.5 flex-1">
                          {channelTitle && (
                            <div className="flex items-center gap-1.5 text-xs text-zinc-400">
                              <Tv className="h-3.5 w-3.5 text-indigo-400" />
                              <span className="font-medium text-zinc-300">{channelTitle}</span>
                            </div>
                          )}
                          <Link href={`/videos/${seg.video_id}?t=${Math.floor(seg.start_sec)}`} className="group">
                            <CardTitle className="text-base font-semibold text-zinc-100 group-hover:text-indigo-400 transition-colors leading-snug">
                              {videoTitle}
                            </CardTitle>
                          </Link>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          <Badge variant="secondary" className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-mono">
                            {(seg.rank * 100).toFixed(1)}% match
                          </Badge>
                          <Badge variant="outline" className="capitalize text-xs text-zinc-400 border-zinc-800">
                            {seg.search_type}
                          </Badge>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="flex flex-col gap-4">
                      <div className="border-l-2 border-indigo-500/80 bg-zinc-950/50 py-3 px-4 rounded-r-lg">
                        <p className="text-sm text-zinc-300 italic leading-relaxed">
                          "{seg.text}"
                        </p>
                      </div>
                      <div className="flex items-center gap-3">
                        <Link href={`/videos/${seg.video_id}?t=${Math.floor(seg.start_sec)}`}>
                          <Button variant="outline" size="sm" className="border-zinc-800 text-zinc-300 hover:bg-zinc-800 hover:text-white h-8 text-xs gap-1.5">
                            <Play className="h-3.5 w-3.5" />
                            Play @ {formatTime(seg.start_sec)}
                          </Button>
                        </Link>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}

              {(!results.segments || results.segments.length === 0) && (
                <div className="rounded-xl border border-dashed border-zinc-800 p-8 text-center text-zinc-500">
                  No matching transcript segments found. Try adjusting your query or search type.
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Right Sidebar - Dynamic Top Stocks */}
      <div className="w-80 flex-shrink-0 flex flex-col gap-4">
        <Card className="border-zinc-800 bg-zinc-900/40">
          <CardHeader>
            <CardTitle className="text-base font-semibold">
              {results?.stocks && results.stocks.length > 0 ? "Discovered Stocks" : "Stocks Mentioned"}
            </CardTitle>
            <CardDescription className="text-xs">
              {results?.stocks && results.stocks.length > 0
                ? "Top stocks matching your query"
                : "Relevant to your search query"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {/* Show discovered stocks if sector_discovery, else show predictions */}
            {results && results.stocks && results.stocks.length > 0 ? (
              <div className="flex flex-col gap-3">
                {results.stocks.slice(0, 8).map((stock: StockDiscoveryResult, i: number) => (
                  <div key={i} className="flex items-center justify-between border-b border-zinc-800/60 pb-2.5 last:border-0 last:pb-0">
                    <div className="flex flex-col gap-0.5 max-w-[190px]">
                      <Link href={`/tickers/${stock.ticker}`} className="font-bold text-sm text-zinc-200 hover:text-indigo-400 hover:underline">
                        ${stock.ticker}
                      </Link>
                      <span className="text-xs text-zinc-400 line-clamp-1">
                        {stock.themes.slice(0, 2).join(", ") || "—"}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] text-zinc-500 font-mono">{stock.mention_count}×</span>
                      <Badge
                        variant={stock.avg_sentiment > 0.2 ? "default" : stock.avg_sentiment < -0.2 ? "destructive" : "secondary"}
                        className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5"
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
                    <div key={i} className="flex items-center justify-between border-b border-zinc-800/60 pb-2.5 last:border-0 last:pb-0">
                      <div className="flex flex-col gap-0.5 max-w-[190px]">
                        <Link href={`/tickers/${p.ticker}`} className="font-bold text-sm text-zinc-200 hover:text-indigo-400 hover:underline">
                          ${p.ticker}
                        </Link>
                        <span className="text-xs text-zinc-400 line-clamp-1">
                          {p.prediction_text}
                        </span>
                      </div>
                      <Badge
                        variant={p.direction === "bullish" ? "default" : p.direction === "bearish" ? "destructive" : "secondary"}
                        className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5"
                      >
                        {p.direction}
                      </Badge>
                    </div>
                  ))}
              </div>
            ) : (
              <p className="text-xs text-zinc-500">
                No explicit stocks found in these search results.
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Timestamp Playback Modal */}
      {playbackModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-150">
          <div className="relative w-full max-w-3xl rounded-xl border border-zinc-800 bg-zinc-950 p-6 shadow-2xl flex flex-col gap-4">
            {/* Modal Header */}
            <div className="flex items-start justify-between gap-4">
              <div className="flex flex-col gap-1 pr-6">
                {playbackModal.channelTitle && (
                  <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">
                    {playbackModal.channelTitle}
                  </span>
                )}
                <h2 className="text-lg font-bold text-zinc-100 leading-snug">
                  {playbackModal.title}
                </h2>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="font-mono text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
                    Playing @ {formatTime(playbackModal.startSec)}
                  </span>
                </div>
              </div>
              <button
                onClick={() => setPlaybackModal(null)}
                className="rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-800 hover:text-white transition-colors"
                aria-label="Close modal"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Video Player Embed */}
            {playbackModal.youtubeVideoId ? (
              <div className="aspect-video w-full overflow-hidden rounded-lg border border-zinc-800 bg-black shadow-lg">
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
              <div className="aspect-video w-full flex flex-col items-center justify-center gap-2 rounded-lg border border-zinc-800 bg-zinc-900 text-zinc-400 text-sm">
                <p>YouTube ID not found for this video segment.</p>
                <Link href={`/videos/${playbackModal.videoId}`}>
                  <Button variant="secondary" size="sm">Go to Video Page</Button>
                </Link>
              </div>
            )}

            {/* Transcript Snippet & Direct Link */}
            <div className="flex items-center justify-between gap-4 bg-zinc-900/80 p-3.5 rounded-lg border border-zinc-800">
              <p className="text-xs text-zinc-300 italic line-clamp-2 flex-1">
                "{playbackModal.text}"
              </p>
              <Link href={`/videos/${playbackModal.videoId}?t=${Math.floor(playbackModal.startSec)}`}>
                <Button variant="outline" size="sm" className="whitespace-nowrap text-xs gap-1 border-zinc-700 text-zinc-200">
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
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    }>
      <SearchPageContent />
    </Suspense>
  );
}
