"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loader2, Plus, X, Tv } from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/PageHeader";
import { EmptyState } from "@/components/EmptyState";
import { DataTable, type Column } from "@/components/DataTable";
import { DashboardSkeleton } from "@/components/skeletons/LayoutSkeletons";
import { useChannels, useBackfillChannel, useMe } from "@/lib/hooks";

type ChannelRow = NonNullable<Awaited<ReturnType<typeof useChannels>>["data"]>[number];

export default function ChannelsPage() {
  const router = useRouter();
  const { data: channels = [], isLoading } = useChannels();
  const backfillMutation = useBackfillChannel();
  const { isAdmin } = useMe();

  // Form state
  const [showForm, setShowForm] = useState(false);
  const [channelId, setChannelId] = useState("");
  const [maxVideos, setMaxVideos] = useState("50");
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = channelId.trim();
    if (!trimmed) return;

    setFeedback(null);
    try {
      const res = await backfillMutation.mutateAsync({
        youtubeChannelId: trimmed,
        maxVideos: parseInt(maxVideos, 10) || 50,
      });
      setFeedback({
        type: "success",
        message: `Backfill queued! Task ID: ${res.task_id}`,
      });
      setChannelId("");
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : "Something went wrong";
      setFeedback({
        type: "error",
        message: errorMessage,
      });
    }
  }

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Channels"
        description="Browse all tracked financial YouTube channels and ingest new sources."
      >
        {isAdmin && (
          <Button
            onClick={() => {
              setShowForm((prev) => !prev);
              setFeedback(null);
            }}
            variant={showForm ? "outline" : "default"}
          >
            {showForm ? (
              <>
                <X className="mr-2 h-4 w-4" /> Cancel
              </>
            ) : (
              <>
                <Plus className="mr-2 h-4 w-4" /> Add Channel
              </>
            )}
          </Button>
        )}
      </PageHeader>

      {/* Inline add-channel form */}
      {showForm && isAdmin && (
        <Card>
          <CardHeader>
            <CardTitle>Add a YouTube Channel</CardTitle>
            <CardDescription>
              Enter a YouTube Channel ID (e.g. <code className="rounded bg-panel-raised px-1 py-0.5 font-mono text-micro text-signal">UC...</code>) to backfill its videos.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="flex flex-col gap-4 sm:flex-row sm:items-end">
              <div className="flex-1 space-y-1.5">
                <label htmlFor="channelId" className="text-small font-medium text-ink">
                  YouTube Channel ID
                </label>
                <Input
                  id="channelId"
                  placeholder="UCxxxxxxxxxxxxxxxxxxxxxxxx"
                  value={channelId}
                  onChange={(e) => setChannelId(e.target.value)}
                  required
                />
              </div>
              <div className="w-28 space-y-1.5">
                <label htmlFor="maxVideos" className="text-small font-medium text-ink">
                  Max Videos
                </label>
                <Input
                  id="maxVideos"
                  type="number"
                  min={1}
                  max={500}
                  value={maxVideos}
                  onChange={(e) => setMaxVideos(e.target.value)}
                />
              </div>
              <Button type="submit" disabled={backfillMutation.isPending || !channelId.trim()}>
                {backfillMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Submitting…
                  </>
                ) : (
                  "Start Backfill"
                )}
              </Button>
            </form>

            {feedback && (
              <p
                className={`mt-3 text-small ${
                  feedback.type === "success" ? "text-bullish" : "text-bearish"
                }`}
              >
                {feedback.message}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {channels.length === 0 ? (
        <EmptyState
          icon={<Tv className="h-6 w-6" />}
          title="No channels tracked yet"
          description="Add a channel above to begin backfilling and analyzing video transcripts."
        />
      ) : (
        <DataTable
          columns={channelColumns}
          data={channels}
          keyExtractor={(ch) => ch.id}
          onRowClick={(ch) => router.push(`/channels/${ch.id}`)}
          emptyState={
            <EmptyState
              icon={<Tv className="h-6 w-6" />}
              title="No channels tracked yet"
              description="Add a channel above to begin backfilling and analyzing video transcripts."
            />
          }
        />
      )}
    </div>
  );
}

const channelColumns: Column<ChannelRow>[] = [
  {
    key: "title",
    header: "Channel",
    render: (ch) => (
      <div className="flex min-w-0 flex-col gap-0.5 py-0.5">
        <Link
          href={`/channels/${ch.id}`}
          className="truncate text-small font-semibold text-ink hover:text-signal hover:underline"
          onClick={(e) => e.stopPropagation()}
        >
          {ch.title}
        </Link>
        {ch.description && (
          <span className="truncate text-caption text-ink-faint" title={ch.description}>
            {ch.description}
          </span>
        )}
      </div>
    ),
  },
  {
    key: "video_count",
    header: "Videos",
    numeric: true,
    headerClassName: "w-20",
    render: (ch) =>
      typeof ch.video_count === "number" ? (
        <span className="numeric text-small text-ink">{ch.video_count}</span>
      ) : (
        <span className="text-ink-faint">—</span>
      ),
  },
];
