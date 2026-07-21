"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";

export default function ThemesPage() {
  const [themes, setThemes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const res = await api.getThemes();
        setThemes(res);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // Group themes by sector
  const sectors = themes.filter((t) => t.level === "sector");

  return (
    <div className="flex flex-col gap-6 pb-10">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Theme Explorer</h1>
        <p className="text-muted-foreground">Browse the hierarchical taxonomy of financial themes and narratives.</p>
      </div>

      <div className="grid gap-6">
        {sectors.map((sector: any) => {
          const industries = themes.filter((t) => t.parent_id === sector.id);
          return (
            <Card key={sector.id} className="overflow-hidden">
              <CardHeader className="bg-muted/50 pb-4">
                <CardTitle className="text-2xl">{sector.name}</CardTitle>
              </CardHeader>
              <CardContent className="pt-6 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {industries.map((industry: any) => {
                  const industryThemes = themes.filter((t) => t.parent_id === industry.id);
                  return (
                    <div key={industry.id} className="flex flex-col gap-3">
                      <h3 className="font-semibold text-lg border-b pb-1">{industry.name}</h3>
                      <div className="flex flex-col gap-2">
                        {industryThemes.map((theme: any) => (
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

      <div className="mt-8">
        <h2 className="text-2xl font-bold mb-4">Extracted Narratives</h2>
        <Card>
          <CardContent className="pt-6 grid gap-4 md:grid-cols-2">
            {themes
              .filter((t) => t.level === "narrative")
              .map((n: any) => (
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
    </div>
  );
}
