"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function ChannelPage() {
  const params = useParams();
  const id = params.id as string;

  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const res = await api.getChannel(id);
        setData(res);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4">
        <h2 className="text-2xl font-bold">Channel Not Found</h2>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 pb-10">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{data.channel.title}</h1>
        <p className="text-muted-foreground line-clamp-2 max-w-3xl mt-2">
          {data.channel.description}
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <div className="md:col-span-2 flex flex-col gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Videos ({data.videos?.length || 0})</CardTitle>
              <CardDescription>Processed videos from this channel</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4">
                {data.videos?.map((v: any) => (
                  <div key={v.id} className="flex flex-col gap-2 rounded-lg border p-4">
                    <Link href={`/videos/${v.id}`} className="font-semibold hover:underline text-lg">
                      {v.title}
                    </Link>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>Published: {new Date(v.published_at).toLocaleDateString()}</span>
                      <span>Duration: {Math.floor(v.duration_sec / 60)} mins</span>
                    </div>
                  </div>
                ))}
                {(!data.videos || data.videos.length === 0) && (
                  <p className="text-sm text-muted-foreground">No videos processed yet.</p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="flex flex-col gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Top Stocks Discussed</CardTitle>
              <CardDescription>Based on extraction & theme mapping</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              {data.top_stocks?.slice(0, 15).map((s: any) => (
                <div key={s.ticker} className="flex items-center justify-between border-b pb-2 last:border-0 last:pb-0">
                  <div className="flex flex-col">
                    <Link href={`/tickers/${s.ticker}`} className="font-bold hover:underline">
                      {s.ticker}
                    </Link>
                    <span className="text-xs text-muted-foreground">
                      Score: {(s.weighted_relevance * 100).toFixed(0)}
                    </span>
                  </div>
                  <Badge variant={s.avg_sentiment > 0.2 ? "default" : s.avg_sentiment < -0.2 ? "destructive" : "secondary"}>
                    {s.total_mentions} Mentions
                  </Badge>
                </div>
              ))}
              {(!data.top_stocks || data.top_stocks.length === 0) && (
                <p className="text-sm text-muted-foreground">No stocks aggregated yet.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
