import Link from "next/link";
import { AtSign, Code2, Play, Rss } from "lucide-react";
import { Logo } from "@/components/landing/Logo";

const columns = [
  {
    title: "Product",
    links: [
      { label: "Search", href: "/search" },
      { label: "Overview", href: "/dashboard" },
      { label: "Tickerflow", href: "/tickerflow" },
    ],
  },
  {
    title: "Company",
    links: [
      { label: "About", href: "#" },
      { label: "Blog", href: "#" },
      { label: "Contact", href: "#" },
    ],
  },
  {
    title: "Legal",
    links: [
      { label: "Privacy", href: "#" },
      { label: "Terms", href: "#" },
      { label: "Disclaimer", href: "#" },
    ],
  },
];

const socials = [
  { Icon: AtSign, label: "X / Twitter", href: "#" },
  { Icon: Code2, label: "GitHub", href: "#" },
  { Icon: Play, label: "YouTube", href: "#" },
  { Icon: Rss, label: "RSS", href: "#" },
];

export function Footer() {
  return (
    <footer className="border-t border-line/70">
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="grid gap-12 lg:grid-cols-[1.4fr_2fr]">
          <div className="max-w-sm">
            <Logo />
            <p className="mt-4 text-body leading-relaxed text-ink-faint">
              Market commentary intelligence. Search the tape, verify the calls,
              and read the mood — sourced to the second.
            </p>
            <div className="mt-6 flex items-center gap-1.5">
              {socials.map(({ Icon, label, href }) => (
                <Link
                  key={label}
                  href={href}
                  aria-label={label}
                  className="flex size-9 items-center justify-center rounded-md text-ink-faint transition-colors hover:bg-panel hover:text-ink"
                >
                  <Icon className="size-4" />
                </Link>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-8 sm:grid-cols-3">
            {columns.map((col) => (
              <div key={col.title}>
                <h4 className="font-mono text-micro font-semibold uppercase tracking-[0.14em] text-ink-faint">
                  {col.title}
                </h4>
                <ul className="mt-4 flex flex-col gap-2.5">
                  {col.links.map((link) => (
                    <li key={link.label}>
                      <Link
                        href={link.href}
                        className="text-body text-ink-secondary transition-colors hover:text-ink"
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

        <div className="mt-14 flex flex-col items-start justify-between gap-3 border-t border-line/70 pt-6 sm:flex-row sm:items-center">
          <p className="font-mono text-micro text-ink-faint">
            © 2026 Carry Intelligence. All rights reserved.
          </p>
          <p className="font-mono text-micro text-ink-faint">
            Carry aggregates commentary for research. It is not investment, legal, or tax advice.
          </p>
        </div>
      </div>
    </footer>
  );
}
