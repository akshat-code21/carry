"use client";

import { Badge } from "@/components/ui/badge";
import { AtSign, MessageCircle, Newspaper, Tv } from "lucide-react";
import type { MCSourceCard, SocialTickerSnapshot } from "@/lib/api";

const SOURCE_META: Record<string, { label: string; icon: typeof AtSign }> = {
  youtube: { label: "YouTube", icon: Tv },
  reddit: { label: "Reddit", icon: MessageCircle },
  x: { label: "X", icon: AtSign },
  news: { label: "News", icon: Newspaper },
};

function sentimentClass(score: number | null | undefined): string {
  if (score == null) return "border-line/60 bg-panel-raised text-ink-secondary";
  if (score > 0.05) return "border-bullish/40 bg-bullish/10 text-bullish";
  if (score < -0.05) return "border-bearish/40 bg-bearish/10 text-bearish";
  return "border-line/60 bg-panel-raised text-ink-secondary";
}

/**
 * Source-breakdown badges (YouTube / Reddit / X / News) for stock cards.
 * Each badge is tinted by that source's sentiment direction and shows its
 * mention count. Social sources are omitted when no snapshot is available.
 */
export function SocialSourceBadges({ social }: { social?: SocialTickerSnapshot | null }) {
  const sources: { key: string; sentiment: number | null; mentions: number | null }[] = [
    { key: "youtube", sentiment: null, mentions: null },
    ...(social?.sources ?? []).map((s: MCSourceCard) => ({
      key: s.source,
      sentiment: s.sentiment_score,
      mentions: s.mentions,
    })),
  ];

  return (
    <div className="flex min-w-0 flex-wrap items-center gap-1.5">
      {sources.map(({ key, sentiment, mentions }) => {
        const meta = SOURCE_META[key] ?? { label: key, icon: AtSign };
        const Icon = meta.icon;
        return (
          <Badge
            key={key}
            variant="outline"
            className={`gap-1 px-1.5 py-0 font-mono text-micro ${sentimentClass(sentiment)}`}
          >
            <Icon className="h-3 w-3" />
            {meta.label}
            {mentions != null && mentions > 0 ? ` · ${mentions}` : ""}
          </Badge>
        );
      })}
      {social?.buzz_score != null && (
        <span className="ml-1 font-mono text-micro text-ink-secondary">
          buzz {Math.round(social.buzz_score)}
        </span>
      )}
    </div>
  );
}
