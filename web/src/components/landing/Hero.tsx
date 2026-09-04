"use client";

import Link from "next/link";
import { motion, useReducedMotion, type Variants } from "framer-motion";
import {
  ArrowRight,
  PlayCircle,
  Search,
  TrendingUp,
  TrendingDown,
  Minus,
  Quote,
  Radio,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

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
  theme: string;
  snippet: string;
  sentiment: "bullish" | "bearish" | "neutral";
  score: number;
}

const previewRows: PreviewRow[] = [
  {
    ticker: "NVDA",
    theme: "Semiconductors",
    snippet: "\u201c…compute demand is still growing faster than supply…\u201d",
    sentiment: "bullish",
    score: 92,
  },
  {
    ticker: "TLT",
    theme: "Rates / Bonds",
    snippet: "\u201c…the Fed starts easing in September, this tape rips…\u201d",
    sentiment: "bullish",
    score: 78,
  },
  {
    ticker: "XBI",
    theme: "Biotech",
    snippet: "\u201c…rate-sensitive names finally catch a bid…\u201d",
    sentiment: "neutral",
    score: 54,
  },
];

const sentimentMeta = {
  bullish: { Icon: TrendingUp, className: "text-bullish", bg: "bg-bullish/10 border-bullish/25" },
  bearish: { Icon: TrendingDown, className: "text-bearish", bg: "bg-bearish/10 border-bearish/25" },
  neutral: { Icon: Minus, className: "text-ink-faint", bg: "bg-panel-raised border-line-strong" },
} as const;

