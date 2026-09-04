"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { useQuery } from "@tanstack/react-query";
import { api, type HfiConsensusHolding, type HfiConsensusResponse } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  TrendingUp,
  TrendingDown,
  Activity,
  AlertCircle,
  Building2,
  Calendar,
  X,
  ChevronRight,
  ExternalLink,
  Loader2,
} from "lucide-react";

function formatNumber(num: number | null | undefined): string {
  if (num == null) return "0";
  return num.toLocaleString();
}

function formatCurrency(val: number | null | undefined): string {
  if (val == null || val === 0) return "—";
  if (val >= 1_000_000_000) return `$${(val / 1_000_000_000).toFixed(2)}B`;
  if (val >= 1_000_000) return `$${(val / 1_000_000).toFixed(2)}M`;
  if (val >= 1_000) return `$${(val / 1_000).toFixed(1)}K`;
  return `$${val.toLocaleString()}`;
}

const MiniPieChart = ({ percent }: { percent: number }) => {
  const radius = 15;
  const circumference = 2 * Math.PI * radius;
  const validPercent = Math.min(100, Math.max(0, percent));
  const strokeLength = (validPercent / 100) * circumference;

  return (
    <div className="relative w-11 h-11 shrink-0 flex items-center justify-center">
      <svg viewBox="0 0 40 40" className="w-full h-full transform -rotate-90">
        <circle
          cx="20"
          cy="20"
          r={radius}
          fill="transparent"
          stroke="currentColor"
          strokeWidth="4"
          className="text-line/40"
        />
        <circle
          cx="20"
          cy="20"
          r={radius}
          fill="transparent"
          stroke="currentColor"
          strokeWidth="4"
          strokeDasharray={`${strokeLength} ${circumference}`}
          strokeLinecap="round"
          className="text-signal transition-all duration-500"
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-[10px] font-mono font-bold text-ink">
        {percent < 10 ? percent.toFixed(1) : Math.round(percent)}%
      </span>
    </div>
  );
};

const getChangeBadge = (type: string, sharesCurrent?: number, sharesPrevious?: number) => {
  let pctStr = "";
  if (sharesPrevious !== undefined && sharesCurrent !== undefined) {
    if (type === "new_position" || (sharesPrevious === 0 && sharesCurrent > 0)) {
      pctStr = "+100%";
    } else if (type === "closed" || (sharesCurrent === 0 && sharesPrevious > 0)) {
      pctStr = "-100%";
    } else if (sharesPrevious > 0) {
      const pct = ((sharesCurrent - sharesPrevious) / sharesPrevious) * 100;
      pctStr = `${pct >= 0 ? "+" : ""}${pct.toFixed(1)}%`;
    } else if (sharesCurrent === sharesPrevious) {
      pctStr = "0%";
    }
  }

  switch (type) {
    case "new_position":
    case "increased":
      return (
        <span
          className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-xs font-black bg-bullish/10 text-bullish border border-bullish/30"
          title={`Buy / Increased ${pctStr ? `(${pctStr})` : ""}`}
        >
          <span>B</span>
          {pctStr && <span className="font-mono text-[11px] font-bold text-bullish">{pctStr}</span>}
        </span>
      );
    case "decreased":
    case "closed":
      return (
        <span
          className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-xs font-black bg-bearish/10 text-bearish border border-bearish/30"
          title={`Sell / Decreased ${pctStr ? `(${pctStr})` : ""}`}
        >
          <span>S</span>
          {pctStr && <span className="font-mono text-[11px] font-bold text-bearish">{pctStr}</span>}
        </span>
      );
    default:
      return (
        <span
          className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-xs font-black bg-ink/10 text-ink-secondary border border-line"
          title={`Neutral / Unchanged ${pctStr ? `(${pctStr})` : ""}`}
        >
          <span>N</span>
          {pctStr && <span className="font-mono text-[11px] font-bold text-ink-secondary">{pctStr}</span>}
        </span>
      );
  }
};

