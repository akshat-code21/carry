"use client";

import React from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  Area,
} from "recharts";
import { motion, useReducedMotion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, TrendingDown, Minus, ExternalLink, PlayCircle } from "lucide-react";
import { useChartColors } from "@/lib/useChartColors";

export interface PredictionDataPoint {
  id: string;
  video_id: string;
  ticker?: string | null;
  prediction_text: string;
  direction?: string | null;
  confidence?: number | null;
  accurate?: boolean | null;
  created_at: string;
  video_title?: string | null;
  youtube_video_id?: string | null;
  published_at?: string | null;
  channel_title?: string | null;
  performance?: any;
}

interface Props {
  predictions: PredictionDataPoint[];
  ticker: string;
}

export function PredictionSentimentChart({ predictions, ticker }: Props) {
  const chartColors = useChartColors();
  const reducedMotion = useReducedMotion();

  if (!predictions || predictions.length === 0) {
    return null;
  }

  const successColor = chartColors.success;
  const dangerColor = chartColors.danger;
  const mutedFgColor = chartColors.mutedForeground;
  const canvasColor = chartColors.canvas;
  const inkSecondaryColor = chartColors.inkSecondary;
  const lineColor = chartColors.line;
  const inkColor = chartColors.ink;

  // 1. Group predictions by video_id (or prediction id if video_id is missing)
  const videoGroups = new Map<string, PredictionDataPoint[]>();
  predictions.forEach((p) => {
    const key = p.video_id || p.id;
    if (!videoGroups.has(key)) {
      videoGroups.set(key, []);
    }
    videoGroups.get(key)!.push(p);
  });

  // 2. Aggregate each video group into a single video-level trajectory node
  const videoNodes = Array.from(videoGroups.values()).map((group) => {
    const sortedGroup = [...group].sort((a, b) => (b.confidence ?? 0) - (a.confidence ?? 0));
    const primary = sortedGroup[0];

    let totalScore = 0;
    let totalConf = 0;
    let bullishCount = 0;
    let bearishCount = 0;

    group.forEach((p) => {
      const dir = (p.direction || "neutral").toLowerCase();
      const conf = p.confidence ?? 0.75;
      totalConf += conf;
      if (dir === "bullish") {
        totalScore += conf;
        bullishCount++;
      } else if (dir === "bearish") {
        totalScore -= conf;
        bearishCount++;
      }
    });

    const count = group.length;
    const avgScore = Number((totalScore / count).toFixed(2));
    const avgConf = Number((totalConf / count).toFixed(2));

    const overallDirection =
      bullishCount > bearishCount
        ? "bullish"
        : bearishCount > bullishCount
          ? "bearish"
          : "neutral";

    const rawDate = primary.published_at || primary.created_at;
    const formattedDate = rawDate
      ? new Date(rawDate).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
      : "Unknown Date";

    return {
      videoId: primary.video_id,
      publishedAt: rawDate,
      date: formattedDate,
      score: avgScore,
      direction: overallDirection,
      confidence: avgConf,
      predictionText: primary.prediction_text,
      totalStatements: count,
      allStatements: group,
      videoTitle: primary.video_title || undefined,
      channelTitle: primary.channel_title || undefined,
      youtubeVideoId: primary.youtube_video_id,
      accurate: primary.accurate,
    };
  });

  // 3. Sort videos chronologically (oldest to newest) and assign 1-based index
  const chartData = videoNodes
    .sort((a, b) => new Date(a.publishedAt || 0).getTime() - new Date(b.publishedAt || 0).getTime())
    .map((item, idx) => ({ ...item, index: idx + 1 }));

  // Summary metrics
  const totalVideos = chartData.length;
  const bullishVideos = chartData.filter((d) => d.direction === "bullish").length;
  const bearishVideos = chartData.filter((d) => d.direction === "bearish").length;
  const avgConfidence =
    (chartData.reduce((acc, d) => acc + d.confidence, 0) / (totalVideos || 1)) * 100;

  const consensus =
    bullishVideos > bearishVideos
      ? "Bullish"
      : bearishVideos > bullishVideos
        ? "Bearish"
        : "Neutral";

  // ── Signal tape node: a square B/S/– chip, confidence halo, verified ring ──
  const TapeNode = (props: any) => {
    const { cx, cy, payload } = props;
    if (!cx || !cy) return null;

    const dir = payload.direction;
    let fill = mutedFgColor;
    if (dir === "bullish") fill = successColor;
    if (dir === "bearish") fill = dangerColor;

    const glyph = dir === "bullish" ? "B" : dir === "bearish" ? "S" : "–";
    const glyphFill = dir === "bullish" || dir === "bearish" ? canvasColor : inkColor;
    const halo = 7 + Math.round((payload.confidence || 0.5) * 7);
    const verified = payload.accurate !== null && payload.accurate !== undefined;

    return (
      <g>
        <circle cx={cx} cy={cy} r={halo} fill={fill} opacity={0.14} />
        {verified && (
          <circle
            cx={cx}
            cy={cy}
            r={halo + 3.5}
            fill="none"
            stroke={inkSecondaryColor}
            strokeOpacity={0.7}
            strokeWidth={1}
          />
        )}
        <rect
          x={cx - 6.5}
          y={cy - 6.5}
          width={13}
          height={13}
          rx={2}
          fill={fill}
          stroke={canvasColor}
          strokeWidth={1.5}
        />
        <text
          x={cx}
          y={cy}
          textAnchor="middle"
          dominantBaseline="central"
          fontSize={9}
          fontWeight={600}
          fontFamily="var(--font-plex-mono)"
          fill={glyphFill}
        >
          {glyph}
        </text>
        {verified && (
          <text
            x={cx + 10.5}
            y={cy - 10.5}
            textAnchor="middle"
            dominantBaseline="central"
            fontSize={8}
            fontFamily="var(--font-plex-mono)"
            fill={inkSecondaryColor}
          >
            ✓
          </text>
        )}
      </g>
    );
  };

  // Active (hover) node: enlarged halo + chip
  const TapeActiveNode = (props: any) => {
    const { cx, cy, payload } = props;
    if (!cx || !cy) return null;

    const dir = payload.direction;
    let fill = mutedFgColor;
    if (dir === "bullish") fill = successColor;
    if (dir === "bearish") fill = dangerColor;

    const glyph = dir === "bullish" ? "B" : dir === "bearish" ? "S" : "–";
    const glyphFill = dir === "bullish" || dir === "bearish" ? canvasColor : inkColor;
    const halo = 10 + Math.round((payload.confidence || 0.5) * 7);

    return (
      <g>
        <circle cx={cx} cy={cy} r={halo} fill={fill} opacity={0.22} />
        <rect
          x={cx - 7}
          y={cy - 7}
          width={14}
          height={14}
          rx={2}
          fill={fill}
          stroke={canvasColor}
          strokeWidth={2}
        />
        <text
          x={cx}
          y={cy}
          textAnchor="middle"
          dominantBaseline="central"
          fontSize={9.5}
          fontWeight={600}
          fontFamily="var(--font-plex-mono)"
          fill={glyphFill}
        >
          {glyph}
        </text>
      </g>
    );
  };

  // Custom Tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null;
    const data = payload[0].payload;

    return (
      <div className="z-50 max-w-sm rounded-md border border-line bg-panel p-3 shadow-xl text-ink">
        <div className="flex items-center justify-between gap-2 border-b border-line pb-2">
          <span className="font-mono text-micro text-ink-faint">{data.date}</span>
          <span
            className={
              data.direction === "bullish"
                ? "rounded bg-bullish/10 px-1.5 py-0.5 font-mono text-micro font-semibold text-bullish"
                : data.direction === "bearish"
                  ? "rounded bg-bearish/10 px-1.5 py-0.5 font-mono text-micro font-semibold text-bearish"
                  : "rounded bg-panel-raised px-1.5 py-0.5 font-mono text-micro font-semibold text-ink-secondary"
            }
          >
            {data.direction} · {(data.confidence * 100).toFixed(0)}%
          </span>
        </div>

        {(data.videoTitle || data.channelTitle) && (
          <div className="mt-2 space-y-0.5">
            {data.videoTitle && <p className="line-clamp-2 text-body font-semibold">{data.videoTitle}</p>}
            {data.channelTitle && <p className="text-small text-ink-secondary">{data.channelTitle}</p>}
          </div>
        )}

        <div className="mt-3 line-clamp-3 rounded border-l-2 border-line-strong bg-panel-raised p-2 text-small italic text-ink-secondary">
          &ldquo;{data.predictionText}&rdquo;
        </div>

        {data.totalStatements > 1 && (
          <p className="mt-1.5 font-mono text-micro text-ink-faint">
            {data.totalStatements} prediction statements in this video
          </p>
        )}

        {data.accurate !== null && data.accurate !== undefined && (
          <div className="mt-2">
            <span
              className={
                data.accurate
                  ? "rounded bg-bullish/10 px-1.5 py-0.5 font-mono text-micro font-semibold text-bullish"
                  : "rounded bg-bearish/10 px-1.5 py-0.5 font-mono text-micro font-semibold text-bearish"
              }
            >
              {data.accurate ? "✓ Direction verified" : "✕ Direction inaccurate"}
            </span>
          </div>
        )}

        {data.youtubeVideoId && (
          <a
            href={`https://www.youtube.com/watch?v=${data.youtubeVideoId}`}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-3 flex items-center gap-1 text-small font-medium text-signal hover:underline"
          >
            <PlayCircle className="h-3.5 w-3.5" />
            Watch on YouTube
            <ExternalLink className="ml-auto h-3 w-3" />
          </a>
        )}
      </div>
    );
  };

  const consensusTone =
    consensus === "Bullish"
      ? "bg-bullish/10 text-bullish border-bullish/30"
      : consensus === "Bearish"
        ? "bg-bearish/10 text-bearish border-bearish/30"
        : "bg-panel-raised text-ink-secondary border-line";

  return (
    <Card className="w-full">
      <CardHeader className="pb-2">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              Signal tape — ${ticker}
            </CardTitle>
            <CardDescription>
              Sentiment trajectory, one chip per video, weighted by confidence
            </CardDescription>
          </div>

          <Badge variant="outline" className={consensusTone}>
            Consensus: {consensus}
          </Badge>
        </div>

        {/* Tape metrics strip */}
        <div className="mt-4 grid grid-cols-2 gap-x-4 gap-y-2 rounded-md border border-line bg-panel-raised p-3 sm:grid-cols-4">
          <div>
            <span className="label-overline">Videos</span>
            <p className="mt-0.5 font-mono text-title font-semibold tabular-nums text-ink">{totalVideos}</p>
          </div>
          <div>
            <span className="label-overline">Bullish</span>
            <p className="mt-0.5 font-mono text-title font-semibold tabular-nums text-bullish">
              {((bullishVideos / totalVideos) * 100).toFixed(0)}%
            </p>
          </div>
          <div>
            <span className="label-overline">Bearish</span>
            <p className="mt-0.5 font-mono text-title font-semibold tabular-nums text-bearish">
              {((bearishVideos / totalVideos) * 100).toFixed(0)}%
            </p>
          </div>
          <div>
            <span className="label-overline">Avg conf</span>
            <p className="mt-0.5 font-mono text-title font-semibold tabular-nums text-ink">
              {avgConfidence.toFixed(0)}%
            </p>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
        >
          <div className="h-[280px] w-full pt-4">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart
                data={chartData}
                margin={{ top: 20, right: 30, left: 0, bottom: 20 }}
              >
                <defs>
                  <linearGradient id="bullishGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={successColor} stopOpacity={0.22} />
                    <stop offset="100%" stopColor={successColor} stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="bearishGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={dangerColor} stopOpacity={0} />
                    <stop offset="100%" stopColor={dangerColor} stopOpacity={0.22} />
                  </linearGradient>
                </defs>

                <CartesianGrid strokeDasharray="2 4" opacity={0.5} stroke={lineColor} vertical={false} />

                <XAxis
                  dataKey="index"
                  type="number"
                  domain={[0.5, chartData.length + 0.5]}
                  ticks={chartData.map((d) => d.index)}
                  tickFormatter={(idx) => chartData[idx - 1]?.date || ""}
                  tick={{ fontSize: 10, fill: inkSecondaryColor, fontFamily: "var(--font-plex-mono)" }}
                  tickLine={false}
                  axisLine={{ stroke: lineColor }}
                  tickMargin={8}
                />

                <YAxis
                  domain={[-1, 1]}
                  ticks={[-1, -0.5, 0, 0.5, 1]}
                  tickFormatter={(value) => {
                    if (value === 1) return "+1.0";
                    if (value === -1) return "-1.0";
                    return value.toString();
                  }}
                  tick={{ fontSize: 10, fill: inkSecondaryColor, fontFamily: "var(--font-plex-mono)" }}
                  tickLine={false}
                  axisLine={false}
                  width={42}
                />

                <Tooltip content={<CustomTooltip />} wrapperStyle={{ outline: "none", pointerEvents: "none" }} />

                <ReferenceLine
                  y={0}
                  stroke={inkSecondaryColor}
                  strokeDasharray="3 3"
                  strokeOpacity={0.5}
                  label={{
                    value: "NEUTRAL",
                    fill: inkSecondaryColor,
                    fontSize: 9,
                    fontFamily: "var(--font-plex-mono)",
                    position: "insideBottomRight",
                  }}
                />

                <Area
                  type="stepAfter"
                  dataKey="score"
                  fill="url(#bullishGradient)"
                  stroke="none"
                  animationDuration={reducedMotion ? 0 : 650}
                  animationBegin={150}
                />

                <Line
                  type="stepAfter"
                  dataKey="score"
                  stroke={mutedFgColor}
                  strokeWidth={1.5}
                  strokeOpacity={0.75}
                  dot={<TapeNode />}
                  activeDot={<TapeActiveNode />}
                  name="Sentiment Trajectory"
                  animationDuration={reducedMotion ? 0 : 700}
                  animationBegin={150}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Tape legend */}
        <div className="mt-2 flex flex-wrap items-center gap-x-5 gap-y-1.5 border-t border-line pt-3 font-mono text-micro text-ink-faint">
          <span className="flex items-center gap-1.5">
            <span className="flex h-3.5 w-3.5 items-center justify-center rounded-[2px] bg-bullish text-micro font-bold leading-none text-canvas">B</span>
            Bullish
          </span>
          <span className="flex items-center gap-1.5">
            <span className="flex h-3.5 w-3.5 items-center justify-center rounded-[2px] bg-bearish text-micro font-bold leading-none text-canvas">S</span>
            Bearish
          </span>
          <span className="flex items-center gap-1.5">
            <span className="flex h-3.5 w-3.5 items-center justify-center rounded-[2px] bg-panel-raised text-micro leading-none text-ink-secondary">–</span>
            Neutral
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-signal/30" />
            Halo = confidence
          </span>
          <span className="flex items-center gap-1.5">
            <span className="text-ink-secondary">✓</span>
            Outcome verified
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
