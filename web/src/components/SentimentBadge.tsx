import React from "react";
import { cn } from "@/lib/utils";

interface SentimentBadgeProps {
  direction?: "bullish" | "bearish" | "neutral" | string | null;
  score?: number; // e.g. -1.0 to 1.0 or bullish percentage
  confidence?: number; // e.g. 0 to 1
  size?: "sm" | "md";
  showIcon?: boolean;
  className?: string;
}

export function SentimentBadge({
  direction,
  score,
  confidence,
  size = "md",
  showIcon = true,
  className,
}: SentimentBadgeProps) {
  let resolvedDirection = (direction || "neutral").toLowerCase();

  if (!direction && score !== undefined) {
    if (score > 0.2) resolvedDirection = "bullish";
    else if (score < -0.2) resolvedDirection = "bearish";
    else resolvedDirection = "neutral";
  }

  const isBullish = resolvedDirection === "bullish";
  const isBearish = resolvedDirection === "bearish";

  const glyph = isBullish ? "B" : isBearish ? "S" : "–";

  const chipClass = isBullish
    ? "bg-bullish/12 text-bullish border-bullish/30"
    : isBearish
      ? "bg-bearish/12 text-bearish border-bearish/30"
      : "bg-panel-raised text-ink-secondary border-line";

  const sizeClass = size === "sm" ? "h-4 gap-1 px-1 text-micro" : "h-5 gap-1.5 px-1.5 text-micro";

  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center rounded-md border font-mono font-semibold tracking-[0.02em]",
        chipClass,
        sizeClass,
        className
      )}
    >
      {showIcon && (
        <span
          className={cn(
            "flex h-3.5 w-3.5 items-center justify-center rounded-sm border font-bold",
            isBullish
              ? "border-bullish/40 bg-bullish/15"
              : isBearish
                ? "border-bearish/40 bg-bearish/15"
                : "border-line bg-panel"
          )}
        >
          {glyph}
        </span>
      )}
      <span className="lowercase">{resolvedDirection}</span>
      {confidence !== undefined && (
        <span className="font-normal opacity-80 tabular-nums">
          ({(confidence * 100).toFixed(0)}%)
        </span>
      )}
    </span>
  );
}
