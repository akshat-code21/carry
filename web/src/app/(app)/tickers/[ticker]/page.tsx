"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Loader2, ExternalLink, PlayCircle, Video, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { PredictionSentimentChart } from "@/components/PredictionSentimentChart";
import {
  TradingViewPriceChart,
  type TvChartSeriesType,
  type TvSignalMarker,
} from "@/components/TradingViewPriceChart";
import { SocialSentimentPanel } from "@/components/SocialSentimentPanel";
import { PageHeader } from "@/components/PageHeader";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { ErrorState } from "@/components/ErrorState";
import { DetailSkeleton } from "@/components/skeletons/LayoutSkeletons";
import { useTicker, useTickerSentiment, useTickerPriceHistory } from "@/lib/hooks";
import { useChartColors } from "@/lib/useChartColors";
import { cn } from "@/lib/utils";

const PRICE_SERIES_OPTIONS: { label: string; type: TvChartSeriesType }[] = [
  { label: "Line", type: "line" },
  { label: "Area", type: "area" },
  { label: "Candles", type: "candlestick" },
];

const PRICE_RANGE_OPTIONS: { label: string; days: number }[] = [
  { label: "1M", days: 30 },
  { label: "3M", days: 90 },
  { label: "6M", days: 180 },
  { label: "1Y", days: 365 },
];

/** Nearest price bar on/before `date` (ISO), for anchoring markers. */
function findClosestPricePoint(date: string, priceHistory: any[]) {
  if (!priceHistory.length) return null;
  const target = new Date(date).getTime();
  const before = priceHistory
    .filter((p: any) => new Date(p.date).getTime() <= target)
    .sort((a: any, b: any) => new Date(b.date).getTime() - new Date(a.date).getTime());
  return before[0] ?? priceHistory[0];
}

