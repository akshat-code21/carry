"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SectorThemeNode } from "@/lib/api";
import { ChevronDown, ChevronUp, Sparkles, ArrowUpRight } from "lucide-react";
import { Button } from "@/components/ui/button";

interface NarrativesSectionProps {
  narratives: SectorThemeNode[];
}

export function NarrativesSection({ narratives }: NarrativesSectionProps) {
  const [isExpanded, setIsExpanded] = useState<boolean>(true);

  if (narratives.length === 0) return null;

  return (
    <div className="rounded-xl border border-line bg-panel overflow-hidden">
      <div className="p-4 bg-panel-raised flex items-center justify-between border-b border-line">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-md bg-signal/10 border border-signal/20 text-signal">
            <Sparkles className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-display text-title font-semibold text-ink">Extracted Narratives</h3>
              <Badge variant="outline" className="font-mono text-micro text-signal border-signal/30">
                {narratives.length} Active
              </Badge>
            </div>
            <p className="text-micro text-ink-secondary mt-0.5">
              Macro trends and qualitative market chatter extracted from video commentary.
            </p>
          </div>
        </div>

        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsExpanded(!isExpanded)}
          className="h-8 px-2 text-ink-secondary hover:text-ink"
        >
          {isExpanded ? (
            <>
              <span className="text-micro font-mono mr-1">Collapse</span>
              <ChevronUp className="h-4 w-4" />
            </>
          ) : (
            <>
              <span className="text-micro font-mono mr-1">Expand</span>
              <ChevronDown className="h-4 w-4" />
            </>
          )}
        </Button>
      </div>

      {isExpanded && (
        <div className="p-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {narratives.map((n) => (
            <Link key={n.id} href={`/themes/${n.id}`}>
              <Card className="h-full border-line hover:border-signal/50 bg-panel-raised/30 hover:bg-panel-raised transition-all group cursor-pointer">
                <CardHeader className="p-4">
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="line-clamp-2 text-title font-semibold text-ink group-hover:text-signal transition-colors">
                      {n.name}
                    </CardTitle>
                    <ArrowUpRight className="h-4 w-4 text-ink-faint group-hover:text-signal transition-colors shrink-0 mt-0.5" />
                  </div>
                  {n.description && (
                    <CardDescription className="mt-2 line-clamp-3 text-small text-ink-secondary leading-relaxed">
                      {n.description}
                    </CardDescription>
                  )}
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
