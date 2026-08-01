import React from "react";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
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

  const Icon = isBullish ? TrendingUp : isBearish ? TrendingDown : Minus;

  const variantClass = isBullish
    ? "bg-success/10 text-success border-success/30 hover:bg-success/20"
    : isBearish
    ? "bg-danger/10 text-danger border-danger/30 hover:bg-danger/20"
    : "bg-secondary text-secondary-foreground border-border";

  const sizeClass = size === "sm" ? "text-[10px] px-1.5 py-0" : "text-xs px-2 py-0.5";

  return (
    <Badge
      variant="outline"
      className={cn(
        "font-semibold uppercase tracking-wider gap-1 font-mono shrink-0",
        variantClass,
        sizeClass,
        className
      )}
    >
      {showIcon && <Icon className={size === "sm" ? "h-3 w-3" : "h-3.5 w-3.5"} />}
      <span>{resolvedDirection}</span>
      {confidence !== undefined && (
        <span className="opacity-80 font-normal">({(confidence * 100).toFixed(0)}%)</span>
      )}
    </Badge>
  );
}
