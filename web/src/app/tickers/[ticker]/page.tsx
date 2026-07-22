"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, ExternalLink, PlayCircle, Video, TrendingUp, TrendingDown, Minus } from "lucide-react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceDot,
} from "recharts";
import { PredictionSentimentChart } from "@/components/PredictionSentimentChart";

export default function TickerPage() {
  const params = useParams();
  const ticker = params.ticker as string;

  const [data, setData] = useState<any>(null);
  const [sentimentTimeline, setSentimentTimeline] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [res, timelineRes] = await Promise.all([
          api.getTicker(ticker),
          api.getTickerSentimentTimeline(ticker),
        ]);
        setData(res);
        setSentimentTimeline(timelineRes);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [ticker]);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 py-20">
        <h2 className="text-2xl font-bold">Ticker Not Found</h2>
        <p className="text-muted-foreground">No data found for {ticker}</p>
      </div>
    );
  }

  // Construct chart data based on performance records
  const chartData = data.performance?.map((p: any) => ({
    name: new Date(p.created_at || Date.now()).toLocaleDateString(),
    price: p.price_at_video,
    price_1w: p.price_1w,
  })) || [];

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight uppercase">{ticker}</h1>
        <p className="text-muted-foreground">
          Market Intelligence & Video Predictions for {ticker}
        </p>
      </div>

      {/* Video Level Prediction Trajectory Chart */}
      {data.predictions && data.predictions.length > 0 && (
        <PredictionSentimentChart predictions={data.predictions} ticker={ticker} />
      )}

      {/* Price Chart & Performance */}
      {chartData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Price Chart & Predictions</CardTitle>
            <CardDescription>Historical stock price performance aligned with prediction timestamps</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[400px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis dataKey="name" />
                  <YAxis domain={["auto", "auto"]} />
                  <Tooltip />
                  <Line type="monotone" dataKey="price" stroke="#8884d8" name="Price at Prediction" strokeWidth={2} />
                  <Line type="monotone" dataKey="price_1w" stroke="#82ca9d" name="Price 1W Later" strokeWidth={2} />
                  {data.predictions?.map((pred: any, i: number) => {
                    const perf = data.performance?.find((p: any) => p.prediction_id === pred.id);
                    if (!perf) return null;
                    const dateStr = new Date(perf.created_at || Date.now()).toLocaleDateString();
                    return (
                      <ReferenceDot
                        key={i}
                        x={dateStr}
                        y={perf.price_at_video}
                        r={7}
                        fill={pred.direction === "bullish" ? "#22c55e" : pred.direction === "bearish" ? "#ef4444" : "#64748b"}
                        stroke="#ffffff"
                        strokeWidth={2}
                      />
                    );
                  })}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      {sentimentTimeline.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Daily Bullish vs Bearish Mentions</CardTitle>
            <CardDescription>
              Number of bullish and bearish mentions of {ticker} per day, across predictions and theme mentions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[350px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={sentimentTimeline.map((d: any) => ({
                    ...d,
                    label: new Date(d.date).toLocaleDateString(),
                  }))}
                  margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="label" />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="bullish_count" name="Bullish" fill="#22c55e" />
                  <Bar dataKey="bearish_count" name="Bearish" fill="#ef4444" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Video className="h-5 w-5 text-primary" />
              Video Level Predictions
            </CardTitle>
            <CardDescription>All extracted video predictions for {ticker}</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {data.predictions?.map((p: any) => {
              const dir = (p.direction || "neutral").toLowerCase();
              return (
                <div key={p.id} className="flex flex-col gap-2.5 rounded-lg border p-4 hover:border-primary/50 transition-colors">
                  <div className="flex items-center justify-between gap-2">
                    <Badge
                      variant={
                        dir === "bullish"
                          ? "default"
                          : dir === "bearish"
                          ? "destructive"
                          : "secondary"
                      }
                      className="capitalize"
                    >
                      {dir === "bullish" && <TrendingUp className="mr-1 h-3 w-3 inline" />}
                      {dir === "bearish" && <TrendingDown className="mr-1 h-3 w-3 inline" />}
                      {dir === "neutral" && <Minus className="mr-1 h-3 w-3 inline" />}
                      {dir}
                    </Badge>
                    <span className="text-xs text-muted-foreground font-medium">
                      Confidence: {((p.confidence ?? 0.75) * 100).toFixed(0)}%
                    </span>
                  </div>

                  {p.video_title && (
                    <div>
                      <p className="text-xs font-semibold text-foreground line-clamp-1">{p.video_title}</p>
                      {p.channel_title && <p className="text-[11px] text-muted-foreground">{p.channel_title}</p>}
                    </div>
                  )}

                  <p className="text-sm italic text-muted-foreground bg-muted/30 p-2.5 rounded border border-muted/50">
                    &ldquo;{p.prediction_text}&rdquo;
                  </p>

                  <div className="flex items-center justify-between pt-1">
                    {p.accurate !== null && p.accurate !== undefined ? (
                      <Badge variant="outline" className={p.accurate ? "border-green-500 text-green-500 bg-green-500/10 text-xs" : "border-red-500 text-red-500 bg-red-500/10 text-xs"}>
                        {p.accurate ? "Accurate ✅" : "Inaccurate ❌"}
                      </Badge>
                    ) : <div />}

                    {p.youtube_video_id && (
                      <a
                        href={`https://www.youtube.com/watch?v=${p.youtube_video_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-xs font-medium text-primary hover:underline"
                      >
                        <PlayCircle className="h-3.5 w-3.5" />
                        Watch Video
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    )}
                  </div>
                </div>
              );
            })}
            {(!data.predictions || data.predictions.length === 0) && (
              <p className="text-sm text-muted-foreground">No explicit predictions found for {ticker}.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Associated Themes</CardTitle>
            <CardDescription>Market themes mapped to {ticker}</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {data.themes?.map((t: any) => (
              <div key={t.id} className="flex flex-col gap-1 border-b pb-3 last:border-0 last:pb-0">
                <span className="font-medium">{t.name}</span>
                <span className="text-xs text-muted-foreground capitalize">{t.level}</span>
                {t.description && <p className="text-xs text-muted-foreground mt-0.5">{t.description}</p>}
              </div>
            ))}
            {(!data.themes || data.themes.length === 0) && (
              <p className="text-sm text-muted-foreground">No themes mapped to this ticker.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

