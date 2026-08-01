"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  TrendingUp,
  TrendingDown,
  Layers,
  MessageCircle,
  AtSign,
  Newspaper,
  Flame,
  ArrowUpRight,
  ShieldAlert,
} from "lucide-react";
import { MCDashboardData, MCDashboardTickerItem } from "@/lib/api";
import { GlowCard } from "@/components/market-chatter/GlowCard";
import { AnimatedCounter } from "@/components/market-chatter/AnimatedCounter";
import { SectionLabel } from "@/components/market-chatter/SectionLabel";
import { cn } from "@/lib/utils";

interface DashboardOverviewProps {
  data: MCDashboardData;
  onSelectTicker: (symbol: string) => void;
}

export function DashboardOverview({
  data,
  onSelectTicker,
}: DashboardOverviewProps) {
  const [filter, setFilter] = useState<"all" | "stocks" | "etfs">("all");

  const displayTickers =
    filter === "stocks"
      ? data.top_stocks
      : filter === "etfs"
      ? data.top_etfs
      : [...data.top_stocks, ...data.top_etfs].slice(0, 12);

  const { summary, platform_breakdown } = data;

  return (
    <div className="mt-8 space-y-10">
      {/* ── Summary KPI Grid ────────────────────────────────────────────── */}
      <section aria-label="Social Chatter Overview Metrics">
        <div className="grid grid-cols-4 gap-4 max-lg:grid-cols-2 max-sm:grid-cols-1">
          <GlowCard glowColor="signal" className="p-5">
            <div className="flex items-center justify-between text-tf-faint">
              <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-tf-muted">
                Total Social Mentions
              </span>
              <Layers className="h-4 w-4 text-tf-signal" />
            </div>
            <div className="mt-4">
              <AnimatedCounter
                value={summary.total_mentions}
                decimals={0}
                className="text-[34px] font-medium leading-none tracking-[-0.06em] text-tf-ink"
              />
              <p className="mt-2 text-[11px] text-tf-faint">
                Ingested across Reddit, X, News & StockTwits
              </p>
            </div>
          </GlowCard>

          <GlowCard glowColor="neutral" className="p-5">
            <div className="flex items-center justify-between text-tf-faint">
              <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-tf-muted">
                Tracked Universe
              </span>
              <Flame className="h-4 w-4 text-amber-400" />
            </div>
            <div className="mt-4">
              <AnimatedCounter
                value={summary.tracked_tickers}
                decimals={0}
                className="text-[34px] font-medium leading-none tracking-[-0.06em] text-tf-ink"
              />
              <p className="mt-2 text-[11px] text-tf-faint">
                {summary.tracked_stocks} Equities · {summary.tracked_etfs} ETFs
              </p>
            </div>
          </GlowCard>

          <GlowCard glowColor="neutral" className="p-5">
            <div className="flex items-center justify-between text-tf-faint">
              <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-tf-muted">
                Market Sentiment Index
              </span>
              <TrendingUp className="h-4 w-4 text-emerald-400" />
            </div>
            <div className="mt-4">
              <AnimatedCounter
                value={summary.overall_bullish_pct}
                decimals={1}
                suffix="%"
                className="text-[34px] font-medium leading-none tracking-[-0.06em] text-emerald-400"
              />
              <p className="mt-2 text-[11px] text-tf-faint">
                Weighted average OCS bullish sentiment
              </p>
            </div>
          </GlowCard>

          <GlowCard glowColor="neutral" className="p-5">
            <div className="flex items-center justify-between text-tf-faint">
              <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-tf-muted">
                Platform Activity Ratio
              </span>
              <AtSign className="h-4 w-4 text-tf-signal" />
            </div>
            <div className="mt-4">
              <div className="text-[28px] font-medium leading-none tracking-[-0.04em] text-tf-ink">
                {Math.round((platform_breakdown.reddit_mentions / Math.max(1, platform_breakdown.total_mentions)) * 100)}%
                <span className="text-[13px] font-normal text-tf-muted font-mono ml-1.5">Reddit</span>
              </div>
              <p className="mt-2 text-[11px] text-tf-faint">
                {Math.round((platform_breakdown.x_mentions / Math.max(1, platform_breakdown.total_mentions)) * 100)}% X/FinTwit · {Math.round((platform_breakdown.news_mentions / Math.max(1, platform_breakdown.total_mentions)) * 100)}% News
              </p>
            </div>
          </GlowCard>
        </div>
      </section>

      {/* ── Top Tracked Stocks & ETFs Grid ────────────────────────────────────────── */}
      <section aria-labelledby="top-tickers-title">
        <div className="flex items-center justify-between gap-4 border-b border-tf-stroke pb-4 max-sm:flex-col max-sm:items-start">
          <div>
            <SectionLabel dotColor="#efb864">Market Chatter Leaders</SectionLabel>
            <h2 id="top-tickers-title" className="mt-1 text-[20px] font-semibold text-tf-ink tracking-tight">
              Top Tracked Equities & Sector ETFs
            </h2>
          </div>
          <div className="flex rounded-md border border-tf-stroke bg-tf-panel p-1">
            <button
              type="button"
              onClick={() => setFilter("all")}
              className={cn(
                "rounded px-3 py-1 text-[11px] font-medium text-tf-muted transition-colors",
                filter === "all" && "bg-tf-panel-raised text-tf-ink shadow-sm"
              )}
            >
              All Tickers
            </button>
            <button
              type="button"
              onClick={() => setFilter("stocks")}
              className={cn(
                "rounded px-3 py-1 text-[11px] font-medium text-tf-muted transition-colors",
                filter === "stocks" && "bg-tf-panel-raised text-tf-ink shadow-sm"
              )}
            >
              Stocks Only
            </button>
            <button
              type="button"
              onClick={() => setFilter("etfs")}
              className={cn(
                "rounded px-3 py-1 text-[11px] font-medium text-tf-muted transition-colors",
                filter === "etfs" && "bg-tf-panel-raised text-tf-ink shadow-sm"
              )}
            >
              ETFs Only
            </button>
          </div>
        </div>

        <div className="mt-5 grid grid-cols-3 gap-4 max-lg:grid-cols-2 max-sm:grid-cols-1">
          {displayTickers.map((item) => (
            <motion.div
              key={item.symbol}
              whileHover={{ y: -2 }}
              onClick={() => onSelectTicker(item.symbol)}
              className="group cursor-pointer rounded-xl border border-tf-stroke bg-tf-panel p-4 transition-all hover:border-tf-signal/30 hover:bg-tf-panel-raised"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-[18px] font-semibold text-tf-ink group-hover:text-tf-signal transition-colors">
                      ${item.symbol}
                    </span>
                    {item.is_etf ? (
                      <span className="rounded bg-amber-400/10 px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wider text-amber-400 border border-amber-400/20">
                        ETF
                      </span>
                    ) : (
                      <span className="rounded bg-tf-stroke px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wider text-tf-muted">
                        Stock
                      </span>
                    )}
                  </div>
                  <p className="mt-0.5 text-[12px] text-tf-muted line-clamp-1">
                    {item.company_name}
                  </p>
                </div>
                <ArrowUpRight className="h-4 w-4 text-tf-faint group-hover:text-tf-signal group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
              </div>

              <div className="mt-5 flex items-end justify-between border-t border-tf-stroke/50 pt-3">
                <div>
                  <span className="text-[10px] uppercase tracking-wider text-tf-faint block">
                    Social Mentions
                  </span>
                  <span className="font-mono text-[16px] font-medium text-tf-ink">
                    {item.mentions}
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] uppercase tracking-wider text-tf-faint block">
                    Bullish OCS
                  </span>
                  <span className="font-mono text-[16px] font-medium text-emerald-400">
                    {item.bullish_pct}%
                  </span>
                </div>
              </div>

              <div className="mt-3 h-1 w-full overflow-hidden rounded-full bg-tf-stroke">
                <div
                  className="h-full bg-emerald-400 transition-all duration-500"
                  style={{ width: `${Math.min(100, Math.max(0, item.bullish_pct))}%` }}
                />
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── Sentiment Leaderboard (Bullish vs Bearish) ────────────────────────── */}
      <section className="grid grid-cols-2 gap-6 max-lg:grid-cols-1">
        <GlowCard glowColor="signal" className="p-5">
          <div className="flex items-center gap-2 border-b border-tf-stroke pb-3 text-emerald-400">
            <TrendingUp className="h-5 w-5" />
            <h3 className="text-[15px] font-semibold text-tf-ink">
              Top Bullish Sentiment Leaders
            </h3>
          </div>
          <div className="mt-4 space-y-3">
            {data.bullish_leaders.map((item) => (
              <div
                key={`bullish-${item.symbol}`}
                onClick={() => onSelectTicker(item.symbol)}
                className="flex items-center justify-between rounded-lg border border-tf-stroke/40 bg-tf-canvas p-3 transition-colors hover:border-emerald-500/30 cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <span className="font-mono text-[15px] font-semibold text-tf-ink">
                    ${item.symbol}
                  </span>
                  <span className="text-[12px] text-tf-muted line-clamp-1">
                    {item.company_name}
                  </span>
                </div>
                <div className="flex items-center gap-2 font-mono text-[14px] font-semibold text-emerald-400">
                  {item.bullish_pct}%
                </div>
              </div>
            ))}
          </div>
        </GlowCard>

        <GlowCard glowColor="neutral" className="p-5">
          <div className="flex items-center gap-2 border-b border-tf-stroke pb-3 text-rose-400">
            <ShieldAlert className="h-5 w-5" />
            <h3 className="text-[15px] font-semibold text-tf-ink">
              Top Bearish / Pullback Risks
            </h3>
          </div>
          <div className="mt-4 space-y-3">
            {data.bearish_laggards.map((item) => (
              <div
                key={`bearish-${item.symbol}`}
                onClick={() => onSelectTicker(item.symbol)}
                className="flex items-center justify-between rounded-lg border border-tf-stroke/40 bg-tf-canvas p-3 transition-colors hover:border-rose-500/30 cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <span className="font-mono text-[15px] font-semibold text-tf-ink">
                    ${item.symbol}
                  </span>
                  <span className="text-[12px] text-tf-muted line-clamp-1">
                    {item.company_name}
                  </span>
                </div>
                <div className="flex items-center gap-2 font-mono text-[14px] font-semibold text-rose-400">
                  {item.bullish_pct}%
                </div>
              </div>
            ))}
          </div>
        </GlowCard>
      </section>

      {/* ── Platform Distribution Breakdown ─────────────────────────────────── */}
      <section aria-label="Platform Chatter Volume Breakdown">
        <GlowCard glowColor="neutral" className="p-5">
          <SectionLabel dotColor="#efb864">Cross-Platform Distribution</SectionLabel>
          <h3 className="mt-2 text-[17px] font-semibold text-tf-ink">
            Chatter Ingestion by Platform
          </h3>
          <div className="mt-5 grid grid-cols-3 gap-4 max-sm:grid-cols-1">
            <div className="rounded-lg border border-tf-stroke bg-tf-canvas p-4">
              <div className="flex items-center gap-2 text-tf-muted">
                <MessageCircle className="h-4 w-4 text-amber-400" />
                <span className="text-[12px] font-medium">Reddit Retail</span>
              </div>
              <p className="mt-2 font-mono text-[22px] font-medium text-tf-ink">
                {platform_breakdown.reddit_mentions} <span className="text-[12px] font-normal text-tf-faint">posts</span>
              </p>
            </div>
            <div className="rounded-lg border border-tf-stroke bg-tf-canvas p-4">
              <div className="flex items-center gap-2 text-tf-muted">
                <AtSign className="h-4 w-4 text-sky-400" />
                <span className="text-[12px] font-medium">X / FinTwit</span>
              </div>
              <p className="mt-2 font-mono text-[22px] font-medium text-tf-ink">
                {platform_breakdown.x_mentions} <span className="text-[12px] font-normal text-tf-faint">tweets</span>
              </p>
            </div>
            <div className="rounded-lg border border-tf-stroke bg-tf-canvas p-4">
              <div className="flex items-center gap-2 text-tf-muted">
                <Newspaper className="h-4 w-4 text-emerald-400" />
                <span className="text-[12px] font-medium">Financial News</span>
              </div>
              <p className="mt-2 font-mono text-[22px] font-medium text-tf-ink">
                {platform_breakdown.news_mentions} <span className="text-[12px] font-normal text-tf-faint">articles</span>
              </p>
            </div>
          </div>
        </GlowCard>
      </section>
    </div>
  );
}
