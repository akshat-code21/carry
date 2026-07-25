"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, Plus, X } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function ChannelPage() {
  const params = useParams();
  const id = params.id as string;

  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Ingest-video form state
  const [showIngestForm, setShowIngestForm] = useState(false);
  const [youtubeVideoId, setYoutubeVideoId] = useState("");
  const [ingesting, setIngesting] = useState(false);
  const [ingestFeedback, setIngestFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

  async function loadChannel() {
    try {
      const res = await api.getChannel(id);
      setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadChannel();
  }, [id]);

  async function handleIngest(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = youtubeVideoId.trim();
    if (!trimmed) return;

    setIngesting(true);
    setIngestFeedback(null);

    try {
      const res = await api.ingestSingleVideo(id, trimmed);
      setIngestFeedback({
        type: "success",
        message: `Video ingestion queued! Task ID: ${res.task_id}`,
      });
      setYoutubeVideoId("");
      // Reload channel data after a short delay to pick up the new video
      setTimeout(() => loadChannel(), 5000);
    } catch (err: any) {
      setIngestFeedback({
        type: "error",
        message: err.message || "Something went wrong",
      });
    } finally {
      setIngesting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4">
        <h2 className="text-2xl font-bold">Channel Not Found</h2>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 pb-10">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{data.channel.title}</h1>
          <p className="text-muted-foreground line-clamp-2 max-w-3xl mt-2">
            {data.channel.description}
          </p>
        </div>
        <Button
          onClick={() => {
            setShowIngestForm((prev) => !prev);
            setIngestFeedback(null);
          }}
          variant={showIngestForm ? "outline" : "default"}
          className="shrink-0"
        >
          {showIngestForm ? (
            <>
              <X className="mr-2 h-4 w-4" /> Cancel
            </>
          ) : (
            <>
              <Plus className="mr-2 h-4 w-4" /> Process Video
            </>
          )}
        </Button>
      </div>

      {/* Inline ingest-video form */}
      {showIngestForm && (
        <Card>
          <CardHeader>
            <CardTitle>Ingest a Single Video</CardTitle>
            <CardDescription>
              Enter a YouTube Video ID (e.g. <code className="text-xs bg-muted px-1 py-0.5 rounded">dQw4w9WgXcQ</code>) to ingest and process it for this channel.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleIngest} className="flex flex-col gap-4 sm:flex-row sm:items-end">
              <div className="flex-1 space-y-1.5">
                <label htmlFor="youtubeVideoId" className="text-sm font-medium">
                  YouTube Video ID
                </label>
                <Input
                  id="youtubeVideoId"
                  placeholder="e.g. _RXAoo-V9Nw"
                  value={youtubeVideoId}
                  onChange={(e) => setYoutubeVideoId(e.target.value)}
                  required
                />
              </div>
              <Button type="submit" disabled={ingesting || !youtubeVideoId.trim()}>
                {ingesting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Submitting…
                  </>
                ) : (
                  "Start Ingestion"
                )}
              </Button>
            </form>

            {ingestFeedback && (
              <p
                className={`mt-3 text-sm ${
                  ingestFeedback.type === "success" ? "text-green-600" : "text-red-600"
                }`}
              >
                {ingestFeedback.message}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 md:grid-cols-3">
        <div className="md:col-span-2 flex flex-col gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Videos ({data.videos?.length || 0})</CardTitle>
              <CardDescription>Processed videos from this channel</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4">
                {data.videos?.map((v: any) => (
                  <div key={v.id} className="flex flex-col gap-2 rounded-lg border p-4">
                    <Link href={`/videos/${v.id}`} className="font-semibold hover:underline text-lg">
                      {v.title}
                    </Link>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>Published: {new Date(v.published_at).toLocaleDateString()}</span>
                      <span>Duration: {Math.floor(v.duration_sec / 60)} mins</span>
                    </div>
                  </div>
                ))}
                {(!data.videos || data.videos.length === 0) && (
                  <p className="text-sm text-muted-foreground">No videos processed yet.</p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="flex flex-col gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Top Stocks Discussed</CardTitle>
              <CardDescription>Based on extraction & theme mapping</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              {data.top_stocks?.slice(0, 15).map((s: any) => (
                <div key={s.ticker} className="flex items-center justify-between border-b pb-2 last:border-0 last:pb-0">
                  <div className="flex flex-col">
                    <Link href={`/tickers/${s.ticker}`} className="font-bold hover:underline">
                      {s.ticker}
                    </Link>
                    <span className="text-xs text-muted-foreground">
                      Score: {(s.weighted_relevance * 100).toFixed(0)}
                    </span>
                  </div>
                  <Badge variant={s.avg_sentiment > 0.2 ? "default" : s.avg_sentiment < -0.2 ? "destructive" : "secondary"}>
                    {s.total_mentions} Mentions
                  </Badge>
                </div>
              ))}
              {(!data.top_stocks || data.top_stocks.length === 0) && (
                <p className="text-sm text-muted-foreground">No stocks aggregated yet.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
