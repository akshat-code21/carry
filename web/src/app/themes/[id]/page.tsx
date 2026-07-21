"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";
import Link from "next/link";

export default function ThemePage() {
  const params = useParams();
  const id = params.id as string;

  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const res = await api.getTheme(id);
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

  if (!data || !data.theme) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4">
        <h2 className="text-2xl font-bold">Theme Not Found</h2>
      </div>
    );
  }

  const { theme, mapped_tickers, videos } = data;

  return (
    <div className="flex flex-col gap-6 pb-10">
      <div>
        <div className="flex items-center gap-3 mb-2">
          <Badge variant="outline" className="uppercase tracking-widest">{theme.level}</Badge>
        </div>
        <h1 className="text-3xl font-bold tracking-tight">{theme.name}</h1>
        {theme.description && (
          <p className="text-muted-foreground mt-2">{theme.description}</p>
        )}
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <div className="md:col-span-2 flex flex-col gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Videos Discussing This Theme</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4">
                {videos?.map((v: any) => (
                  <div key={v.id} className="flex flex-col gap-2 rounded-lg border p-4">
                    <div className="flex justify-between items-start">
                      <Link href={`/videos/${v.id}`} className="font-semibold hover:underline text-lg">
                        {v.title}
                      </Link>
                    </div>
                    <p className="text-sm border-l-2 border-primary pl-4 italic text-muted-foreground mt-2">
                      "{v.mention_text}"
                    </p>
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-xs text-muted-foreground">
                        Published: {new Date(v.published_at).toLocaleDateString()}
                      </span>
                      <Badge variant={v.sentiment === "bullish" ? "default" : v.sentiment === "bearish" ? "destructive" : "secondary"}>
                        {v.sentiment}
                      </Badge>
                    </div>
                  </div>
                ))}
                {(!videos || videos.length === 0) && (
                  <p className="text-sm text-muted-foreground">No videos found discussing this theme.</p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="flex flex-col gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Mapped Tickers</CardTitle>
              <CardDescription>Stocks directly associated with this theme</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              {mapped_tickers?.map((t: any) => (
                <div key={t.ticker} className="flex items-center justify-between border-b pb-2 last:border-0 last:pb-0">
                  <div className="flex flex-col">
                    <Link href={`/tickers/${t.ticker}`} className="font-bold hover:underline">
                      {t.ticker}
                    </Link>
                    <span className="text-xs text-muted-foreground capitalize">
                      Source: {t.source}
                    </span>
                  </div>
                  <Badge variant="outline">
                    Score: {(t.relevance_score * 100).toFixed(0)}
                  </Badge>
                </div>
              ))}
              {(!mapped_tickers || mapped_tickers.length === 0) && (
                <p className="text-sm text-muted-foreground">No tickers mapped to this theme.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
