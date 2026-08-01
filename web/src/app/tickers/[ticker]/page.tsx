"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
import { PageHeader } from "@/components/PageHeader";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { ErrorState } from "@/components/ErrorState";
import { DetailSkeleton } from "@/components/skeletons/LayoutSkeletons";
import { useTicker, useTickerSentiment, useTickerPriceHistory } from "@/lib/hooks";
import { useChartColors } from "@/lib/useChartColors";

/**
 * Reads a CSS custom property from :root / .dark and returns its computed value.
 */
function getCSSVar(name: string, fallback: string): string {
  if (typeof window === "undefined") return fallback;
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback;
}

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
  const successColor = getCSSVar("--success", "#22c55e");
  const dangerColor = getCSSVar("--danger", "#ef4444");
  const bgColor = getCSSVar("--background", "#0a0a0a");
  const color = signal === "B" ? successColor : dangerColor;
  return (
    <g>
      <circle cx={cx} cy={cy} r={10} fill={color} stroke={bgColor} strokeWidth={1.5} />
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

const PriceTooltip = ({ active, payload }: any) => {
  if (!active || !payload || !payload.length) return null;
  const data = payload[0].payload;
  const closePrice = typeof data.close === "number" ? data.close.toFixed(2) : data.close;

  return (
    <div className="z-50 rounded-lg border bg-popover px-3.5 py-2.5 text-popover-foreground shadow-md">
      <p className="text-xs font-medium text-muted-foreground">{data.label || data.date}</p>
      <p className="mt-1 text-sm font-bold font-mono text-foreground">
        Close Price: <span className="text-primary">${closePrice}</span>
      </p>
    </div>
  );
};

const PerfTooltip = ({ active, payload }: any) => {
  if (!active || !payload || !payload.length) return null;
  const data = payload[0].payload;

  return (
    <div className="z-50 rounded-lg border bg-popover px-3.5 py-2.5 text-popover-foreground shadow-md space-y-1">
      <p className="text-xs font-medium text-muted-foreground">{data.name}</p>
      {payload.map((entry: any, i: number) => (
        <p key={i} className="text-xs font-mono" style={{ color: entry.color }}>
          {entry.name}: ${typeof entry.value === "number" ? entry.value.toFixed(2) : entry.value}
        </p>
      ))}
    </div>
  );
};

const MentionsTooltip = ({ active, payload }: any) => {
  if (!active || !payload || !payload.length) return null;
  const data = payload[0].payload;

  return (
    <div className="z-50 rounded-lg border bg-popover px-3.5 py-2.5 text-popover-foreground shadow-md space-y-1">
      <p className="text-xs font-medium text-muted-foreground">{data.label || data.date}</p>
      <div className="flex items-center gap-3 text-xs font-mono">
        <span className="text-success font-semibold">Bullish: {data.bullish_count || 0}</span>
        <span className="text-danger font-semibold">Bearish: {data.bearish_count || 0}</span>
      </div>
    </div>
  );
};

export default function TickerPage() {
  const params = useParams();
  const ticker = params.ticker as string;

  const [priceRangeDays, setPriceRangeDays] = useState(30);

  const { data, isLoading } = useTicker(ticker);
  const { data: sentimentTimeline = [] } = useTickerSentiment(ticker);
  const { data: priceHistory = [] } = useTickerPriceHistory(ticker, priceRangeDays);

  const chartColors = useChartColors();
  const successColor = chartColors.success;
  const dangerColor = chartColors.danger;
  const mutedFgColor = chartColors.mutedForeground;
  const chart1Color = chartColors.chart1;
  const chart2Color = chartColors.chart2;

  if (isLoading) {
    return <DetailSkeleton />;
  }

  if (!data) {
    return (
      <div className="p-8">
        <ErrorState title="Ticker Not Found" message={`No market intelligence found for $${ticker}`} />
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

  // Construct performance chart data if present
  const perfChartData = data.performance?.map((p: any) => ({
    name: new Date(p.created_at || Date.now()).toLocaleDateString(),
    price: p.price_at_video,
    price_1w: p.price_1w,
  })) || [];

  return (
    <div className="flex flex-col gap-6">
      <div>
        <Breadcrumbs
          items={[
            { label: "Dashboard", href: "/dashboard" },
            { label: "Tickers", href: "/dashboard" },
            { label: `$${ticker.toUpperCase()}` },
          ]}
        />
        <PageHeader
          title={`$${ticker.toUpperCase()}`}
          description={`Market Intelligence & Video Predictions for ${ticker.toUpperCase()}`}
        />
      </div>

      {/* Video Level Prediction Trajectory Chart */}
      {data.predictions && data.predictions.length > 0 && (
        <PredictionSentimentChart predictions={data.predictions} ticker={ticker} />
      )}

      {/* Real Stock Price Chart with Bullish/Bearish Signal Markers */}
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
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis dataKey="label" />
                  <YAxis domain={["auto", "auto"]} />
                  <Tooltip content={<PriceTooltip />} wrapperStyle={{ outline: "none" }} />
                  <Line type="monotone" dataKey="close" stroke={chart1Color} dot={false} name="Close Price" strokeWidth={2} />
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

      {/* Historical Stock Price & Prediction Performance Chart */}
      {perfChartData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Price Chart & Predictions Performance</CardTitle>
            <CardDescription>Historical stock price performance aligned with prediction timestamps</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[400px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={perfChartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis dataKey="name" />
                  <YAxis domain={["auto", "auto"]} />
                  <Tooltip content={<PerfTooltip />} wrapperStyle={{ outline: "none" }} />
                  <Legend />
                  <Line type="monotone" dataKey="price" stroke={chart1Color} name="Price at Prediction" strokeWidth={2} />
                  <Line type="monotone" dataKey="price_1w" stroke={chart2Color} name="Price 1W Later" strokeWidth={2} />
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
                        fill={pred.direction === "bullish" ? successColor : pred.direction === "bearish" ? dangerColor : mutedFgColor}
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

      {/* Daily Bullish vs Bearish Mentions Bar Chart */}
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
                  <Tooltip content={<MentionsTooltip />} wrapperStyle={{ outline: "none" }} />
                  <Legend />
                  <Bar dataKey="bullish_count" name="Bullish" fill={successColor} />
                  <Bar dataKey="bearish_count" name="Bearish" fill={dangerColor} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Video Level Predictions & Associated Themes */}
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
                      <Badge variant="outline" className={p.accurate ? "border-success text-success bg-success/10 text-xs" : "border-danger text-danger bg-danger/10 text-xs"}>
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
