"use client";

import Link from "next/link";
import { motion, useReducedMotion, type Variants } from "framer-motion";
import { ArrowRight, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { Button } from "@/components/ui/button";

const EASE: [number, number, number, number] = [0.16, 1, 0.3, 1];

const container: Variants = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.11, delayChildren: 0.15 },
  },
};

const item: Variants = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { duration: 0.65, ease: EASE } },
};

interface PreviewRow {
  ticker: string;
  company: string;
  mentions: number;
  bullish: number;
  bearish: number;
  daysAgo: string;
}

/* Realistic ticker-mentions snapshot - the shape of Tickerflow/Dashboard output */
const previewRows: PreviewRow[] = [
  { ticker: "NVDA", company: "NVIDIA", mentions: 42, bullish: 78, bearish: 14, daysAgo: "2h ago" },
  { ticker: "TSLA", company: "Tesla", mentions: 35, bullish: 44, bearish: 40, daysAgo: "5h ago" },
  { ticker: "PLTR", company: "Palantir", mentions: 27, bullish: 61, bearish: 22, daysAgo: "1d ago" },
  { ticker: "SOFI", company: "SoFi", mentions: 19, bullish: 52, bearish: 31, daysAgo: "1d ago" },
  { ticker: "GLD", company: "SPDR Gold", mentions: 16, bullish: 66, bearish: 19, daysAgo: "3d ago" },
];

const sentimentMeta = {
  bullish: { Icon: TrendingUp, className: "text-bullish", bg: "bg-bullish/10 border-bullish/25" },
  bearish: { Icon: TrendingDown, className: "text-bearish", bg: "bg-bearish/10 border-bearish/25" },
  neutral: { Icon: Minus, className: "text-ink-secondary", bg: "bg-panel-raised border-line-strong" },
} as const;

function netSentiment(row: PreviewRow): "bullish" | "bearish" | "neutral" {
  if (row.bullish - row.bearish >= 20) return "bullish";
  if (row.bearish - row.bullish >= 20) return "bearish";
  return "neutral";
}

function DataPreview() {
  const reducedMotion = useReducedMotion();

  return (
    <motion.div
      initial={reducedMotion ? false : { opacity: 0, y: 40 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.75, delay: 0.5, ease: EASE }}
      className="relative mx-auto mt-14 w-full max-w-4xl lg:mt-16"
    >
      {/* Single focal shimmer - the only scan animation on the page */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 overflow-hidden rounded-lg"
      >
        <div
          className={
            "animate-scan absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-transparent via-signal/[0.05] to-transparent" +
            (reducedMotion ? " hidden" : "")
          }
        />
      </div>

      <div className="relative overflow-hidden rounded-lg border border-line-strong bg-panel">
        {/* Window chrome - echoes the app's dashboard framing */}
        <div className="flex h-10 items-center justify-between border-b border-line px-4">
          <p className="font-mono text-micro font-semibold uppercase tracking-[0.12em] text-ink-faint">
            Ticker mentions · last 7 days
          </p>
          <div className="flex items-center gap-1.5 font-mono text-micro text-ink-faint">
            <span className="size-1.5 rounded-full bg-signal" aria-hidden="true" />
            sample data
          </div>
        </div>

        {/* Dense mentions table - mirrors the dashboard's terminal-table style */}
        <div className="overflow-x-auto">
          <table className="w-full min-w-[540px] border-collapse font-mono text-small tabular-nums">
            <thead>
              <tr className="border-b border-line bg-canvas/60 text-left">
                <th className="px-4 py-2 text-micro font-semibold uppercase tracking-[0.1em] text-ink-faint">
                  Ticker
                </th>
                <th className="px-3 py-2 text-right text-micro font-semibold uppercase tracking-[0.1em] text-ink-faint">
                  Mentions
                </th>
                <th className="px-3 py-2 text-right text-micro font-semibold uppercase tracking-[0.1em] text-ink-faint">
                  Bullish
                </th>
                <th className="px-3 py-2 text-right text-micro font-semibold uppercase tracking-[0.1em] text-ink-faint">
                  Bearish
                </th>
                <th className="px-4 py-2 text-right text-micro font-semibold uppercase tracking-[0.1em] text-ink-faint">
                  Last
                </th>
              </tr>
            </thead>
            <tbody>
              {previewRows.map((row) => {
                const meta = sentimentMeta[netSentiment(row)];
                return (
                  <tr
                    key={row.ticker}
                    className="border-b border-line/70 transition-colors last:border-0 hover:bg-panel-raised"
                  >
                    <td className="px-4 py-2.5">
                      <span className="font-semibold tracking-tight text-ink">
                        {row.ticker}
                      </span>
                      <span className="ml-2.5 hidden text-caption text-ink-faint sm:inline">
                        {row.company}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 text-right text-ink">
                      {row.mentions}
                    </td>
                    <td className="px-3 py-2.5 text-right">
                      <span
                        className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 font-mono text-micro font-semibold ${meta.bg} ${meta.className}`}
                      >
                        <meta.Icon className="size-3" />
                        {row.bullish}%
                      </span>
                    </td>
                    <td className="px-3 py-2.5 text-right text-ink-secondary">
                      {row.bearish}%
                    </td>
                    <td className="px-4 py-2.5 text-right text-ink-faint">
                      {row.daysAgo}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between border-t border-line px-4 py-2.5">
          <p className="font-mono text-micro text-ink-faint">
            5 of 1,284 tracked tickers · aggregated across 4 social + news sources
          </p>
          <p className="font-mono text-micro text-ink-faint">
            not investment advice
          </p>
        </div>
      </div>
    </motion.div>
  );
}

export function Hero() {
  const reducedMotion = useReducedMotion();

  return (
    <section className="relative overflow-hidden pt-32 pb-20 lg:pt-40 lg:pb-24">
      <div
        aria-hidden="true"
        className="bg-grid absolute inset-0 -z-10 [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,black,transparent)]"
      />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <motion.div
          variants={container}
          initial={reducedMotion ? false : "hidden"}
          animate="show"
          className="mx-auto max-w-3xl text-center"
        >
          <motion.h1
            variants={item}
            className="font-display text-4xl font-bold leading-[1.05] tracking-tight text-ink sm:text-5xl lg:text-6xl"
          >
            Market chatter, distilled into{" "}
            <span className="text-gradient">tickers, themes, and sentiment.</span>
          </motion.h1>

          <motion.p
            variants={item}
            className="mx-auto mt-6 max-w-2xl text-title leading-relaxed text-ink-secondary"
          >
            Carry aggregates YouTube, Reddit, X, and the news, plus quarterly
            13F filings, then extracts every ticker, theme, and
            bullish-or-bearish call into one searchable dashboard.
          </motion.p>

          <motion.div variants={item} className="mt-10 flex justify-center">
            <Link href="/sign-up">
              <Button size="lg" className="h-11 gap-2 px-7 text-body">
                Get started
                <ArrowRight className="size-4" />
              </Button>
            </Link>
          </motion.div>

          {/* Sources - what the pipeline actually ingests */}
          <motion.p
            variants={item}
            className="mt-8 font-mono text-micro uppercase tracking-[0.14em] text-ink-faint"
          >
            YouTube · Reddit · X · News · SEC 13F filings
          </motion.p>
        </motion.div>

        {/* Real product output, directly under the hero - the primary trust-builder */}
        <DataPreview />
      </div>
    </section>
  );
}
