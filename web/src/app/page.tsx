"use client";

import { useState } from "react";
import { api, SearchResult } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Search, Loader2 } from "lucide-react";
import Link from "next/link";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [type, setType] = useState<"keyword" | "semantic" | "hybrid">("hybrid");
  const [results, setResults] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setLoading(true);
    try {
      const data = await api.search(query, type);
      setResults(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
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

        <Card>
          <CardContent className="pt-6">
            <form onSubmit={handleSearch} className="flex flex-col gap-4">
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    type="search"
                    placeholder="Search for 'AI chips', 'inflation', 'Nvidia'..."
                    className="pl-9"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                  />
                </div>
                <Button type="submit" disabled={loading}>
                  {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Search
                </Button>
              </div>
              
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">Search Type:</span>
                <div className="flex gap-1 bg-muted p-1 rounded-md">
                  {(["keyword", "semantic", "hybrid"] as const).map((t) => (
                    <Button
                      key={t}
                      type="button"
                      variant={type === t ? "default" : "ghost"}
                      size="sm"
                      className="capitalize h-7"
                      onClick={() => setType(t)}
                    >
                      {t}
                    </Button>
                  ))}
                </div>
              </div>
            </form>
          </CardContent>
        </Card>

        {results && (
          <div className="flex flex-col gap-4 pb-10">
            <h2 className="text-xl font-semibold">
              Results ({results.segments?.length || 0})
            </h2>
            
            <div className="grid gap-4">
              {results.segments?.map((seg) => {
                const video = results.videos[seg.video_id];
                const channel = video ? results.channels[video.channel_id] : null;
                
                return (
                  <Card key={seg.id}>
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base">
                          {channel?.title} • {video?.title}
                        </CardTitle>
                        <Badge variant="outline" className="capitalize">
                          {seg.search_type}
                        </Badge>
                      </div>
                      <CardDescription>
                        Match Score: {(seg.rank * 100).toFixed(1)}%
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <p className="border-l-2 border-primary pl-4 italic text-muted-foreground">
                        "{seg.text}"
                      </p>
                      <div className="mt-4 flex items-center gap-4">
                        <Link href={`/videos/${seg.video_id}`}>
                          <Button variant="secondary" size="sm">
                            View Video @ {formatTime(seg.start_sec)}
                          </Button>
                        </Link>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Right Sidebar - Dynamic Top Stocks */}
      <div className="w-80 flex-shrink-0 flex flex-col gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Stocks Mentioned</CardTitle>
            <CardDescription>Relevant to your search</CardDescription>
          </CardHeader>
          <CardContent>
            {results && results.predictions?.length > 0 ? (
              <div className="flex flex-col gap-3">
                {results.predictions
                  .filter((p: any) => p.ticker)
                  .map((p: any, i: number) => (
                    <div key={i} className="flex items-center justify-between border-b pb-2 last:border-0 last:pb-0">
                      <div className="flex flex-col">
                        <Link href={`/tickers/${p.ticker}`} className="font-bold hover:underline">
                          {p.ticker}
                        </Link>
                        <span className="text-xs text-muted-foreground line-clamp-1">
                          {p.prediction_text}
                        </span>
                      </div>
                      <Badge variant={p.direction === "bullish" ? "default" : p.direction === "bearish" ? "destructive" : "secondary"}>
                        {p.direction}
                      </Badge>
                    </div>
                  ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                No explicit stocks found in these results.
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
