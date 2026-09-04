"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Reveal } from "@/components/landing/Reveal";

export function CTA() {
  const reducedMotion = useReducedMotion();

  return (
    <section className="relative border-t border-line/70 py-24 lg:py-32">
      <div className="mx-auto max-w-3xl px-4 text-center sm:px-6 lg:px-8">
        <Reveal>
          <h2 className="font-display text-3xl font-bold tracking-tight text-ink sm:text-5xl">
            Stop watching everything.
            <br />
            Start reading what matters.
          </h2>
          <p className="mx-auto mt-5 max-w-xl text-body leading-relaxed text-ink-secondary sm:text-title">
            Point Carry at the sources you already trust. Every ticker, theme,
            and call - extracted, searchable, and timestamped.
          </p>
        </Reveal>

        <motion.div
          initial={reducedMotion ? false : { opacity: 0, y: 16 }}
          whileInView={reducedMotion ? undefined : { opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-60px" }}
          transition={{ duration: 0.6, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
          className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row"
        >
          <Link href="/sign-up">
            <Button size="lg" className="h-11 gap-2 px-7 text-body">
              Get started
              <ArrowRight className="size-4" />
            </Button>
          </Link>
          <Link
            href="/sign-in"
            className="text-body font-medium text-ink-secondary transition-colors hover:text-ink"
          >
            Sign in
          </Link>
        </motion.div>

        <Reveal delay={0.25}>
          <p className="mt-8 font-mono text-micro uppercase tracking-[0.14em] text-ink-faint">
            Research intelligence · Not investment advice
          </p>
        </Reveal>
      </div>
    </section>
  );
}
