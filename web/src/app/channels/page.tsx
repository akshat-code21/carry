"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Loader2, Plus, X } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function ChannelsPage() {
  const [channels, setChannels] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Add-channel form state
  const [showForm, setShowForm] = useState(false);
  const [channelId, setChannelId] = useState("");
  const [maxVideos, setMaxVideos] = useState("20");
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

  async function loadChannels() {
    try {
      const res = await api.getChannels();
      setChannels(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadChannels();
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = channelId.trim();
    if (!trimmed) return;

    setSubmitting(true);
    setFeedback(null);

    try {
      const res = await api.backfillChannel(trimmed, parseInt(maxVideos, 10) || 20);
      setFeedback({
        type: "success",
        message: `Backfill queued! Task ID: ${res.task_id}`,
      });
      setChannelId("");
      setMaxVideos("20");
      // Reload channels after a short delay to pick up the newly ingested channel
      setTimeout(() => loadChannels(), 3000);
    } catch (err: any) {
      setFeedback({
        type: "error",
        message: err.message || "Something went wrong",
      });
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Channels</h1>
          <p className="text-muted-foreground">Browse all tracked financial YouTube channels.</p>
        </div>
        <Button
          onClick={() => {
            setShowForm((prev) => !prev);
            setFeedback(null);
          }}
          variant={showForm ? "outline" : "default"}
          className="shrink-0"
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
      </div>

      {/* Inline add-channel form */}
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Add a YouTube Channel</CardTitle>
            <CardDescription>
              Enter a YouTube Channel ID (e.g. <code className="text-xs bg-muted px-1 py-0.5 rounded">UC...</code>) to backfill its videos.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="flex flex-col gap-4 sm:flex-row sm:items-end">
              <div className="flex-1 space-y-1.5">
                <label htmlFor="channelId" className="text-sm font-medium">
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
                <label htmlFor="maxVideos" className="text-sm font-medium">
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
              <Button type="submit" disabled={submitting || !channelId.trim()}>
                {submitting ? (
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
                className={`mt-3 text-sm ${
                  feedback.type === "success" ? "text-green-600" : "text-red-600"
                }`}
              >
                {feedback.message}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {channels.map((ch: any) => (
          <Card key={ch.id}>
            <CardHeader>
              <CardTitle>{ch.title}</CardTitle>
              <CardDescription className="line-clamp-2">{ch.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <Link href={`/channels/${ch.id}`}>
                <Button className="w-full">View Channel</Button>
              </Link>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
