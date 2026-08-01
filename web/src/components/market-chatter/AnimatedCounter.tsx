"use client";

import { useEffect, useRef } from "react";
import {
  useMotionValue,
  useSpring,
  useInView,
  motion,
  useTransform,
} from "framer-motion";

import { cn } from "@/lib/utils";

interface AnimatedCounterProps {
  value: number | null | undefined;
  decimals?: number;
  prefix?: string;
  suffix?: string;
  className?: string;
  duration?: number;
}

export function AnimatedCounter({
  value,
  decimals = 0,
  prefix = "",
  suffix = "",
  className,
  duration = 1.2,
}: AnimatedCounterProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-50px" });
  const motionVal = useMotionValue(0);
  const spring = useSpring(motionVal, {
    stiffness: 60,
    damping: 20,
    duration: duration * 1000,
  });
  const display = useTransform(spring, (latest: number) =>
    new Intl.NumberFormat("en-US", {
      maximumFractionDigits: decimals,
      minimumFractionDigits: decimals,
    }).format(latest)
  );

  useEffect(() => {
    if (isInView && value !== null && value !== undefined) {
      motionVal.set(value);
    }
  }, [isInView, value, motionVal]);

  if (value === null || value === undefined) {
    return <span className={className}>—</span>;
  }

  return (
    <span ref={ref} className={cn("font-mono tabular-nums", className)}>
      {prefix}
      <motion.span>{display}</motion.span>
      {suffix}
    </span>
  );
}
