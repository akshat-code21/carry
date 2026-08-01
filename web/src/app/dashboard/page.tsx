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
        <Link href={`/tickers/${t.ticker}`} className="font-bold hover:underline">
          ${t.ticker}
        </Link>
      ),
    },
    {
      key: "mentions",
      header: "Mentions",
      numeric: true,
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
        <div className="flex flex-col">
          <Link href={`/tickers/${etf.ticker}`} className="font-bold text-warning hover:underline flex items-center gap-1.5">
            ${etf.ticker}
            <Badge variant="outline" className="text-[10px] px-1 py-0 bg-warning/10 border-warning/30 text-warning">
              ETF
            </Badge>
          </Link>
          {etf.themes && etf.themes.length > 0 && (
            <span className="text-xs text-muted-foreground capitalize line-clamp-1">
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
          value={data.videos.length}
          icon={<PlaySquare className="h-4 w-4" />}
        />
        <StatCard
          title="Tracked Tickers"
          value={data.tickers.length}
          icon={<TrendingUp className="h-4 w-4" />}
        />
        <StatCard
          title="Themes Extracted"
          value={data.themes.length}
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
            <CardTitle className="text-base font-semibold">Top Tracked Stocks</CardTitle>
          </CardHeader>
          <CardContent>
            {stocksData.length > 0 ? (
              <DataTable
                columns={stockColumns}
                data={stocksData.slice(0, 8)}
                keyExtractor={(t) => t.ticker}
              />
            ) : (
              <div className="text-xs text-muted-foreground py-6 text-center">
                No individual stocks tracked yet.
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between text-base font-semibold">
              <span>Top Sector ETFs</span>
              <Badge variant="outline" className="text-xs bg-warning/10 text-warning border-warning/20">
                Institutional
              </Badge>
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
              <div className="text-xs text-muted-foreground py-6 text-center">
                No sector ETFs tracked yet.
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base font-semibold">Recent Videos</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {data.videos.slice(0, 8).map((v) => (
              <div key={v.id} className="flex flex-col gap-1 border-b pb-2 last:border-0 last:pb-0">
                <Link href={`/videos/${v.id}`} className="font-medium hover:underline line-clamp-1 text-sm">
                  {v.title}
                </Link>
                <span className="text-xs text-muted-foreground font-mono">
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
