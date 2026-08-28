/**
 * Sector color palettes and helper utilities for Theme visualizers.
 * Designed to harmonize with yt-chatter's dark/light instrument token layer.
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
    stroke: "#00e5ff", // Bright Electric Cyan
    fill: "rgba(0, 229, 255, 0.08)",
    glow: "rgba(0, 229, 255, 0.4)",
    text: "#38bdf8",
    badgeBg: "rgba(0, 229, 255, 0.15)",
    badgeBorder: "rgba(0, 229, 255, 0.4)",
    innerFill: "rgba(0, 229, 255, 0.12)",
    leafFill: "rgba(0, 229, 255, 0.22)",
    leafStroke: "rgba(0, 229, 255, 0.6)",
  },
  healthcare: {
    name: "Healthcare",
    stroke: "#10b981", // Vibrant Emerald Green
    fill: "rgba(16, 185, 129, 0.08)",
    glow: "rgba(16, 185, 129, 0.4)",
    text: "#34d399",
    badgeBg: "rgba(16, 185, 129, 0.15)",
    badgeBorder: "rgba(16, 185, 129, 0.4)",
    innerFill: "rgba(16, 185, 129, 0.12)",
    leafFill: "rgba(16, 185, 129, 0.22)",
    leafStroke: "rgba(16, 185, 129, 0.6)",
  },
  financials: {
    name: "Financials",
    stroke: "#f59e0b", // Radiant Amber / Gold
    fill: "rgba(245, 158, 11, 0.08)",
    glow: "rgba(245, 158, 11, 0.4)",
    text: "#fbbf24",
    badgeBg: "rgba(245, 158, 11, 0.15)",
    badgeBorder: "rgba(245, 158, 11, 0.4)",
    innerFill: "rgba(245, 158, 11, 0.12)",
    leafFill: "rgba(245, 158, 11, 0.22)",
    leafStroke: "rgba(245, 158, 11, 0.6)",
  },
  industrials: {
    name: "Industrials",
    stroke: "#3b82f6", // Vibrant Blue
    fill: "rgba(59, 130, 246, 0.08)",
    glow: "rgba(59, 130, 246, 0.4)",
    text: "#60a5fa",
    badgeBg: "rgba(59, 130, 246, 0.15)",
    badgeBorder: "rgba(59, 130, 246, 0.4)",
    innerFill: "rgba(59, 130, 246, 0.12)",
    leafFill: "rgba(59, 130, 246, 0.22)",
    leafStroke: "rgba(59, 130, 246, 0.6)",
  },
  consumer: {
    name: "Consumer",
    stroke: "#f43f5e", // Coral Rose
    fill: "rgba(244, 63, 94, 0.08)",
    glow: "rgba(244, 63, 94, 0.4)",
    text: "#fb7185",
    badgeBg: "rgba(244, 63, 94, 0.15)",
    badgeBorder: "rgba(244, 63, 94, 0.4)",
    innerFill: "rgba(244, 63, 94, 0.12)",
    leafFill: "rgba(244, 63, 94, 0.22)",
    leafStroke: "rgba(244, 63, 94, 0.6)",
  },
  "consumer discretionary": {
    name: "Consumer Discretionary",
    stroke: "#f43f5e",
    fill: "rgba(244, 63, 94, 0.08)",
    glow: "rgba(244, 63, 94, 0.4)",
    text: "#fb7185",
    badgeBg: "rgba(244, 63, 94, 0.15)",
    badgeBorder: "rgba(244, 63, 94, 0.4)",
    innerFill: "rgba(244, 63, 94, 0.12)",
    leafFill: "rgba(244, 63, 94, 0.22)",
    leafStroke: "rgba(244, 63, 94, 0.6)",
  },
  "geopolitics / macro": {
    name: "Geopolitics / Macro",
    stroke: "#a855f7", // Electric Purple / Violet
    fill: "rgba(168, 85, 247, 0.08)",
    glow: "rgba(168, 85, 247, 0.4)",
    text: "#c084fc",
    badgeBg: "rgba(168, 85, 247, 0.15)",
    badgeBorder: "rgba(168, 85, 247, 0.4)",
    innerFill: "rgba(168, 85, 247, 0.12)",
    leafFill: "rgba(168, 85, 247, 0.22)",
    leafStroke: "rgba(168, 85, 247, 0.6)",
  },
  energy: {
    name: "Energy",
    stroke: "#eab308", // Vivid Yellow
    fill: "rgba(234, 179, 8, 0.08)",
    glow: "rgba(234, 179, 8, 0.4)",
    text: "#fde047",
    badgeBg: "rgba(234, 179, 8, 0.15)",
    badgeBorder: "rgba(234, 179, 8, 0.4)",
    innerFill: "rgba(234, 179, 8, 0.12)",
    leafFill: "rgba(234, 179, 8, 0.22)",
    leafStroke: "rgba(234, 179, 8, 0.6)",
  },
};

const DEFAULT_PALETTE: SectorPalette = {
  name: "Sector",
  stroke: "#22c55e", // Green Signal
  fill: "rgba(34, 197, 94, 0.08)",
  glow: "rgba(34, 197, 94, 0.4)",
  text: "#4ade80",
  badgeBg: "rgba(34, 197, 94, 0.15)",
  badgeBorder: "rgba(34, 197, 94, 0.4)",
  innerFill: "rgba(34, 197, 94, 0.12)",
  leafFill: "rgba(34, 197, 94, 0.22)",
  leafStroke: "rgba(34, 197, 94, 0.6)",
};

export function getSectorPalette(sectorName?: string | null): SectorPalette {
  if (!sectorName) return DEFAULT_PALETTE;
  const key = sectorName.toLowerCase().trim();
  return SECTOR_PALETTES[key] || DEFAULT_PALETTE;
}
