"use client";

import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/PageHeader";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { eventLabel, eventBadgeClass } from "@/lib/activity";
import { Bell, CheckCheck } from "lucide-react";
import { useActivity } from "@/lib/hooks";

export default function ActivityPage() {
  const [unreadOnly, setUnreadOnly] = useState(false);
  const { data: events = [], isLoading, isError, error, refetch } = useActivity({ limit: 100, unreadOnly });

  const handleMarkAllRead = async () => {
    try {
      await api.markAllActivityRead();
      refetch();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Activity Log"
        description="System events, ingested videos, processing notifications, and errors."
      >
        <div className="flex items-center gap-2">
          <Button
            variant={unreadOnly ? "default" : "outline"}
            size="sm"
            onClick={() => setUnreadOnly(!unreadOnly)}
          >
            {unreadOnly ? "Showing Unread Only" : "Filter Unread"}
          </Button>
          <Button variant="outline" size="sm" onClick={handleMarkAllRead} className="gap-1.5">
            <CheckCheck className="h-4 w-4 text-ink-faint" />
            Mark all read
          </Button>
        </div>
      </PageHeader>

      <Card>
        <CardHeader className="py-4">
          <CardTitle className="text-title font-semibold">Events ({events.length})</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading && (
            <p className="px-6 py-8 text-center text-small text-ink-secondary">
              Loading events...
            </p>
          )}

          {isError && (
            <div className="p-4">
              <ErrorState message={error instanceof Error ? error.message : "Failed to load activity log."} onRetry={refetch} />
            </div>
          )}

          {!isLoading && !isError && events.length === 0 && (
            <div className="p-6">
              <EmptyState
                icon={<Bell className="h-6 w-6" />}
                title="No activity events"
                description={unreadOnly ? "You have no unread notifications." : "No events recorded yet."}
              />
            </div>
          )}

          {!isLoading && !isError && events.length > 0 && (
            <div className="divide-y divide-line">
              {events.map((evt) => (
                <div
                  key={evt.id}
                  className={`flex flex-col gap-1 p-4 transition-colors sm:flex-row sm:items-center sm:justify-between ${
                    !evt.read_at ? "bg-panel-raised/40" : ""
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <span
                      className={`inline-flex shrink-0 items-center rounded-full px-2 py-0.5 font-mono text-micro font-semibold uppercase tracking-wider ${eventBadgeClass(
                        evt.event_type
                      )}`}
                    >
                      {eventLabel(evt.event_type)}
                    </span>
                    <div>
                      <p className="text-small font-medium leading-snug text-ink">{evt.title}</p>
                      {evt.message && (
                        <p className="mt-0.5 text-micro text-ink-secondary">{evt.message}</p>
                      )}
                      {evt.video_id && (
                        <Link
                          href={`/videos/${evt.video_id}`}
                          className="mt-1 inline-block text-micro font-medium text-signal hover:underline"
                        >
                          View Video →
                        </Link>
                      )}
                    </div>
                  </div>
                  <span className="shrink-0 font-mono text-micro tabular-nums text-ink-faint">
                    {new Date(evt.created_at).toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
