"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";
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
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4">
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
          Market Intelligence & Predictions for {ticker}
        </p>
      </div>

      {chartData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Price Chart & Predictions</CardTitle>
            <CardDescription>Historical performance aligned with predictions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[400px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis domain={["auto", "auto"]} />
                  <Tooltip />
                  <Line type="monotone" dataKey="price" stroke="#8884d8" name="Price at Prediction" />
                  <Line type="monotone" dataKey="price_1w" stroke="#82ca9d" name="Price 1W Later" />
                  {data.predictions?.map((pred: any, i: number) => {
                    const perf = data.performance?.find((p: any) => p.prediction_id === pred.id);
                    if (!perf) return null;
                    const dateStr = new Date(perf.created_at || Date.now()).toLocaleDateString();
                    return (
                      <ReferenceDot
                        key={i}
                        x={dateStr}
                        y={perf.price_at_video}
                        r={6}
                        fill={pred.direction === "bullish" ? "#22c55e" : pred.direction === "bearish" ? "#ef4444" : "#64748b"}
                        stroke="none"
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
            <CardTitle>Recent Predictions</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {data.predictions?.map((p: any) => (
              <div key={p.id} className="flex flex-col gap-2 rounded-lg border p-4">
                <div className="flex items-center justify-between">
                  <Badge variant={p.direction === "bullish" ? "default" : p.direction === "bearish" ? "destructive" : "secondary"}>
                    {p.direction}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    Confidence: {(p.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="text-sm">{p.prediction_text}</p>
                {p.accurate !== null && (
                  <Badge variant="outline" className={p.accurate ? "text-green-500 w-fit" : "text-red-500 w-fit"}>
                    {p.accurate ? "Accurate ✅" : "Inaccurate ❌"}
                  </Badge>
                )}
              </div>
            ))}
            {(!data.predictions || data.predictions.length === 0) && (
              <p className="text-sm text-muted-foreground">No explicit predictions found.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Associated Themes</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {data.themes?.map((t: any) => (
              <div key={t.id} className="flex flex-col gap-1 border-b pb-2 last:border-0 last:pb-0">
                <span className="font-medium">{t.name}</span>
                <span className="text-xs text-muted-foreground capitalize">{t.level}</span>
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
