"use client";

import React, { useState, useMemo, useRef, useCallback } from "react";
import * as d3 from "d3-hierarchy";
import { HierarchyCircularNode } from "d3-hierarchy";
import { PackedThemeDatum, SelectedNodeInfo } from "./types";
import { getSectorPalette } from "./theme-colors";
import { ChevronRight, RotateCcw, ZoomIn, ZoomOut, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface ThemeCirclePackProps {
  data: PackedThemeDatum;
  searchQuery?: string;
  selectedNodeId?: string | null;
  onSelectNode: (node: SelectedNodeInfo | null) => void;
  onNavigateToTheme?: (themeId: string) => void;
}

const VIEW_SIZE = 900;

export function ThemeCirclePack({
  data,
  searchQuery = "",
  selectedNodeId,
  onSelectNode,
}: ThemeCirclePackProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoveredNode, setHoveredNode] = useState<HierarchyCircularNode<PackedThemeDatum> | null>(null);

  // 1. Build D3 Hierarchy and Pack Layout
  const packRoot = useMemo(() => {
    const root = d3
      .hierarchy<PackedThemeDatum>(data)
      .sum((d) => d.value || 0)
      .sort((a, b) => (b.value || 0) - (a.value || 0));

    const packLayout = d3
      .pack<PackedThemeDatum>()
      .size([VIEW_SIZE, VIEW_SIZE])
      .padding((d) => {
        if (d.depth === 0) return 24;
        if (d.depth === 1) return 18;
        if (d.depth === 2) return 10;
        return 6;
      });

    return packLayout(root);
  }, [data]);

  // Lookup node by ID
  const nodesById = useMemo(() => {
    const map = new Map<string, HierarchyCircularNode<PackedThemeDatum>>();
    packRoot.each((node) => {
      map.set(node.data.id, node);
    });
    return map;
  }, [packRoot]);

  // Helper to construct SelectedNodeInfo from a hierarchy node
  const createSelectedInfo = useCallback(
    (node: HierarchyCircularNode<PackedThemeDatum>): SelectedNodeInfo | null => {
      const d = node.data;
      if (d.level === "root") return null;
      return {
        id: d.id,
        name: d.name,
        level: d.level,
        description: d.description,
        sectorName: d.sectorName,
        sectorId: d.sectorId,
        industryName: d.industryName,
        industryId: d.industryId,
        tickers: d.tickers,
        subThemesCount: d.childCount ?? node.children?.length ?? 0,
        industriesCount: d.level === "sector" ? node.children?.length : undefined,
        childThemes:
          d.level === "industry" && node.children
            ? node.children.map((c) => ({
                id: c.data.id,
                name: c.data.name,
                description: c.data.description,
                level: "theme",
                tickers: c.data.tickers,
              }))
            : undefined,
      };
    },
    []
  );

  // 2. Focus / Zoom state
  const [internalFocusId, setInternalFocusId] = useState<string>("root");

  // Determine current focus node
  const currentFocus = useMemo(() => {
    if (internalFocusId !== "root" && nodesById.has(internalFocusId)) {
      return nodesById.get(internalFocusId)!;
    }
    if (selectedNodeId && nodesById.has(selectedNodeId)) {
      const node = nodesById.get(selectedNodeId)!;
      if (node.children && node.children.length > 0) return node;
      if (node.parent) return node.parent;
    }
    return packRoot;
  }, [internalFocusId, selectedNodeId, nodesById, packRoot]);

  const currentFocusLevel = currentFocus.data.level; // "root" | "sector" | "industry" | "theme"

  // 3. Search matching node set
  const query = searchQuery.trim().toLowerCase();
  const searchMatchIds = useMemo(() => {
    if (!query) return null;
    const matchSet = new Set<string>();

    packRoot.each((node) => {
      const d = node.data;
      const nameMatch = d.name?.toLowerCase().includes(query);
      const descMatch = d.description?.toLowerCase().includes(query);
      const tickerMatch = d.tickers?.some((t) => t.ticker.toLowerCase().includes(query.replace("$", "")));
      const sectorMatch = d.sectorName?.toLowerCase().includes(query);
      const industryMatch = d.industryName?.toLowerCase().includes(query);

      if (nameMatch || descMatch || tickerMatch || sectorMatch || industryMatch) {
        matchSet.add(d.id);
        let p = node.parent;
        while (p) {
          matchSet.add(p.data.id);
          p = p.parent;
        }
      }
    });

    return matchSet;
  }, [packRoot, query]);

  // Handle node selection & zoom
  const handleNodeClick = useCallback(
    (e: React.MouseEvent, node: HierarchyCircularNode<PackedThemeDatum>) => {
      e.stopPropagation();

      const d = node.data;
      const info = createSelectedInfo(node);
      onSelectNode(info);

      // If it's a sector or industry with children, zoom in
      if (node.children && node.children.length > 0) {
        setInternalFocusId(d.id);
      } else if (d.level === "theme" && node.parent) {
        // Zoom to its industry parent so theme is prominent
        setInternalFocusId(node.parent.data.id);
      }
    },
    [createSelectedInfo, onSelectNode]
  );

  // Reset view to Root
  const handleResetView = useCallback(
    (e?: React.MouseEvent) => {
      e?.stopPropagation();
      setInternalFocusId("root");
      onSelectNode(null);
    },
    [onSelectNode]
  );

  // Zoom out one level
  const handleZoomOut = useCallback(
    (e?: React.MouseEvent) => {
      e?.stopPropagation();
      if (currentFocus.parent) {
        const parentNode = currentFocus.parent;
        setInternalFocusId(parentNode.data.id);
        if (parentNode.data.level === "root") {
          onSelectNode(null);
        } else {
          onSelectNode(createSelectedInfo(parentNode));
        }
      } else {
        handleResetView();
      }
    },
    [currentFocus, createSelectedInfo, onSelectNode, handleResetView]
  );

  // Zoom in one level (to largest child cluster)
  const handleZoomIn = useCallback(
    (e?: React.MouseEvent) => {
      e?.stopPropagation();
      if (currentFocus.children && currentFocus.children.length > 0) {
        const firstChild = currentFocus.children[0];
        setInternalFocusId(firstChild.data.id);
        onSelectNode(createSelectedInfo(firstChild));
      }
    },
    [currentFocus, createSelectedInfo, onSelectNode]
  );

  // Breadcrumb click handler
  const handleBreadcrumbClick = useCallback(
    (e: React.MouseEvent, crumb: HierarchyCircularNode<PackedThemeDatum>) => {
      e.stopPropagation();
      if (crumb.data.level === "root") {
        handleResetView();
      } else {
        setInternalFocusId(crumb.data.id);
        onSelectNode(createSelectedInfo(crumb));
      }
    },
    [handleResetView, createSelectedInfo, onSelectNode]
  );

  // Zoom transform calculation for each node
  const scale = VIEW_SIZE / (currentFocus.r * 2);
  const viewX = currentFocus.x;
  const viewY = currentFocus.y;

  const getNodeTransform = (node: HierarchyCircularNode<PackedThemeDatum>) => {
    const k = scale;
    const cx = (node.x - viewX) * k + VIEW_SIZE / 2;
    const cy = (node.y - viewY) * k + VIEW_SIZE / 2;
    const r = node.r * k;
    return { cx, cy, r };
  };

  // Breadcrumb path from root to current focus
  const breadcrumbs = useMemo(() => {
    const path: HierarchyCircularNode<PackedThemeDatum>[] = [];
    let curr: HierarchyCircularNode<PackedThemeDatum> | null = currentFocus;
    while (curr) {
      path.unshift(curr);
      curr = curr.parent;
    }
    return path;
  }, [currentFocus]);

  // All nodes flattened
  const allNodes = useMemo(() => packRoot.descendants(), [packRoot]);

  const canZoomIn = currentFocus.children && currentFocus.children.length > 0;
  const canZoomOut = currentFocus.parent !== null && currentFocus.data.level !== "root";

  return (
    <div
      ref={containerRef}
      onClick={handleZoomOut}
      className="relative w-full h-full min-h-[580px] lg:min-h-[680px] rounded-xl border border-line bg-[#0a0f1d] overflow-hidden select-none flex flex-col justify-between shadow-2xl"
    >
      {/* ── Top Canvas HUD: Interactive Breadcrumbs & Stats ───────── */}
      <div className="absolute top-4 left-4 z-20 flex flex-wrap items-center gap-1.5 bg-[#0f172a]/90 backdrop-blur-md px-3 py-2 rounded-lg border border-slate-700/60 shadow-lg max-w-[calc(100%-120px)]">
        <button
          onClick={(e) => handleBreadcrumbClick(e, packRoot)}
          className={`font-mono text-small px-2 py-0.5 rounded transition-colors ${
            currentFocus.data.level === "root"
              ? "text-signal font-bold bg-signal/15"
              : "text-slate-400 hover:text-white hover:bg-slate-800"
          }`}
        >
          All Sectors
        </button>

        {breadcrumbs.slice(1).map((crumb, idx) => (
          <React.Fragment key={crumb.data.id}>
            <ChevronRight className="h-3.5 w-3.5 text-slate-500 shrink-0" />
            <button
              onClick={(e) => handleBreadcrumbClick(e, crumb)}
              className={`font-mono text-small px-2 py-0.5 rounded truncate max-w-[150px] transition-colors ${
                idx === breadcrumbs.length - 2
                  ? "text-signal font-bold bg-signal/15"
                  : "text-slate-400 hover:text-white hover:bg-slate-800"
              }`}
            >
              {crumb.data.name}
            </button>
          </React.Fragment>
        ))}

        {currentFocus.data.level !== "root" && (
          <Badge variant="outline" className="font-mono text-micro text-slate-400 border-slate-700 ml-1">
            {currentFocus.children?.length || 0} sub-clusters
          </Badge>
        )}
      </div>

      {/* ── Top Right: Zoom & Reset Controls ─────────────────────── */}
      <div className="absolute top-4 right-4 z-20 flex flex-col gap-1.5 bg-[#0f172a]/90 backdrop-blur-md p-1 rounded-lg border border-slate-700/60 shadow-lg">
        {/* Reset View Button */}
        <Button
          variant="ghost"
          size="sm"
          title="Reset Zoom to All Sectors"
          onClick={handleResetView}
          className="h-8 w-8 p-0 text-slate-300 hover:text-signal hover:bg-slate-800 rounded-md transition-colors"
        >
          <RotateCcw className="h-4 w-4" />
        </Button>

        {/* Zoom In Button */}
        <Button
          variant="ghost"
          size="sm"
          title="Zoom In"
          disabled={!canZoomIn}
          onClick={handleZoomIn}
          className="h-8 w-8 p-0 text-slate-300 hover:text-signal hover:bg-slate-800 disabled:opacity-20 rounded-md transition-colors"
        >
          <ZoomIn className="h-4 w-4" />
        </Button>

        {/* Zoom Out Button */}
        <Button
          variant="ghost"
          size="sm"
          title="Zoom Out One Level"
          disabled={!canZoomOut}
          onClick={handleZoomOut}
          className="h-8 w-8 p-0 text-slate-300 hover:text-signal hover:bg-slate-800 disabled:opacity-20 rounded-md transition-colors"
        >
          <ZoomOut className="h-4 w-4" />
        </Button>
      </div>

      {/* ── SVG Canvas Viewport ───────────────────────────────────── */}
      <div className="relative w-full flex-1 flex items-center justify-center p-2 sm:p-4">
        <svg
          viewBox={`0 0 ${VIEW_SIZE} ${VIEW_SIZE}`}
          className="w-full h-full max-h-[720px] object-contain overflow-visible"
        >
          <defs>
            {/* Glow Filters */}
            <filter id="softGlow" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="8" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <filter id="neonGlow" x="-40%" y="-40%" width="180%" height="180%">
              <feGaussianBlur stdDeviation="12" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <filter id="spotlightGlow" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="6" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>

            {/* Background Grid Pattern */}
            <pattern id="canvasGrid" width="40" height="40" patternUnits="userSpaceOnUse">
              <circle cx="20" cy="20" r="1.2" fill="#334155" opacity="0.35" />
            </pattern>
          </defs>

          {/* Canvas Background Grid */}
          <rect width={VIEW_SIZE} height={VIEW_SIZE} fill="url(#canvasGrid)" rx="16" />

          {/* ═════════════════════════════════════════════════════════════ */}
          {/* LAYER 1: CIRCLE SHAPES & BORDERS                             */}
          {/* ═════════════════════════════════════════════════════════════ */}
          {allNodes.map((node) => {
            const d = node.data;
            if (d.level === "root") return null;

            const { cx, cy, r } = getNodeTransform(node);

            // Bounds check
            if (r < 2 || cx + r < -100 || cx - r > VIEW_SIZE + 100 || cy + r < -100 || cy - r > VIEW_SIZE + 100) {
              return null;
            }

            const isSector = d.level === "sector";
            const isIndustry = d.level === "industry";
            const isTheme = d.level === "theme";
            const palette = getSectorPalette(d.sectorName);

            const isSelected = selectedNodeId === d.id;
            const isHovered = hoveredNode?.data.id === d.id;

            // Search filter state
            const isSearchActive = searchMatchIds !== null;
            const isSearchMatch = searchMatchIds?.has(d.id);
            const opacity = isSearchActive ? (isSearchMatch ? 1 : 0.15) : 1;

            // Compute Fill Color
            let fillColor = "transparent";
            let strokeColor = palette.stroke;
            let strokeWidth = 1.5;
            let filterId: string | undefined = undefined;

            if (isSector) {
              fillColor = palette.fill;
              strokeColor = palette.stroke;
              strokeWidth = 2;
              filterId = isSelected ? "url(#neonGlow)" : "url(#softGlow)";
            } else if (isIndustry) {
              fillColor = palette.innerFill;
              strokeColor = isHovered ? palette.stroke : palette.badgeBorder;
              strokeWidth = isHovered ? 2 : 1.2;
            } else if (isTheme) {
              fillColor = isSelected || isHovered ? palette.leafStroke : palette.leafFill;
              strokeColor = isSelected ? "var(--signal)" : isHovered ? "#ffffff" : palette.leafStroke;
              strokeWidth = isSelected ? 3 : isHovered ? 2 : 1;
              if (isSelected || (isSearchActive && isSearchMatch)) {
                filterId = "url(#spotlightGlow)";
              }
            }

            return (
              <g
                key={`circle-${d.id}`}
                onClick={(e) => handleNodeClick(e, node)}
                onMouseEnter={() => setHoveredNode(node)}
                onMouseLeave={() => setHoveredNode(null)}
                className="cursor-pointer transition-all duration-300"
                style={{
                  opacity,
                  transition: "opacity 0.25s ease-out",
                }}
              >
                <circle
                  cx={cx}
                  cy={cy}
                  r={Math.max(1, r)}
                  fill={fillColor}
                  stroke={strokeColor}
                  strokeWidth={strokeWidth}
                  filter={filterId}
                  style={{
                    transition: "cx 0.5s cubic-bezier(0.16, 1, 0.3, 1), cy 0.5s cubic-bezier(0.16, 1, 0.3, 1), r 0.5s cubic-bezier(0.16, 1, 0.3, 1), fill 0.2s ease, stroke 0.2s ease",
                  }}
                />
              </g>
            );
          })}

          {/* ═════════════════════════════════════════════════════════════ */}
          {/* LAYER 2: CLEAN GATED LABELS & BADGES (NO TEXT COLLISION)     */}
          {/* ═════════════════════════════════════════════════════════════ */}
          {allNodes.map((node) => {
            const d = node.data;
            if (d.level === "root") return null;

            const { cx, cy, r } = getNodeTransform(node);

            // Bounds check
            if (r < 8 || cx + r < -50 || cx - r > VIEW_SIZE + 50 || cy + r < -50 || cy - r > VIEW_SIZE + 50) {
              return null;
            }

            const isSector = d.level === "sector";
            const isIndustry = d.level === "industry";
            const isTheme = d.level === "theme";
            const palette = getSectorPalette(d.sectorName);

            // ── TEXT VISIBILITY RULES (STRICTLY GATED TO PREVENT OVERLAP) ──
            //
            // 1. Sector Labels:
            //    Visible when at Root level OR when this sector is the current focus
            const showSectorLabel = isSector && (currentFocusLevel === "root" || currentFocus.data.id === d.id) && r > 40;

            // 2. Industry Labels:
            //    ONLY visible when zoomed into a Sector OR when this industry is the focus
            const showIndustryLabel = isIndustry && (currentFocusLevel === "sector" || currentFocus.data.id === d.id) && r > 28;

            // 3. Theme Labels:
            //    Visible when zoomed into a Sector (if theme radius > 24px) OR when zoomed into an Industry
            const showThemeLabel = isTheme && (
              (currentFocusLevel === "sector" && r > 24) ||
              (currentFocusLevel === "industry" && r > 16) ||
              (selectedNodeId === d.id && r > 16)
            );

            const showTickers = isTheme && (
              (currentFocusLevel === "industry" && r > 36) ||
              (currentFocusLevel === "sector" && r > 46)
            ) && d.tickers && d.tickers.length > 0;

            return (
              <g key={`label-${d.id}`} className="pointer-events-none select-none">
                {/* ── SECTOR LABEL BADGE ─────────────────────────────────── */}
                {showSectorLabel && (
                  <g
                    transform={`translate(${cx}, ${cy - r + 26})`}
                    className="transition-transform duration-500"
                  >
                    <rect
                      x={-Math.min(110, d.name.length * 6 + 18)}
                      y={-13}
                      width={Math.min(220, d.name.length * 12 + 36)}
                      height={26}
                      rx={13}
                      fill="#0f172a"
                      stroke={palette.stroke}
                      strokeWidth={1.5}
                      fillOpacity={0.96}
                    />
                    <text
                      textAnchor="middle"
                      dominantBaseline="central"
                      className="font-display font-bold text-micro uppercase tracking-wider"
                      fill={palette.stroke}
                      style={{ fontSize: "11px", fontWeight: 700 }}
                    >
                      {d.name}
                    </text>
                  </g>
                )}

                {/* ── INDUSTRY LABEL BADGE ───────────────────────────────── */}
                {showIndustryLabel && (
                  <g
                    transform={`translate(${cx}, ${cy - r + (r > 60 ? 20 : 14)})`}
                    className="transition-transform duration-500"
                  >
                    <rect
                      x={-Math.min(90, d.name.length * 4.5 + 14)}
                      y={-10}
                      width={Math.min(180, d.name.length * 9 + 28)}
                      height={20}
                      rx={10}
                      fill="#1e293b"
                      stroke={palette.stroke}
                      strokeWidth={1}
                      fillOpacity={0.92}
                    />
                    <text
                      textAnchor="middle"
                      dominantBaseline="central"
                      className="font-display font-semibold"
                      fill="#f8fafc"
                      style={{ fontSize: `${Math.max(10, Math.min(12, r * 0.16))}px` }}
                    >
                      {d.name.length > 22 && r < 70 ? `${d.name.slice(0, 20)}…` : d.name}
                    </text>
                  </g>
                )}

                {/* ── THEME LABEL & TICKERS ──────────────────────────────── */}
                {showThemeLabel && (
                  <g
                    transform={`translate(${cx}, ${cy})`}
                    className="text-center transition-transform duration-500"
                  >
                    <text
                      textAnchor="middle"
                      dominantBaseline={showTickers ? "alphabetic" : "central"}
                      y={showTickers ? -6 : 0}
                      className="font-display font-semibold"
                      fill="#ffffff"
                      style={{
                        fontSize: `${Math.max(9.5, Math.min(14, r * 0.28))}px`,
                        textShadow: "0 2px 4px rgba(0,0,0,0.8)",
                      }}
                    >
                      {d.name.length > 18 && r < 45 ? `${d.name.slice(0, 16)}…` : d.name}
                    </text>

                    {/* Stock Ticker Tags floating inside Theme Bubble */}
                    {showTickers && (
                      <g transform="translate(0, 12)">
                        {d.tickers!.slice(0, 2).map((tk, idx, arr) => {
                          const spacing = arr.length === 1 ? 0 : idx === 0 ? -22 : 22;
                          return (
                            <g key={tk.ticker} transform={`translate(${spacing}, 0)`}>
                              <rect
                                x={-18}
                                y={-8}
                                width={36}
                                height={16}
                                rx={4}
                                fill="#0f172a"
                                stroke="var(--signal)"
                                strokeWidth={1}
                              />
                              <text
                                textAnchor="middle"
                                dominantBaseline="central"
                                className="font-mono font-bold text-micro"
                                fill="var(--signal)"
                                style={{ fontSize: "9px" }}
                              >
                                ${tk.ticker}
                              </text>
                            </g>
                          );
                        })}
                      </g>
                    )}
                  </g>
                )}
              </g>
            );
          })}
        </svg>
      </div>

      {/* ── Bottom HUD Bar: Instructions & Quick Ticker Stats ─────── */}
      <div className="px-4 py-2.5 border-t border-slate-800 bg-[#0f172a]/90 backdrop-blur-md flex items-center justify-between text-micro text-slate-400">
        <div className="flex items-center gap-2">
          <Sparkles className="h-3.5 w-3.5 text-signal" />
          <span>Click a sector bubble to drill down · Click themes to inspect tickers</span>
        </div>
        {hoveredNode && hoveredNode.data.level !== "root" && (
          <div className="font-mono text-slate-300 truncate max-w-[320px]">
            <span className="text-signal font-semibold">{hoveredNode.data.name}</span>
            {hoveredNode.data.tickers && hoveredNode.data.tickers.length > 0 && (
              <span className="text-slate-400 ml-1.5">
                (${hoveredNode.data.tickers.map((t) => t.ticker).join(", $")})
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
