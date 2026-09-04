"use client";

import { useMemo } from "react";
import {
  Activity,
  AtSign,
  Gauge,
  MessageCircle,
  Newspaper,
  Tv,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  TradingViewPriceChart,
  type TvMetricPoint,
  type TvPricePoint,
  type TvSignalMarker,
} from "@/components/TradingViewPriceChart";
import type {
  MCChartPoint,
  MCSourceCard,
  MCTickerData,
  Prediction,
  TickerSentimentTimelineItem,
} from "@/lib/api";

const SOURCE_META: Record<string, { label: string; icon: typeof AtSign }> = {
  youtube: { label: "YouTube", icon: Tv },
  reddit: { label: "Reddit", icon: MessageCircle },
  x: { label: "X", icon: AtSign },
  news: { label: "News", icon: Newspaper },
};

function sentimentTextClass(score: number | null | undefined): string {
  if (score == null) return "text-ink-secondary";
  if (score > 0.05) return "text-bullish";
  if (score < -0.05) return "text-bearish";
  return "text-ink-secondary";
}

function fmtSentiment(score: number | null | undefined): string {
  return score == null ? "-" : score > 0 ? `+${score.toFixed(2)}` : score.toFixed(2);
}

function findClosestChartDate(targetDateStr: string, chart: MCChartPoint[]): string | null {
  if (!chart.length) return null;
  const targetTime = new Date(targetDateStr).getTime();
  if (isNaN(targetTime)) return null;

  let closest = chart[0];
  let minDiff = Math.abs(new Date(closest.date).getTime() - targetTime);

  for (let i = 1; i < chart.length; i++) {
    const diff = Math.abs(new Date(chart[i].date).getTime() - targetTime);
    if (diff < minDiff) {
      minDiff = diff;
      closest = chart[i];
    }
  }

  // Allow up to 4 calendar days diff to snap weekend/holiday mentions to the nearest trading day
  if (minDiff <= 4 * 24 * 60 * 60 * 1000) {
    return closest.date;
  }
  return null;
}

export interface SocialSentimentPanelProps {
  social: MCTickerData;
  predictions?: Prediction[];
  sentimentTimeline?: TickerSentimentTimelineItem[];
  youtubeMentions?: number;
  youtubeAvgSentiment?: number | null;
}

/**
 * Social & Video sentiment panel (YouTube / Reddit / X / News) for ticker detail & search:
 * aggregate signal, per-source breakdown, and a combined mentions/buzz chart
 * with consensus buy/sell markers overlaid on the close price using TradingView Lightweight Charts.
 */
