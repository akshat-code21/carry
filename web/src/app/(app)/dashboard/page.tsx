"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, Hash, PlaySquare, BarChart } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import { DataTable, type Column } from "@/components/DataTable";
import { DashboardSkeleton } from "@/components/skeletons/LayoutSkeletons";
import { useDashboardData } from "@/lib/hooks";
import type { TickerItem } from "@/lib/api";

export default function DashboardPage() {
  const { isLoading, data } = useDashboardData();

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  const stocksData = data.tickers.filter((t) => !t.is_etf);

  const stockColumns: Column<TickerItem>[] = [
    {
      key: "ticker",
      header: "Ticker",
      render: (t) => (
        <Link href={`/tickers/${t.ticker}`} className="font-mono font-semibold text-ink hover:text-signal hover:underline">
          ${t.ticker}
        </Link>
      ),
    },
    {
      key: "mentions",
      header: "Mentions",
      numeric: true,
      headerClassName: "w-24 text-right",
      className: "w-24 text-right",
      render: (t) => (
        <Badge variant="secondary" className="font-mono">
          {t.total_mentions}
        </Badge>
      ),
    },
  ];

  const etfColumns: Column<TickerItem>[] = [
    {
      key: "ticker",
      header: "ETF",
      render: (etf) => (
        <div className="flex flex-col min-w-0">
          <Link href={`/tickers/${etf.ticker}`} className="flex items-center gap-1.5 font-mono font-semibold text-ink hover:text-signal hover:underline">
            ${etf.ticker}
            <Badge variant="outline" className="border-info/30 bg-info/10 px-1 py-0 text-micro text-info">
              ETF
            </Badge>
          </Link>
          {etf.themes && etf.themes.length > 0 && (
            <span
              className="truncate text-small capitalize text-ink-secondary"
              title={etf.themes.join(", ")}
            >
              {etf.themes.join(", ")}
            </span>
          )}
        </div>
      ),
    },
    {
      key: "mentions",
      header: "Mentions",
      numeric: true,
      headerClassName: "w-24 text-right",
      className: "w-24 text-right",
      render: (etf) => (
        <Badge variant="secondary" className="shrink-0 font-mono">
          {etf.total_mentions || 0}
        </Badge>
      ),
    },
  ];

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Dashboard"
        description="Overview of processed financial content, tracked universe, and sector sentiment."
      />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Videos"
          value={data.total_videos}
          icon={<PlaySquare className="h-4 w-4" />}
        />
        <StatCard
          title="Tracked Tickers"
          value={data.tickers.length}
          icon={<TrendingUp className="h-4 w-4" />}
        />
        <StatCard
          title="Themes Extracted"
          value={data.theme_counts?.themes ?? 0}
          icon={<Hash className="h-4 w-4" />}
        />
        <StatCard
          title="Tracked Channels"
          value={data.channels.length}
          icon={<BarChart className="h-4 w-4" />}
        />
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-title font-semibold">Top Tracked Stocks</CardTitle>
          </CardHeader>
          <CardContent>
            {stocksData.length > 0 ? (
              <DataTable
                columns={stockColumns}
                data={stocksData.slice(0, 8)}
                keyExtractor={(t) => t.ticker}
              />
            ) : (
              <div className="py-6 text-center">
                <p className="text-small font-medium text-ink">No individual stocks tracked yet</p>
                <p className="mt-1 text-small text-ink-secondary">Add channels and process videos to build the watchlist.</p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between text-title font-semibold">
              <span>Top Sector ETFs</span>
              {/* <Badge variant="outline" className="bg-warning/10 text-micro text-warning">
                Institutional
              </Badge> */}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {data.etfs.length > 0 ? (
              <DataTable
                columns={etfColumns}
                data={data.etfs.slice(0, 8)}
                keyExtractor={(etf) => etf.ticker}
              />
            ) : (
              <div className="py-6 text-center">
                <p className="text-small font-medium text-ink">No sector ETFs tracked yet</p>
                <p className="mt-1 text-small text-ink-secondary">Sector ETFs will appear as themes are mapped to instruments.</p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-title font-semibold">Recent Videos</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {data.videos.slice(0, 8).map((v) => (
              <div key={v.id} className="flex flex-col gap-1 border-b border-line pb-2 last:border-0 last:pb-0">
                <Link href={`/videos/${v.id}`} className="line-clamp-1 text-small font-medium text-ink hover:underline">
                  {v.title}
                </Link>
                <span className="font-mono text-micro text-ink-secondary">
                  Published: {new Date(v.published_at).toLocaleDateString()}
                </span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
