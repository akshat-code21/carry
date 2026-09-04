"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, type HfiInvestor, type HfiCompareResponse } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Loader2, GitCompareArrows, Check } from "lucide-react";

export default function ComparePage() {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [selectedPeriod, setSelectedPeriod] = useState<string | undefined>(undefined);

  const { data: investors = [] } = useQuery({
    queryKey: ["hfi-investors"],
    queryFn: () => api.getHfiInvestors(),
  });

  const { data: periods = [] } = useQuery({
    queryKey: ["hfi-periods"],
    queryFn: () => api.getHfiPeriods(),
  });

  const {
    data: comparison,
    isLoading: isComparing,
    refetch,
  } = useQuery({
    queryKey: ["hfi-compare", selectedIds, selectedPeriod],
    queryFn: () => api.getHfiCompare(selectedIds, selectedPeriod),
    enabled: selectedIds.length >= 2,
  });

  const toggleInvestor = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Compare"
        description="Side-by-side portfolio comparison across selected investors"
      />

      {/* Investor selector + period picker */}
      <div className="flex flex-wrap items-end gap-4">
        <div className="flex-1 min-w-[280px]">
          <label className="block text-small font-medium text-ink-secondary mb-2">
            Select Investors to Compare
          </label>
          <div className="flex flex-wrap gap-2">
            {investors.map((inv) => {
              const selected = selectedIds.includes(inv.id);
              return (
                <Button
                  key={inv.id}
                  variant={selected ? "default" : "outline"}
                  size="sm"
                  onClick={() => toggleInvestor(inv.id)}
                  className={`gap-1.5 ${
                    selected
                      ? "bg-signal text-black hover:bg-signal/90"
                      : "border-line text-ink-secondary hover:border-signal/40 hover:text-ink"
                  }`}
                >
                  {selected && <Check className="h-3.5 w-3.5" />}
                  {inv.name}
                </Button>
              );
            })}
          </div>
        </div>

        {periods.length > 0 && (
          <div>
            <label className="block text-small font-medium text-ink-secondary mb-2">
              Period
            </label>
            <select
              value={selectedPeriod || ""}
              onChange={(e) => setSelectedPeriod(e.target.value || undefined)}
              className="rounded-md border border-line bg-panel px-3 py-2 text-small text-ink font-mono focus:border-signal focus:outline-none focus:ring-1 focus:ring-signal"
            >
              <option value="">Latest</option>
              {periods.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Comparison result */}
      {selectedIds.length < 2 ? (
        <Card className="border-dashed border-2 border-line bg-transparent">
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <div className="rounded-full bg-panel p-4 mb-4">
              <GitCompareArrows className="h-8 w-8 text-ink-faint" />
            </div>
            <h3 className="text-lg font-semibold text-ink mb-2">Select at least 2 investors</h3>
            <p className="text-body text-ink-secondary max-w-md">
              Pick two or more investors above to see their portfolio holdings side by side.
            </p>
          </CardContent>
        </Card>
      ) : isComparing ? (
        <div className="flex items-center justify-center min-h-[40vh]">
          <Loader2 className="h-8 w-8 animate-spin text-signal" />
        </div>
      ) : comparison && comparison.all_tickers.length > 0 ? (
        <Card className="border-line">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">
                Portfolio Comparison — {comparison.period}
              </CardTitle>
              <Badge variant="secondary" className="font-mono">
                {comparison.all_tickers.length} tickers
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-small">
                <thead>
                  <tr className="border-b border-line bg-panel">
                    <th className="text-left px-4 py-2.5 font-medium text-ink-secondary sticky left-0 bg-panel z-10">
                      Ticker
                    </th>
                    {comparison.investors.map((inv) => (
                      <th
                        key={inv.investor_id}
                        className="text-center px-4 py-2.5 font-medium text-ink-secondary min-w-[180px]"
                        colSpan={2}
                      >
                        {inv.investor_name}
                      </th>
                    ))}
                  </tr>
                  <tr className="border-b border-line bg-panel/50">
                    <th className="sticky left-0 bg-panel/50 z-10" />
                    {comparison.investors.map((inv) => (
                      <>
                        <th
                          key={`${inv.investor_id}-shares`}
                          className="text-right px-3 py-1.5 font-normal text-micro text-ink-faint uppercase tracking-wider"
                        >
                          Shares
                        </th>
                        <th
                          key={`${inv.investor_id}-value`}
                          className="text-right px-3 py-1.5 font-normal text-micro text-ink-faint uppercase tracking-wider"
                        >
                          Value
                        </th>
                      </>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {comparison.all_tickers.map((ticker) => (
                    <tr key={ticker} className="hover:bg-panel/50 transition-colors">
                      <td className="px-4 py-2 font-mono font-semibold text-signal sticky left-0 bg-canvas z-10">
                        {ticker}
                      </td>
                      {comparison.investors.map((inv) => {
                        const cell = inv.holdings.find(
                          (h) => h.ticker_symbol === ticker
                        );
                        if (!cell || cell.change_type === "not_held") {
                          return (
                            <>
                              <td
                                key={`${inv.investor_id}-${ticker}-s`}
                                className="text-right px-3 py-2 text-ink-faint"
                              >
                                —
                              </td>
                              <td
                                key={`${inv.investor_id}-${ticker}-v`}
                                className="text-right px-3 py-2 text-ink-faint"
                              >
                                —
                              </td>
                            </>
                          );
                        }

                        const changeColors: Record<string, string> = {
                          new_position: "text-green-400",
                          increased: "text-signal",
                          decreased: "text-warning",
                          unchanged: "text-ink-secondary",
                          closed: "text-bearish",
                        };
                        const color = changeColors[cell.change_type] || "text-ink-secondary";

                        return (
                          <>
                            <td
                              key={`${inv.investor_id}-${ticker}-s`}
                              className={`text-right px-3 py-2 font-mono ${color}`}
                            >
                              {cell.shares.toLocaleString()}
                            </td>
                            <td
                              key={`${inv.investor_id}-${ticker}-v`}
                              className={`text-right px-3 py-2 font-mono ${color}`}
                            >
                              {cell.value_usd != null
                                ? `$${(cell.value_usd / 1000).toLocaleString()}K`
                                : "—"}
                            </td>
                          </>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card className="border-dashed border-2 border-line bg-transparent">
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <h3 className="text-lg font-semibold text-ink mb-2">No portfolio data</h3>
            <p className="text-body text-ink-secondary max-w-md">
              The selected investors don&apos;t have any 13F filing data yet. Try syncing them first.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
