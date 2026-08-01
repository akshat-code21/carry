"use client";

import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";
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
    <div className="flex flex-col gap-6 pb-10">
      <div>
        <Breadcrumbs
          items={[
            { label: "Themes", href: "/themes" },
            { label: theme.name },
          ]}
        />
        <div className="flex items-center gap-3 mb-2">
          <Badge variant="outline" className="uppercase tracking-widest">{theme.level}</Badge>
        </div>
        <PageHeader
          title={theme.name}
          description={theme.description}
        />
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <div className="md:col-span-2 flex flex-col gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-semibold">Videos Discussing This Theme</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4">
                {videos?.map((v) => (
                  <div key={v.id} className="flex flex-col gap-2 rounded-lg border p-4">
                    <div className="flex justify-between items-start">
                      <Link href={`/videos/${v.id}`} className="font-semibold hover:underline text-lg">
                        {v.title}
                      </Link>
                    </div>
                    <p className="text-sm border-l-2 border-primary pl-4 italic text-muted-foreground mt-2">
                      &quot;{v.mention_text}&quot;
                    </p>
                    <div className="flex items-center justify-between mt-2">
                      <span className="text-xs text-muted-foreground font-mono">
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
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-semibold">Mapped Tickers</CardTitle>
              <CardDescription>Stocks directly associated with this theme</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              {mapped_tickers?.map((t) => (
                <div key={t.ticker} className="flex items-center justify-between border-b pb-2 last:border-0 last:pb-0">
                  <div className="flex flex-col">
                    <Link href={`/tickers/${t.ticker}`} className="font-bold hover:underline">
                      ${t.ticker}
                    </Link>
                    <span className="text-xs text-muted-foreground capitalize">
                      Source: {t.source}
                    </span>
                  </div>
                  <Badge variant="outline" className="font-mono">
                    Score: {(t.relevance_score * 100).toFixed(0)}
                  </Badge>
                </div>
              ))}
              {(!mapped_tickers || mapped_tickers.length === 0) && (
                <p className="text-sm text-muted-foreground">No tickers mapped to this theme.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
