import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

interface GradientTextProps {
  children: ReactNode;
  className?: string;
}

export function GradientText({ children, className }: GradientTextProps) {
  return (
    <span className={cn("relative inline-block text-tf-signal", className)}>
      {children}
    </span>
  );
}