function HeroPreview() {
  const reducedMotion = useReducedMotion();

  return (
    <motion.div
      initial={reducedMotion ? false : { opacity: 0, y: 48, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.8, delay: 0.55, ease: EASE }}
      className="relative mx-auto mt-16 w-full max-w-3xl lg:mt-20"
    >
      <motion.div
        animate={reducedMotion ? undefined : { y: [0, -10, 0] }}
        transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
        className="relative overflow-hidden rounded-2xl border border-line-strong bg-panel/80 shadow-[0_40px_120px_-40px_color-mix(in_oklch,var(--ink)_60%,transparent)] backdrop-blur-xl"
      >
        <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-signal/70 to-transparent" />

        <div className="flex h-11 items-center gap-3 border-b border-line px-4">
          <div className="flex items-center gap-1.5">
            <span className="size-2.5 rounded-full bg-bearish/50" />
            <span className="size-2.5 rounded-full bg-warning/50" />
            <span className="size-2.5 rounded-full bg-bullish/50" />
          </div>
          <div className="mx-auto flex h-6 w-full max-w-sm items-center gap-2 rounded-md border border-line bg-canvas px-2.5 text-caption text-ink-faint">
            <Search className="size-3" />
            <span>“rate cuts” · semantic</span>
            <kbd className="ml-auto rounded border border-line bg-panel-raised px-1 font-mono text-micro">
              ⌘K
            </kbd>
          </div>
          <div className="flex items-center gap-1.5 font-mono text-micro text-ink-faint">
            <Radio className="size-3 text-signal" />
            live
          </div>
        </div>

        <div className="grid gap-px bg-line/70 sm:grid-cols-[1fr_240px]">
          <div className="flex flex-col gap-2.5 bg-panel p-4">
            <p className="font-mono text-micro uppercase tracking-[0.12em] text-ink-faint">
              Top matches · 3 of 1,284
            </p>
            {previewRows.map((row) => {
              const meta = sentimentMeta[row.sentiment];
              return (
                <div
                  key={row.ticker}
                  className="group flex flex-col gap-2 rounded-lg border border-line bg-canvas/60 p-3 transition-colors hover:border-signal/40 hover:bg-panel-raised"
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-body font-semibold text-ink">
                        {row.ticker}
                      </span>
                      <span className="font-mono text-micro text-ink-faint">
                        {row.theme}
                      </span>
                    </div>
                    <span
                      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 font-mono text-micro font-semibold ${meta.bg} ${meta.className}`}
                    >
                      <meta.Icon className="size-3" />
                      {row.score}% · {row.sentiment}
                    </span>
                  </div>
                  <p className="line-clamp-1 text-body italic text-ink-secondary">
                    <Quote className="mr-1 inline size-3 text-ink-faint" />
                    {row.snippet}
                  </p>
                </div>
              );
            })}
          </div>

          <div className="hidden flex-col justify-between gap-4 border-l border-line bg-panel p-4 sm:flex">
            <div>
              <p className="font-mono text-micro uppercase tracking-[0.12em] text-ink-faint">
                Market sentiment
              </p>
              <p className="mt-2 font-display text-display-xl font-bold tracking-tight text-bullish">
                71<span className="text-title text-ink-faint">%</span>
              </p>
              <p className="mt-1 text-caption text-ink-secondary">
                bullish across 4 platforms
              </p>
              <div className="mt-4 flex h-20 items-end gap-1.5">
                {[34, 52, 40, 66, 48, 74, 58, 88, 62, 96].map((h, i) => (
                  <motion.span
                    key={i}
                    initial={reducedMotion ? false : { scaleY: 0 }}
                    animate={{ scaleY: 1 }}
                    transition={{ duration: 0.6, delay: 0.9 + i * 0.05, ease: EASE }}
                    style={{ height: `${h}%` }}
                    className="w-full origin-bottom rounded-sm bg-signal/60"
                  />
                ))}
              </div>
            </div>

            <div className="rounded-lg border border-bullish/20 bg-bullish/10 p-3">
              <p className="font-mono text-micro uppercase tracking-[0.12em] text-bullish">
                Prediction · verified
              </p>
              <p className="mt-1.5 text-caption leading-snug text-ink-secondary">
                “SOXX +6% by Q3” — logged Apr 2, resolved true in 89 days.
              </p>
            </div>
          </div>
        </div>
      </motion.div>

      <motion.div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 -z-10 rounded-2xl bg-signal/10 blur-2xl"
        animate={reducedMotion ? undefined : { opacity: [0.5, 0.9, 0.5] }}
        transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
      />
    </motion.div>
  );
}

export function Hero() {
  const reducedMotion = useReducedMotion();

  return (
    <section className="relative overflow-hidden">
      <div
        aria-hidden="true"
        className="bg-grid absolute inset-0 -z-10 [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,black,transparent)]"
      />
      <div
        aria-hidden="true"
        className="animate-glow-pulse absolute -top-32 left-1/2 -z-10 h-96 w-[42rem] -translate-x-1/2 rounded-full bg-signal/15 blur-3xl"
      />
      <div
        aria-hidden="true"
        className="animate-glow-pulse absolute -left-32 top-1/3 -z-10 h-80 w-80 rounded-full bg-info/10 blur-3xl"
        style={{ animationDelay: "1.5s" }}
      />

      <div className="mx-auto max-w-7xl px-4 pb-24 pt-32 sm:px-6 sm:pt-36 lg:px-8 lg:pb-32 lg:pt-40">
        <motion.div
          variants={container}
          initial={reducedMotion ? false : "hidden"}
          animate="show"
          className="mx-auto max-w-3xl text-center"
        >
          {/* <motion.div variants={item}>
            <span className="inline-flex items-center gap-2 rounded-full border border-line bg-panel/70 px-3.5 py-1.5 font-mono text-micro font-medium uppercase tracking-[0.14em] text-ink-secondary backdrop-blur">
              <span className="relative flex size-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-signal opacity-60" />
                <span className="relative inline-flex size-2 rounded-full bg-signal" />
              </span>
              Live · 340+ channels · 4 platforms
            </span>
          </motion.div> */}

          <motion.h1
            variants={item}
            className="mt-8 font-display text-5xl font-bold leading-[1.02] tracking-tight text-ink sm:text-6xl lg:text-7xl"
          >
            Hear what the
            <br />
            <span className="text-gradient">market is saying.</span>
          </motion.h1>

          <motion.p
            variants={item}
            className="mx-auto mt-6 max-w-xl text-body leading-relaxed text-ink-secondary sm:text-title sm:leading-relaxed"
          >
            Carry ingests thousands of hours of finance commentary from YouTube,
            Reddit, X, and news — then extracts the tickers, predictions, and
            sentiment that actually matter, timestamped to the second.
          </motion.p>

          <motion.div
            variants={item}
            className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row"
          >
            <Link href="/search">
              <Button size="lg" className="cursor-pointer btn-glow h-11 gap-2 px-6 text-body">
                Try it Out
                <ArrowRight className="size-4" />
              </Button>
            </Link>
            {/* <Link href="#why-carry">
              <Button
                size="lg"
                variant="ghost"
                className="h-11 gap-2 px-6 text-body text-ink-secondary hover:text-ink"
              >
                <PlayCircle className="size-4 text-signal" />
                See how it works
              </Button>
            </Link> */}
          </motion.div>

          <motion.div
            variants={item}
            className="mt-10 flex items-center justify-center gap-4"
          >
            {/* <div className="flex -space-x-2">
              {["MC", "DR", "SL"].map((initials, i) => (
                <Avatar key={initials} size="sm" className="ring-2 ring-canvas">
                  <AvatarFallback
                    className={`text-micro font-semibold ${i === 0
                        ? "bg-signal/20 text-signal"
                        : i === 1
                          ? "bg-info/20 text-info"
                          : "bg-bullish/20 text-bullish"
                      }`}
                  >
                    {initials}
                  </AvatarFallback>
                </Avatar>
              ))}
            </div> */}
            {/* <p className="text-caption text-ink-faint">
              Trusted by research analysts, portfolio managers, and finance
              content teams
            </p> */}
          </motion.div>
        </motion.div>

        <HeroPreview />
      </div>
    </section>
  );
}
