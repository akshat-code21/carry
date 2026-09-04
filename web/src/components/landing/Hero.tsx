"use client";

import Link from "next/link";
import { motion, useReducedMotion, type Variants } from "framer-motion";
import { ArrowRight, Search, Sparkles, Tv, ChevronDown } from "lucide-react";
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

/* ── Sample data mirroring the real Search Engine page ───────────────── */

const sampleSummary = {
  text: "NVIDIA remains the dominant AI infrastructure play. Analysts and YouTube creators highlight strong data-center revenue driven by H100/H200 demand, with consensus pointing to continued growth through 2026. Key concerns include valuation multiples and potential competition from custom ASICs.",
  keyPoints: [
    "Data-center revenue up 154% YoY, driven by hyperscaler AI capex",
    "H200 and Blackwell ramp expected to sustain growth through mid-2026",
    "Valuation concern: trading at ~35x forward earnings, above 5-year average",
    "Custom ASIC competition from Google TPU and Amazon Trainium noted as risk",
  ],
  social: { symbol: "NVDA", mentions: 1284, sentiment: 0.42, bullishPct: 72 },
};

interface SampleResult {
  channel: string;
  title: string;
  date: string;
  hits: number;
  snippet: string;
  timestamp: string;
  sentiment: "bullish" | "bearish" | "neutral";
}

const sampleResults: SampleResult[] = [
  {
    channel: "Meet Kevin",
    title: "NVIDIA Just Changed Everything — Here's What Nobody Sees Coming",
    date: "Aug 28, 2026",
    hits: 6,
    snippet: "The Blackwell architecture is going to be a massive upgrade cycle. Every single hyperscaler is lining up for these chips...",
    timestamp: "12:34",
    sentiment: "bullish",
  },
  {
    channel: "Joseph Carlson",
    title: "Is NVIDIA Still a Buy After the Earnings Beat?",
    date: "Aug 26, 2026",
    hits: 4,
    snippet: "Data center revenue came in at $26.3 billion, which is just staggering. But at 35x forward, you have to ask yourself...",
    timestamp: "8:15",
    sentiment: "neutral",
  },
  {
    channel: "Tom Nash",
    title: "The AI Trade Is NOT Over — NVDA, MSFT, GOOGL Deep Dive",
    date: "Aug 22, 2026",
    hits: 3,
    snippet: "Custom ASICs are not replacing NVIDIA. They're complementary. Google's TPU handles specific workloads but CUDA's ecosystem moat is enormous...",
    timestamp: "22:07",
    sentiment: "bullish",
  },
];

const sentimentColors = {
  bullish: "text-bullish",
  bearish: "text-bearish",
  neutral: "text-ink-secondary",
} as const;

