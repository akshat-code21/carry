/**
 * Sector color palettes and helper utilities for Theme visualizers.
 * Harmonized with yt-chatter's dark/light instrument token layer.
 */

export interface SectorPalette {
  name: string;
  stroke: string;
  fill: string;
  glow: string;
  text: string;
  badgeBg: string;
  badgeBorder: string;
  innerFill: string;
  leafFill: string;
  leafStroke: string;
}

export const SECTOR_PALETTES: Record<string, SectorPalette> = {
  technology: {
    name: "Technology",
    stroke: "#0284c7", // Sky Blue
    fill: "rgba(2, 132, 199, 0.08)",
    glow: "rgba(2, 132, 199, 0.35)",
    text: "var(--signal)",
    badgeBg: "rgba(2, 132, 199, 0.12)",
    badgeBorder: "rgba(2, 132, 199, 0.35)",
    innerFill: "rgba(2, 132, 199, 0.06)",
    leafFill: "rgba(2, 132, 199, 0.14)",
    leafStroke: "rgba(2, 132, 199, 0.5)",
  },
  healthcare: {
    name: "Healthcare",
    stroke: "#059669", // Emerald Green
    fill: "rgba(5, 150, 105, 0.08)",
    glow: "rgba(5, 150, 105, 0.35)",
    text: "var(--bullish)",
    badgeBg: "rgba(5, 150, 105, 0.12)",
    badgeBorder: "rgba(5, 150, 105, 0.35)",
    innerFill: "rgba(5, 150, 105, 0.06)",
    leafFill: "rgba(5, 150, 105, 0.14)",
    leafStroke: "rgba(5, 150, 105, 0.5)",
  },
  financials: {
    name: "Financials",
    stroke: "#d97706", // Amber / Gold
    fill: "rgba(217, 119, 6, 0.08)",
    glow: "rgba(217, 119, 6, 0.35)",
    text: "var(--warning)",
    badgeBg: "rgba(217, 119, 6, 0.12)",
    badgeBorder: "rgba(217, 119, 6, 0.35)",
    innerFill: "rgba(217, 119, 6, 0.06)",
    leafFill: "rgba(217, 119, 6, 0.14)",
    leafStroke: "rgba(217, 119, 6, 0.5)",
  },
  industrials: {
    name: "Industrials",
    stroke: "#2563eb", // Blue
    fill: "rgba(37, 99, 235, 0.08)",
    glow: "rgba(37, 99, 235, 0.35)",
    text: "var(--info)",
    badgeBg: "rgba(37, 99, 235, 0.12)",
    badgeBorder: "rgba(37, 99, 235, 0.35)",
    innerFill: "rgba(37, 99, 235, 0.06)",
    leafFill: "rgba(37, 99, 235, 0.14)",
    leafStroke: "rgba(37, 99, 235, 0.5)",
  },
  consumer: {
    name: "Consumer",
    stroke: "#e11d48", // Rose / Coral
    fill: "rgba(225, 29, 72, 0.08)",
    glow: "rgba(225, 29, 72, 0.35)",
    text: "var(--price)",
    badgeBg: "rgba(225, 29, 72, 0.12)",
    badgeBorder: "rgba(225, 29, 72, 0.35)",
    innerFill: "rgba(225, 29, 72, 0.06)",
    leafFill: "rgba(225, 29, 72, 0.14)",
    leafStroke: "rgba(225, 29, 72, 0.5)",
  },
  "consumer discretionary": {
    name: "Consumer Discretionary",
    stroke: "#e11d48",
    fill: "rgba(225, 29, 72, 0.08)",
    glow: "rgba(225, 29, 72, 0.35)",
    text: "var(--price)",
    badgeBg: "rgba(225, 29, 72, 0.12)",
    badgeBorder: "rgba(225, 29, 72, 0.35)",
    innerFill: "rgba(225, 29, 72, 0.06)",
    leafFill: "rgba(225, 29, 72, 0.14)",
    leafStroke: "rgba(225, 29, 72, 0.5)",
  },
  "geopolitics / macro": {
    name: "Geopolitics / Macro",
    stroke: "#7c3aed", // Purple
    fill: "rgba(124, 58, 237, 0.08)",
    glow: "rgba(124, 58, 237, 0.35)",
    text: "#a855f7",
    badgeBg: "rgba(124, 58, 237, 0.12)",
    badgeBorder: "rgba(124, 58, 237, 0.35)",
    innerFill: "rgba(124, 58, 237, 0.06)",
    leafFill: "rgba(124, 58, 237, 0.14)",
    leafStroke: "rgba(124, 58, 237, 0.5)",
  },
  energy: {
    name: "Energy",
    stroke: "#ca8a04", // Yellow / Gold
    fill: "rgba(202, 138, 4, 0.08)",
    glow: "rgba(202, 138, 4, 0.35)",
    text: "#eab308",
    badgeBg: "rgba(202, 138, 4, 0.12)",
    badgeBorder: "rgba(202, 138, 4, 0.35)",
    innerFill: "rgba(202, 138, 4, 0.06)",
    leafFill: "rgba(202, 138, 4, 0.14)",
    leafStroke: "rgba(202, 138, 4, 0.5)",
  },
};

const DEFAULT_PALETTE: SectorPalette = {
  name: "Sector",
  stroke: "var(--signal)",
  fill: "color-mix(in oklch, var(--signal) 8%, transparent)",
  glow: "color-mix(in oklch, var(--signal) 30%, transparent)",
  text: "var(--signal)",
  badgeBg: "color-mix(in oklch, var(--signal) 12%, transparent)",
  badgeBorder: "color-mix(in oklch, var(--signal) 35%, transparent)",
  innerFill: "color-mix(in oklch, var(--signal) 6%, transparent)",
  leafFill: "color-mix(in oklch, var(--signal) 14%, transparent)",
  leafStroke: "color-mix(in oklch, var(--signal) 50%, transparent)",
};

export function getSectorPalette(sectorName?: string | null): SectorPalette {
  if (!sectorName) return DEFAULT_PALETTE;
  const key = sectorName.toLowerCase().trim();
  return SECTOR_PALETTES[key] || DEFAULT_PALETTE;
}

