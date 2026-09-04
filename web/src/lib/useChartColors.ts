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
        success: getVar("--success", "#2E7D5F"),
        danger: getVar("--danger", "#C24A31"),
        warning: getVar("--warning", "#AF7C2B"),
        info: getVar("--info", "#4A6FA5"),
        primary: getVar("--primary", "#2E7D46"),
        mutedForeground: getVar("--muted-foreground", "#656C77"),
        chart1: getVar("--chart-1", "#2E7D46"),
        chart2: getVar("--chart-2", "#4A6FA5"),
        canvas: getVar("--canvas", "#F7F8FA"),
        ink: getVar("--ink", "#343B47"),
        inkSecondary: getVar("--ink-secondary", "#656C77"),
        line: getVar("--line", "#E1E4E9"),
      }),
    () =>
      JSON.stringify({
        success: "#2E7D5F",
        danger: "#C24A31",
        warning: "#AF7C2B",
        info: "#4A6FA5",
        primary: "#2E7D46",
        mutedForeground: "#656C77",
        chart1: "#2E7D46",
        chart2: "#4A6FA5",
        canvas: "#F7F8FA",
        ink: "#343B47",
        inkSecondary: "#656C77",
        line: "#E1E4E9",
      })
  );

  return JSON.parse(colorsJson) as ChartColors;
}
