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
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, TrendingDown, Minus, ExternalLink, PlayCircle } from "lucide-react";

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
  if (!predictions || predictions.length === 0) {
    return null;
  }

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
    // Sort group predictions by confidence descending to get top quote
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

  // Calculate summary metrics across videos
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

  // Custom Dot Renderer for the trajectory line
  const CustomDot = (props: any) => {
    const { cx, cy, payload } = props;
    if (!cx || !cy) return null;

    let fill = "#64748b"; // Neutral slate
    if (payload.direction === "bullish") fill = "#22c55e"; // Green
    if (payload.direction === "bearish") fill = "#ef4444"; // Red

    const radius = 6 + Math.round((payload.confidence || 0.5) * 3);

    return (
      <circle
        cx={cx}
        cy={cy}
        r={radius}
        fill={fill}
        stroke="#ffffff"
        strokeWidth={2}
      />
    );
  };

  // Custom Active Dot Renderer when hovering
  const CustomActiveDot = (props: any) => {
    const { cx, cy, payload } = props;
    if (!cx || !cy) return null;

    let fill = "#64748b";
    if (payload.direction === "bullish") fill = "#22c55e";
    if (payload.direction === "bearish") fill = "#ef4444";

    const radius = 9 + Math.round((payload.confidence || 0.5) * 3);

    return (
      <g>
        <circle cx={cx} cy={cy} r={radius + 4} fill={fill} opacity={0.25} />
        <circle
          cx={cx}
          cy={cy}
          r={radius}
          fill={fill}
          stroke="#ffffff"
          strokeWidth={2.5}
        />
      </g>
    );
  };

  // Custom Tooltip Renderer
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null;
    const data = payload[0].payload;

    return (
      <div className="z-50 max-w-sm rounded-lg border bg-popover p-4 shadow-md text-popover-foreground">
        <div className="flex items-center justify-between gap-2 border-b pb-2">
          <span className="text-xs font-semibold text-muted-foreground">
            {data.date}
          </span>
          <Badge
            variant={
              data.direction === "bullish"
                ? "default"
                : data.direction === "bearish"
                  ? "destructive"
                  : "secondary"
            }
            className="capitalize"
          >
            {data.direction === "bullish" && <TrendingUp className="mr-1 h-3 w-3 inline" />}
            {data.direction === "bearish" && <TrendingDown className="mr-1 h-3 w-3 inline" />}
            {data.direction === "neutral" && <Minus className="mr-1 h-3 w-3 inline" />}
            {data.direction} ({(data.confidence * 100).toFixed(0)}%)
          </Badge>
        </div>

        {(data.videoTitle || data.channelTitle) && (
          <div className="mt-2 space-y-0.5">
            {data.videoTitle && <p className="font-semibold text-sm line-clamp-2">{data.videoTitle}</p>}
            {data.channelTitle && <p className="text-xs text-muted-foreground">{data.channelTitle}</p>}
          </div>
        )}

        <div className="mt-3 rounded bg-muted/50 p-2 text-xs italic text-muted-foreground line-clamp-3">
          &ldquo;{data.predictionText}&rdquo;
        </div>

        {data.totalStatements > 1 && (
          <p className="mt-1.5 text-[11px] font-medium text-muted-foreground">
            Includes {data.totalStatements} prediction statements in this video
          </p>
        )}

        {data.accurate !== null && data.accurate !== undefined && (
          <div className="mt-2">
            <Badge
              variant="outline"
              className={
                data.accurate
                  ? "border-green-500 text-green-500 bg-green-500/10 text-xs"
                  : "border-red-500 text-red-500 bg-red-500/10 text-xs"
              }
            >
              {data.accurate ? "Direction Verified ✅" : "Direction Inaccurate ❌"}
            </Badge>
          </div>
        )}

        {data.youtubeVideoId && (
          <a
            href={`https://www.youtube.com/watch?v=${data.youtubeVideoId}`}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-3 flex items-center gap-1 text-xs font-medium text-primary hover:underline"
          >
            <PlayCircle className="h-3.5 w-3.5" />
            Watch Video on YouTube
            <ExternalLink className="h-3 w-3 ml-auto" />
          </a>
        )}
      </div>
    );
  };

  return (
    <Card className="w-full">
      <CardHeader className="pb-2">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-xl font-bold">
              Video Prediction Trajectory ({ticker})
            </CardTitle>
            <CardDescription>
              Chronological video-by-video sentiment trajectory weighted by confidence
            </CardDescription>
          </div>

          <div className="flex items-center gap-2">
            <Badge
              variant={
                consensus === "Bullish"
                  ? "default"
                  : consensus === "Bearish"
                    ? "destructive"
                    : "secondary"
              }
              className="text-xs px-2.5 py-1"
            >
              Consensus: {consensus}
            </Badge>
          </div>
        </div>

        {/* Quick Metrics Bar */}
        <div className="mt-4 grid grid-cols-2 gap-4 rounded-lg bg-muted/40 p-3 sm:grid-cols-4 text-xs">
          <div>
            <span className="text-muted-foreground">Total Mentions:</span>
            <p className="text-sm font-semibold">{totalVideos}</p>
          </div>
          <div>
            <span className="text-muted-foreground">Bullish Ratio:</span>
            <p className="text-sm font-semibold text-green-500">
              {((bullishVideos / totalVideos) * 100).toFixed(0)}% ({bullishVideos})
            </p>
          </div>
          <div>
            <span className="text-muted-foreground">Bearish Ratio:</span>
            <p className="text-sm font-semibold text-red-500">
              {((bearishVideos / totalVideos) * 100).toFixed(0)}% ({bearishVideos})
            </p>
          </div>
          <div>
            <span className="text-muted-foreground">Avg Confidence:</span>
            <p className="text-sm font-semibold">{avgConfidence.toFixed(0)}%</p>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <div className="h-[280px] w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart
              data={chartData}
              margin={{ top: 20, right: 30, left: 0, bottom: 20 }}
            >
              <defs>
                <linearGradient id="bullishGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#22c55e" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="#22c55e" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="bearishGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#ef4444" stopOpacity={0.0} />
                  <stop offset="100%" stopColor="#ef4444" stopOpacity={0.4} />
                </linearGradient>
              </defs>

              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />

              <XAxis
                dataKey="index"
                type="number"
                domain={[0.5, chartData.length + 0.5]}
                ticks={chartData.map((d) => d.index)}
                tickFormatter={(idx) => chartData[idx - 1]?.date || ""}
                tick={{ fontSize: 11 }}
                tickMargin={8}
              />

              <YAxis
                domain={[-1, 1]}
                ticks={[-1, -0.5, 0, 0.5, 1]}
                tickFormatter={(value) => {
                  if (value === 1) return "+1.0 (Bullish)";
                  if (value === -1) return "-1.0 (Bearish)";
                  if (value === 0) return "Neutral";
                  return value.toString();
                }}
                tick={{ fontSize: 10 }}
                width={95}
              />

              <Tooltip content={<CustomTooltip />} wrapperStyle={{ outline: "none", pointerEvents: "none" }} />

              <ReferenceLine y={0} stroke="#94a3b8" strokeDasharray="3 3" label={{ value: "Neutral Line", fill: "#94a3b8", fontSize: 10, position: "insideBottomRight" }} />

              <Area
                type="stepAfter"
                dataKey="score"
                fill="url(#bullishGradient)"
                stroke="none"
              />

              <Line
                type="stepAfter"
                dataKey="score"
                stroke="#3b82f6"
                strokeWidth={2.5}
                dot={<CustomDot />}
                activeDot={<CustomActiveDot />}
                name="Sentiment Trajectory"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
