import Link from "next/link";
import { cn } from "@/lib/utils";

interface LogoProps {
  className?: string;
  href?: string;
}

export function Logo({ className, href = "/" }: LogoProps) {
  return (
    <Link href={href} className={cn("group flex items-center gap-2.5", className)}>
      <span className="relative flex h-8 w-8 items-center justify-center rounded-lg bg-signal font-display text-base font-bold tracking-tight text-signal-foreground">
        C
      </span>
      <span className="font-display text-lg font-semibold tracking-tight text-ink">
        Carry
      </span>
    </Link>
  );
}
