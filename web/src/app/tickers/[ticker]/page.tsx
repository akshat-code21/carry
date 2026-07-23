"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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

function SignalMarker({
  cx,
  cy,
  signal,
}: {
  cx?: number;
  cy?: number;
  signal: "B" | "S";
}) {
  if (cx == null || cy == null) return null;
  const color = signal === "B" ? "#22c55e" : "#ef4444";
  return (
    <g>
      <circle cx={cx} cy={cy} r={10} fill={color} stroke="#0a0a0a" strokeWidth={1.5} />
      <text
        x={cx}
        y={cy}
        textAnchor="middle"
        dominantBaseline="central"
        fontSize={11}
        fontWeight="bold"
        fill="#fff"
      >
        {signal}
      </text>
    </g>
  );
}

/** Find the price point closest in time to a target date (within 5 days),
 * so a mention on a weekend/holiday still lands on the nearest trading day. */
function findClosestPricePoint(targetDateStr: string, priceHistory: any[]) {
  if (priceHistory.length === 0) return null;
  const target = new Date(targetDateStr).getTime();
  let best: any = null;
  let bestDiff = Infinity;
  for (const p of priceHistory) {
    const diff = Math.abs(new Date(p.date).getTime() - target);
    if (diff < bestDiff) {
      bestDiff = diff;
      best = p;
    }
  }
  const FIVE_DAYS_MS = 5 * 24 * 60 * 60 * 1000;
  return best && bestDiff <= FIVE_DAYS_MS ? best : null;
}

const PRICE_RANGE_OPTIONS: { label: string; days: number }[] = [
  { label: "1M", days: 30 },
  { label: "3M", days: 90 },
  { label: "6M", days: 180 },
  { label: "1Y", days: 365 },
  { label: "All", days: 3650 },
];

export default function TickerPage() {
  const params = useParams();
  const ticker = params.ticker as string;

  const [data, setData] = useState<any>(null);
  const [sentimentTimeline, setSentimentTimeline] = useState<any[]>([]);
  const [priceHistory, setPriceHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [priceRangeDays, setPriceRangeDays] = useState(30);

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

  useEffect(() => {
    async function loadPriceHistory() {
      try {
        const priceRes = await api.getTickerPriceHistory(ticker, priceRangeDays);
        setPriceHistory(priceRes);
      } catch (err) {
        console.error(err);
      }
    }
    loadPriceHistory();
  }, [ticker, priceRangeDays]);

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

  // Real price history, with a category-axis-friendly label per point.
  const priceChartData = priceHistory.map((p: any) => ({
    date: p.date,
    label: new Date(p.date).toLocaleDateString(),
    close: p.close,
  }));

  // For each day with a clear bullish/bearish lean, place a B/S marker at
  // the nearest available trading day's close price.
  const signalMarkers = sentimentTimeline
    .map((d: any) => {
      let signal: "B" | "S" | null = null;
      if (d.bullish_count > d.bearish_count) signal = "B";
      else if (d.bearish_count > d.bullish_count) signal = "S";
      if (!signal) return null;

      const matched = findClosestPricePoint(d.date, priceHistory);
      if (!matched) return null;

      return {
        label: new Date(matched.date).toLocaleDateString(),
        price: matched.close,
        signal,
      };
    })
    .filter((m): m is { label: string; price: number; signal: "B" | "S" } => m !== null);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight uppercase">{ticker}</h1>
        <p className="text-muted-foreground">
          Market Intelligence & Predictions for {ticker}
        </p>
      </div>

      {priceChartData.length > 0 && (
        <Card>
          <CardHeader className="flex flex-row items-start justify-between gap-4">
            <div>
              <CardTitle>Price Chart with Bullish/Bearish Signals</CardTitle>
              <CardDescription>
                {ticker} price history, with B (bullish) / S (bearish) markers placed on the
                days it was mentioned that way in a video
              </CardDescription>
            </div>
            <div className="flex gap-1">
              {PRICE_RANGE_OPTIONS.map((opt) => (
                <Button
                  key={opt.label}
                  size="sm"
                  variant={priceRangeDays === opt.days ? "default" : "outline"}
                  onClick={() => setPriceRangeDays(opt.days)}
                >
                  {opt.label}
                </Button>
              ))}
            </div>
          </CardHeader>
          <CardContent>
            <div className="h-[420px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={priceChartData} margin={{ top: 30, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="label" />
                  <YAxis domain={["auto", "auto"]} />
                  <Tooltip />
                  <Line type="monotone" dataKey="close" stroke="#8884d8" dot={false} name="Close Price" />
                  {signalMarkers.map((m, i) => (
                    <ReferenceDot
                      key={i}
                      x={m.label}
                      y={m.price}
                      r={10}
                      shape={(props: any) => <SignalMarker {...props} signal={m.signal} />}
                    />
                  ))}
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
