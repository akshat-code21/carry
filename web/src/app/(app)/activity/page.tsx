"use client";

import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/PageHeader";
import { DataTable, type Column } from "@/components/DataTable";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { eventLabel, eventBadgeClass } from "@/lib/activity";
import { Bell, CheckCheck } from "lucide-react";
import { useActivity } from "@/lib/hooks";

type ActivityEvent = NonNullable<Awaited<ReturnType<typeof useActivity>>["data"]>[number];

const activityColumns: Column<ActivityEvent>[] = [
  {
    key: "time",
    header: "Time",
    headerClassName: "w-44 min-w-[170px]",
    className: "whitespace-nowrap",
    render: (evt) => (
      <span className="font-mono text-caption text-ink-faint tabular-nums whitespace-nowrap">
        {new Date(evt.created_at).toLocaleString(undefined, {
          month: "short",
          day: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        })}
      </span>
    ),
  },
  {
    key: "type",
    header: "Type",
    headerClassName: "w-48 min-w-[180px]",
    className: "whitespace-nowrap",
    render: (evt) => (
      <span
        className={`inline-flex items-center rounded px-2 py-0.5 font-mono text-micro font-semibold uppercase tracking-wider whitespace-nowrap ${eventBadgeClass(
          evt.event_type
        )}`}
      >
        {eventLabel(evt.event_type)}
      </span>
    ),
  },
  {
    key: "event",
    header: "Event",
    render: (evt) => (
      <div className="flex min-w-0 flex-col gap-1 py-0.5">
        <span className="text-small font-medium text-ink leading-snug break-words">{evt.title}</span>
        {evt.message && (
          <span className="text-caption text-ink-secondary leading-snug break-words">{evt.message}</span>
        )}
        {evt.video_id && (
          <Link
            href={`/videos/${evt.video_id}`}
            className="mt-0.5 w-fit font-mono text-micro font-medium text-signal hover:underline"
            onClick={(e) => e.stopPropagation()}
          >
            VIEW VIDEO →
          </Link>
        )}
      </div>
    ),
  },
];

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

      {isLoading && (
        <p className="py-8 text-center text-small text-ink-secondary">Loading events...</p>
      )}

      {isError && (
        <ErrorState message={error instanceof Error ? error.message : "Failed to load activity log."} onRetry={refetch} />
      )}

      {!isLoading && !isError && (
        <DataTable
          columns={activityColumns}
          data={events}
          keyExtractor={(evt) => evt.id}
          stickyHeader
          className="max-h-[640px] overflow-y-auto"
          emptyState={
            <EmptyState
              icon={<Bell className="h-6 w-6" />}
              title="No activity events"
              description={unreadOnly ? "You have no unread notifications." : "No events recorded yet."}
            />
          }
        />
      )}
    </div>
  );
}
