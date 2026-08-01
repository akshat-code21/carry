"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Hash } from "lucide-react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/PageHeader";
import { EmptyState } from "@/components/EmptyState";
import { DashboardSkeleton } from "@/components/skeletons/LayoutSkeletons";
import { useThemes } from "@/lib/hooks";

export default function ThemesPage() {
  const { data: themes = [], isLoading } = useThemes();

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  const sectors = themes.filter((t) => t.level === "sector");
  const narratives = themes.filter((t) => t.level === "narrative");

  return (
    <div className="flex flex-col gap-6 pb-10">
      <PageHeader
        title="Theme Explorer"
        description="Browse the hierarchical taxonomy of financial themes, sectors, and narratives."
      />

      {themes.length === 0 ? (
        <EmptyState
          icon={<Hash className="h-6 w-6" />}
          title="No themes extracted yet"
          description="Themes will appear here as videos are processed."
        />
      ) : (
        <>
          <div className="grid gap-6">
            {sectors.map((sector) => {
              const industries = sector.industries || [];
              const totalThemesInSector = industries.reduce((acc, ind) => acc + (ind.themes?.length || 0), 0);

              return (
                <Card key={sector.id} className="overflow-hidden border-line">
                  <CardHeader className="bg-panel-raised pb-4 flex flex-row items-center justify-between border-b border-line">
                    <div>
                      <CardTitle className="font-display text-heading font-semibold text-ink">{sector.name}</CardTitle>
                      {sector.description && (
                        <CardDescription className="mt-0.5 text-small text-ink-secondary">{sector.description}</CardDescription>
                      )}
                    </div>
                    <Badge variant="outline" className="font-mono text-micro text-ink-faint">
                      {industries.length} industries · {totalThemesInSector} themes
                    </Badge>
                  </CardHeader>
                  <CardContent className="pt-6">
                    {industries.length === 0 ? (
                      <p className="text-small text-ink-faint py-2 italic">
                        No sub-themes or industries configured for this sector yet.
                      </p>
                    ) : (
                      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                        {industries.map((industry) => {
                          const industryThemes = industry.themes || [];
                          return (
                            <div key={industry.id} className="flex flex-col gap-3 rounded-lg border border-line bg-panel/50 p-4">
                              <div className="flex items-center justify-between border-b border-line pb-2">
                                <h3 className="font-display text-title font-semibold text-ink">{industry.name}</h3>
                                <Badge variant="outline" className="font-mono text-micro text-ink-faint">
                                  {industryThemes.length}
                                </Badge>
                              </div>
                              <div className="flex flex-col gap-2">
                                {industryThemes.length === 0 ? (
                                  <span className="text-micro text-ink-faint italic py-1">No active sub-themes</span>
                                ) : (
                                  industryThemes.map((theme) => (
                                    <Link key={theme.id} href={`/themes/${theme.id}`}>
                                      <Badge
                                        variant="outline"
                                        className="w-full justify-between py-2 px-3 text-small transition-all hover:border-signal/40 hover:bg-panel-raised group"
                                      >
                                        <span className="truncate group-hover:text-signal transition-colors">{theme.name}</span>
                                        {theme.tickers && theme.tickers.length > 0 && (
                                          <div className="flex items-center gap-1.5 shrink-0 ml-2">
                                            {theme.tickers.slice(0, 2).map((tk) => (
                                              <span key={tk.ticker} className="font-mono text-micro text-signal/80 bg-signal/10 px-1 rounded">
                                                ${tk.ticker}
                                              </span>
                                            ))}
                                            {theme.tickers.length > 2 && (
                                              <span className="font-mono text-micro text-ink-faint">
                                                +{theme.tickers.length - 2}
                                              </span>
                                            )}
                                          </div>
                                        )}
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

          {narratives.length > 0 && (
            <div className="mt-8">
              <h2 className="mb-4 font-display text-heading font-semibold text-ink">Extracted Narratives</h2>
              <Card>
                <CardContent className="pt-6 grid gap-4 md:grid-cols-2">
                  {narratives.map((n) => (
                    <Link key={n.id} href={`/themes/${n.id}`}>
                      <Card className="h-full transition-colors hover:border-signal/40">
                        <CardHeader className="p-4">
                          <CardTitle className="line-clamp-2 text-title font-semibold">{n.name}</CardTitle>
                          {n.description && <CardDescription className="mt-1 line-clamp-2">{n.description}</CardDescription>}
                        </CardHeader>
                      </Card>
                    </Link>
                  ))}
                </CardContent>
              </Card>
            </div>
          )}
        </>
      )}
    </div>
  );
}

