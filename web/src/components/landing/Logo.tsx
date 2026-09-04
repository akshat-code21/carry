import Link from "next/link";
import { cn } from "@/lib/utils";

interface LogoProps {
  className?: string;
  href?: string;
}

export function Logo({ className, href = "/" }: LogoProps) {
  return (
    <Link href={href} className={cn("group flex items-center gap-2.5", className)}>
      <span className="relative flex h-8 w-8 items-center justify-center rounded-lg bg-signal font-display text-base font-bold tracking-tight text-signal-foreground transition-shadow group-hover:shadow-[0_0_24px_-4px_color-mix(in_oklch,var(--signal)_70%,transparent)]">
        C
      </span>
      <span className="font-display text-lg font-semibold tracking-tight text-ink">
        Carry
      </span>
    </Link>
  );
}
