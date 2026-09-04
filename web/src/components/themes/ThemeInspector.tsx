"use client";

import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ChevronRight, ExternalLink, Sparkles, TrendingUp, X, ZoomIn } from "lucide-react";
import { SelectedNodeInfo } from "./types";
import { getSectorPalette } from "./theme-colors";

interface ThemeInspectorProps {
  selectedNode: SelectedNodeInfo | null;
  onClose: () => void;
  onZoomToNode?: (nodeId: string) => void;
  onSelectThemeById?: (themeId: string) => void;
  stats?: {
    totalSectors: number;
    totalIndustries: number;
    totalThemes: number;
  };
}

export function ThemeInspector({
  selectedNode,
  onClose,
  onZoomToNode,
  onSelectThemeById,
  stats,
}: ThemeInspectorProps) {
  if (!selectedNode) {
    return (
      <Card className="h-full flex flex-col justify-between border-line bg-panel rounded-md overflow-hidden">
        <CardHeader className="p-4 pb-3 border-b border-line bg-panel-raised">
          <div className="flex items-center gap-2 text-ink-secondary">
            <Sparkles className="h-4 w-4 text-signal" />
            <span className="font-mono text-caption uppercase tracking-wider">Explore Market Clusters</span>
          </div>
          <CardDescription className="text-small text-ink-secondary">
            Click any sector or industry bubble to zoom in. Click a sub-theme bubble to inspect mapped stocks and video mentions.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-4 pt-5 flex-1 flex flex-col justify-between">
          <div className="space-y-4">
            {stats && (
              <div className="grid grid-cols-3 gap-2">
                <div className="rounded-md border border-line bg-panel-raised p-2.5 text-center">
                  <div className="font-mono text-title font-bold text-ink tabular-nums">{stats.totalSectors}</div>
                  <div className="text-micro text-ink-faint uppercase font-mono">Sectors</div>
                </div>
                <div className="rounded-md border border-line bg-panel-raised p-2.5 text-center">
                  <div className="font-mono text-title font-bold text-ink tabular-nums">{stats.totalIndustries}</div>
                  <div className="text-micro text-ink-faint uppercase font-mono">Industries</div>
                </div>
                <div className="rounded-md border border-line bg-panel-raised p-2.5 text-center">
                  <div className="font-mono text-title font-bold text-signal tabular-nums">{stats.totalThemes}</div>
                  <div className="text-micro text-ink-faint uppercase font-mono">Themes</div>
                </div>
              </div>
            )}
          </div>

          <div className="mt-6 rounded-md border border-signal/20 bg-signal/5 p-3 text-micro text-ink-secondary flex items-start gap-2">
            <TrendingUp className="h-4 w-4 text-signal shrink-0 mt-0.5" />
            <span>
              Themes and tickers are automatically extracted from finance YouTube channels via Whisper and LLM pipelines.
            </span>
          </div>
        </CardContent>
      </Card>
    );
  }

  const palette = getSectorPalette(selectedNode.sectorName);

  return (
    <Card className="h-full flex flex-col border-line bg-panel rounded-md overflow-hidden">
      {/* Header with Level & Close */}
      <CardHeader className="p-4 pb-3 border-b border-line bg-panel-raised">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Badge
              variant="outline"
              className="font-mono text-micro uppercase tracking-wider px-2 py-0.5 rounded-sm"
              style={{
                borderColor: palette.stroke,
                color: palette.text,
                backgroundColor: palette.fill,
              }}
            >
              {selectedNode.level}
            </Badge>
            {selectedNode.sectorName && selectedNode.level !== "sector" && (
              <span className="text-micro font-mono text-ink-faint truncate max-w-[140px]">
                {selectedNode.sectorName}
              </span>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="h-7 w-7 p-0 text-ink-faint hover:text-ink hover:bg-panel rounded-sm"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Title */}
        <CardTitle className="font-display text-title font-bold text-ink mt-2">
          {selectedNode.name}
        </CardTitle>

        {/* Breadcrumbs Lineage */}
        <div className="flex items-center gap-1.5 text-micro text-ink-faint font-mono overflow-x-auto py-0.5 no-scrollbar">
          <span>Root</span>
          {selectedNode.sectorName && (
            <>
              <ChevronRight className="h-3 w-3 shrink-0 text-line-strong" />
              <span className="text-ink-secondary">{selectedNode.sectorName}</span>
            </>
          )}
          {selectedNode.industryName && (
            <>
              <ChevronRight className="h-3 w-3 shrink-0 text-line-strong" />
              <span className="text-ink-secondary">{selectedNode.industryName}</span>
            </>
          )}
        </div>
      </CardHeader>

      {/* Body Content */}
      <CardContent className="p-4 flex-1 overflow-y-auto space-y-4">
        {selectedNode.description && (
          <p className="text-small text-ink-secondary leading-relaxed bg-panel-raised/50 p-3 rounded-md border border-line">
            {selectedNode.description}
          </p>
        )}

        {/* THEME LEVEL */}
        {selectedNode.level === "theme" && (
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="font-mono text-caption uppercase tracking-wider text-ink-secondary flex items-center gap-1.5">
                  <TrendingUp className="h-3.5 w-3.5 text-signal" />
                  Mapped Tickers ({selectedNode.tickers?.length || 0})
                </span>
              </div>

              {!selectedNode.tickers || selectedNode.tickers.length === 0 ? (
                <p className="text-micro text-ink-faint italic py-2">
                  No stock tickers mapped to this theme yet.
                </p>
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {selectedNode.tickers.map((tk) => (
                    <Link key={tk.ticker} href={`/tickers/${tk.ticker}`}>
                      <Badge
                        variant="outline"
                        className="font-mono text-small py-1 px-2.5 gap-1.5 rounded-md transition-all hover:border-signal/40 hover:bg-signal/10 hover:text-signal cursor-pointer"
                      >
                        <span className="font-bold text-signal">{tk.ticker}</span>
                        {tk.relevance_score > 0 && (
                          <span className="text-micro text-ink-faint tabular-nums">
                            {(tk.relevance_score * 100).toFixed(0)}%
                          </span>
                        )}
                      </Badge>
                    </Link>
                  ))}
                </div>
              )}
            </div>

            {/* Primary Action Button */}
            <div className="pt-2">
              <Link href={`/themes/${selectedNode.id}`} className="w-full block">
                <Button className="w-full font-mono text-small gap-2 bg-signal text-signal-foreground hover:bg-signal/90 font-medium rounded-md">
                  <ExternalLink className="h-4 w-4" />
                  Explore Theme Videos & Sentiment
                </Button>
              </Link>
            </div>
          </div>
        )}

        {/* INDUSTRY LEVEL */}
        {selectedNode.level === "industry" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between text-small py-1 border-b border-line">
              <span className="text-ink-secondary">Active Sub-themes</span>
              <Badge variant="outline" className="font-mono text-micro tabular-nums">
                {selectedNode.subThemesCount ?? selectedNode.childThemes?.length ?? 0}
              </Badge>
            </div>

            {selectedNode.childThemes && selectedNode.childThemes.length > 0 && (
              <div className="space-y-2">
                <span className="font-mono text-caption uppercase tracking-wider text-ink-secondary">
                  Sub-Themes in this Industry
                </span>
                <div className="flex flex-col gap-1.5 max-h-[180px] overflow-y-auto pr-1">
                  {selectedNode.childThemes.map((th) => (
                    <button
                      key={th.id}
                      onClick={() => onSelectThemeById?.(th.id)}
                      className="text-left w-full flex items-center justify-between p-2 rounded-md border border-line bg-panel hover:border-signal/40 hover:bg-panel-raised transition-colors group text-small"
                    >
                      <span className="truncate group-hover:text-signal transition-colors font-medium text-ink">
                        {th.name}
                      </span>
                      {th.tickers && th.tickers.length > 0 && (
                        <span className="font-mono text-micro text-signal bg-signal/10 px-1.5 py-0.5 rounded-sm shrink-0 font-bold">
                          {th.tickers[0].ticker}
                          {th.tickers.length > 1 ? ` +${th.tickers.length - 1}` : ""}
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {onZoomToNode && (
              <Button
                variant="outline"
                onClick={() => onZoomToNode(selectedNode.id)}
                className="w-full font-mono text-small gap-2 rounded-md hover:border-signal/50"
              >
                <ZoomIn className="h-4 w-4 text-signal" />
                Zoom into {selectedNode.name}
              </Button>
            )}
          </div>
        )}

        {/* SECTOR LEVEL */}
        {selectedNode.level === "sector" && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-2">
              <div className="rounded-md border border-line bg-panel-raised p-3 text-center">
                <div className="font-mono text-heading font-semibold text-ink tabular-nums">
                  {selectedNode.industriesCount ?? 0}
                </div>
                <div className="text-micro text-ink-faint uppercase font-mono">Industries</div>
              </div>
              <div className="rounded-md border border-line bg-panel-raised p-3 text-center">
                <div className="font-mono text-heading font-semibold text-signal tabular-nums">
                  {selectedNode.subThemesCount ?? 0}
                </div>
                <div className="text-micro text-ink-faint uppercase font-mono">Total Themes</div>
              </div>
            </div>

            {onZoomToNode && (
              <Button
                onClick={() => onZoomToNode(selectedNode.id)}
                className="w-full font-mono text-small gap-2 bg-signal text-signal-foreground hover:bg-signal/90 rounded-md"
              >
                <ZoomIn className="h-4 w-4" />
                Zoom into {selectedNode.name}
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

