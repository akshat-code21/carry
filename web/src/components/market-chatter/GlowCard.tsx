import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

interface GlowCardProps {
  children: ReactNode;
  className?: string;
  glowColor?: "signal" | "price" | "negative" | "neutral";
  hover?: boolean;
  delay?: number;
}

const accentClasses = {
  signal: "before:bg-tf-signal",
  price: "before:bg-tf-price",
  negative: "before:bg-tf-negative",
  neutral: "before:bg-transparent",
};

export function GlowCard({
  children,
  className,
  glowColor = "neutral",
  hover = true,
  delay: _delay = 0,
}: GlowCardProps) {
  return (
    <div
      className={cn(
        "relative rounded-lg border border-tf-stroke bg-tf-panel",
        "before:absolute before:inset-x-0 before:top-0 before:h-px before:rounded-t-lg",
        "transition-[background-color,border-color,transform] duration-200",
        accentClasses[glowColor],
        hover &&
          "hover:-translate-y-px hover:border-tf-stroke-strong hover:bg-tf-panel-raised",
        className,
      )}
    >
      {children}
    </div>
  );
}
