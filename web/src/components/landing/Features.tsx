"use client";

import { motion, useReducedMotion } from "framer-motion";
import {
  ScanSearch,
  TrendingUp,
  Activity,
  Layers,
  type LucideIcon,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Reveal } from "@/components/landing/Reveal";
import { SectionLabel } from "@/components/landing/SectionLabel";

interface Feature {
  Icon: LucideIcon;
  title: string;
  description: string;
}

const features: Feature[] = [
  {
    Icon: ScanSearch,
    title: "Transcript Search",
    description:
      "Semantic and keyword search over millions of words of commentary. Jump straight to the exact second an expert made the call.",
  },
  {
    Icon: TrendingUp,
    title: "Predictions, Verified",
    description:
      "Every call is logged the moment it's made, then scored against what actually happened. See who's consistently right — not just loud.",
  },
  {
    Icon: Activity,
    title: "Sentiment Signal",
    description:
      "Bullish and bearish scores per ticker, normalized across Reddit, X, news, and StockTwits into one clean, comparable number.",
  },
  {
    Icon: Layers,
    title: "Narrative Maps",
    description:
      "Watch themes emerge, spread across sectors, and shift in real time as the commentary that drives them evolves.",
  },
];

export function Features() {
  const reducedMotion = useReducedMotion();

  return (
    <section id="features" className="relative scroll-mt-24 py-24 lg:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <Reveal className="mx-auto max-w-2xl text-center">
          <div className="flex justify-center">
            <SectionLabel>Features</SectionLabel>
          </div>
          <h2 className="mt-5 font-display text-4xl font-bold tracking-tight text-ink sm:text-5xl">
            Everything the tape leaves out,
            <br className="hidden sm:block" /> surfaced.
          </h2>
          <p className="mx-auto mt-5 max-w-xl text-body leading-relaxed text-ink-secondary">
            Four primitives that turn raw commentary into an edge — built for
            the pace of live markets, not weekly digests.
          </p>
        </Reveal>

        <div className="mt-16 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {features.map((feature, i) => (
            <motion.div
              key={feature.title}
              initial={reducedMotion ? false : { opacity: 0, y: 28 }}
              whileInView={reducedMotion ? undefined : { opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.55, delay: i * 0.08, ease: [0.16, 1, 0.3, 1] }}
              whileHover={{ y: -6 }}
              className="h-full"
            >
              <Card className="card-glow group/card h-full bg-panel/60 backdrop-blur">
                <CardContent className="flex h-full flex-col p-6">
                  <div className="flex h-11 w-11 items-center justify-center rounded-lg border border-signal/20 bg-signal/10 transition-colors group-hover/card:border-signal/40 group-hover/card:bg-signal/15">
                    <feature.Icon className="size-5 text-signal" />
                  </div>
                  <h3 className="mt-6 font-display text-title font-semibold tracking-tight text-ink">
                    {feature.title}
                  </h3>
                  <p className="mt-2.5 text-body leading-relaxed text-ink-secondary">
                    {feature.description}
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
