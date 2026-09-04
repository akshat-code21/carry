"use client";

import { Fragment } from "react";
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
          <div className="overflow-hidden rounded-lg border border-line bg-panel">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead className="w-[45%]">Name</TableHead>
                  <TableHead className="w-24">Level</TableHead>
                  <TableHead className="w-[35%]">Description</TableHead>
                  <TableHead className="text-right">Themes</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sectors.map((sector) => {
                  const industries = sector.industries || [];
                  const totalThemesInSector = industries.reduce((acc, ind) => acc + (ind.themes?.length || 0), 0);

                  return (
                    <Fragment key={sector.id}>
                      <TableRow className="bg-panel-raised/60">
                        <TableCell className="font-medium text-ink">{sector.name}</TableCell>
                        <TableCell>
                          <span className="font-mono text-micro uppercase tracking-wider text-ink-faint">
                            SECTOR
                          </span>
                        </TableCell>
                        <TableCell className="max-w-0 truncate text-caption text-ink-secondary">
                          {sector.description || "—"}
                        </TableCell>
                        <TableCell className="text-right numeric text-caption text-ink-faint">
                          {totalThemesInSector}
                        </TableCell>
                      </TableRow>
                      {industries.map((industry) => {
                        const industryThemes = industry.themes || [];
                        return (
                          <Fragment key={industry.id}>
                            <TableRow>
                              <TableCell className="pl-8 text-small text-ink">
                                {industry.name}
                              </TableCell>
                              <TableCell>
                                <span className="font-mono text-micro uppercase tracking-wider text-ink-faint">
                                  INDUSTRY
                                </span>
                              </TableCell>
                              <TableCell className="text-caption text-ink-faint">—</TableCell>
                              <TableCell className="text-right numeric text-caption text-ink-faint">
                                {industryThemes.length}
                              </TableCell>
                            </TableRow>
                            {(industryThemes.length === 0 ? [] : industryThemes).map((theme) => (
                              <TableRow key={theme.id} className="group/row">
                                <TableCell className="pl-12">
                                  <Link
                                    href={`/themes/${theme.id}`}
                                    className="text-small text-ink-secondary group-hover/row:text-signal hover:text-signal hover:underline"
                                  >
                                    {theme.name}
                                  </Link>
                                </TableCell>
                                <TableCell>
                                  <span className="font-mono text-micro uppercase tracking-wider text-signal">
                                    THEME
                                  </span>
                                </TableCell>
                                <TableCell className="max-w-0 truncate text-caption text-ink-faint">
                                  {theme.description || "—"}
                                </TableCell>
                                <TableCell className="text-right">
                                  {theme.tickers && theme.tickers.length > 0 ? (
                                    <span className="numeric font-mono text-caption text-signal">
                                      {theme.tickers.map((tk) => `$${tk.ticker}`).join(" ")}
                                    </span>
                                  ) : (
                                    <span className="text-ink-faint">—</span>
                                  )}
                                </TableCell>
                              </TableRow>
                            ))}
                          </Fragment>
                        );
                      })}
                    </Fragment>
                  );
                })}
              </TableBody>
            </Table>
          </div>

          {narratives.length > 0 && (
            <div className="mt-2">
              <h2 className="mb-3 font-mono text-micro font-semibold uppercase tracking-widest text-ink-faint">
                Extracted Narratives
              </h2>
              <div className="overflow-hidden rounded-lg border border-line bg-panel">
                <Table>
                  <TableBody>
                    {narratives.map((n) => (
                      <TableRow key={n.id} className="group/row">
                        <TableCell className="w-[35%]">
                          <Link
                            href={`/themes/${n.id}`}
                            className="text-small font-medium text-signal hover:underline"
                          >
                            {n.name}
                          </Link>
                        </TableCell>
                        <TableCell className="max-w-0 truncate text-caption text-ink-secondary">
                          {n.description || "—"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

