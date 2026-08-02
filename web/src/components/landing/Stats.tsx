"use client";

import { AnimatedCounter } from "@/components/market-chatter/AnimatedCounter";
import { Reveal } from "@/components/landing/Reveal";

const stats = [
  { value: 12000, suffix: "+", decimals: 0, label: "Hours of commentary indexed" },
  { value: 340, suffix: "+", decimals: 0, label: "Finance channels tracked" },
  { value: 4, suffix: "", decimals: 0, label: "Platforms ingested" },
  { value: 96, suffix: "%", decimals: 0, label: "Signals sourced to the second" },
];

export function Stats() {
  return (
    <section className="border-y border-line/70 bg-panel/30 py-14 lg:py-16">
      <div className="mx-auto grid max-w-7xl grid-cols-2 gap-x-6 gap-y-10 px-4 sm:px-6 lg:grid-cols-4 lg:px-8">
        {stats.map((stat, i) => (
          <Reveal key={stat.label} delay={i * 0.08} className="text-center">
            <p className="font-display text-4xl font-bold tracking-tight text-ink sm:text-5xl">
              <AnimatedCounter
                value={stat.value}
                suffix={stat.suffix}
                decimals={stat.decimals}
                className="text-gradient font-display font-bold tracking-tight"
              />
            </p>
            <p className="mt-2 text-caption font-medium uppercase tracking-[0.1em] text-ink-faint">
              {stat.label}
            </p>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
