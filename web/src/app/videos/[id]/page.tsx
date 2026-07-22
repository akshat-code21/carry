"use client";

import { Suspense, useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";
import Link from "next/link";

function VideoPageContent() {
  const params = useParams();
  const searchParams = useSearchParams();
  const id = params.id as string;

  const startTimeParam = searchParams.get("t") || searchParams.get("start");
  const startTime = startTimeParam ? Math.floor(parseFloat(startTimeParam)) : 0;

  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const res = await api.getVideo(id);
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
      <div className="flex h-full items-center justify-center p-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 p-12">
        <h2 className="text-2xl font-bold">Video Not Found</h2>
      </div>
    );
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const embedUrl = startTime > 0
    ? `https://www.youtube.com/embed/${data.youtube_video_id}?start=${startTime}&autoplay=1`
    : `https://www.youtube.com/embed/${data.youtube_video_id}`;

  return (
    <div className="flex flex-col gap-6 pb-10">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{data.title}</h1>
        <p className="text-muted-foreground">
          Published: {data.published_at ? new Date(data.published_at).toLocaleDateString() : "N/A"}
        </p>
      </div>

      <div className="aspect-video w-full max-w-4xl overflow-hidden rounded-xl border bg-black shadow-sm">
        <iframe
          width="100%"
          height="100%"
          src={embedUrl}
          title="YouTube video player"
          frameBorder="0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
        ></iframe>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <div className="md:col-span-2 flex flex-col gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Transcript</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex h-[400px] flex-col gap-4 overflow-y-auto pr-4">
                {data.segments?.map((seg: any) => (
                  <div key={seg.id} className="flex gap-4">
                    <span className="w-12 shrink-0 text-xs text-muted-foreground font-mono">
                      {formatTime(seg.start_sec)}
                    </span>
                    <p className="text-sm">{seg.text}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="flex flex-col gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Predictions</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              {data.predictions?.map((p: any) => (
                <div key={p.id} className="flex flex-col gap-2 rounded-lg border p-3">
                  <div className="flex items-center justify-between">
                    {p.ticker ? (
                      <Link href={`/tickers/${p.ticker}`} className="font-bold hover:underline">
                        {p.ticker}
                      </Link>
                    ) : (
                      <span className="font-bold">Macro/Thematic</span>
                    )}
                    <Badge variant={p.direction === "bullish" ? "default" : p.direction === "bearish" ? "destructive" : "secondary"}>
                      {p.direction}
                    </Badge>
                  </div>
                  <p className="text-sm">{p.prediction_text}</p>
                </div>
              ))}
              {(!data.predictions || data.predictions.length === 0) && (
                <p className="text-sm text-muted-foreground">No predictions extracted.</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Themes Discussed</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              {data.themes?.map((t: any) => (
                <div key={t.id} className="flex flex-col gap-1 border-b pb-2 last:border-0 last:pb-0">
                  <Link href={`/themes/${t.theme_id}`} className="font-medium hover:underline">
                    {t.name}
                  </Link>
                  <p className="text-xs text-muted-foreground italic">"{t.narrative}"</p>
                </div>
              ))}
              {(!data.themes || data.themes.length === 0) && (
                <p className="text-sm text-muted-foreground">No themes extracted.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default function VideoPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-full items-center justify-center p-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      }
    >
      <VideoPageContent />
    </Suspense>
  );
}