export default function ConsensusPage() {
  const [selectedPeriod, setSelectedPeriod] = useState<string | null>(null);
  const [selectedHolding, setSelectedHolding] = useState<HfiConsensusHolding | null>(null);

  const { data, isLoading, error } = useQuery<HfiConsensusResponse>({
    queryKey: ["hfi-consensus", selectedPeriod],
    queryFn: () => api.getHfiConsensus(selectedPeriod || undefined),
  });

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setSelectedHolding(null);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[50vh]">
        <Loader2 className="w-8 h-8 text-signal animate-spin" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex flex-col items-center justify-center h-[50vh] text-center space-y-4">
        <AlertCircle className="w-12 h-12 text-bearish" />
        <h2 className="text-xl font-bold text-ink">Failed to Load Consensus</h2>
        <p className="text-ink-secondary">
          {error instanceof Error ? error.message : "Could not load consensus data."}
        </p>
      </div>
    );
  }

  const { filing_period, available_periods = [], total_funds_analyzed, holdings = [] } = data;

  const topBuys = [...holdings].sort((a, b) => b.funds_buying - a.funds_buying).slice(0, 3);
  const topSells = [...holdings].sort((a, b) => b.funds_selling - a.funds_selling).slice(0, 3);
  const mostPopular = [...holdings].sort((a, b) => b.total_funds_holding - a.total_funds_holding).slice(0, 1)[0];

  return (
    <div className="space-y-6 pb-12">
      {/* Header & Period Selector */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-ink tracking-tight font-mono">Smart Money Consensus</h1>
          <p className="text-ink-secondary mt-1 text-small">
            Aggregated 13F portfolio holdings across all active funds ({total_funds_analyzed} funds analyzed).
          </p>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 bg-panel rounded-lg border border-line self-start md:self-auto">
          <Calendar className="w-4 h-4 text-ink-faint" />
          <span className="text-small text-ink-secondary">Period: </span>
          {available_periods.length > 0 ? (
            <select
              value={selectedPeriod || filing_period}
              onChange={(e) => setSelectedPeriod(e.target.value)}
              className="bg-transparent font-bold font-mono text-small focus:outline-none cursor-pointer border-none py-0 pl-1 pr-2 text-signal"
            >
              {available_periods.map((p: string) => (
                <option key={p} value={p} className="bg-canvas text-ink">
                  {p}
                </option>
              ))}
            </select>
          ) : (
            <span className="font-bold font-mono text-small text-signal">{filing_period}</span>
          )}
        </div>
      </div>

      {/* 3 Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="border-line bg-canvas">
          <CardHeader className="pb-2">
            <CardTitle className="text-small font-medium text-ink-secondary flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-bullish" /> Top Buy Consensus
            </CardTitle>
          </CardHeader>
          <CardContent>
            {topBuys.length > 0 && topBuys[0].funds_buying > 0 ? (
              <div className="space-y-3">
                {topBuys.map((h, i) => (
                  <div key={i} className="flex justify-between items-center gap-2">
                    <span className="font-bold text-small truncate text-ink" title={h.company_name || ""}>
                      {h.company_name || h.ticker_symbol}
                    </span>
                    <span className="text-micro text-bullish font-semibold font-mono whitespace-nowrap">
                      +{h.funds_buying} funds
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <span className="text-ink-faint text-small">No buy data</span>
            )}
          </CardContent>
        </Card>

        <Card className="border-line bg-canvas">
          <CardHeader className="pb-2">
            <CardTitle className="text-small font-medium text-ink-secondary flex items-center gap-2">
              <TrendingDown className="w-4 h-4 text-bearish" /> Top Sell Consensus
            </CardTitle>
          </CardHeader>
          <CardContent>
            {topSells.length > 0 && topSells[0].funds_selling > 0 ? (
              <div className="space-y-3">
                {topSells.map((h, i) => (
                  <div key={i} className="flex justify-between items-center gap-2">
                    <span className="font-bold text-small truncate text-ink" title={h.company_name || ""}>
                      {h.company_name || h.ticker_symbol}
                    </span>
                    <span className="text-micro text-bearish font-semibold font-mono whitespace-nowrap">
                      -{h.funds_selling} funds
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <span className="text-ink-faint text-small">No sell data</span>
            )}
          </CardContent>
        </Card>

        <Card className="border-line bg-canvas">
          <CardHeader className="pb-2">
            <CardTitle className="text-small font-medium text-ink-secondary flex items-center gap-2">
              <Activity className="w-4 h-4 text-signal" /> Most Popular Holding
            </CardTitle>
          </CardHeader>
          <CardContent>
            {mostPopular && mostPopular.total_funds_holding > 0 ? (
              <div className="space-y-1">
                <div className="text-lg font-bold truncate text-ink" title={mostPopular.company_name || ""}>
                  {mostPopular.company_name || mostPopular.ticker_symbol}
                </div>
                {mostPopular.ticker_symbol && (
                  <div className="text-micro font-mono text-signal font-bold">${mostPopular.ticker_symbol}</div>
                )}
                <div className="mt-2 text-small text-ink-secondary">
                  Held by <span className="font-bold text-ink font-mono">{mostPopular.total_funds_holding}</span> funds
                </div>
              </div>
            ) : (
              <span className="text-ink-faint text-small">No holdings data</span>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Main Consensus Table */}
      <Card className="border-line bg-canvas overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-small text-left">
            <thead className="text-micro text-ink-secondary uppercase bg-panel/70 border-b border-line">
              <tr>
                <th className="px-6 py-4 font-medium">Company</th>
                <th className="px-6 py-4 font-medium">Ticker</th>
                <th className="px-6 py-4 font-medium">Fund Consensus</th>
                <th className="px-6 py-4 font-medium text-right">Aggregated Value</th>
                <th className="w-10 px-4 py-4"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {holdings.map((h: HfiConsensusHolding, i: number) => {
                const buying = h.funds_buying || 0;
                const selling = h.funds_selling || 0;
                const totalHolding = h.total_funds_holding || 0;
                const neutral = Math.max(0, totalHolding - (buying + selling));

                const totalActivity = buying + neutral + selling;
                const buyRatio = totalActivity > 0 ? (buying / totalActivity) * 100 : 0;
                const neutralRatio = totalActivity > 0 ? (neutral / totalActivity) * 100 : 0;
                const sellRatio = totalActivity > 0 ? (selling / totalActivity) * 100 : 0;
                const isSelected = selectedHolding?.company_name === h.company_name;

                return (
                  <motion.tr
                    key={h.company_name || h.ticker_symbol || i}
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.01 }}
                    onClick={() => setSelectedHolding(h)}
                    className={`hover:bg-panel/50 transition-colors cursor-pointer group ${
                      isSelected ? "bg-signal/10 hover:bg-signal/15" : ""
                    }`}
                  >
                    <td className="px-6 py-4 font-semibold text-ink truncate max-w-[260px]" title={h.company_name || ""}>
                      {h.company_name || "—"}
                    </td>
                    <td className="px-6 py-4 font-mono text-micro">
                      {h.ticker_symbol ? (
                        <span className="bg-signal/15 text-signal px-2 py-0.5 rounded font-bold border border-signal/20">
                          ${h.ticker_symbol}
                        </span>
                      ) : (
                        <span className="text-ink-faint/50">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="space-y-1.5 max-w-[320px]">
                        {/* 3-color stacked ratio bar */}
                        <div className="h-2 bg-panel rounded-full overflow-hidden flex w-full border border-line/40">
                          {buyRatio > 0 && (
                            <div
                              className="bg-bullish h-full transition-all"
                              style={{ width: `${buyRatio}%` }}
                              title={`Buy: ${buying}`}
                            />
                          )}
                          {neutralRatio > 0 && (
                            <div
                              className="bg-ink-faint h-full transition-all"
                              style={{ width: `${neutralRatio}%` }}
                              title={`Neutral: ${neutral}`}
                            />
                          )}
                          {sellRatio > 0 && (
                            <div
                              className="bg-bearish h-full transition-all"
                              style={{ width: `${sellRatio}%` }}
                              title={`Sell: ${selling}`}
                            />
                          )}
                        </div>
                        {/* B, N, S Badges */}
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md font-bold text-micro bg-bullish/10 text-bullish border border-bullish/30">
                            <span className="font-extrabold">{buying}</span> B
                          </span>
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md font-bold text-micro bg-ink/10 text-ink-secondary border border-line">
                            <span className="font-extrabold">{neutral}</span> N
                          </span>
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md font-bold text-micro bg-bearish/10 text-bearish border border-bearish/30">
                            <span className="font-extrabold">{selling}</span> S
                          </span>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right font-mono font-medium text-ink">
                      {h.total_value_usd ? formatCurrency(h.total_value_usd) : "—"}
                    </td>
                    <td className="px-4 py-4 text-ink-faint group-hover:text-signal group-hover:translate-x-0.5 transition-all text-right">
                      <ChevronRight className="w-4 h-4 inline" />
                    </td>
                  </motion.tr>
                );
              })}
            </tbody>
          </table>
          {holdings.length === 0 && (
            <div className="p-8 text-center text-ink-secondary">
              No holdings data found for this period.
            </div>
          )}
        </div>
      </Card>

      {/* Slide-over Right Sidebar */}
      <AnimatePresence>
        {selectedHolding && (
          <>
            {/* Backdrop Overlay */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSelectedHolding(null)}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
            />

            {/* Slide-over Drawer */}
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="fixed top-0 right-0 bottom-0 w-full max-w-lg bg-canvas border-l border-line z-50 flex flex-col"
            >
              {/* Header */}
              <div className="p-6 border-b border-line flex items-start justify-between bg-panel/50">
                <div>
                  <h3 className="font-bold text-xl text-ink font-mono">{selectedHolding.company_name}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    {selectedHolding.ticker_symbol && (
                      <span className="bg-signal/15 text-signal text-micro px-2.5 py-0.5 rounded font-mono font-bold border border-signal/25">
                        ${selectedHolding.ticker_symbol}
                      </span>
                    )}
                    <span className="text-micro px-2.5 py-0.5 rounded-full bg-panel text-ink-secondary font-mono font-semibold border border-line">
                      {selectedHolding.funds?.length || 0} Funds
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedHolding(null)}
                  className="p-2 rounded-lg hover:bg-panel text-ink-secondary hover:text-ink transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Scrollable Content */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {/* Summary Cards */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-4 rounded-md bg-panel/60 border border-line">
                    <span className="text-micro text-ink-secondary block font-medium uppercase tracking-wider">
                      Aggregated Value
                    </span>
                    <span className="text-xl font-bold font-mono text-ink mt-1 block">
                      {selectedHolding.total_value_usd ? formatCurrency(selectedHolding.total_value_usd) : "—"}
                    </span>
                  </div>
                  <div className="p-4 rounded-md bg-panel/60 border border-line">
                    <span className="text-micro text-ink-secondary block font-medium uppercase tracking-wider">
                      Fund Breakdown
                    </span>
                    <div className="flex items-center gap-1.5 mt-1.5 flex-wrap">
                      <span className="text-micro font-extrabold px-2.5 py-0.5 rounded bg-bullish/10 text-bullish border border-bullish/30">
                        {selectedHolding.funds_buying || 0} B
                      </span>
                      <span className="text-micro font-extrabold px-2.5 py-0.5 rounded bg-ink/10 text-ink-secondary border border-line">
                        {Math.max(
                          0,
                          (selectedHolding.total_funds_holding || 0) -
                            ((selectedHolding.funds_buying || 0) + (selectedHolding.funds_selling || 0))
                        )}{" "}
                        N
                      </span>
                      <span className="text-micro font-extrabold px-2.5 py-0.5 rounded bg-bearish/10 text-bearish border border-bearish/30">
                        {selectedHolding.funds_selling || 0} S
                      </span>
                    </div>
                  </div>
                </div>

                {/* Tracked Funds Breakdown */}
                <div className="space-y-3">
                  <h4 className="text-micro uppercase font-semibold text-ink-secondary tracking-wider flex items-center gap-2">
                    <Building2 className="w-3.5 h-3.5 text-signal" /> Tracked Funds ({selectedHolding.funds?.length || 0})
                  </h4>

                  <div className="space-y-2.5">
                    {(selectedHolding.funds || []).map((f) => (
                      <div
                        key={f.investor_id}
                        className="p-4 bg-panel/40 border border-line rounded-md hover:border-signal/40 transition-all space-y-3"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <Link
                              href={`/investors/${f.investor_id}`}
                              className="font-semibold text-small hover:underline text-ink hover:text-signal flex items-center gap-1.5 transition-colors"
                            >
                              {f.investor_name}
                              <ExternalLink className="w-3.5 h-3.5 text-ink-faint" />
                            </Link>
                          </div>
                          {getChangeBadge(f.change_type, f.shares_current, f.shares_previous)}
                        </div>

                        <div className="grid grid-cols-2 gap-3 text-small pt-2 border-t border-line/40">
                          <div>
                            <span className="text-ink-secondary block text-micro uppercase font-medium">Shares</span>
                            <span className="font-mono font-bold text-ink">
                              {f.shares_current > 0 ? formatNumber(f.shares_current) : "0 (Exited)"}
                            </span>
                            {f.shares_previous > 0 && f.shares_current > 0 && f.shares_current !== f.shares_previous && (
                              <span className="block text-micro font-mono text-ink-faint mt-0.5">
                                Prev: {formatNumber(f.shares_previous)}
                              </span>
                            )}
                          </div>
                          <div>
                            <span className="text-ink-secondary block text-micro uppercase font-medium">
                              Holding Value
                            </span>
                            <span className="font-mono font-bold text-ink">
                              {f.value_usd ? formatCurrency(f.value_usd) : "—"}
                            </span>
                          </div>
                        </div>

                        {f.percent_of_portfolio !== null && (
                          <div className="flex items-center justify-between pt-2 border-t border-line/40">
                            <div>
                              <span className="text-ink-secondary block text-micro uppercase font-medium">
                                Portfolio Weight
                              </span>
                              <span className="text-small font-mono font-bold text-ink">
                                {f.percent_of_portfolio}% of portfolio
                              </span>
                            </div>
                            <MiniPieChart percent={f.percent_of_portfolio} />
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
