import React from "react";
import Link from "next/link";
import { ChevronRight, Home } from "lucide-react";
import { cn } from "@/lib/utils";

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
  className?: string;
}

export function Breadcrumbs({ items, className }: BreadcrumbsProps) {
  return (
    <nav
      aria-label="Breadcrumb"
      className={cn("flex items-center gap-1.5 font-mono text-micro text-ink-faint", className)}
    >
      <Link
        href="/"
        className="flex items-center gap-1 transition-colors hover:text-ink"
      >
        <Home className="h-3.5 w-3.5" />
      </Link>

      {items.map((item, idx) => {
        const isLast = idx === items.length - 1;

        return (
          <React.Fragment key={idx}>
            <ChevronRight className="h-3 w-3 shrink-0 text-ink-faint/60" />
            {item.href && !isLast ? (
              <Link
                href={item.href}
                className="max-w-[150px] truncate transition-colors hover:text-ink"
              >
                {item.label}
              </Link>
            ) : (
              <span className="max-w-[200px] truncate font-semibold text-ink-secondary">
                {item.label}
              </span>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
}
