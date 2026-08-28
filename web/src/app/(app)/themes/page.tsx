"use client";

import React, { useState, useMemo, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Fragment } from "react";
import React, { useState, useMemo, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Hash } from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/PageHeader";
import { EmptyState } from "@/components/EmptyState";
import { DashboardSkeleton } from "@/components/skeletons/LayoutSkeletons";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useThemes } from "@/lib/hooks";
import { ThemeCirclePack } from "@/components/themes/ThemeCirclePack";
import { ThemeInspector } from "@/components/themes/ThemeInspector";
import { ThemeControls, ViewMode } from "@/components/themes/ThemeControls";
import { ThemeGridView } from "@/components/themes/ThemeGridView";
import { NarrativesSection } from "@/components/themes/NarrativesSection";
import { buildHierarchyTree, SelectedNodeInfo } from "@/components/themes/types";

export default function ThemesPage() {
  const router = useRouter();
  const { data: themes = [], isLoading } = useThemes();

  const [searchQuery, setSearchQuery] = useState<string>("");
  const [viewMode, setViewMode] = useState<ViewMode>("circle-pack");
  const [selectedNode, setSelectedNode] = useState<SelectedNodeInfo | null>(null);
  const [selectedSectorId, setSelectedSectorId] = useState<string | null>(null);

  const sectors = useMemo(() => themes.filter((t) => t.level === "sector"), [themes]);
  const narratives = useMemo(() => themes.filter((t) => t.level === "narrative"), [themes]);

  // Build the D3 packed hierarchy tree from sector nodes
  const hierarchyData = useMemo(() => buildHierarchyTree(sectors), [sectors]);

  // Aggregate stats
  const stats = useMemo(() => {
    const totalSectors = sectors.length;
    const totalIndustries = sectors.reduce((acc, s) => acc + (s.industries?.length || 0), 0);
    const totalThemes = sectors.reduce(
      (acc, s) =>
        acc +
        (s.industries || []).reduce((iAcc, ind) => iAcc + (ind.themes?.length || 0), 0),
      0
    );
    return { totalSectors, totalIndustries, totalThemes };
  }, [sectors]);

  const handleSelectSector = useCallback((sectorId: string | null) => {
    setSelectedSectorId(sectorId);
    if (sectorId) {
      const sector = sectors.find((s) => s.id === sectorId);
      if (sector) {
        setSelectedNode({
          id: sector.id,
          name: sector.name,
          level: "sector",
          description: sector.description,
          sectorName: sector.name,
          sectorId: sector.id,
          industriesCount: sector.industries?.length || 0,
          subThemesCount: (sector.industries || []).reduce(
            (acc, ind) => acc + (ind.themes?.length || 0),
            0
          ),
        });
      }
    } else {
      setSelectedNode(null);
    }
  }, [sectors]);

  const handleSelectThemeById = useCallback((themeId: string) => {
    for (const s of sectors) {
      for (const ind of s.industries || []) {
        for (const th of ind.themes || []) {
          if (th.id === themeId) {
            setSelectedNode({
              id: th.id,
              name: th.name,
              level: "theme",
              description: th.description,
              sectorName: s.name,
              sectorId: s.id,
              industryName: ind.name,
              industryId: ind.id,
              tickers: th.tickers,
            });
            return;
          }
        }
      }
    }
  }, [sectors]);

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="flex flex-col gap-6 pb-12">
      <PageHeader
        title="Theme Explorer"
        description="Interactive circular taxonomy of market sectors, emerging industries, and stock themes."
      />

      {themes.length === 0 ? (
        <EmptyState
          icon={<Hash className="h-6 w-6" />}
          title="No themes extracted yet"
          description="Themes will appear here as videos are processed."
        />
      ) : (
        <>
          {/* Controls: Search, Sector Filter Pills, View Switcher */}
          <ThemeControls
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            viewMode={viewMode}
            onViewModeChange={setViewMode}
            sectors={sectors}
            selectedSectorId={selectedSectorId}
            onSelectSector={handleSelectSector}
          />

          {/* Main Visualizer Area */}
          {viewMode === "circle-pack" ? (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
              {/* Left/Center: Zoomable Circle Packing Canvas */}
              <div className="lg:col-span-8 xl:col-span-8 flex flex-col">
                <ThemeCirclePack
                  data={hierarchyData}
                  searchQuery={searchQuery}
                  selectedNodeId={selectedNode?.id}
                  onSelectNode={(node) => {
                    setSelectedNode(node);
                    if (!node) {
                      setSelectedSectorId(null);
                    } else if (node.level === "sector") {
                      setSelectedSectorId(node.id);
                    }
                  }}
                  onNavigateToTheme={(themeId) => router.push(`/themes/${themeId}`)}
                />
              </div>

              {/* Right: Interactive Inspector HUD */}
              <div className="lg:col-span-4 xl:col-span-4 h-full min-h-[480px]">
                <ThemeInspector
                  selectedNode={selectedNode}
                  onClose={() => {
                    setSelectedNode(null);
                    setSelectedSectorId(null);
                  }}
                  onZoomToNode={(nodeId) => {
                    handleSelectSector(nodeId);
                  }}
                  onSelectThemeById={handleSelectThemeById}
                  stats={stats}
                />
              </div>
            </div>
          ) : (
            /* Alternate Structured Card Grid View */
            <ThemeGridView
              sectors={sectors}
              searchQuery={searchQuery}
              selectedSectorId={selectedSectorId}
            />
          )}

          {/* Extracted Macro Narratives Section */}
          <NarrativesSection narratives={narratives} />
        </>
      )}
    </div>
  );
}
