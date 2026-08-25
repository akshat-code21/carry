"use client";

import { useState, useMemo, Fragment } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  api,
  type HfiInvestor,
  type HfiPortfolioChange,
  type HfiContentItem,
  type HfiSource,
  type HfiReportListItem,
  type HfiAlert,
} from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { EmptyState } from "@/components/EmptyState";
import { DetailSkeleton } from "@/components/skeletons/LayoutSkeletons";
import {
  RefreshCw,
  FileText,
  Clock,
  TrendingUp,
  TrendingDown,
  Minus,
  Plus,
  X,
  GitCompareArrows,
  Globe,
  Tv,
  Rss,
  Link as LinkIcon,
  Trash2,
  ExternalLink,
  Loader2,
  AlertTriangle,
  Check,
  ChevronDown,
  ChevronUp,
  LayoutList,
  Grid3X3,
  Search,
} from "lucide-react";

function formatUsd(val: number | null | undefined): string {
  if (val == null || val === 0) return "—";
  if (val >= 1_000_000_000) return `$${(val / 1_000_000_000).toFixed(2)}B`;
  if (val >= 1_000_000) return `$${(val / 1_000_000).toFixed(2)}M`;
  if (val >= 1_000) return `$${(val / 1_000).toFixed(1)}K`;
  return `$${val.toLocaleString()}`;
}

function formatPercent(val: number | null | undefined): string {
  if (val == null) return "—";
  return `${Number(val).toFixed(2)}%`;
}

const changeConfig: Record<string, { label: string; icon: React.ElementType; color: string }> = {
  new_position: { label: "New", icon: Plus, color: "bg-green-500/20 text-green-400 border-green-500/30" },
  increased: { label: "Increased", icon: TrendingUp, color: "bg-blue-500/20 text-blue-400 border-blue-500/30" },
  decreased: { label: "Decreased", icon: TrendingDown, color: "bg-orange-500/20 text-orange-400 border-orange-500/30" },
  closed: { label: "Closed", icon: X, color: "bg-red-500/20 text-red-400 border-red-500/30" },
  unchanged: { label: "Unchanged", icon: Minus, color: "bg-zinc-500/20 text-zinc-400 border-zinc-500/30" },
};

const sourceIcons: Record<string, React.ElementType> = {
  website: Globe,
  youtube: Tv,
  rss: Rss,
  sec_13f: FileText,
  custom: LinkIcon,
};

