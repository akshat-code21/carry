"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Loader2, Plus, X } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/PageHeader";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { SentimentBadge } from "@/components/SentimentBadge";
import { DetailSkeleton } from "@/components/skeletons/LayoutSkeletons";
import { useChannel, useIngestVideo, useMe } from "@/lib/hooks";

export default function ChannelPage() {
  const params = useParams();
  const id = params.id as string;

  const { data, isLoading } = useChannel(id);
  const ingestMutation = useIngestVideo();
  const { isAdmin } = useMe();

  // Ingest-video form state
  const [showIngestForm, setShowIngestForm] = useState(false);
  const [youtubeVideoId, setYoutubeVideoId] = useState("");
  const [ingestFeedback, setIngestFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

  async function handleIngest(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = youtubeVideoId.trim();
    if (!trimmed) return;

    setIngestFeedback(null);

    try {
      const res = await ingestMutation.mutateAsync({ channelDbId: id, youtubeVideoId: trimmed });
      setIngestFeedback({
        type: "success",
        message: `Video ingestion queued! Task ID: ${res.task_id}`,
      });
      setYoutubeVideoId("");
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Something went wrong";
      setIngestFeedback({
        type: "error",
        message: errorMessage,
      });
    }
  }

  if (isLoading) {
    return <DetailSkeleton />;
  }

  if (!data || !data.channel) {
    return (
      <div className="p-8">
        <ErrorState title="Channel Not Found" message={`No channel details found for ID: ${id}`} />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 pb-10">
      <div className="mb-2 flex gap-2 flex-col items-start w-full">
        <Breadcrumbs
          items={[
            { label: "Channels", href: "/channels" },
            { label: data.channel.title },
          ]}
        />
        <PageHeader
          className="w-full"
          title={data.channel.title}
          description={data.channel.description}
        >
          {isAdmin && (
            <Button
              onClick={() => {
                setShowIngestForm((prev) => !prev);
                setIngestFeedback(null);
              }}
              variant={showIngestForm ? "outline" : "default"}
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
        )}
        </PageHeader>
      </div>

      {/* Inline ingest-video form */}
      {showIngestForm && isAdmin && (
        <Card>
          <CardHeader>
            <CardTitle>Ingest a Single Video</CardTitle>
            <CardDescription>
              Enter a YouTube Video ID (e.g. <code className="rounded bg-panel-raised px-1 py-0.5 font-mono text-micro text-signal">dQw4w9WgXcQ</code>) to ingest and process it for this channel.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleIngest} className="flex flex-col gap-4 sm:flex-row sm:items-end">
              <div className="flex-1 space-y-1.5">
                <label htmlFor="youtubeVideoId" className="text-small font-medium text-ink">
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
              <Button type="submit" disabled={ingestMutation.isPending || !youtubeVideoId.trim()}>
                {ingestMutation.isPending ? (
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
                className={`mt-3 text-small ${ingestFeedback.type === "success" ? "text-bullish" : "text-bearish"
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
              <CardTitle className="text-base font-semibold">Videos ({data.videos?.length || 0})</CardTitle>
              <CardDescription>Processed videos from this channel</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4">
                {data.videos?.map((v) => (
                  <div key={v.id} className="flex flex-col gap-2 rounded-md border border-line p-4">
                    <Link href={`/videos/${v.id}`} className="font-medium text-ink hover:text-signal hover:underline">
                      {v.title}
                    </Link>
                    <div className="flex items-center gap-4 font-mono text-micro text-ink-secondary">
                      <span>Published: {new Date(v.published_at).toLocaleDateString()}</span>
                      <span>Duration: {Math.floor(v.duration_sec / 60)} mins</span>
                    </div>
                  </div>
                ))}
                {(!data.videos || data.videos.length === 0) && (
                  <EmptyState title="No videos processed" description="No videos processed for this channel yet." />
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="flex flex-col gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-semibold">Top Stocks Discussed</CardTitle>
              <CardDescription>Based on extraction & theme mapping</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              {data.top_stocks?.slice(0, 15).map((s) => (
                <div key={s.ticker} className="flex items-center justify-between border-b border-line pb-2 last:border-0 last:pb-0">
                  <div className="flex flex-col">
                    <Link href={`/tickers/${s.ticker}`} className="font-mono font-semibold text-ink hover:text-signal hover:underline">
                      ${s.ticker}
                    </Link>
                    <span className="font-mono text-micro text-ink-secondary">
                      Score: {(s.weighted_relevance * 100).toFixed(0)}
                    </span>
                  </div>
                  <SentimentBadge score={s.avg_sentiment} />
                </div>
              ))}
              {(!data.top_stocks || data.top_stocks.length === 0) && (
                <p className="text-small text-ink-secondary">No stocks aggregated yet.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
