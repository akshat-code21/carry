"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type HfiInvestor } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { DataTable, type Column } from "@/components/DataTable";
import {
  Plus,
  RefreshCw,
  Trash2,
  ExternalLink,
  FileText,
  Loader2,
  AlertTriangle,
} from "lucide-react";

function InvestorStat({
  investorId,
  kind,
}: {
  investorId: string;
  kind: "content_items" | "reports" | "unread_alerts";
}) {
  const { data: stats } = useQuery({
    queryKey: ["hfi-investor-stats", investorId],
    queryFn: () => api.getHfiInvestorStats(investorId),
  });
  const value = stats?.[kind];
  if (value == null) return <span className="text-ink-faint">-</span>;
  const highlight = kind === "unread_alerts" && value > 0;
  return (
    <span className={`numeric text-small ${highlight ? "font-semibold text-warning" : "text-ink"}`}>
      {value}
    </span>
  );
}

export default function InvestorsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);

  const { data: investors = [], isLoading } = useQuery({
    queryKey: ["hfi-investors"],
    queryFn: () => api.getHfiInvestors(),
  });

  const syncMutation = useMutation({
    mutationFn: (investorId: string) => api.syncHfiInvestor(investorId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hfi-investors"] });
      queryClient.invalidateQueries({ queryKey: ["hfi-investor-stats"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (investorId: string) => api.deleteHfiInvestor(investorId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hfi-investors"] });
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="h-8 w-8 animate-spin text-signal" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Investors"
        description="Track hedge fund managers and their 13F filings"
      >
        <Button onClick={() => setShowCreate(true)} className="gap-2">
          <Plus className="h-4 w-4" />
          Add Investor
        </Button>
      </PageHeader>

      {/* Create modal */}
      {showCreate && (
        <CreateInvestorCard onClose={() => setShowCreate(false)} />
      )}

      {/* Investors grid */}
      {investors.length === 0 ? (
        <Card className="border-dashed border-2 border-line bg-transparent">
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <div className="rounded-full bg-panel p-4 mb-4">
              <FileText className="h-8 w-8 text-ink-faint" />
            </div>
            <h3 className="text-lg font-semibold text-ink mb-2">No investors yet</h3>
            <p className="text-body text-ink-secondary max-w-sm mb-6">
              Add a hedge fund manager to start tracking their 13F filings, portfolio changes, and investment theses.
            </p>
            <Button onClick={() => setShowCreate(true)} className="gap-2">
              <Plus className="h-4 w-4" />
              Add Your First Investor
            </Button>
          </CardContent>
        </Card>
      ) : (
        <DataTable
          columns={investorColumns(
            (id) => syncMutation.mutate(id),
            (inv) => {
              if (confirm(`Delete "${inv.name}"? This cannot be undone.`)) {
                deleteMutation.mutate(inv.id);
              }
            },
            (id) => syncMutation.isPending && syncMutation.variables === id
          )}
          data={investors}
          keyExtractor={(inv) => inv.id}
          onRowClick={(inv) => router.push(`/investors/${inv.id}`)}
        />
      )}
    </div>
  );
}

function investorColumns(
  onSync: (investorId: string) => void,
  onDelete: (investor: HfiInvestor) => void,
  isSyncing: (investorId: string) => boolean
): Column<HfiInvestor>[] {
  return [
    {
      key: "name",
      header: "Investor",
      render: (inv) => (
        <div className="flex min-w-0 flex-col gap-0.5 py-0.5">
          <Link
            href={`/investors/${inv.id}`}
            className="truncate text-small font-semibold text-ink hover:text-signal hover:underline"
            onClick={(e) => e.stopPropagation()}
          >
            {inv.name}
          </Link>
          {inv.description && (
            <span className="truncate text-caption text-ink-faint" title={inv.description}>
              {inv.description}
            </span>
          )}
        </div>
      ),
    },
    {
      key: "status",
      header: "Status",
      headerClassName: "w-24",
      render: (inv) => (
        <Badge variant={inv.is_active ? "default" : "secondary"} className="font-mono text-signal-foreground! tracking-wider">
          {inv.is_active ? "ACTIVE" : "INACTIVE"}
        </Badge>
      ),
    },
    {
      key: "cik",
      header: "CIK",
      headerClassName: "w-28",
      render: (inv) =>
        inv.cik_number ? (
          <a
            href={`https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=${inv.cik_number}&type=13F-HR`}
            target="_blank"
            rel="noopener noreferrer"
            className="numeric inline-flex items-center gap-1 text-caption text-ink-secondary hover:text-signal hover:underline"
            onClick={(e) => e.stopPropagation()}
            title="View 13F filings on SEC EDGAR"
          >
            {inv.cik_number}
            <ExternalLink className="h-3 w-3" />
          </a>
        ) : (
          <span className="text-ink-faint">-</span>
        ),
    },
    {
      key: "content_items",
      header: "Items",
      numeric: true,
      headerClassName: "w-14",
      render: (inv) => <InvestorStat investorId={inv.id} kind="content_items" />,
    },
    {
      key: "reports",
      header: "Reports",
      numeric: true,
      headerClassName: "w-16",
      render: (inv) => <InvestorStat investorId={inv.id} kind="reports" />,
    },
    {
      key: "unread_alerts",
      header: "Alerts",
      numeric: true,
      headerClassName: "w-14",
      render: (inv) => <InvestorStat investorId={inv.id} kind="unread_alerts" />,
    },
    {
      key: "last_synced_at",
      header: "Synced",
      numeric: true,
      headerClassName: "w-24",
      render: (inv) => (
        <span className="numeric text-caption text-ink-faint">
          {inv.last_synced_at
            ? new Date(inv.last_synced_at).toLocaleDateString(undefined, {
              month: "short",
              day: "numeric",
            })
            : "never"}
        </span>
      ),
    },
    {
      key: "actions",
      header: "",
      headerClassName: "w-20",
      render: (inv) => (
        <div className="flex items-center justify-end gap-0.5">
          <Button
            variant="ghost"
            size="icon-sm"
            className="text-ink-faint hover:text-signal"
            title={isSyncing(inv.id) ? "Syncing…" : "Sync 13F filings"}
            disabled={isSyncing(inv.id)}
            onClick={(e) => {
              e.stopPropagation();
              onSync(inv.id);
            }}
          >
            {isSyncing(inv.id) ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <RefreshCw className="h-3.5 w-3.5" />
            )}
          </Button>
          <Button
            variant="ghost"
            size="icon-sm"
            className="text-ink-faint hover:text-bearish"
            title="Delete investor"
            onClick={(e) => {
              e.stopPropagation();
              onDelete(inv);
            }}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      ),
    },
  ];
}

function CreateInvestorCard({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [cik, setCik] = useState("");
  const [description, setDescription] = useState("");

  const createMutation = useMutation({
    mutationFn: () =>
      api.createHfiInvestor({
        name,
        cik_number: cik || undefined,
        description: description || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hfi-investors"] });
      onClose();
    },
  });

  return (
    <Card className="border-signal/40 bg-canvas">
      <CardHeader>
        <CardTitle className="text-lg">Add Investor</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <label className="block text-small font-medium text-ink-secondary mb-1.5">
            Name <span className="text-bearish">*</span>
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-md border border-line bg-panel px-3 py-2 text-body text-ink placeholder:text-ink-faint focus:border-signal focus:outline-none focus:ring-1 focus:ring-signal"
            placeholder="e.g. Berkshire Hathaway"
            autoFocus
          />
        </div>
        <div>
          <label className="block text-small font-medium text-ink-secondary mb-1.5">
            CIK Number
          </label>
          <input
            type="text"
            value={cik}
            onChange={(e) => setCik(e.target.value)}
            className="w-full rounded-md border border-line bg-panel px-3 py-2 text-body text-ink placeholder:text-ink-faint focus:border-signal focus:outline-none focus:ring-1 focus:ring-signal font-mono"
            placeholder="e.g. 1067983"
          />
          <p className="mt-1 text-micro text-ink-faint">
            Find CIK on{" "}
            <a href="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany" target="_blank" rel="noopener noreferrer" className="text-signal hover:underline">
              SEC EDGAR
            </a>
          </p>
        </div>
        <div>
          <label className="block text-small font-medium text-ink-secondary mb-1.5">
            Description
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={2}
            className="w-full rounded-md border border-line bg-panel px-3 py-2 text-body text-ink placeholder:text-ink-faint focus:border-signal focus:outline-none focus:ring-1 focus:ring-signal resize-none"
            placeholder="Optional notes about this investor"
          />
        </div>
        <div className="flex items-center justify-end gap-3 pt-2">
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={() => createMutation.mutate()}
            disabled={!name.trim() || createMutation.isPending}
            className="gap-2 bg-signal text-black hover:bg-signal/90"
          >
            {createMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            Add Investor
          </Button>
        </div>
        {createMutation.isError && (
          <div className="flex items-center gap-2 text-small text-bearish mt-2">
            <AlertTriangle className="h-4 w-4" />
            <span>{(createMutation.error as Error)?.message || "Failed to create investor"}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