export default function InvestorDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<"holdings" | "content" | "sources" | "reports" | "alerts">("holdings");
  const [selectedReport, setSelectedReport] = useState<string | null>(null);
  const [holdingsView, setHoldingsView] = useState<"breakdown" | "matrix">("breakdown");
  const [selectedQuarter, setSelectedQuarter] = useState<string>("all");
  const [holdingsSearch, setHoldingsSearch] = useState<string>("");

  // Queries
  const { data: investor, isLoading: loadingInvestor } = useQuery({
    queryKey: ["hfi-investor", id],
    queryFn: () => api.getHfiInvestor(id),
    enabled: !!id,
  });

  const { data: stats } = useQuery({
    queryKey: ["hfi-investor-stats", id],
    queryFn: () => api.getHfiInvestorStats(id),
    enabled: !!id,
  });

  const { data: portfolioChanges = [], isLoading: loadingPortfolio } = useQuery({
    queryKey: ["hfi-portfolio", id],
    queryFn: () => api.getHfiPortfolio(id),
    enabled: !!id,
  });

  const { data: contentItems = [], isLoading: loadingContent } = useQuery({
    queryKey: ["hfi-content", id],
    queryFn: () => api.getHfiInvestorContent(id),
    enabled: !!id,
  });

  const { data: sources = [], isLoading: loadingSources } = useQuery({
    queryKey: ["hfi-sources", id],
    queryFn: () => api.getHfiInvestorSources(id),
    enabled: !!id,
  });

  const { data: reports = [], isLoading: loadingReports } = useQuery({
    queryKey: ["hfi-reports", id],
    queryFn: () => api.getHfiReports(id),
    enabled: !!id,
  });

  const { data: alertsData, isLoading: loadingAlerts } = useQuery({
    queryKey: ["hfi-alerts", id],
    queryFn: () => api.getHfiAlerts({ investor_id: id }),
    enabled: !!id,
  });

  // Mutations
  const syncMutation = useMutation({
    mutationFn: () => api.syncHfiInvestor(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hfi-investor", id] });
      queryClient.invalidateQueries({ queryKey: ["hfi-investor-stats", id] });
      queryClient.invalidateQueries({ queryKey: ["hfi-content", id] });
      queryClient.invalidateQueries({ queryKey: ["hfi-portfolio", id] });
    },
  });

  const generateReportMutation = useMutation({
    mutationFn: () => api.generateHfiReport(id),
    onSuccess: (report) => {
      queryClient.invalidateQueries({ queryKey: ["hfi-reports", id] });
      queryClient.invalidateQueries({ queryKey: ["hfi-investor-stats", id] });
      setSelectedReport(report.id);
      setActiveTab("reports");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => api.deleteHfiInvestor(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hfi-investors"] });
      router.push("/investors");
    },
  });

  // Group portfolio changes by filing period
  const portfolioByPeriod = useMemo(() => {
    return (portfolioChanges ?? []).reduce<Record<string, HfiPortfolioChange[]>>((acc, pc) => {
      (acc[pc.filing_period] ||= []).push(pc);
      return acc;
    }, {});
  }, [portfolioChanges]);

  const periods = useMemo(() => {
    return Object.keys(portfolioByPeriod).sort().reverse();
  }, [portfolioByPeriod]);

  const displayedPeriods = useMemo(() => {
    if (selectedQuarter === "all") return periods;
    return periods.filter((p) => p === selectedQuarter);
  }, [periods, selectedQuarter]);

  const matrixHoldings = useMemo(() => {
    if (!portfolioChanges.length) return [];
    const holdingsMap: Record<
      string,
      {
        key: string;
        company_name: string;
        ticker_symbol: string;
        changesByPeriod: Record<string, HfiPortfolioChange>;
        latestValue: number;
        latestPercent: number;
      }
    > = {};

    portfolioChanges.forEach((pc) => {
      const key = pc.ticker_symbol || pc.cusip || pc.company_name || "UNKNOWN";
      if (!holdingsMap[key]) {
        holdingsMap[key] = {
          key,
          company_name: pc.company_name || "—",
          ticker_symbol: pc.ticker_symbol || "—",
          changesByPeriod: {},
          latestValue: 0,
          latestPercent: 0,
        };
      }
      holdingsMap[key].changesByPeriod[pc.filing_period] = pc;
    });

    return Object.values(holdingsMap)
      .map((h) => {
        for (const p of periods) {
          if (h.changesByPeriod[p]) {
            h.latestValue = h.changesByPeriod[p].value_usd ?? 0;
            h.latestPercent = h.changesByPeriod[p].percent_of_portfolio ?? 0;
            break;
          }
        }
        return h;
      })
      .sort(
        (a, b) =>
          b.latestPercent - a.latestPercent ||
          b.latestValue - a.latestValue ||
          a.company_name.localeCompare(b.company_name)
      );
  }, [portfolioChanges, periods]);

  if (loadingInvestor) {
    return <DetailSkeleton />;
  }

  if (!investor) {
    return (
      <EmptyState
        title="Investor not found"
        description={`No investor record found with ID ${id}`}
      />
    );
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Breadcrumbs & Header */}
      <Breadcrumbs
        items={[
          { label: "Investors", href: "/investors" },
          { label: investor.name },
        ]}
      />

      <PageHeader
        title={investor.name}
        description={investor.description || (investor.cik_number ? `CIK: ${investor.cik_number}` : "Tracked hedge fund manager")}
      >
        <div className="flex items-center gap-2 flex-wrap">
          <Link href={`/compare`}>
            <Button variant="outline" size="sm" className="gap-1.5 border-line text-ink-secondary hover:text-ink">
              <GitCompareArrows className="h-4 w-4" /> Compare
            </Button>
          </Link>
          <Button
            variant="outline"
            size="sm"
            onClick={() => generateReportMutation.mutate()}
            disabled={generateReportMutation.isPending}
            className="gap-1.5 border-line text-ink-secondary hover:text-ink"
          >
            {generateReportMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin text-signal" />
            ) : (
              <FileText className="h-4 w-4" />
            )}
            {generateReportMutation.isPending ? "Generating…" : "Generate Report"}
          </Button>
          <Button
            variant="default"
            size="sm"
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending}
            className="gap-1.5 bg-signal text-black hover:bg-signal/90 font-medium"
          >
            {syncMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            {syncMutation.isPending ? "Syncing…" : "Sync Filings"}
          </Button>
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={() => {
              if (confirm(`Delete "${investor.name}"? This cannot be undone.`)) {
                deleteMutation.mutate();
              }
            }}
            className="text-ink-faint hover:text-red-400"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </PageHeader>

      {/* Metric Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="border-line bg-canvas">
          <CardContent className="p-4">
            <p className="text-micro uppercase tracking-wider text-ink-faint">Filing Periods</p>
            <p className="font-mono text-2xl font-bold text-ink mt-1">
              {periods.length > 0 ? periods.length : "0"}
            </p>
            <p className="text-micro text-ink-secondary mt-0.5">
              {periods[0] ? `Latest: ${periods[0]}` : "No filings yet"}
            </p>
          </CardContent>
        </Card>
        <Card className="border-line bg-canvas">
          <CardContent className="p-4">
            <p className="text-micro uppercase tracking-wider text-ink-faint">Content Items</p>
            <p className="font-mono text-2xl font-bold text-ink mt-1">
              {stats?.content_items ?? contentItems.length}
            </p>
            <p className="text-micro text-ink-secondary mt-0.5">Raw documents</p>
          </CardContent>
        </Card>
        <Card className="border-line bg-canvas">
          <CardContent className="p-4">
            <p className="text-micro uppercase tracking-wider text-ink-faint">AI Reports</p>
            <p className="font-mono text-2xl font-bold text-ink mt-1">
              {stats?.reports ?? reports.length}
            </p>
            <p className="text-micro text-ink-secondary mt-0.5">Intelligence briefings</p>
          </CardContent>
        </Card>
        <Card className="border-line bg-canvas">
          <CardContent className="p-4">
            <p className="text-micro uppercase tracking-wider text-ink-faint">Alerts</p>
            <p className="font-mono text-2xl font-bold text-signal mt-1">
              {stats?.unread_alerts ?? (alertsData?.unread_count ?? 0)}
            </p>
            <p className="text-micro text-ink-secondary mt-0.5">Unread alerts</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs Navigation */}
      <div className="border-b border-line flex items-center gap-2 overflow-x-auto">
        <TabButton
          active={activeTab === "holdings"}
          onClick={() => setActiveTab("holdings")}
          label="13F Holdings"
          badge={portfolioChanges.length > 0 ? String(portfolioChanges.length) : undefined}
        />
        <TabButton
          active={activeTab === "content"}
          onClick={() => setActiveTab("content")}
          label="Content Feed"
          badge={contentItems.length > 0 ? String(contentItems.length) : undefined}
        />
        <TabButton
          active={activeTab === "sources"}
          onClick={() => setActiveTab("sources")}
          label="Data Sources"
          badge={sources.length > 0 ? String(sources.length) : undefined}
        />
        <TabButton
          active={activeTab === "reports"}
          onClick={() => setActiveTab("reports")}
          label="Reports"
          badge={reports.length > 0 ? String(reports.length) : undefined}
        />
        <TabButton
          active={activeTab === "alerts"}
          onClick={() => setActiveTab("alerts")}
          label="Alerts"
          badge={alertsData?.alerts.length ? String(alertsData.alerts.length) : undefined}
        />
      </div>

      {/* Tab 1: 13F Holdings */}
      {activeTab === "holdings" && (
        <Card className="border-line bg-canvas">
          <CardHeader className="pb-3 border-b border-line/60">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  <span>13F Portfolio Holdings</span>
                  {periods.length > 0 && (
                    <Badge variant="outline" className="font-mono text-micro text-ink-secondary">
                      {periods.length} Quarters
                    </Badge>
                  )}
                </CardTitle>
                <CardDescription className="text-small text-ink-secondary mt-0.5">
                  Holdings and position changes extracted from SEC EDGAR 13F filings
                </CardDescription>
              </div>

              {/* View Switcher & Search */}
              <div className="flex items-center gap-2 flex-wrap">
                {/* Search */}
                <div className="relative">
                  <Search className="h-3.5 w-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-faint" />
                  <Input
                    placeholder="Filter ticker / company..."
                    value={holdingsSearch}
                    onChange={(e) => setHoldingsSearch(e.target.value)}
                    className="h-8 pl-8 pr-3 w-48 text-small bg-surface border-line"
                  />
                </div>

                {/* View Toggle */}
                <div className="flex items-center rounded-lg border border-line bg-surface p-0.5">
                  <button
                    onClick={() => setHoldingsView("breakdown")}
                    className={`flex items-center gap-1.5 px-2.5 py-1 text-micro font-medium rounded-md transition-colors ${
                      holdingsView === "breakdown"
                        ? "bg-panel text-ink shadow-sm"
                        : "text-ink-secondary hover:text-ink"
                    }`}
                  >
                    <LayoutList className="h-3.5 w-3.5" />
                    Quarterly
                  </button>
                  <button
                    onClick={() => setHoldingsView("matrix")}
                    className={`flex items-center gap-1.5 px-2.5 py-1 text-micro font-medium rounded-md transition-colors ${
                      holdingsView === "matrix"
                        ? "bg-panel text-ink shadow-sm"
                        : "text-ink-secondary hover:text-ink"
                    }`}
                  >
                    <Grid3X3 className="h-3.5 w-3.5" />
                    Matrix View
                  </button>
                </div>
              </div>
            </div>

            {/* Quarter Filter Pills (in breakdown mode) */}
            {periods.length > 0 && holdingsView === "breakdown" && (
              <div className="flex items-center gap-1.5 overflow-x-auto pt-3 pb-1">
                <span className="text-micro text-ink-faint font-medium uppercase tracking-wider mr-1 shrink-0">
                  Quarter:
                </span>
                <button
                  onClick={() => setSelectedQuarter("all")}
                  className={`px-2.5 py-1 rounded-md text-micro font-mono font-medium transition-colors shrink-0 ${
                    selectedQuarter === "all"
                      ? "bg-signal text-black font-semibold shadow-sm"
                      : "bg-surface border border-line text-ink-secondary hover:text-ink hover:border-line-hover"
                  }`}
                >
                  All ({periods.length})
                </button>
                {periods.map((p) => {
                  const count = portfolioByPeriod[p]?.length || 0;
                  const isLatest = p === periods[0];
                  return (
                    <button
                      key={p}
                      onClick={() => setSelectedQuarter(p)}
                      className={`px-2.5 py-1 rounded-md text-micro font-mono font-medium transition-colors shrink-0 flex items-center gap-1.5 ${
                        selectedQuarter === p
                          ? "bg-signal text-black font-semibold shadow-sm"
                          : "bg-surface border border-line text-ink-secondary hover:text-ink hover:border-line-hover"
                      }`}
                    >
                      <span>{p}</span>
                      {isLatest && <span className="text-[9px] font-sans px-1 rounded bg-black/20 text-black font-bold">Latest</span>}
                      <span className="text-[10px] opacity-60">({count})</span>
                    </button>
                  );
                })}
              </div>
            )}
          </CardHeader>
          <CardContent className="pt-4">
            {loadingPortfolio ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-signal" />
              </div>
            ) : periods.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-ink-secondary text-body">No 13F portfolio data yet.</p>
                <p className="text-micro text-ink-faint mt-1">
                  Click &ldquo;Sync Filings&rdquo; above to fetch and parse 13F filings from the SEC.
                </p>
              </div>
            ) : holdingsView === "matrix" ? (
              /* Multi-Quarter Matrix View */
              <div className="relative overflow-x-auto overflow-y-auto max-h-[70vh] border border-line rounded-lg">
                <table className="w-full text-small border-collapse min-w-max text-left">
                  <thead className="sticky top-0 z-20 bg-panel/95 backdrop-blur border-b border-line shadow-sm">
                    <tr>
                      <th
                        rowSpan={2}
                        className="py-3 px-4 font-semibold text-small text-ink sticky left-0 z-30 min-w-[220px] max-w-[220px] w-[220px] bg-panel border-r border-line"
                      >
                        Company
                      </th>
                      <th
                        rowSpan={2}
                        className="py-3 px-3 font-semibold text-small text-ink sticky left-[220px] z-30 min-w-[90px] max-w-[90px] w-[90px] bg-panel border-r border-line"
                      >
                        Ticker
                      </th>
                      {periods.map((period) => (
                        <th
                          key={period}
                          colSpan={4}
                          className="py-2 px-3 text-center font-mono font-semibold text-small border-r border-line text-signal"
                        >
                          {period}
                        </th>
                      ))}
                    </tr>
                    <tr className="border-t border-line text-micro text-ink-secondary bg-surface">
                      {periods.map((period) => (
                        <Fragment key={`${period}-sub`}>
                          <th className="py-1.5 px-3 text-right font-medium min-w-[100px]">Shares</th>
                          <th className="py-1.5 px-3 text-right font-medium min-w-[110px]">Value</th>
                          <th className="py-1.5 px-3 text-right font-medium min-w-[80px]">% Port</th>
                          <th className="py-1.5 px-3 text-center font-medium min-w-[95px] border-r border-line">Change</th>
                        </Fragment>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-line">
                    {matrixHoldings
                      .filter((h) => {
                        if (!holdingsSearch.trim()) return true;
                        const q = holdingsSearch.toLowerCase();
                        return (
                          h.company_name.toLowerCase().includes(q) ||
                          h.ticker_symbol.toLowerCase().includes(q) ||
                          h.key.toLowerCase().includes(q)
                        );
                      })
                      .map((h) => (
                        <tr key={h.key} className="hover:bg-panel/50 transition-colors group">
                          <td className="py-2.5 px-4 text-ink font-medium sticky left-0 z-10 bg-canvas group-hover:bg-panel/70 transition-colors min-w-[220px] max-w-[220px] w-[220px] truncate border-r border-line">
                            {h.company_name}
                          </td>
                          <td className="py-2.5 px-3 font-mono font-semibold text-signal sticky left-[220px] z-10 bg-canvas group-hover:bg-panel/70 transition-colors min-w-[90px] max-w-[90px] w-[90px] border-r border-line">
                            {h.ticker_symbol && h.ticker_symbol !== "—" ? (
                              <Link href={`/tickers/${h.ticker_symbol}`} className="hover:underline">
                                ${h.ticker_symbol}
                              </Link>
                            ) : (
                              "—"
                            )}
                          </td>
                          {periods.map((period) => {
                            const pc = h.changesByPeriod[period];
                            if (!pc) {
                              return (
                                <Fragment key={`${h.key}-${period}`}>
                                  <td className="py-2.5 px-3 text-right text-ink-faint/40">—</td>
                                  <td className="py-2.5 px-3 text-right text-ink-faint/40">—</td>
                                  <td className="py-2.5 px-3 text-right text-ink-faint/40">—</td>
                                  <td className="py-2.5 px-3 text-center text-ink-faint/40 border-r border-line">—</td>
                                </Fragment>
                              );
                            }
                            const cfg = changeConfig[pc.change_type] || changeConfig.unchanged;
                            const ChangeIcon = cfg.icon;
                            return (
                              <Fragment key={`${h.key}-${period}`}>
                                <td className="py-2.5 px-3 text-right font-mono text-ink-secondary tabular-nums">
                                  {pc.shares_current > 0 ? pc.shares_current.toLocaleString() : "0"}
                                </td>
                                <td className="py-2.5 px-3 text-right font-mono text-ink-secondary tabular-nums">
                                  {formatUsd(pc.value_usd)}
                                </td>
                                <td className="py-2.5 px-3 text-right font-mono text-ink tabular-nums font-medium">
                                  {formatPercent(pc.percent_of_portfolio)}
                                </td>
                                <td className="py-2.5 px-3 text-center border-r border-line">
                                  <Badge variant="outline" className={`text-micro gap-1 whitespace-nowrap ${cfg.color}`}>
                                    <ChangeIcon className="h-3 w-3" />
                                    {cfg.label}
                                  </Badge>
                                </td>
                              </Fragment>
                            );
                          })}
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            ) : (
              /* Quarterly Breakdown View */
              <div className="space-y-8">
                {displayedPeriods.map((period) => {
                  const allChanges = portfolioByPeriod[period] || [];
                  const changes = allChanges.filter((pc) => {
                    if (!holdingsSearch.trim()) return true;
                    const q = holdingsSearch.toLowerCase();
                    return (
                      (pc.company_name && pc.company_name.toLowerCase().includes(q)) ||
                      (pc.ticker_symbol && pc.ticker_symbol.toLowerCase().includes(q)) ||
                      (pc.cusip && pc.cusip.toLowerCase().includes(q))
                    );
                  });

                  return (
                    <div key={period} className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Badge variant="default" className="font-mono text-small bg-signal text-black font-semibold">
                            {period}
                          </Badge>
                          {period === periods[0] && (
                            <Badge variant="outline" className="text-[10px] text-signal border-signal/40">
                              Latest Filing
                            </Badge>
                          )}
                          <span className="text-small text-ink-secondary">
                            {changes.length} positions {changes.length !== allChanges.length && `(filtered from ${allChanges.length})`}
                          </span>
                        </div>
                      </div>
                      <div className="overflow-x-auto border border-line rounded-lg">
                        <table className="w-full text-small">
                          <thead>
                            <tr className="border-b border-line bg-panel">
                              <th className="text-left px-4 py-2.5 font-medium text-ink-secondary">Company</th>
                              <th className="text-left px-4 py-2.5 font-medium text-ink-secondary">Ticker</th>
                              <th className="text-right px-4 py-2.5 font-medium text-ink-secondary">Shares</th>
                              <th className="text-right px-4 py-2.5 font-medium text-ink-secondary">Value ($K)</th>
                              <th className="text-right px-4 py-2.5 font-medium text-ink-secondary">% Port</th>
                              <th className="text-center px-4 py-2.5 font-medium text-ink-secondary">Change</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-line">
                            {changes.length === 0 ? (
                              <tr>
                                <td colSpan={6} className="py-6 text-center text-ink-secondary">
                                  No positions match &ldquo;{holdingsSearch}&rdquo; in {period}.
                                </td>
                              </tr>
                            ) : (
                              changes.map((pc) => {
                                const cfg = changeConfig[pc.change_type] || changeConfig.unchanged;
                                const ChangeIcon = cfg.icon;
                                return (
                                  <tr key={pc.id} className="hover:bg-panel/50 transition-colors">
                                    <td className="px-4 py-2.5 font-medium text-ink">
                                      {pc.company_name ?? "—"}
                                    </td>
                                    <td className="px-4 py-2.5 font-mono font-semibold text-signal">
                                      {pc.ticker_symbol ? (
                                        <Link href={`/tickers/${pc.ticker_symbol}`} className="hover:underline">
                                          ${pc.ticker_symbol}
                                        </Link>
                                      ) : (
                                        "—"
                                      )}
                                    </td>
                                    <td className="px-4 py-2.5 text-right font-mono text-ink-secondary">
                                      {pc.shares_current > 0 ? pc.shares_current.toLocaleString() : "—"}
                                    </td>
                                    <td className="px-4 py-2.5 text-right font-mono text-ink-secondary">
                                      {formatUsd(pc.value_usd)}
                                    </td>
                                    <td className="px-4 py-2.5 text-right font-mono text-ink-secondary">
                                      {formatPercent(pc.percent_of_portfolio)}
                                    </td>
                                    <td className="px-4 py-2.5 text-center">
                                      <Badge variant="outline" className={`text-micro gap-1 ${cfg.color}`}>
                                        <ChangeIcon className="h-3 w-3" />
                                        {cfg.label}
                                      </Badge>
                                    </td>
                                  </tr>
                                );
                              })
                            )}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tab 2: Content Feed */}
      {activeTab === "content" && (
        <Card className="border-line bg-canvas">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Ingested Content Items</CardTitle>
            <CardDescription className="text-small text-ink-secondary">
              Raw filings, articles, and transcripts scanned for this investor
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loadingContent ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-signal" />
              </div>
            ) : contentItems.length === 0 ? (
              <div className="text-center py-12 text-ink-secondary">
                No content items ingested yet.
              </div>
            ) : (
              <div className="divide-y divide-line">
                {contentItems.map((item) => (
                  <div key={item.id} className="py-3 flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0 space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-small text-ink truncate">
                          {item.title || "Untitled Document"}
                        </span>
                        <Badge variant="outline" className="text-micro font-mono uppercase">
                          {item.content_type}
                        </Badge>
                      </div>
                      {item.url && (
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-micro text-ink-faint hover:text-signal truncate block transition-colors"
                        >
                          {item.url}
                        </a>
                      )}
                      <p className="text-micro text-ink-faint flex items-center gap-1.5">
                        <Clock className="h-3 w-3" />
                        {new Date(item.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <Badge
                      variant="outline"
                      className={`text-micro capitalize ${
                        item.processing_status === "completed"
                          ? "border-green-500/30 text-green-400 bg-green-500/10"
                          : item.processing_status === "processing"
                          ? "border-blue-500/30 text-blue-400 bg-blue-500/10 animate-pulse"
                          : item.processing_status === "failed"
                          ? "border-red-500/30 text-red-400 bg-red-500/10"
                          : "border-line text-ink-faint"
                      }`}
                    >
                      {item.processing_status}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tab 3: Sources */}
      {activeTab === "sources" && (
        <SourcesTabContent investorId={id} sources={sources} isLoading={loadingSources} />
      )}

      {/* Tab 4: Intelligence Reports */}
      {activeTab === "reports" && (
        <Card className="border-line bg-canvas">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base">AI Intelligence Reports</CardTitle>
                <CardDescription className="text-small text-ink-secondary">
                  Automated briefings synthesized across all investor sources and 13F changes
                </CardDescription>
              </div>
              <Button
                size="sm"
                onClick={() => generateReportMutation.mutate()}
                disabled={generateReportMutation.isPending}
                className="gap-1.5 bg-signal text-black hover:bg-signal/90 text-small"
              >
                {generateReportMutation.isPending ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Plus className="h-3.5 w-3.5" />
                )}
                Generate Report
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {loadingReports ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-signal" />
              </div>
            ) : reports.length === 0 ? (
              <div className="text-center py-12 text-ink-secondary">
                No reports generated yet. Click &ldquo;Generate Report&rdquo; to create your first briefing.
              </div>
            ) : (
              <div className="space-y-3">
                {reports.map((report) => (
                  <ReportAccordionItem
                    key={report.id}
                    reportItem={report}
                    isOpen={selectedReport === report.id}
                    onToggle={() =>
                      setSelectedReport((prev) => (prev === report.id ? null : report.id))
                    }
                  />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Tab 5: Alerts */}
      {activeTab === "alerts" && (
        <Card className="border-line bg-canvas">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Investor Alerts</CardTitle>
            <CardDescription className="text-small text-ink-secondary">
              High-priority events and significant position changes
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loadingAlerts ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-signal" />
              </div>
            ) : !alertsData?.alerts.length ? (
              <div className="text-center py-12 text-ink-secondary">
                No alerts recorded for this investor.
              </div>
            ) : (
              <div className="divide-y divide-line">
                {alertsData.alerts.map((alert) => (
                  <div key={alert.id} className="py-3 flex items-start gap-3">
                    <div className="flex-1 min-w-0 space-y-1">
                      <div className="flex items-center gap-2">
                        <p className="font-semibold text-small text-ink">{alert.title}</p>
                        <Badge
                          variant="outline"
                          className={`text-micro uppercase ${
                            alert.severity === "critical"
                              ? "bg-red-500/20 text-red-400 border-red-500/30"
                              : alert.severity === "high"
                              ? "bg-orange-500/20 text-orange-400 border-orange-500/30"
                              : "bg-blue-500/20 text-blue-400 border-blue-500/30"
                          }`}
                        >
                          {alert.severity}
                        </Badge>
                      </div>
                      {alert.summary && (
                        <p className="text-small text-ink-secondary">{alert.summary}</p>
                      )}
                      <p className="text-micro text-ink-faint flex items-center gap-1.5">
                        <Clock className="h-3 w-3" />
                        {new Date(alert.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function TabButton({
  active,
  onClick,
  label,
  badge,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
  badge?: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-3 py-2 text-small font-medium border-b-2 transition-colors whitespace-nowrap ${
        active
          ? "border-signal text-signal"
          : "border-transparent text-ink-secondary hover:text-ink hover:border-line"
      }`}
    >
      {label}
      {badge && (
        <span
          className={`rounded-full px-1.5 py-0.2 text-micro font-mono ${
            active ? "bg-signal/20 text-signal" : "bg-panel text-ink-faint"
          }`}
        >
          {badge}
        </span>
      )}
    </button>
  );
}

function SourcesTabContent({
  investorId,
  sources,
  isLoading,
}: {
  investorId: string;
  sources: HfiSource[];
  isLoading: boolean;
}) {
  const queryClient = useQueryClient();
  const [showAdd, setShowAdd] = useState(false);
  const [sourceType, setSourceType] = useState("website");
  const [url, setUrl] = useState("");

  const addSourceMutation = useMutation({
    mutationFn: () =>
      api.createHfiSource(investorId, {
        source_type: sourceType,
        url,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hfi-sources", investorId] });
      setShowAdd(false);
      setUrl("");
    },
  });

  const deleteSourceMutation = useMutation({
    mutationFn: (sourceId: string) => api.deleteHfiSource(sourceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hfi-sources", investorId] });
    },
  });

  return (
    <Card className="border-line bg-canvas">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base">Configured Sources</CardTitle>
            <CardDescription className="text-small text-ink-secondary">
              SEC 13F filings, website scrapers, and news feeds tracked for this manager
            </CardDescription>
          </div>
          <Button
            size="sm"
            variant={showAdd ? "outline" : "default"}
            onClick={() => setShowAdd((p) => !p)}
            className="gap-1.5 text-small bg-signal text-black hover:bg-signal/90"
          >
            {showAdd ? <X className="h-3.5 w-3.5" /> : <Plus className="h-3.5 w-3.5" />}
            {showAdd ? "Cancel" : "Add Source"}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {showAdd && (
          <div className="p-4 rounded-lg border border-line bg-panel space-y-3">
            <h4 className="font-semibold text-small text-ink">Add Data Source</h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-micro text-ink-faint uppercase tracking-wider mb-1">
                  Source Type
                </label>
                <select
                  value={sourceType}
                  onChange={(e) => setSourceType(e.target.value)}
                  className="w-full rounded-md border border-line bg-canvas px-3 py-2 text-small text-ink"
                >
                  <option value="website">Website</option>
                  <option value="sec_13f">SEC 13F</option>
                  <option value="rss">RSS Feed</option>
                  <option value="youtube">YouTube Channel</option>
                </select>
              </div>
              <div className="sm:col-span-2">
                <label className="block text-micro text-ink-faint uppercase tracking-wider mb-1">
                  URL / Endpoint
                </label>
                <Input
                  type="text"
                  placeholder={sourceType === "sec_13f" ? "https://www.sec.gov/edgar/..." : "https://..."}
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="text-small"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-1">
              <Button variant="ghost" size="sm" onClick={() => setShowAdd(false)}>
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={() => addSourceMutation.mutate()}
                disabled={!url.trim() || addSourceMutation.isPending}
                className="bg-signal text-black hover:bg-signal/90"
              >
                {addSourceMutation.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" />}
                Add Source
              </Button>
            </div>
          </div>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-signal" />
          </div>
        ) : sources.length === 0 ? (
          <div className="text-center py-12 text-ink-secondary">
            No sources configured.
          </div>
        ) : (
          <div className="divide-y divide-line">
            {sources.map((source) => {
              const Icon = sourceIcons[source.source_type] || Globe;
              return (
                <div key={source.id} className="py-3 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="rounded-md bg-panel p-2 text-signal shrink-0">
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="min-w-0">
                      <p className="font-medium text-small text-ink truncate">{source.label || source.url}</p>
                      <p className="text-micro text-ink-faint truncate">{source.url}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Badge variant="outline" className="text-micro font-mono uppercase">
                      {source.source_type}
                    </Badge>
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      onClick={() => deleteSourceMutation.mutate(source.id)}
                      className="text-ink-faint hover:text-red-400"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ReportAccordionItem({
  reportItem,
  isOpen,
  onToggle,
}: {
  reportItem: HfiReportListItem;
  isOpen: boolean;
  onToggle: () => void;
}) {
  const { data: fullReport, isLoading } = useQuery({
    queryKey: ["hfi-report-detail", reportItem.id],
    queryFn: () => api.getHfiReport(reportItem.id),
    enabled: isOpen,
  });

  return (
    <div className="border border-line rounded-lg overflow-hidden bg-canvas">
      <button
        onClick={onToggle}
        className="w-full text-left p-4 flex items-center justify-between gap-4 hover:bg-panel/50 transition-colors"
      >
        <div className="space-y-1 min-w-0">
          <div className="flex items-center gap-2">
            <h4 className="font-semibold text-small text-ink truncate">{reportItem.title}</h4>
            <Badge variant="outline" className="text-micro capitalize">
              {reportItem.report_type.replace("_", " ")}
            </Badge>
          </div>
          {reportItem.summary && (
            <p className="text-small text-ink-secondary line-clamp-1">{reportItem.summary}</p>
          )}
          <p className="text-micro text-ink-faint flex items-center gap-1">
            <Clock className="h-3 w-3" />
            Generated {new Date(reportItem.generated_at).toLocaleString()}
          </p>
        </div>
        <div className="shrink-0 text-ink-faint">
          {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </div>
      </button>

      {isOpen && (
        <div className="border-t border-line p-5 bg-panel/30">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-signal" />
            </div>
          ) : fullReport?.content_markdown ? (
            <div className="prose prose-invert max-w-none text-small text-ink leading-relaxed whitespace-pre-wrap font-sans">
              {fullReport.content_markdown}
            </div>
          ) : (
            <p className="text-small text-ink-faint">No report content.</p>
          )}
        </div>
      )}
    </div>
  );
}
