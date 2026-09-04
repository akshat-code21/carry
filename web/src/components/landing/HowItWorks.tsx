import { Reveal } from "@/components/landing/Reveal";
import { SectionLabel } from "@/components/landing/SectionLabel";

const steps = [
  {
    title: "We ingest the sources.",
    description:
      "Finance YouTube channels, subreddits, X accounts, and news feeds are monitored continuously. New videos, posts, and articles are picked up automatically - no manual uploads.",
  },
  {
    title: "We extract what was said.",
    description:
      "Every transcript and post is analyzed for tickers, market themes, sentiment, and explicit calls - each one linked back to its source, down to the second for video.",
  },
  {
    title: "You see it on one dashboard.",
    description:
      "Mentions, themes, sentiment, and 13F positioning are aggregated across every source - searchable, comparable, and always traceable to where each claim was made.",
  },
];

export function HowItWorks() {
  return (
    <section
      id="how-it-works"
      className="relative scroll-mt-24 border-t border-line/70 py-24 lg:py-28"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <Reveal className="mx-auto max-w-2xl text-center">
          <div className="flex justify-center">
            <SectionLabel>How it works</SectionLabel>
          </div>
          <h2 className="mt-5 font-display text-3xl font-bold tracking-tight text-ink sm:text-4xl">
            From scattered commentary to one clear picture.
          </h2>
        </Reveal>

        <ol className="mt-14 grid gap-px overflow-hidden rounded-lg border border-line-strong bg-line md:grid-cols-3">
          {steps.map((step, i) => (
            <li key={step.title} className="bg-panel">
              <Reveal delay={i * 0.08} className="h-full">
                <div className="flex h-full flex-col p-6">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-micro font-semibold tabular-nums text-signal">
                      0{i + 1}
                    </span>
                    {/* Connector - hidden on the last column and on mobile */}
                    {i < steps.length - 1 && (
                      <span
                        aria-hidden="true"
                        className="hidden h-px w-10 bg-line-strong md:block"
                      />
                    )}
                  </div>
                  <h3 className="mt-5 font-display text-title font-semibold tracking-tight text-ink">
                    {step.title}
                  </h3>
                  <p className="mt-2.5 text-body leading-relaxed text-ink-secondary">
                    {step.description}
                  </p>
                </div>
              </Reveal>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}