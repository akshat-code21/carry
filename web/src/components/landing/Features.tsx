"use client";

import { Search } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Reveal } from "@/components/landing/Reveal";
import { SectionLabel } from "@/components/landing/SectionLabel";

/* Small, realistic data snippets - one per feature block */
const tickerflowRows = [
  { ticker: "NVDA", mentions: 42, bullish: "78%", bearish: "14%" },
  { ticker: "TSLA", mentions: 35, bullish: "44%", bearish: "40%" },
  { ticker: "GLD", mentions: 16, bullish: "66%", bearish: "19%" },
];

const themeChips = ["Technology", "Semiconductors", "AI capex"];

const consensusRows = [
  { ticker: "NVDA", action: "+14 funds bought", value: "$2.1B" },
  { ticker: "LLY", action: "+9 funds bought", value: "$860M" },
  { ticker: "PFE", action: "−11 funds sold", value: "$1.3B" },
];

const searchRows = [
  { time: "12:41", quote: "“compute demand is still outpacing supply”" },
  { time: "31:07", quote: "“they're guiding capex higher again”" },
];

function SnippetTickerflow() {
  return (
    <div className="rounded-md border border-line bg-canvas/60 font-mono text-caption tabular-nums">
      <div className="flex items-center gap-2 border-b border-line px-3 py-1.5 text-ink-faint">
        <span>7d</span>
        <span className="text-line-strong">|</span>
        <span>mentions</span>
        <span className="ml-auto">bull / bear</span>
      </div>
      {tickerflowRows.map((row) => (
        <div
          key={row.ticker}
          className="flex items-center gap-2 border-b border-line/60 px-3 py-1.5 last:border-0"
        >
          <span className="font-semibold text-ink">{row.ticker}</span>
          <span className="ml-auto tabular-nums text-ink-secondary">{row.mentions}</span>
          <span className="w-12 text-right tabular-nums text-bullish">{row.bullish}</span>
          <span className="w-12 text-right tabular-nums text-bearish">{row.bearish}</span>
        </div>
      ))}
    </div>
  );
}

function SnippetThemes() {
  return (
    <div className="rounded-md border border-line bg-canvas/60 p-3">
      <div className="flex flex-wrap items-center gap-1.5 font-mono text-micro">
        {themeChips.map((chip, i) => (
          <span key={chip} className="flex items-center gap-1.5">
            {i > 0 && <span className="text-ink-faint">›</span>}
            <span
              className={
                i === themeChips.length - 1
                  ? "rounded-sm bg-signal/10 px-1.5 py-0.5 text-signal"
                  : "text-ink-secondary"
              }
            >
              {chip}
            </span>
          </span>
        ))}
      </div>
      <div className="mt-2.5 flex flex-wrap gap-1.5">
        {["NVDA", "AMD", "TSM", "ASML"].map((ticker) => (
          <span
            key={ticker}
            className="rounded-sm border border-line bg-panel px-1.5 py-0.5 font-mono text-micro font-semibold text-ink"
          >
            {ticker}
          </span>
        ))}
        <span className="px-0.5 font-mono text-micro text-ink-faint">+9 more</span>
      </div>
    </div>
  );
}

function SnippetConsensus() {
  return (
    <div className="rounded-md border border-line bg-canvas/60 font-mono text-caption tabular-nums">
      {consensusRows.map((row) => (
        <div
          key={row.ticker}
          className="flex items-center gap-2 border-b border-line/60 px-3 py-1.5 last:border-0"
        >
          <span className="font-semibold text-ink">{row.ticker}</span>
          <span
            className={
              row.action.startsWith("+") ? "text-bullish" : "text-bearish"
            }
          >
            {row.action}
          </span>
          <span className="ml-auto tabular-nums text-ink-secondary">{row.value}</span>
        </div>
      ))}
    </div>
  );
}

function SnippetSearch() {
  return (
    <div className="rounded-md border border-line bg-canvas/60 font-mono text-caption">
      <div className="flex items-center gap-2 border-b border-line px-3 py-1.5 text-ink-faint">
        <Search className="size-3" />
        <span>“who is bullish on semis”</span>
      </div>
      {searchRows.map((row) => (
        <div
          key={row.time}
          className="flex items-center gap-2.5 border-b border-line/60 px-3 py-1.5 last:border-0"
        >
          <span className="tabular-nums text-signal">{row.time}</span>
          <span className="truncate text-ink-secondary">{row.quote}</span>
        </div>
      ))}
    </div>
  );
}

const blocks = [
  {
    title: "Tickerflow",
    description:
      "Every ticker mention across YouTube, Reddit, X, and the news, in one dense feed. Bullish and bearish counts per ticker - a real-time read of what the market is talking about.",
    snippet: <SnippetTickerflow />,
  },
  {
    title: "Themes",
    description:
      "Watch market themes form in real time and drill from a narrative straight into the tickers driving it - with the source coverage behind each claim.",
    snippet: <SnippetThemes />,
  },
  {
    title: "Consensus",
    description:
      "Aggregated from quarterly SEC 13F filings. See which funds are buying or selling a name together - direction and dollar size at a glance.",
    snippet: <SnippetConsensus />,
  },
  {
    title: "Transcript search",
    description:
      "Search across every ingested transcript, thread, and article, and jump straight to where a claim was made. The source, timestamped - not a summary you have to take on faith.",
    snippet: <SnippetSearch />,
  },
];

export function Features() {
  return (
    <section
      id="features"
      className="relative scroll-mt-24 border-t border-line/70 py-24 lg:py-28"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <Reveal className="mx-auto max-w-2xl text-center">
          <div className="flex justify-center">
            <SectionLabel>Features</SectionLabel>
          </div>
          <h2 className="mt-5 font-display text-3xl font-bold tracking-tight text-ink sm:text-4xl">
            Four views of the same signal.
          </h2>
          <p className="mx-auto mt-4 text-body leading-relaxed text-ink-secondary">
            Everything extracted from the sources you follow, organized the way
            you actually make decisions.
          </p>
        </Reveal>

        <div className="mt-14 grid gap-5 md:grid-cols-2">
          {blocks.map((block, i) => (
            <Reveal key={block.title} delay={i * 0.08} className="h-full">
              <Card className="h-full rounded-lg bg-panel transition-colors hover:bg-panel-raised">
                <CardContent className="flex h-full flex-col gap-5 p-6">
                  <div className="flex-1">
                    <h3 className="font-display text-title font-semibold tracking-tight text-ink">
                      {block.title}
                    </h3>
                    <p className="mt-2.5 max-w-md text-body leading-relaxed text-ink-secondary">
                      {block.description}
                    </p>
                  </div>
                  {block.snippet}
                </CardContent>
              </Card>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
