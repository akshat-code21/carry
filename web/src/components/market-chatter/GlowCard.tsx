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
        "relative rounded-md border border-tf-stroke bg-tf-panel",
        // Flat accent hairline retained as the only source-color cue (no glow/translate)
        "before:absolute before:inset-x-0 before:top-0 before:h-px before:rounded-t-md",
        "transition-colors duration-150",
        accentClasses[glowColor],
        hover && "hover:border-tf-stroke-strong hover:bg-tf-panel-raised",
        className,
      )}
    >
      {children}
    </div>
  );
}
