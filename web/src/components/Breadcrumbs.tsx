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
      className={cn("flex items-center gap-1.5 text-xs text-muted-foreground mb-3", className)}
    >
      <Link
        href="/"
        className="flex items-center gap-1 hover:text-foreground transition-colors"
      >
        <Home className="h-3.5 w-3.5" />
      </Link>

      {items.map((item, idx) => {
        const isLast = idx === items.length - 1;

        return (
          <React.Fragment key={idx}>
            <ChevronRight className="h-3 w-3 text-muted-foreground/60 shrink-0" />
            {item.href && !isLast ? (
              <Link
                href={item.href}
                className="hover:text-foreground transition-colors max-w-[150px] truncate"
              >
                {item.label}
              </Link>
            ) : (
              <span className="font-semibold text-foreground max-w-[200px] truncate">
                {item.label}
              </span>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
}
