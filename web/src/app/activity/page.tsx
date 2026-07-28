"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, type ActivityEvent } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

function eventLabel(type: string): string {
  switch (type) {
    case "video_detected":
      return "Detected";
    case "video_processed":
      return "Ready";
    case "video_failed":
      return "Failed";
    default:
      return type;
  }
}

function eventBadgeClass(type: string): string {
  switch (type) {
    case "video_detected":
      return "bg-blue-500/15 text-blue-600 dark:text-blue-400";
    case "video_processed":
      return "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400";
    case "video_failed":
      return "bg-red-500/15 text-red-600 dark:text-red-400";
    default:
      return "bg-muted text-muted-foreground";
  }
}

export default function ActivityPage() {
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [unreadOnly, setUnreadOnly] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await api.getActivity({ limit: 100, unreadOnly });
      setEvents(list);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load activity");
    } finally {
      setLoading(false);
    }
  }, [unreadOnly]);

  useEffect(() => {
    load();
  }, [load]);

  const markAll = async () => {
    await api.markAllActivityRead();
    await load();
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Activity</h1>
          <p className="text-sm text-muted-foreground">
            New videos detected on tracked channels and processing status.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant={unreadOnly ? "default" : "outline"}
            size="sm"
            onClick={() => setUnreadOnly((v) => !v)}
          >
            {unreadOnly ? "Showing unread" : "Show unread only"}
          </Button>
          <Button variant="outline" size="sm" onClick={markAll}>
            Mark all read
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Feed</CardTitle>
        </CardHeader>
        <CardContent className="space-y-0 p-0">
          {loading && (
            <p className="px-6 py-8 text-center text-sm text-muted-foreground">
              Loading…
            </p>
          )}
          {error && (
            <p className="px-6 py-8 text-center text-sm text-red-500">{error}</p>
          )}
          {!loading && !error && events.length === 0 && (
            <p className="px-6 py-8 text-center text-sm text-muted-foreground">
              No activity yet. Once WebSub is configured, new channel uploads appear
              here automatically.
            </p>
          )}
          {!loading &&
            !error &&
            events.map((event) => {
              const href = event.video_id
                ? `/videos/${event.video_id}`
                : `/channels/${event.channel_id}`;
              return (
                <Link
                  key={event.id}
                  href={href}
                  className={`flex flex-col gap-1 border-t px-6 py-4 transition-colors hover:bg-muted/40 ${
                    event.read_at ? "opacity-70" : ""
                  }`}
                  onClick={async () => {
                    if (!event.read_at) {
                      try {
                        await api.markActivityRead(event.id);
                      } catch {
                        // ignore
                      }
                    }
                  }}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span
                      className={`rounded px-1.5 py-0.5 text-[11px] font-medium ${eventBadgeClass(
                        event.event_type
                      )}`}
                    >
                      {eventLabel(event.event_type)}
                    </span>
                    <time className="text-xs text-muted-foreground">
                      {new Date(event.created_at).toLocaleString()}
                    </time>
                  </div>
                  <p className="text-sm font-medium leading-snug">{event.title}</p>
                  <p className="text-sm text-muted-foreground">{event.message}</p>
                </Link>
              );
            })}
        </CardContent>
      </Card>
    </div>
  );
}
