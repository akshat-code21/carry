"use client";

import { useSyncExternalStore } from "react";
import { useTheme } from "@/components/ThemeProvider";

export interface ChartColors {
  success: string;
  danger: string;
  warning: string;
  info: string;
  primary: string;
  mutedForeground: string;
  chart1: string;
  chart2: string;
}

function getVar(name: string, fallback: string): string {
  if (typeof window === "undefined") return fallback;
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback;
}

function subscribe(callback: () => void) {
  const observer = new MutationObserver(callback);
  if (typeof document !== "undefined") {
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
  }
  return () => observer.disconnect();
}

export function useChartColors(): ChartColors {
  useTheme(); // trigger subscription on theme change

  const colorsJson = useSyncExternalStore(
    subscribe,
    () =>
      JSON.stringify({
        success: getVar("--success", "#22c55e"),
        danger: getVar("--danger", "#ef4444"),
        warning: getVar("--warning", "#eab308"),
        info: getVar("--info", "#3b82f6"),
        primary: getVar("--primary", "#6366f1"),
        mutedForeground: getVar("--muted-foreground", "#64748b"),
        chart1: getVar("--chart-1", "#8884d8"),
        chart2: getVar("--chart-2", "#82ca9d"),
      }),
    () =>
      JSON.stringify({
        success: "#22c55e",
        danger: "#ef4444",
        warning: "#eab308",
        info: "#3b82f6",
        primary: "#6366f1",
        mutedForeground: "#64748b",
        chart1: "#8884d8",
        chart2: "#82ca9d",
      })
  );

  return JSON.parse(colorsJson) as ChartColors;
}
