"use client";

import React from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { CircleDot, LayoutGrid, Search, X } from "lucide-react";
import { SectorThemeNode } from "@/lib/api";
import { getSectorPalette } from "./theme-colors";

export type ViewMode = "circle-pack" | "grid";

interface ThemeControlsProps {
  searchQuery: string;
  onSearchChange: (val: string) => void;
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  sectors: SectorThemeNode[];
  selectedSectorId: string | null;
  onSelectSector: (sectorId: string | null) => void;
}

export function ThemeControls({
  searchQuery,
  onSearchChange,
  viewMode,
  onViewModeChange,
  sectors,
  selectedSectorId,
  onSelectSector,
}: ThemeControlsProps) {
  const cleanSectors = sectors.filter((s) => s.level === "sector");

  return (
    <div className="flex flex-col gap-3">
      {/* ── Top Bar: Search & View Toggle ─────────────────────────── */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        {/* Search Input */}
        <div className="relative flex-1 max-w-xl">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-ink-faint" />
          <Input
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search themes, sectors, tickers (e.g. AI, Semiconductors, $NVDA)..."
            className="pl-9 pr-8 h-8 font-mono text-small bg-panel border-line text-ink placeholder:text-ink-faint focus-visible:ring-signal rounded-md"
          />
          {searchQuery && (
            <button
              onClick={() => onSearchChange("")}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-ink-faint hover:text-ink"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>

        {/* View Mode Toggle */}
        <div className="flex items-center gap-0.5 bg-panel border border-line p-0.5 rounded-md shrink-0">
          <Button
            variant={viewMode === "circle-pack" ? "secondary" : "ghost"}
            size="sm"
            onClick={() => onViewModeChange("circle-pack")}
            className={`font-mono text-small gap-1.5 h-7 px-2.5 rounded-sm ${viewMode === "circle-pack"
                ? "bg-panel-raised text-signal font-semibold border border-line"
                : "text-ink-secondary hover:text-ink"
              }`}
          >
            <CircleDot className="h-3.5 w-3.5 text-signal" />
            <span>Bubble Map</span>
          </Button>

          <Button
            variant={viewMode === "grid" ? "secondary" : "ghost"}
            size="sm"
            onClick={() => onViewModeChange("grid")}
            className={`font-mono text-small gap-1.5 h-7 px-2.5 rounded-sm ${viewMode === "grid"
                ? "bg-panel-raised text-signal font-semibold border border-line"
                : "text-ink-secondary hover:text-ink"
              }`}
          >
            <LayoutGrid className="h-3.5 w-3.5 text-ink-secondary" />
            <span>Card Grid</span>
          </Button>
        </div>
      </div>

      {/* ── Sector Quick Filter Chips ─────────────────────────────── */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onSelectSector(null)}
          className={`h-7 px-2.5 font-mono text-micro rounded-md transition-all shrink-0 ${selectedSectorId === null
              ? "bg-signal text-signal-foreground border-signal font-bold"
              : "border-line bg-panel text-ink-secondary hover:text-ink hover:bg-panel-raised"
            }`}
        >
          All Sectors ({cleanSectors.length})
        </Button>

        {cleanSectors.map((sector) => {
          const isSelected = selectedSectorId === sector.id;
          const palette = getSectorPalette(sector.name);
          const totalThemes = (sector.industries || []).reduce(
            (acc, ind) => acc + (ind.themes?.length || 0),
            0
          );

          return (
            <button
              key={sector.id}
              onClick={() => onSelectSector(isSelected ? null : sector.id)}
              className={`h-7 px-2.5 font-mono text-micro rounded-md border transition-all shrink-0 flex items-center gap-1.5 ${isSelected
                  ? "border-signal/50 bg-signal/10 text-signal font-bold shadow-2xs"
                  : "border-line bg-panel hover:bg-panel-raised text-ink-secondary hover:text-ink"
                }`}
            >
              <span
                className="h-1.5 w-1.5 rounded-full shrink-0"
                style={{ backgroundColor: palette.stroke }}
              />
              <span>{sector.name}</span>
              <span className="opacity-60 text-micro">({totalThemes})</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

