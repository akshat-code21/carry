"use client";

import { useState } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Gauge, Search, MousePointerClick, Sparkles, Zap } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import { Skeleton } from "@/components/Skeleton";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { useMe, useMyUsage } from "@/lib/hooks";
import { useChartColors } from "@/lib/useChartColors";
import type { UsageDailyPoint } from "@/lib/api";

const RANGES = [7, 30, 90] as const;

export default function MyUsagePage() {
  const { isAdmin, isLoading: meLoading } = useMe();
  const [days, setDays] = useState<(typeof RANGES)[number]>(30);
  const { data, isLoading, isError, refetch } = useMyUsage(days);
  const c = useChartColors();

  if (meLoading) return <Skeleton className="h-96" />;
  if (!isAdmin) {
    return (
      <div className="space-y-6">
        <PageHeader title="Usage" description="Restricted area." />
        <ErrorState message="You need admin privileges to view this page." />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title="My usage" description="Your activity across Carry." />
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-72" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="space-y-6">
        <PageHeader title="My usage" description="Your activity across Carry." />
        <ErrorState message="Couldn't load your usage data." onRetry={() => refetch()} />
      </div>
    );
  }

  const t = data.totals;
  const totalSearches = Number(t.searches ?? 0);
  const totalPageViews = Number(t.page_views ?? 0);
  const totalTokens = Number(t.llm_input_tokens ?? 0) + Number(t.llm_output_tokens ?? 0);
  const totalApiCalls = Number(t.api_calls ?? 0);

  const chartData: UsageDailyPoint[] = data.daily.map((d) => ({
    ...d,
  }));

  return (
    <div className="space-y-6">
      <PageHeader
        title="My usage"
        description={
          t.member_since
            ? `Member since ${t.member_since}. Your activity and resource footprint.`
            : "Your activity and resource footprint."
        }
      >
        <div className="flex rounded-md border border-line p-0.5">
          {RANGES.map((r) => (
            <button
              key={r}
              onClick={() => setDays(r)}
              className={`rounded px-2.5 py-1 font-mono text-micro transition-colors ${
                days === r ? "bg-panel text-signal" : "text-ink-faint hover:text-ink"
              }`}
            >
              {r}d
            </button>
          ))}
        </div>
      </PageHeader>

      {/* Lifetime stat cards */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Searches"
          value={totalSearches}
          icon={<Search className="h-4 w-4" />}
          description={`${Number(t.search_zero_results ?? 0)} with no results`}
        />
        <StatCard
          title="API calls"
          value={totalApiCalls}
          icon={<MousePointerClick className="h-4 w-4" />}
          description="All authenticated requests"
        />
        <StatCard
          title="Pages viewed"
          value={totalPageViews}
          icon={<Gauge className="h-4 w-4" />}
          description="Feature exploration"
        />
        <StatCard
          title="LLM tokens"
          value={formatNumber(totalTokens)}
          icon={<Sparkles className="h-4 w-4" />}
          description="Search classification + embeddings"
        />
      </div>

      {/* Daily activity chart */}
      <Card>
        <CardContent className="pt-5">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-title font-semibold text-ink">Daily activity</h2>
            <span className="font-mono text-micro text-ink-faint">last {days} days</span>
          </div>
          <div className="mt-4 h-64">
            {chartData.length === 0 ? (
              <EmptyState title="No activity yet" description="Start searching to see your usage here." />
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
                  <defs>
                    <linearGradient id="gSearches" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={c.success} stopOpacity={0.35} />
                      <stop offset="100%" stopColor={c.success} stopOpacity={0.02} />
                    </linearGradient>
                    <linearGradient id="gViews" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={c.info} stopOpacity={0.3} />
                      <stop offset="100%" stopColor={c.info} stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={c.line} vertical={false} />
                  <XAxis
                    dataKey="day"
                    tick={{ fontSize: 10, fill: c.mutedForeground }}
                    tickFormatter={(v: string) => v.slice(5)}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis tick={{ fontSize: 10, fill: c.mutedForeground }} tickLine={false} axisLine={false} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: c.canvas,
                      border: `1px solid ${c.line}`,
                      borderRadius: 4,
                      fontSize: 12,
                    }}
                    labelStyle={{ color: c.mutedForeground }}
                  />
                  <Area type="monotone" dataKey="searches" name="Searches" stroke={c.success} fill="url(#gSearches)" strokeWidth={1.5} />
                  <Area type="monotone" dataKey="page_views" name="Page views" stroke={c.info} fill="url(#gViews)" strokeWidth={1.5} />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        {/* Top queries */}
        <Card>
          <CardContent className="pt-5">
            <h2 className="font-display text-title font-semibold text-ink">Top queries</h2>
            {data.top_queries.length === 0 ? (
              <p className="mt-4 font-mono text-small text-ink-faint">No searches yet.</p>
            ) : (
              <ul className="mt-3 space-y-1.5">
                {data.top_queries.map((q, i) => (
                  <li key={i} className="flex items-center justify-between gap-3 border-b border-line pb-1.5 last:border-0">
                    <span className="truncate font-mono text-small text-ink-secondary">{q.query}</span>
                    <Badgeish count={q.count} />
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        {/* Recent activity */}
        <Card>
          <CardContent className="pt-5">
            <h2 className="flex items-center gap-2 font-display text-title font-semibold text-ink">
              <Zap className="h-4 w-4 text-ink-faint" /> Recent events
            </h2>
            {data.recent_events.length === 0 ? (
              <p className="mt-4 font-mono text-small text-ink-faint">Nothing yet.</p>
            ) : (
              <ul className="mt-3 space-y-2">
                {data.recent_events.slice(0, 10).map((e, i) => (
                  <li key={i} className="flex items-start justify-between gap-3 border-b border-line pb-2 last:border-0">
                    <div className="min-w-0">
                      <EventLabel type={e.type} payload={e.payload} />
                    </div>
                    <span className="shrink-0 font-mono text-micro text-ink-faint">
                      {new Date(e.created_at).toLocaleDateString()}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Badgeish({ count }: { count: number }) {
  return (
    <span className="shrink-0 rounded bg-panel px-1.5 py-0.5 font-mono text-micro tabular-nums text-signal">
      {count}
    </span>
  );
}

const EVENT_LABELS: Record<string, string> = {
  search_performed: "Searched",
  video_viewed: "Opened video",
  channel_viewed: "Viewed channel",
  theme_viewed: "Viewed theme",
  ticker_viewed: "Viewed ticker",
  pipeline_triggered: "Triggered pipeline",
  chatter_refresh_requested: "Refreshed sentiment",
};

function EventLabel({ type, payload }: { type: string; payload: Record<string, unknown> }) {
  const label = EVENT_LABELS[type] ?? type.replace(/_/g, " ");
  let detail = "";
  if (type === "search_performed") detail = String(payload.query ?? "");
  else if (type === "ticker_viewed") detail = `$${String(payload.ticker ?? "")}`;
  else if (type === "channel_viewed") detail = String(payload.title ?? "");
  else if (type === "theme_viewed") detail = String(payload.name ?? "");
  return (
    <span className="block truncate text-small text-ink-secondary">
      <span className="text-ink">{label}</span>
      {detail && <span className="ml-1.5 font-mono text-micro text-ink-faint">{detail}</span>}
    </span>
  );
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}
