"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Reveal } from "@/components/landing/Reveal";

export function CTA() {
  const reducedMotion = useReducedMotion();

  return (
    <section className="relative overflow-hidden py-24 lg:py-32">
      <div
        aria-hidden="true"
        className="bg-grid absolute inset-0 -z-10 [mask-image:radial-gradient(ellipse_55%_60%_at_50%_50%,black,transparent)]"
      />
      <motion.div
        aria-hidden="true"
        className="animate-glow-pulse absolute left-1/2 top-1/2 -z-10 h-72 w-[36rem] -translate-x-1/2 -translate-y-1/2 rounded-full bg-signal/15 blur-3xl"
      />

      <div className="mx-auto max-w-3xl px-4 text-center sm:px-6 lg:px-8">
        <Reveal>
          <h2 className="font-display text-4xl font-bold tracking-tight text-ink sm:text-6xl">
            Start reading the
            <br />
            <span className="text-gradient">market&apos;s mood.</span>
          </h2>
          <p className="mx-auto mt-6 max-w-xl text-body leading-relaxed text-ink-secondary sm:text-title">
            Search millions of words of finance commentary in seconds. Free to
            explore the tape — no credit card, no noise.
          </p>
        </Reveal>

        <motion.div
          initial={reducedMotion ? false : { opacity: 0, y: 16, scale: 0.98 }}
          whileInView={{ opacity: 1, y: 0, scale: 1 }}
          viewport={{ once: true, margin: "-60px" }}
          transition={{ duration: 0.6, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
          className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row"
        >
          <Link href="/search">
            <Button
              size="lg"
              className="btn-glow h-12 gap-2 px-7 text-body"
            >
              Open Carry
              <ArrowRight className="size-4" />
            </Button>
          </Link>
          <Link href="/dashboard">
            <Button
              size="lg"
              variant="outline"
              className="h-12 gap-2 px-7 text-body bg-panel/50"
            >
              View the live overview
            </Button>
          </Link>
        </motion.div>

        <Reveal delay={0.25}>
          <p className="mt-6 font-mono text-micro uppercase tracking-[0.14em] text-ink-faint">
            Research intelligence · Not investment advice
          </p>
        </Reveal>
      </div>
    </section>
  );
}
