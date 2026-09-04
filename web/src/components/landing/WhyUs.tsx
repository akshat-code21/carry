"use client";

import { motion, useReducedMotion } from "framer-motion";
import { CheckCircle2, TrendingUp, ShieldCheck, Zap } from "lucide-react";
import { Reveal } from "@/components/landing/Reveal";
import { SectionLabel } from "@/components/landing/SectionLabel";

const reasons = [
  {
    Icon: ShieldCheck,
    title: "No summaries. Evidence.",
    description:
      "Every signal links back to the original quote, the channel, and the exact timestamp. Verify anything in one click.",
  },
  {
    Icon: TrendingUp,
    title: "Quantified conviction.",
    description:
      "Every prediction carries a confidence score, so you can weight sources by accuracy instead of charisma.",
  },
  {
    Icon: Zap,
    title: "Signal over volume.",
    description:
      "Rank by momentum, sentiment, and verified outcomes — not by subscriber count or follower size.",
  },
];

const leaderboard = [
  { ticker: "NVDA", theme: "Semiconductors", score: 92 },
  { ticker: "TLT", theme: "Rates / Bonds", score: 78 },
  { ticker: "QQQ", theme: "Broad Tech", score: 71 },
  { ticker: "GLD", theme: "Precious Metals", score: 63 },
  { ticker: "XBI", theme: "Biotech", score: 54 },
];

function WhyVisual() {
  const reducedMotion = useReducedMotion();

  return (
    <div className="relative">
      <div
        aria-hidden="true"
        className="animate-glow-pulse absolute inset-0 -z-10 rounded-3xl bg-signal/10 blur-3xl"
      />
      <motion.div
        initial={reducedMotion ? false : { opacity: 0, scale: 0.96, y: 20 }}
        whileInView={{ opacity: 1, scale: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
        className="relative overflow-hidden rounded-2xl border border-line-strong bg-panel/80 p-6 backdrop-blur-xl"
      >
        <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-signal/70 to-transparent" />
        <div
          aria-hidden="true"
          className="animate-scan pointer-events-none absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-transparent via-signal/[0.06] to-transparent"
        />

        <div className="flex items-center justify-between">
          <p className="font-mono text-micro uppercase tracking-[0.14em] text-ink-faint">
            Sentiment leaderboard
          </p>
          <span className="inline-flex items-center gap-1.5 font-mono text-micro text-bullish">
            <span className="size-1.5 rounded-full bg-bullish" />
            live
          </span>
        </div>

        <div className="mt-5 flex flex-col gap-2.5">
          {leaderboard.map((row, i) => (
            <motion.div
              key={row.ticker}
              initial={reducedMotion ? false : { opacity: 0, x: 24 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.15 + i * 0.08, ease: [0.16, 1, 0.3, 1] }}
              className="rounded-lg border border-line bg-canvas/60 p-3.5"
            >
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <span className="font-mono text-body font-semibold text-ink">
                    {row.ticker}
                  </span>
                  <span className="font-mono text-micro text-ink-faint">
                    {row.theme}
                  </span>
                </div>
                <span className="font-mono text-body font-semibold text-bullish">
                  {row.score}
                  <span className="text-micro text-ink-faint">%</span>
                </span>
              </div>
              <div className="mt-2.5 h-1 w-full overflow-hidden rounded-full bg-panel-raised">
                <motion.div
                  initial={reducedMotion ? false : { width: 0 }}
                  whileInView={{ width: `${row.score}%` }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.9, delay: 0.3 + i * 0.08, ease: [0.16, 1, 0.3, 1] }}
                  className="h-full rounded-full bg-gradient-to-r from-signal/50 to-signal"
                />
              </div>
            </motion.div>
          ))}
        </div>

        <div className="mt-5 flex items-center justify-between rounded-lg border border-bullish/20 bg-bullish/10 px-3.5 py-3">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="size-4 text-bullish" />
            <p className="text-caption text-ink-secondary">
              4 of 5 top calls from the last quarter resolved as logged.
            </p>
          </div>
          <span className="font-mono text-micro font-semibold text-bullish">
            +6.2% avg
          </span>
        </div>
      </motion.div>
    </div>
  );
}

export function WhyUs() {
  return (
    <section id="why-carry" className="relative scroll-mt-24 py-24 lg:py-32">
      <div
        aria-hidden="true"
        className="absolute right-0 top-1/2 -z-10 h-96 w-96 -translate-y-1/2 rounded-full bg-info/10 blur-3xl"
      />
      <div className="mx-auto grid max-w-7xl items-center gap-16 px-4 sm:px-6 lg:grid-cols-2 lg:gap-20 lg:px-8">
        <div>
          <Reveal>
            <SectionLabel>Why Carry</SectionLabel>
            <h2 className="mt-5 font-display text-4xl font-bold tracking-tight text-ink sm:text-5xl">
              Built for the pace
              <br className="hidden sm:block" /> of markets.
            </h2>
            <p className="mt-5 max-w-lg text-body leading-relaxed text-ink-secondary">
              Commentary moves markets before headlines do. Carry turns the
              constant noise of financial media into a small set of signals you
              can actually act on — with the evidence to back every one.
            </p>
          </Reveal>

          <div className="mt-10 flex flex-col gap-6">
            {reasons.map((reason, i) => (
              <Reveal key={reason.title} delay={i * 0.08}>
                <div className="flex gap-4">
                  <div className="flex size-9 shrink-0 items-center justify-center rounded-md border border-signal/20 bg-signal/10">
                    <reason.Icon className="size-4 text-signal" />
                  </div>
                  <div>
                    <h3 className="font-display text-title font-semibold tracking-tight text-ink">
                      {reason.title}
                    </h3>
                    <p className="mt-1.5 text-body leading-relaxed text-ink-secondary">
                      {reason.description}
                    </p>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>

        <WhyVisual />
      </div>
    </section>
  );
}