export default function TickerPage() {
  const params = useParams();
  const ticker = params.ticker as string;

  const [priceRangeDays, setPriceRangeDays] = useState(30);
  const [priceSeriesType, setPriceSeriesType] = useState<TvChartSeriesType>("line");

  const { data, isLoading } = useTicker(ticker);
  const { data: sentimentTimeline = [] } = useTickerSentiment(ticker);
  const { data: priceHistory = [], isFetching: isFetchingPrice } = useTickerPriceHistory(ticker, priceRangeDays);

  const chartColors = useChartColors();
  const successColor = chartColors.success;
  const dangerColor = chartColors.danger;
  const mutedFgColor = chartColors.mutedForeground;

  if (isLoading) {
    return <DetailSkeleton />;
  }

  if (!data) {
    return (
      <div className="p-8">
        <ErrorState title="Ticker Not Found" message={`No market intelligence found for ${ticker.toUpperCase()}`} />
      </div>
    );
  }

  // Real price history, with a UTC-stable date key for the chart.
  const priceChartData = priceHistory.map((p: any) => ({
    date: p.date,
    open: p.open,
    high: p.high,
    low: p.low,
    close: p.close,
  }));

  // Aggregate daily sentiment timeline counts by matched trading day to produce
  // exactly one net consensus marker per trading day (B if bullish > bearish, S if bearish > bullish).
  const sentimentByTradingDay = new Map<string, { bullish: number; bearish: number }>();

  for (const d of sentimentTimeline) {
    const matched = findClosestPricePoint(d.date, priceHistory);
    if (!matched) continue;

    const current = sentimentByTradingDay.get(matched.date) || { bullish: 0, bearish: 0 };
    current.bullish += d.bullish_count || 0;
    current.bearish += d.bearish_count || 0;
    sentimentByTradingDay.set(matched.date, current);
  }

  const signalMarkers: TvSignalMarker[] = Array.from(sentimentByTradingDay.entries())
    .map(([date, counts]): TvSignalMarker | null => {
      if (counts.bullish > counts.bearish) return { date, signal: "B" };
      if (counts.bearish > counts.bullish) return { date, signal: "S" };
      return null; // Tied or neutral days omit the marker
    })
    .filter((m): m is TvSignalMarker => m !== null);

  // For each video prediction, color a dot by its predicted direction at the
  // prediction date's close price (▲ bullish / ▼ bearish / ● neutral).
  const predictionMarkers: TvSignalMarker[] = (data.predictions ?? [])
    .map((pred: any): TvSignalMarker | null => {
      const perf = data.performance?.find((p: any) => p.prediction_id === pred.id);
      if (!perf?.created_at) return null;
      const created = new Date(perf.created_at).toISOString().slice(0, 10);
      const matched = findClosestPricePoint(created, priceHistory);
      if (!matched) return null;
      const signal: TvSignalMarker["signal"] =
        pred.direction === "bullish" ? "B" : pred.direction === "bearish" ? "S" : "N";
      return {
        date: matched.date,
        signal,
        color:
          pred.direction === "bullish"
            ? successColor
            : pred.direction === "bearish"
              ? dangerColor
              : mutedFgColor,
      };
    })
    .filter((m): m is TvSignalMarker => m !== null);

  // Construct performance chart data if present
  const perfChartData = data.performance
    ?.filter((p: any) => !!p.created_at)
    .map((p: any) => ({
      name: new Date(p.created_at).toLocaleDateString(),
      price: p.price_at_video,
      price_1w: p.price_1w,
    })) || [];

  /**
   * Shared TradingView Lightweight-Charts renderer (v5) - replaces the Recharts
   * price charts. B/S sentiment markers are drawn by the library’s marker plugin;
   * the candlestick toggle switches the price series type in place.
   */
  const priceChartEl = (
    <TradingViewPriceChart
      points={priceChartData}
      seriesType={priceSeriesType}
      markers={signalMarkers}
    />
  );

  /**
   * “Price Chart & Predictions Performance” - actual close vs the close one week
   * later (dashed), with prediction dots colored by predicted direction.
   */
  const priceIndexByDate = new Map(priceHistory.map((p: any, idx: number) => [p.date, idx]));
  const perfChartEl = (
    <TradingViewPriceChart
      points={priceChartData}
      seriesType="line"
      markers={predictionMarkers}
      secondaryLine={{
        label: "Price 1W Later",
        points: priceChartData.map((p: any) => {
          const idx = priceIndexByDate.get(p.date) ?? -1;
          const later =
            idx >= 0 ? priceChartData[Math.min(idx + 7, priceChartData.length - 1)] : undefined;
          return { date: p.date, value: later ? later.close : p.close };
        }),
      }}
    />
  );

  return (
    <div className="flex flex-col gap-6">
      <div className="mb-2 flex gap-2 flex-col items-start">
        <Breadcrumbs
          items={[
            { label: "Dashboard", href: "/dashboard" },
            { label: "Tickers", href: "/dashboard" },
            { label: ticker.toUpperCase() },
          ]}
        />
        <PageHeader
          title={ticker.toUpperCase()}
          description={`Market Intelligence & Video Predictions for ${ticker.toUpperCase()}`}
        />
        {(data.social || data.combined_avg_sentiment != null) && (
          <div className="flex flex-wrap items-center gap-2 font-mono text-micro text-ink-secondary">
            {data.combined_avg_sentiment != null && (
              <Badge
                variant="outline"
                className={
                  data.combined_avg_sentiment > 0.05
                    ? "border-bullish/40 bg-bullish/10 text-bullish"
                    : data.combined_avg_sentiment < -0.05
                      ? "border-bearish/40 bg-bearish/10 text-bearish"
                      : "border-line text-ink-secondary"
                }
              >
                Combined sentiment{" "}
                {data.combined_avg_sentiment > 0 ? "+" : ""}
                {data.combined_avg_sentiment.toFixed(2)}
              </Badge>
            )}
            {data.social_mentions != null && (
              <Badge variant="outline" className="border-line text-ink-secondary">
                {data.social_mentions} social mentions
              </Badge>
            )}
            {data.total_mentions != null && (
              <Badge variant="outline" className="border-line text-ink-secondary">
                {data.total_mentions} YouTube mentions
              </Badge>
            )}
          </div>
        )}
      </div>

      {/* TickerFlow & YouTube sentiment (YouTube / Reddit / X / News) */}
      {data.social && (
        <SocialSentimentPanel
          social={data.social}
          predictions={data.predictions}
          sentimentTimeline={sentimentTimeline}
          youtubeMentions={data.total_mentions}
          youtubeAvgSentiment={data.avg_sentiment}
        />
      )}

      {/* Video Level Prediction Trajectory Chart */}
      {data.predictions && data.predictions.length > 0 && (
        <PredictionSentimentChart predictions={data.predictions} ticker={ticker} />
      )}

      {/* Real Stock Price Chart with Bullish/Bearish Signal Markers */}
      {priceChartData.length > 0 && (
        <Card>
          <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <CardTitle>Price Chart with Bullish/Bearish Signals</CardTitle>
              <CardDescription>
                {ticker} price history, with B (bullish) / S (bearish) markers placed on the
                days it was mentioned that way in a video
              </CardDescription>
            </div>
            <div className="flex flex-wrap items-center gap-2 sm:justify-end">
              <div className="flex flex-wrap items-center gap-1">
                {PRICE_SERIES_OPTIONS.map((opt) => (
                  <Button
                    key={opt.type}
                    size="sm"
                    variant={priceSeriesType === opt.type ? "default" : "outline"}
                    onClick={() => setPriceSeriesType(opt.type)}
                  >
                    {opt.label}
                  </Button>
                ))}
              </div>
              <div className="flex flex-wrap items-center gap-1">
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
            </div>
          </CardHeader>
          <CardContent>
            <div
              className={`w-full transition-opacity duration-200 ${isFetchingPrice ? "opacity-60" : "opacity-100"
                }`}
            >
              {priceChartEl}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Historical Stock Price & Prediction Performance Chart */}
      {perfChartData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Price Chart & Predictions Performance</CardTitle>
            <CardDescription>
              Historical price performance with prediction timestamps - dots are colored by
              predicted direction (▲ bullish / ▼ bearish / ● neutral); the dashed line
              shows the close price one week later
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="w-full">{perfChartEl}</div>
          </CardContent>
        </Card>
      )}
      {/* Daily Bullish vs Bearish Mentions Bar Chart */}
      {/* {sentimentTimeline.length > 0 && (
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
                  <CartesianGrid strokeDasharray="3 3" stroke={lineColor} opacity={0.3} vertical={false} />
                  <XAxis dataKey="label" tick={{ fontSize: 10, fill: inkSecondaryColor, fontFamily: "var(--font-geist-mono)" }} tickLine={false} axisLine={{ stroke: lineColor }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 10, fill: inkSecondaryColor, fontFamily: "var(--font-geist-mono)" }} tickLine={false} axisLine={false} width={40} />
                  <Tooltip content={<MentionsTooltip />} wrapperStyle={{ outline: "none" }} />
                  <Legend wrapperStyle={{ fontFamily: "var(--font-geist-mono)", fontSize: 10 }} />
                  <Bar dataKey="bullish_count" name="Bullish" fill={successColor} radius={[2, 2, 0, 0]} />
                  <Bar dataKey="bearish_count" name="Bearish" fill={dangerColor} radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )} */}

      {/* Video Level Predictions & Associated Themes */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Video className="h-4 w-4 text-signal" />
              Video Level Predictions
            </CardTitle>
            <CardDescription>All extracted video predictions for {ticker}</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {data.predictions?.map((p: any) => {
              const dir = (p.direction || "neutral").toLowerCase();
              return (
                <div key={p.id} className="flex flex-col gap-2.5 rounded-md border border-line p-4 transition-colors hover:border-signal/40">
                  <div className="flex items-center justify-between gap-2">
                    <Badge
                      variant={
                        dir === "bullish"
                          ? "default"
                          : dir === "bearish"
                            ? "destructive"
                            : "secondary"
                      }
                      className={cn("font-mono text-micro text-signal-foreground! capitalize", `${dir === "bearish" ? "text-black!" : ""}`)}
                    >
                      {dir === "bullish" && <TrendingUp className="mr-1 h-3 w-3 inline" />}
                      {dir === "bearish" && <TrendingDown className="mr-1 h-3 w-3 inline" />}
                      {dir === "neutral" && <Minus className="mr-1 h-3 w-3 inline" />}
                      {dir}
                    </Badge>
                    <span className="font-mono text-micro text-ink-secondary">
                      Confidence: {((p.confidence ?? 0.75) * 100).toFixed(0)}%
                    </span>
                  </div>

                  {p.video_title && (
                    <div>
                      <p className="line-clamp-1 text-small font-semibold text-ink">{p.video_title}</p>
                      {p.channel_title && <p className="text-caption text-ink-secondary">{p.channel_title}</p>}
                    </div>
                  )}

                  <p className="rounded border border-line bg-panel-raised p-2.5 text-small italic text-ink-secondary">
                    &ldquo;{p.prediction_text}&rdquo;
                  </p>

                  <div className="flex items-center justify-between pt-1">
                    {p.accurate !== null && p.accurate !== undefined ? (
                      <Badge variant="outline" className={p.accurate ? "border-bullish/40 bg-bullish/10 text-micro text-bullish" : "border-bearish/40 bg-bearish/10 text-micro text-bearish"}>
                        {p.accurate ? "✓ Direction verified" : "✕ Direction inaccurate"}
                      </Badge>
                    ) : <div />}

                    {p.youtube_video_id && (
                      <a
                        href={`https://www.youtube.com/watch?v=${p.youtube_video_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-small font-medium text-signal hover:underline"
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
              <p className="text-small text-ink-secondary">No explicit predictions found for {ticker}.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Associated Themes</CardTitle>
            <CardDescription>Market themes mapped to {ticker}</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {data.themes?.map((t: any) => (
              <div key={t.id} className="flex flex-col gap-1 border-b border-line pb-3 last:border-0 last:pb-0">
                <span className="text-small font-medium text-ink">{t.name}</span>
                <span className="font-mono text-micro uppercase tracking-wider text-ink-faint">{t.level}</span>
                {t.description && <p className="mt-0.5 text-small text-ink-secondary">{t.description}</p>}
              </div>
            ))}
            {(!data.themes || data.themes.length === 0) && (
              <p className="text-small text-ink-secondary">No themes mapped to this ticker.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
