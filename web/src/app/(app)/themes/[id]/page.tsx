"use client";

import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { PageHeader } from "@/components/PageHeader";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { SentimentBadge } from "@/components/SentimentBadge";
import { EmptyState } from "@/components/EmptyState";
import { ErrorState } from "@/components/ErrorState";
import { DetailSkeleton } from "@/components/skeletons/LayoutSkeletons";
import { useTheme } from "@/lib/hooks";

export default function ThemePage() {
  const params = useParams();
  const id = params.id as string;

  const { data, isLoading } = useTheme(id);

  if (isLoading) {
    return <DetailSkeleton />;
  }

  if (!data || !data.theme) {
    return (
      <div className="p-8">
        <ErrorState title="Theme Not Found" message={`No theme details found for ID: ${id}`} />
      </div>
    );
  }

  const { theme, mapped_tickers, videos } = data;

  return (
    <div className="flex flex-col gap-6 pb-12">
      <div className="mb-2 flex gap-2 flex-col items-start">
        <Breadcrumbs
          items={[
            { label: "Themes", href: "/themes" },
            { label: theme.name },
          ]}
        />
        <div className="flex items-center gap-3 mb-1">
          <Badge variant="outline" className="font-mono text-micro uppercase tracking-wider text-ink-secondary rounded-sm">
            {theme.level}
          </Badge>
        </div>
        <PageHeader
          title={theme.name}
          description={theme.description || undefined}
        />
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <div className="md:col-span-2 flex flex-col gap-6">
          <Card className="rounded-md border-line bg-panel overflow-hidden">
            <CardHeader className="bg-panel-raised border-b border-line py-3.5 px-4">
              <CardTitle className="text-title font-semibold text-ink">Videos Discussing This Theme</CardTitle>
            </CardHeader>
            <CardContent className="p-4">
              <div className="grid gap-3">
                {videos?.map((v) => (
                  <div key={v.id} className="flex flex-col gap-2 rounded-md border border-line p-4 bg-panel hover:border-signal/40 transition-colors">
                    <div className="flex justify-between items-start">
                      <Link href={`/videos/${v.id}`} className="font-medium text-ink hover:text-signal hover:underline">
                        {v.title}
                      </Link>
                    </div>
                    <p className="mt-1 border-l-2 border-signal pl-3 text-small italic text-ink-secondary">
                      &quot;{v.mention_text}&quot;
                    </p>
                    <div className="mt-2 flex items-center justify-between">
                      <span className="font-mono text-micro tabular-nums text-ink-faint">
                        Published: {new Date(v.published_at).toLocaleDateString()}
                      </span>
                      <SentimentBadge direction={v.sentiment} />
                    </div>
                  </div>
                ))}
                {(!videos || videos.length === 0) && (
                  <EmptyState title="No videos found" description="No processed videos have mentioned this theme yet." />
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="flex flex-col gap-6">
          <Card className="rounded-md border-line bg-panel overflow-hidden">
            <CardHeader className="bg-panel-raised border-b border-line py-3.5 px-4">
              <CardTitle className="text-title font-semibold text-ink">Mapped Tickers</CardTitle>
              <CardDescription className="text-micro text-ink-secondary">Stocks directly associated with this theme</CardDescription>
            </CardHeader>
            <CardContent className="p-4 flex flex-col gap-3">
              {mapped_tickers?.map((t) => (
                <div key={t.ticker} className="flex items-center justify-between border-b border-line pb-2.5 last:border-0 last:pb-0">
                  <div className="flex flex-col">
                    <Link href={`/tickers/${t.ticker}`} className="font-mono font-semibold text-ink hover:text-signal hover:underline">
                      {t.ticker}
                    </Link>
                    <span className="text-micro capitalize text-ink-secondary">
                      Source: {t.source}
                    </span>
                  </div>
                  <Badge variant="outline" className="font-mono text-micro tabular-nums rounded-sm">
                    Score: {(t.relevance_score * 100).toFixed(0)}%
                  </Badge>
                </div>
              ))}
              {(!mapped_tickers || mapped_tickers.length === 0) && (
                <p className="text-small text-ink-secondary">No tickers mapped to this theme.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
