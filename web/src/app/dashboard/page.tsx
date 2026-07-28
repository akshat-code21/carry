"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, TrendingUp, Hash, PlaySquare, BarChart } from "lucide-react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";

export default function DashboardPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [videos, channels, themes, tickers, etfs] = await Promise.all([
          api.getVideos(),
          api.getChannels(),
          api.getThemes(),
          api.getTickers(),
          api.getTopETFs(),
        ]);
        setData({ videos, channels, themes, tickers, etfs });
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">Overview of processed financial content.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Videos</CardTitle>
            <PlaySquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.videos?.length || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tracked Tickers</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.tickers?.length || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Themes Extracted</CardTitle>
            <Hash className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.themes?.length || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tracked Channels</CardTitle>
            <BarChart className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.channels?.length || 0}</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Top Tracked Stocks
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {data.tickers?.filter((t: any) => !t.is_etf).length > 0 ? (
              data.tickers
                ?.filter((t: any) => !t.is_etf)
                .slice(0, 8)
                .map((t: any) => (
                  <div key={t.ticker} className="flex items-center justify-between border-b border-zinc-800 pb-2 last:border-0 last:pb-0">
                    <Link href={`/tickers/${t.ticker}`} className="font-bold hover:underline">
                      {t.ticker}
                    </Link>
                    <Badge variant="secondary">
                      {t.total_mentions} Mentions
                    </Badge>
                  </div>
                ))
            ) : (
              <div className="text-xs text-muted-foreground py-6 text-center">
                No individual stocks tracked yet.
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Top Sector ETFs</span>
              <Badge variant="outline" className="text-xs bg-amber-500/10 text-amber-400 border-amber-500/20">
                Institutional
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {data.etfs && data.etfs.length > 0 ? (
              data.etfs.slice(0, 8).map((etf: any) => (
                <div key={etf.ticker} className="flex items-center justify-between border-b border-zinc-800 pb-2 last:border-0 last:pb-0">
                  <div className="flex flex-col">
                    <Link href={`/tickers/${etf.ticker}`} className="font-bold text-amber-400 hover:underline flex items-center gap-1.5">
                      {etf.ticker}
                      <Badge variant="outline" className="text-[10px] px-1 py-0 bg-amber-500/10 border-amber-500/30 text-amber-400">
                        ETF
                      </Badge>
                    </Link>
                    {etf.themes && etf.themes.length > 0 && (
                      <span className="text-xs text-muted-foreground capitalize line-clamp-1">
                        {etf.themes.join(", ")}
                      </span>
                    )}
                  </div>
                  <Badge variant="secondary" className="shrink-0">
                    {etf.total_mentions || 0} Mentions
                  </Badge>
                </div>
              ))
            ) : (
              <div className="text-xs text-muted-foreground py-6 text-center">
                No sector ETFs tracked yet.
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Videos</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {data.videos?.slice(0, 8).map((v: any) => (
              <div key={v.id} className="flex flex-col gap-1 border-b border-zinc-800 pb-2 last:border-0 last:pb-0">
                <Link href={`/videos/${v.id}`} className="font-medium hover:underline line-clamp-1 text-sm">
                  {v.title}
                </Link>
                <span className="text-xs text-muted-foreground">
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