function DataPreview() {
  const reducedMotion = useReducedMotion();

  return (
    <motion.div
      initial={reducedMotion ? false : { opacity: 0, y: 40 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.75, delay: 0.5, ease: EASE }}
      className="relative mx-auto mt-14 w-full max-w-4xl lg:mt-16"
    >
      {/* Single focal shimmer */}
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

      <div className="relative overflow-hidden rounded-lg border border-line-strong bg-panel shadow-lg">
        {/* ── Window chrome ──────────────────────────────────────────── */}
        <div className="flex h-10 items-center justify-between border-b border-line px-4">
          <div className="flex items-center gap-2">
            <div className="flex gap-1.5" aria-hidden="true">
              <span className="size-2.5 rounded-full bg-bearish/60" />
              <span className="size-2.5 rounded-full bg-warning/60" />
              <span className="size-2.5 rounded-full bg-bullish/60" />
            </div>
            <p className="ml-2 font-mono text-micro font-semibold uppercase tracking-[0.12em] text-ink-faint">
              Search Engine
            </p>
          </div>
          <div className="flex items-center gap-1.5 font-mono text-micro text-ink-faint">
            <span className="size-1.5 rounded-full bg-signal" aria-hidden="true" />
            sample data
          </div>
        </div>

        {/* ── Search bar + type toggles ──────────────────────────────── */}
        <div className="border-b border-line bg-canvas/40 px-4 py-3">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-ink-faint" />
              <div className="flex h-9 items-center rounded-md border border-line bg-panel pl-9 pr-3 text-small text-ink">
                NVIDIA AI outlook 2026
              </div>
            </div>
            <div className="flex h-9 items-center rounded-md bg-signal px-4 font-mono text-small font-semibold text-canvas">
              Search
            </div>
          </div>
          <div className="mt-2.5 flex items-center gap-2">
            <span className="font-mono text-micro font-semibold uppercase tracking-[0.14em] text-ink-faint">
              Search type
            </span>
            <div className="flex gap-0.5 rounded-md border border-line bg-panel p-0.5">
              {(["keyword", "semantic", "hybrid"] as const).map((t) => (
                <span
                  key={t}
                  className={`rounded-md px-2.5 py-1 font-mono text-micro font-medium capitalize ${t === "hybrid"
                    ? "bg-signal text-canvas"
                    : "text-ink-faint"
                    }`}
                >
                  {t}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* ── AI Summary card ────────────────────────────────────────── */}
        <div className="border-b border-line px-4 py-4">
          <div className="rounded-lg border border-signal/30 bg-panel p-4">
            <div className="mb-2.5 flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-signal" />
              <span className="font-mono text-micro font-semibold uppercase tracking-[0.14em] text-signal">
                Summary
              </span>
            </div>
            <p className="text-small leading-relaxed text-ink">
              {sampleSummary.text}
            </p>
            <ul className="mt-3 flex flex-col gap-1.5">
              {sampleSummary.keyPoints.map((point, i) => (
                <li
                  key={i}
                  className="flex items-start gap-2 text-small text-ink-secondary"
                >
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-signal" />
                  {point}
                </li>
              ))}
            </ul>
            {/* Social strip */}
            <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5 border-t border-line/60 pt-2.5">
              <span className="font-mono text-micro font-semibold uppercase tracking-[0.14em] text-ink-faint">
                Social
              </span>
              <span className="font-mono text-micro font-semibold text-ink">
                {sampleSummary.social.symbol}
              </span>
              <span className="font-mono text-micro text-ink-secondary">
                {sampleSummary.social.mentions.toLocaleString()} mentions
              </span>
              <span className="font-mono text-micro font-semibold text-bullish">
                +{sampleSummary.social.sentiment.toFixed(2)}
              </span>
              <span className="font-mono text-micro text-bullish/70">
                {sampleSummary.social.bullishPct}% bull
              </span>
            </div>
          </div>
        </div>

        {/* ── Grouped video results ──────────────────────────────────── */}
        <div className="divide-y divide-line/70">
          {sampleResults.map((result) => (
            <div key={result.title} className="px-4 py-3 transition-colors hover:bg-panel-raised">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <Tv className="h-3.5 w-3.5 shrink-0 text-ink-faint" />
                    <span className="font-mono text-micro font-semibold text-ink-faint">
                      {result.channel}
                    </span>
                    <span className="font-mono text-micro text-ink-faint">
                      · {result.date}
                    </span>
                    <span className={`ml-auto font-mono text-micro font-semibold ${sentimentColors[result.sentiment]}`}>
                      {result.sentiment === "bullish" ? "▲ Bullish" : result.sentiment === "bearish" ? "▼ Bearish" : "— Neutral"}
                    </span>
                  </div>
                  <p className="mt-1 text-small font-medium leading-snug text-ink line-clamp-1">
                    {result.title}
                  </p>
                  <div className="mt-1.5 border-l-2 border-line-strong py-0.5 pl-3">
                    <p className="text-small italic text-ink-secondary line-clamp-2">
                      &quot;{result.snippet}&quot;
                    </p>
                  </div>
                </div>
              </div>
              <div className="mt-2 flex items-center gap-3">
                <span className="inline-flex items-center gap-1 rounded border border-line bg-panel-raised px-1.5 py-0.5 font-mono text-micro text-ink-faint">
                  {result.hits} clips matched
                </span>
                <span className="font-mono text-micro text-ink-faint">
                  @ {result.timestamp}
                </span>
                <ChevronDown className="ml-auto h-3.5 w-3.5 text-ink-faint" />
              </div>
            </div>
          ))}
        </div>

        {/* ── Footer bar ─────────────────────────────────────────────── */}
        <div className="flex items-center justify-between border-t border-line px-4 py-2.5">
          <p className="font-mono text-micro text-ink-faint">
            3 of 47 videos · 13 clips
          </p>
          {/* <p className="font-mono text-micro text-ink-faint">
            not investment advice
          </p> */}
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