export function SocialSentimentPanel({
  social,
  predictions,
  sentimentTimeline,
  youtubeMentions,
  youtubeAvgSentiment,
}: SocialSentimentPanelProps) {
  const hasYoutube = Boolean(
    (youtubeMentions != null && youtubeMentions > 0) ||
    (predictions != null && predictions.length > 0) ||
    (sentimentTimeline != null && sentimentTimeline.length > 0) ||
    youtubeAvgSentiment != null
  );

  // Derive YouTube aggregated metrics for the source card
  const { ytTotalMentions, ytBullishPct, ytBearishPct, ytSentimentScore } = useMemo(() => {
    if (!hasYoutube) {
      return { ytTotalMentions: 0, ytBullishPct: null, ytBearishPct: null, ytSentimentScore: null };
    }

    let bullCount = 0;
    let bearCount = 0;
    let totalCount = youtubeMentions ?? 0;

    if (sentimentTimeline && sentimentTimeline.length > 0) {
      for (const item of sentimentTimeline) {
        bullCount += item.bullish_count || 0;
        bearCount += item.bearish_count || 0;
        if (youtubeMentions == null) totalCount += item.total_count || 0;
      }
    } else if (predictions && predictions.length > 0) {
      if (youtubeMentions == null) totalCount = predictions.length;
      for (const p of predictions) {
        const dir = (p.direction || "").toLowerCase();
        if (dir === "bullish") bullCount++;
        if (dir === "bearish") bearCount++;
      }
    }

    const ratedCount = bullCount + bearCount;
    let sentiment = youtubeAvgSentiment ?? null;
    if (sentiment == null && ratedCount > 0) {
      sentiment = (bullCount - bearCount) / ratedCount;
    }

    let bullPct: number | null = null;
    let bearPct: number | null = null;

    if (ratedCount > 0) {
      bullPct = (bullCount / ratedCount) * 100;
      bearPct = (bearCount / ratedCount) * 100;
    } else if (sentiment != null) {
      // Map sentiment score (-1.0 .. +1.0) to standard 0..100% distribution matching TickerFlow's formula
      const normalized = Math.max(-1, Math.min(1, sentiment));
      bullPct = Math.round(((1 + normalized) / 2) * 100);
      bearPct = 100 - bullPct;
    }

    return {
      ytTotalMentions: totalCount,
      ytBullishPct: bullPct,
      ytBearishPct: bearPct,
      ytSentimentScore: sentiment,
    };
  }, [hasYoutube, youtubeMentions, sentimentTimeline, predictions, youtubeAvgSentiment]);

  // Combined source list (YouTube + Reddit + X + News)
  const allSources = useMemo<MCSourceCard[]>(() => {
    const list = [...social.sources];
    if (hasYoutube) {
      list.unshift({
        source: "youtube",
        status: "active",
        as_of: social.as_of,
        sentiment_score: ytSentimentScore,
        buzz_score: null,
        mentions: ytTotalMentions,
        bullish_pct: ytBullishPct,
        bearish_pct: ytBearishPct,
        trend: null,
        coverage_count: null,
        daily_mentions_available: true,
        message: null,
      });
    }
    return list;
  }, [social.sources, hasYoutube, ytSentimentScore, ytTotalMentions, ytBullishPct, ytBearishPct, social.as_of]);

  // Map YouTube mentions/predictions to closest trading days on the chart
  const ytDailyByChartDate = useMemo(() => {
    const map = new Map<string, { mentions: number; bullish: number; bearish: number }>();
    if (!hasYoutube) return map;

    if (sentimentTimeline && sentimentTimeline.length > 0) {
      for (const item of sentimentTimeline) {
        const chartDate = findClosestChartDate(item.date, social.chart);
        if (!chartDate) continue;
        const curr = map.get(chartDate) || { mentions: 0, bullish: 0, bearish: 0 };
        curr.mentions += item.total_count || 0;
        curr.bullish += item.bullish_count || 0;
        curr.bearish += item.bearish_count || 0;
        map.set(chartDate, curr);
      }
    } else if (predictions && predictions.length > 0) {
      for (const pred of predictions) {
        const rawDate = pred.published_at || pred.created_at;
        if (!rawDate) continue;
        const chartDate = findClosestChartDate(rawDate, social.chart);
        if (!chartDate) continue;
        const dir = (pred.direction || "").toLowerCase();
        const curr = map.get(chartDate) || { mentions: 0, bullish: 0, bearish: 0 };
        curr.mentions += 1;
        if (dir === "bullish") curr.bullish += 1;
        if (dir === "bearish") curr.bearish += 1;
        map.set(chartDate, curr);
      }
    }
    return map;
  }, [hasYoutube, sentimentTimeline, predictions, social.chart]);

  const points = useMemo<TvPricePoint[]>(
    () =>
      social.chart
        .filter((p) => p.close != null)
        .map((p) => ({
          date: p.date,
          open: p.close as number,
          high: p.close as number,
          low: p.close as number,
          close: p.close as number,
        })),
    [social.chart]
  );

  // Consensus markers combining Social signals and YouTube signals per trading day
  const markers = useMemo<TvSignalMarker[]>(() => {
    const list: TvSignalMarker[] = [];
    for (const p of social.chart) {
      if (p.close == null) continue;
      const yt = ytDailyByChartDate.get(p.date);
      const socialBuy = p.signal_label === "B" || p.signal === "buy";
      const socialSell = p.signal_label === "S" || p.signal === "sell";

      const bullVotes = (socialBuy ? 1 : 0) + (yt?.bullish ?? 0);
      const bearVotes = (socialSell ? 1 : 0) + (yt?.bearish ?? 0);

      if (bullVotes > bearVotes) {
        list.push({ date: p.date, signal: "B", label: "B" });
      } else if (bearVotes > bullVotes) {
        list.push({ date: p.date, signal: "S", label: "S" });
      }
    }
    return list;
  }, [social.chart, ytDailyByChartDate]);

  const hasMentions = useMemo(
    () => social.chart.some((p) => p.mentions != null) || hasYoutube,
    [social.chart, hasYoutube]
  );
  const hasBuzz = useMemo(() => social.chart.some((p) => p.buzz_score != null), [social.chart]);
  const metricKey = social.chart_metric === "buzz_score" && hasBuzz ? "buzz_score" : "mentions";
  const metricLabel = metricKey === "buzz_score" ? "Buzz Score" : "Mentions & Video Volume";

  const metrics = useMemo<TvMetricPoint[]>(
    () =>
      social.chart.map((p) => {
        if (metricKey === "buzz_score") {
          return { date: p.date, value: p.buzz_score };
        }
        const yt = ytDailyByChartDate.get(p.date);
        const combinedMentions = (p.mentions ?? 0) + (yt?.mentions ?? 0);
        return {
          date: p.date,
          value: combinedMentions > 0 ? combinedMentions : p.mentions,
        };
      }),
    [social.chart, metricKey, ytDailyByChartDate]
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Social & Video Sentiment
        </CardTitle>
        <CardDescription>
          {hasYoutube ? "YouTube, Reddit, X, and News" : "Reddit, X, and News"} chatter for {social.symbol}
          {social.company_name ? ` (${social.company_name})` : ""}
          {social.as_of
            ? ` · as of ${new Date(social.as_of).toLocaleDateString(undefined, {
              month: "short",
              day: "numeric",
            })}`
            : ""}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {/* Signal strip */}
        {social.signal && (
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            {[
              { label: "Signal Score", value: social.signal.score?.toFixed(0) ?? "-", icon: Gauge },
              {
                label: "Sentiment",
                value:
                  social.signal.sentiment != null
                    ? `${social.signal.sentiment.toFixed(0)}/100`
                    : "-",
                icon: Activity,
              },
              {
                label: "Attention",
                value:
                  social.signal.attention != null
                    ? `${social.signal.attention.toFixed(0)}/100`
                    : "-",
                icon: Activity,
              },
              {
                label: "Confidence",
                value: `${(social.signal.confidence * 100).toFixed(0)}%`,
                icon: Gauge,
              },
            ].map(({ label, value, icon: Icon }) => (
              <div key={label} className="rounded-md border border-line bg-panel-raised p-3">
                <div className="flex items-center gap-1.5 text-micro text-ink-secondary">
                  <Icon className="h-3 w-3" />
                  {label}
                </div>
                <p className="mt-1 font-mono text-title font-semibold text-ink">{value}</p>
              </div>
            ))}
          </div>
        )}

        {/* Per-source cards */}
        {allSources.length > 0 && (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {allSources.map((src: MCSourceCard) => {
              const meta = SOURCE_META[src.source] ?? { label: src.source, icon: AtSign };
              const Icon = meta.icon;
              return (
                <div key={src.source} className="rounded-md border border-line p-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5 text-small font-semibold text-ink">
                      <Icon className="h-3.5 w-3.5 text-signal" />
                      {meta.label}
                    </div>
                    <span
                      className={`font-mono text-small font-semibold ${sentimentTextClass(src.sentiment_score)}`}
                    >
                      {fmtSentiment(src.sentiment_score)}
                    </span>
                  </div>
                  <div className="mt-2 flex items-center justify-between font-mono text-micro text-ink-secondary">
                    <span>{src.mentions ?? 0} mentions</span>
                    {src.buzz_score != null && <span>buzz {Math.round(src.buzz_score)}</span>}
                  </div>
                  {(src.bullish_pct != null || src.bearish_pct != null) && (
                    <div className="mt-2 flex items-center gap-2">
                      {src.bullish_pct != null && (
                        <Badge
                          variant="outline"
                          className="border-bullish/40 bg-bullish/10 px-1.5 py-0 font-mono text-micro text-bullish"
                        >
                          {src.bullish_pct.toFixed(0)}% bull
                        </Badge>
                      )}
                      {src.bearish_pct != null && (
                        <Badge
                          variant="outline"
                          className="border-bearish/40 bg-bearish/10 px-1.5 py-0 font-mono text-micro text-bearish"
                        >
                          {src.bearish_pct.toFixed(0)}% bear
                        </Badge>
                      )}
                    </div>
                  )}
                  {src.message && <p className="mt-2 text-micro text-ink-faint">{src.message}</p>}
                </div>
              );
            })}
          </div>
        )}

        {/* Mentions/buzz chart with price + B/S markers using TradingView */}
        {points.length > 0 && (
          <div className="w-full">
            <TradingViewPriceChart
              points={points}
              seriesType="line"
              markers={markers}
              metrics={hasMentions || hasBuzz ? metrics : undefined}
              metricLabel={metricLabel}
              height={320}
            />
            <div className="mt-2.5 flex flex-wrap items-center justify-between gap-x-4 gap-y-1.5 border-t border-line/40 pt-2 font-mono text-micro text-ink-faint">
              <span className="flex items-center gap-1.5">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-signal" />
                {metricLabel} from {hasYoutube ? "YouTube, Reddit, X & News" : social.chart_source.toUpperCase()}
              </span>
              <span>B / S markers mark consensus days</span>
            </div>
          </div>
        )}

        {social.data_status && social.data_status !== "fresh" && (
          <p className="font-mono text-micro text-ink-faint">
            Data status: {social.data_status.replace(/_/g, " ")}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

