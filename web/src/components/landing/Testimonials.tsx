"use client";

import { motion, useReducedMotion } from "framer-motion";
import { Quote } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Reveal } from "@/components/landing/Reveal";
import { SectionLabel } from "@/components/landing/SectionLabel";

interface Testimonial {
  quote: string;
  name: string;
  role: string;
  initials: string;
  accent: string;
}

const testimonials: Testimonial[] = [
  {
    quote:
      "I replaced an entire morning of channel-scraping with a single search. Carry surfaces the same calls I was tracking manually — with the receipts and timestamps.",
    name: "Maya Chen",
    role: "Equity Research Analyst",
    initials: "MC",
    accent: "bg-signal/20 text-signal",
  },
  {
    quote:
      "The prediction ledger is the killer feature. We finally have a defensible track record of who talks a good game and who is actually right.",
    name: "Diego Ramírez",
    role: "Portfolio Manager",
    initials: "DR",
    accent: "bg-info/20 text-info",
  },
  {
    quote:
      "It feels like a newsroom analyst who never sleeps, has read every transcript, and never editorializes. Just signal, ranked and sourced.",
    name: "Sofia Lindqvist",
    role: "Finance Content Lead",
    initials: "SL",
    accent: "bg-bullish/20 text-bullish",
  },
];

export function Testimonials() {
  const reducedMotion = useReducedMotion();

  return (
    <section id="testimonials" className="relative scroll-mt-24 py-24 lg:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <Reveal className="mx-auto max-w-2xl text-center">
          <div className="flex justify-center">
            <SectionLabel>Customers</SectionLabel>
          </div>
          <h2 className="mt-5 font-display text-4xl font-bold tracking-tight text-ink sm:text-5xl">
            Used where the tape moves.
          </h2>
          <p className="mx-auto mt-5 max-w-xl text-body leading-relaxed text-ink-secondary">
            From research desks to content teams — people who live on market
            commentary now let Carry do the reading.
          </p>
        </Reveal>

        <div className="mt-16 grid gap-5 md:grid-cols-3">
          {testimonials.map((t, i) => (
            <motion.div
              key={t.name}
              initial={reducedMotion ? false : { opacity: 0, y: 28 }}
              whileInView={reducedMotion ? undefined : { opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.55, delay: i * 0.1, ease: [0.16, 1, 0.3, 1] }}
              className="h-full"
            >
              <Card className="card-glow flex h-full flex-col bg-panel/60 backdrop-blur">
                <CardContent className="flex h-full flex-col p-6">
                  <Quote className="size-5 text-signal/70" />
                  <p className="mt-4 flex-1 text-body leading-relaxed text-ink">
                    {t.quote}
                  </p>
                  <div className="mt-6 flex items-center gap-3 border-t border-line/70 pt-5">
                    <Avatar>
                      <AvatarFallback
                        className={`text-small font-semibold ${t.accent}`}
                      >
                        {t.initials}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <p className="text-small font-semibold text-ink">
                        {t.name}
                      </p>
                      <p className="text-micro text-ink-faint">{t.role}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
