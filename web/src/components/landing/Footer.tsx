import Link from "next/link";
import { Logo } from "@/components/landing/Logo";

const columns = [
  {
    title: "Platform",
    links: [
      { label: "Dashboard", href: "/dashboard" },
      { label: "Search Engine", href: "/search" },
      { label: "Themes", href: "/themes" },
      { label: "Consensus", href: "/consensus" },
      { label: "Channels", href: "/channels" },
    ],
  },
];

export function Footer() {
  return (
    <footer className="border-t border-line/70">
      {/* ── Main footer content ─────────────────────────────────────── */}
      <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
        <div className="grid gap-16 lg:grid-cols-[1.6fr_1fr]">
          {/* Left: Logo + hero tagline + subtitle */}
          <div>
            <Logo />
            <h2 className="mt-8 max-w-lg font-display text-[clamp(2.25rem,5vw,3.5rem)] font-bold leading-[1.08] tracking-tight text-ink">
              Aggregating the world&apos;s{" "}
              <span className="text-gradient">market chatter.</span>
            </h2>
            <p className="mt-5 max-w-md text-base leading-relaxed text-ink-faint">
              The intelligence layer that doesn&apos;t compromise on coverage or
              traceability.
            </p>
          </div>

          {/* Right: Nav columns */}
          <div className="flex justify-start gap-16 lg:justify-end">
            {columns.map((col) => (
              <div key={col.title}>
                <h4 className="font-mono text-xs font-semibold uppercase tracking-[0.14em] text-ink-faint">
                  {col.title}
                </h4>
                <ul className="mt-5 flex flex-col gap-3.5">
                  {col.links.map((link) => (
                    <li key={link.label}>
                      <Link
                        href={link.href}
                        className="text-sm text-ink-secondary transition-colors hover:text-ink"
                      >
                        {link.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Oversized decorative brand wordmark ─────────────────────── */}
      <div
        aria-hidden="true"
        className="pointer-events-none select-none overflow-hidden"
      >
        <div
          className="wordmark-fade whitespace-nowrap text-center font-display font-extrabold uppercase leading-[0.82]"
          style={{
            fontSize: "clamp(6rem, 22vw, 24rem)",
            letterSpacing: "-0.04em",
          }}
        >
          CARRY
        </div>
      </div>

      {/* Legal bar */}
      <div className="mx-auto max-w-7xl px-4 pb-6 sm:px-6 lg:px-8">
        <div className="flex flex-col items-start justify-between gap-3 border-t border-line/70 pt-6 sm:flex-row sm:items-center">
          <p className="font-mono text-micro text-ink-faint">
            © 2026 Carry. All rights reserved.
          </p>
          <p className="font-mono text-micro text-ink-faint">
            Carry aggregates commentary for research. It is not investment,
            legal, or tax advice.
          </p>
        </div>
      </div>
    </footer>
  );
}
