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
  canvas: string;
  ink: string;
  inkSecondary: string;
  line: string;
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
        success: getVar("--success", "#3CB173"),
        danger: getVar("--danger", "#E3645E"),
        warning: getVar("--warning", "#E6AC3D"),
        info: getVar("--info", "#7EA9D5"),
        primary: getVar("--primary", "#BED540"),
        mutedForeground: getVar("--muted-foreground", "#9A9FA6"),
        chart1: getVar("--chart-1", "#BED540"),
        chart2: getVar("--chart-2", "#7EA9D5"),
        canvas: getVar("--canvas", "#10141C"),
        ink: getVar("--ink", "#E8EBF0"),
        inkSecondary: getVar("--ink-secondary", "#9A9FA6"),
        line: getVar("--line", "#3A4250"),
      }),
    () =>
      JSON.stringify({
        success: "#3CB173",
        danger: "#E3645E",
        warning: "#E6AC3D",
        info: "#7EA9D5",
        primary: "#BED540",
        mutedForeground: "#9A9FA6",
        chart1: "#BED540",
        chart2: "#7EA9D5",
        canvas: "#10141C",
        ink: "#E8EBF0",
        inkSecondary: "#9A9FA6",
        line: "#3A4250",
      })
  );

  return JSON.parse(colorsJson) as ChartColors;
}
