"use client";

import React, { useMemo } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SectorThemeNode } from "@/lib/api";
import { getSectorPalette } from "./theme-colors";
import { ArrowUpRight, Hash } from "lucide-react";

interface ThemeGridViewProps {
  sectors: SectorThemeNode[];
  searchQuery?: string;
  selectedSectorId?: string | null;
}

export function ThemeGridView({
  sectors,
  searchQuery = "",
  selectedSectorId,
}: ThemeGridViewProps) {
  const query = searchQuery.trim().toLowerCase();

  // Filter sectors and child items based on search query & selected sector
  const filteredSectors = useMemo(() => {
    let list = sectors.filter((s) => s.level === "sector");

    if (selectedSectorId) {
      list = list.filter((s) => s.id === selectedSectorId);
    }

    if (!query) return list;

    return list
      .map((sector) => {
        const sectorMatches = sector.name.toLowerCase().includes(query);
        const industries = sector.industries || [];

        const filteredIndustries = industries
          .map((industry) => {
            const industryMatches = industry.name.toLowerCase().includes(query);
            const themes = industry.themes || [];

            const filteredThemes = themes.filter((theme) => {
              const nameMatch = theme.name.toLowerCase().includes(query);
              const descMatch = theme.description?.toLowerCase().includes(query);
              const tickerMatch = theme.tickers?.some((t) =>
                t.ticker.toLowerCase().includes(query.replace("$", ""))
              );
              return nameMatch || descMatch || tickerMatch;
            });

            if (industryMatches || sectorMatches) {
              return industry;
            }

            if (filteredThemes.length > 0) {
              return {
                ...industry,
                themes: filteredThemes,
              };
            }

            return null;
          })
          .filter(Boolean) as typeof industries;

        if (sectorMatches || filteredIndustries.length > 0) {
          return {
            ...sector,
            industries: filteredIndustries,
          };
        }

        return null;
      })
      .filter(Boolean) as SectorThemeNode[];
  }, [sectors, query, selectedSectorId]);

  if (filteredSectors.length === 0) {
    return (
      <div className="rounded-md border border-line bg-panel p-12 text-center">
        <Hash className="h-8 w-8 text-ink-faint mx-auto mb-3" />
        <h3 className="font-display text-title font-semibold text-ink">No matching themes found</h3>
        <p className="text-small text-ink-secondary mt-1 max-w-sm mx-auto">
          Try searching for another keyword, sector, or stock ticker symbol.
        </p>
      </div>
    );
  }

  return (
    <div className="grid gap-6">
      {filteredSectors.map((sector) => {
        const industries = sector.industries || [];
        const totalThemesInSector = industries.reduce(
          (acc, ind) => acc + (ind.themes?.length || 0),
          0
        );
        const palette = getSectorPalette(sector.name);

        return (
          <Card key={sector.id} className="overflow-hidden border-line bg-panel rounded-md">
            <CardHeader className="bg-panel-raised py-3 px-4 flex flex-row items-center justify-between border-b border-line">
              <div className="flex items-center gap-3">
                <span
                  className="h-2.5 w-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: palette.stroke }}
                />
                <div>
                  <CardTitle className="font-display text-heading font-semibold text-ink">
                    {sector.name}
                  </CardTitle>
                  {sector.description && (
                    <CardDescription className="mt-0.5 text-small text-ink-secondary">
                      {sector.description}
                    </CardDescription>
                  )}
                </div>
              </div>
              <Badge variant="outline" className="font-mono text-micro text-ink-faint rounded-sm tabular-nums">
                {industries.length} industries · {totalThemesInSector} themes
              </Badge>
            </CardHeader>
            <CardContent className="p-4 pt-4">
              {industries.length === 0 ? (
                <p className="text-small text-ink-faint py-2 italic">
                  No sub-themes or industries configured for this sector yet.
                </p>
              ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {industries.map((industry) => {
                    const industryThemes = industry.themes || [];
                    return (
                      <div
                        key={industry.id}
                        className="flex flex-col gap-3 rounded-md border border-line bg-panel-raised/30 p-3.5 hover:border-line-strong transition-colors"
                      >
                        <div className="flex items-center justify-between border-b border-line pb-2">
                          <h3 className="font-display text-title font-semibold text-ink">
                            {industry.name}
                          </h3>
                          <Badge variant="outline" className="font-mono text-micro text-ink-faint rounded-sm tabular-nums">
                            {industryThemes.length}
                          </Badge>
                        </div>
                        <div className="flex flex-col gap-2">
                          {industryThemes.length === 0 ? (
                            <span className="text-micro text-ink-faint italic py-1">
                              No active sub-themes
                            </span>
                          ) : (
                            industryThemes.map((theme) => (
                              <Link key={theme.id} href={`/themes/${theme.id}`}>
                                <Badge
                                  variant="outline"
                                  className="w-full justify-between py-2 px-3 text-small rounded-md border-line bg-panel transition-all hover:border-signal/40 hover:bg-panel-raised group cursor-pointer"
                                >
                                  <span className="truncate group-hover:text-signal transition-colors font-medium">
                                    {theme.name}
                                  </span>
                                  <div className="flex items-center gap-1.5 shrink-0 ml-2">
                                    {theme.tickers && theme.tickers.length > 0 && (
                                      <div className="flex items-center gap-1">
                                        {theme.tickers.slice(0, 2).map((tk) => (
                                          <span
                                            key={tk.ticker}
                                            className="font-mono text-micro text-signal bg-signal/10 px-1 py-0.5 rounded-sm font-bold"
                                          >
                                            {tk.ticker}
                                          </span>
                                        ))}
                                        {theme.tickers.length > 2 && (
                                          <span className="font-mono text-micro text-ink-faint tabular-nums">
                                            +{theme.tickers.length - 2}
                                          </span>
                                        )}
                                      </div>
                                    )}
                                    <ArrowUpRight className="h-3 w-3 text-ink-faint group-hover:text-signal transition-colors" />
                                  </div>
                                </Badge>
                              </Link>
                            ))
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

