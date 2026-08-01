"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Loader2, Hash } from "lucide-react";
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
              const industries = themes.filter((t) => t.parent_id === sector.id);
              return (
                <Card key={sector.id} className="overflow-hidden">
                  <CardHeader className="bg-muted/50 pb-4">
                    <CardTitle className="text-2xl">{sector.name}</CardTitle>
                  </CardHeader>
                  <CardContent className="pt-6 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                    {industries.map((industry) => {
                      const industryThemes = themes.filter((t) => t.parent_id === industry.id);
                      return (
                        <div key={industry.id} className="flex flex-col gap-3">
                          <h3 className="font-semibold text-lg border-b pb-1">{industry.name}</h3>
                          <div className="flex flex-col gap-2">
                            {industryThemes.map((theme) => (
                              <Link key={theme.id} href={`/themes/${theme.id}`}>
                                <Badge variant="outline" className="w-full justify-start hover:bg-muted py-1.5 transition-colors text-sm">
                                  {theme.name}
                                </Badge>
                              </Link>
                            ))}
                          </div>
                        </div>
                      );
                    })}
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {narratives.length > 0 && (
            <div className="mt-8">
              <h2 className="text-2xl font-bold mb-4">Extracted Narratives</h2>
              <Card>
                <CardContent className="pt-6 grid gap-4 md:grid-cols-2">
                  {narratives.map((n) => (
                    <Link key={n.id} href={`/themes/${n.id}`}>
                      <Card className="hover:border-primary transition-colors h-full">
                        <CardHeader className="p-4">
                          <CardTitle className="text-base line-clamp-2">{n.name}</CardTitle>
                          <CardDescription className="line-clamp-2 mt-1">{n.description}</CardDescription>
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
