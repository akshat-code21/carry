"use client";

import { useSyncExternalStore } from "react";
import { useTheme } from "@/components/ThemeProvider";

import { toRgbaColor } from "@/lib/oklchToRgba";

export interface ChartColors {
  success: string;
  danger: string;
  warning: string;
  info: string;
  primary: string;
  price: string;
  signal: string;
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
  const val = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return val ? toRgbaColor(val) : fallback;
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
        info: getVar("--info", "#0284C7"),
        primary: getVar("--primary", "#2E7D46"),
        price: getVar("--signal", "#2962FF"),
        signal: getVar("--signal", "#2962FF"),
        mutedForeground: getVar("--muted-foreground", "#656C77"),
        chart1: getVar("--signal", "#2962FF"),
        chart2: getVar("--chart-2", "#F59E0B"),
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
        info: "#0284C7",
        primary: "#2E7D46",
        price: "#2962FF",
        signal: "#2962FF",
        mutedForeground: "#656C77",
        chart1: "#2962FF",
        chart2: "#F59E0B",
        canvas: "#F7F8FA",
        ink: "#343B47",
        inkSecondary: "#656C77",
        line: "#E1E4E9",
      })
  );

  return JSON.parse(colorsJson) as ChartColors;
}
