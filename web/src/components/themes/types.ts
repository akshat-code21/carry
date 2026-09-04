import { SectorThemeNode, SubThemeNode, ThemeTickerInfo } from "@/lib/api";

export type HierarchyLevel = "root" | "sector" | "industry" | "theme";

export interface PackedThemeDatum {
  id: string;
  name: string;
  level: HierarchyLevel;
  description?: string | null;
  tickers?: ThemeTickerInfo[];
  children?: PackedThemeDatum[];
  value?: number;
  sectorName?: string;
  industryName?: string;
  sectorId?: string;
  industryId?: string;
  childCount?: number;
}

export interface SelectedNodeInfo {
  id: string;
  name: string;
  level: HierarchyLevel;
  description?: string | null;
  sectorName?: string;
  sectorId?: string;
  industryName?: string;
  industryId?: string;
  tickers?: ThemeTickerInfo[];
  subThemesCount?: number;
  industriesCount?: number;
  childThemes?: SubThemeNode[];
}

/**
 * Builds the D3 Hierarchy tree from backend SectorThemeNode[]
 */
export function buildHierarchyTree(sectors: SectorThemeNode[]): PackedThemeDatum {
  const cleanSectors = sectors.filter((s) => s.level === "sector");

  const sectorChildren: PackedThemeDatum[] = cleanSectors.map((sector) => {
    const industries = sector.industries || [];
    const industryChildren: PackedThemeDatum[] = industries.map((industry) => {
      const themes = industry.themes || [];
      const themeChildren: PackedThemeDatum[] = themes.map((theme) => {
        const tickerCount = theme.tickers?.length || 0;
        return {
          id: theme.id,
          name: theme.name,
          level: "theme",
          description: theme.description,
          tickers: theme.tickers || [],
          sectorName: sector.name,
          sectorId: sector.id,
          industryName: industry.name,
          industryId: industry.id,
          value: Math.max(1, tickerCount + 1), // weight node by ticker density
        };
      });

      // If industry has no sub-themes, provide a leaf fallback so it renders as a bubble
      if (themeChildren.length === 0) {
        return {
          id: industry.id,
          name: industry.name,
          level: "industry",
          description: industry.description,
          sectorName: sector.name,
          sectorId: sector.id,
          industryName: industry.name,
          industryId: industry.id,
          childCount: 0,
          value: 1,
        };
      }

      return {
        id: industry.id,
        name: industry.name,
        level: "industry",
        description: industry.description,
        sectorName: sector.name,
        sectorId: sector.id,
        industryName: industry.name,
        industryId: industry.id,
        childCount: themes.length,
        children: themeChildren,
      };
    });

    // If sector has no industries, provide a leaf fallback
    if (industryChildren.length === 0) {
      return {
        id: sector.id,
        name: sector.name,
        level: "sector",
        description: sector.description,
        sectorName: sector.name,
        sectorId: sector.id,
        childCount: 0,
        value: 2,
      };
    }

    return {
      id: sector.id,
      name: sector.name,
      level: "sector",
      description: sector.description,
      sectorName: sector.name,
      sectorId: sector.id,
      childCount: industries.length,
      children: industryChildren,
    };
  });

  return {
    id: "root",
    name: "Market Taxonomy",
    level: "root",
    children: sectorChildren,
  };
}
