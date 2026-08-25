"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type HfiInvestor } from "@/lib/api";
import { PageHeader } from "@/components/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Plus,
  RefreshCw,
  Trash2,
  ExternalLink,
  Clock,
  FileText,
  AlertTriangle,
  Loader2,
} from "lucide-react";

export default function InvestorsPage() {
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
        <Button onClick={() => setShowCreate(true)} className="gap-2 bg-signal text-black hover:bg-signal/90">
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
            <Button onClick={() => setShowCreate(true)} className="gap-2 bg-signal text-black hover:bg-signal/90">
              <Plus className="h-4 w-4" />
              Add Your First Investor
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {investors.map((investor) => (
            <InvestorCard
              key={investor.id}
              investor={investor}
              onSync={() => syncMutation.mutate(investor.id)}
              onDelete={() => {
                if (confirm(`Delete "${investor.name}"? This cannot be undone.`)) {
                  deleteMutation.mutate(investor.id);
                }
              }}
              isSyncing={syncMutation.isPending && syncMutation.variables === investor.id}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function InvestorCard({
  investor,
  onSync,
  onDelete,
  isSyncing,
}: {
  investor: HfiInvestor;
  onSync: () => void;
  onDelete: () => void;
  isSyncing: boolean;
}) {
  const { data: stats } = useQuery({
    queryKey: ["hfi-investor-stats", investor.id],
    queryFn: () => api.getHfiInvestorStats(investor.id),
  });

  return (
    <Card className="group border-line bg-canvas hover:border-signal/30 transition-colors">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-lg font-semibold text-ink truncate">
              <Link href={`/investors/${investor.id}`} className="hover:text-signal hover:underline">
                {investor.name}
              </Link>
            </CardTitle>
            {investor.description && (
              <p className="text-small text-ink-secondary mt-1 line-clamp-2">
                {investor.description}
              </p>
            )}
          </div>
          <Badge
            variant={investor.is_active ? "default" : "secondary"}
            className={investor.is_active ? "bg-signal text-signal border-signal/30" : ""}
          >
            {investor.is_active ? "Active" : "Inactive"}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* CIK */}
        {investor.cik_number && (
          <div className="flex items-center gap-2 text-small text-ink-secondary">
            <ExternalLink className="h-3.5 w-3.5 shrink-0" />
            <span className="font-mono">CIK: {investor.cik_number}</span>
            <a
              href={`https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=${investor.cik_number}&type=13F-HR`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-signal hover:underline ml-auto text-micro"
            >
              SEC →
            </a>
          </div>
        )}

        {/* Stats row */}
        <div className="grid grid-cols-3 gap-3">
          <div className="text-center p-2 rounded-md bg-panel">
            <p className="font-mono text-lg font-semibold text-ink">{stats?.content_items ?? "—"}</p>
            <p className="text-micro text-ink-faint uppercase tracking-wider">Items</p>
          </div>
          <div className="text-center p-2 rounded-md bg-panel">
            <p className="font-mono text-lg font-semibold text-ink">{stats?.reports ?? "—"}</p>
            <p className="text-micro text-ink-faint uppercase tracking-wider">Reports</p>
          </div>
          <div className="text-center p-2 rounded-md bg-panel">
            <p className="font-mono text-lg font-semibold text-signal">{stats?.unread_alerts ?? "—"}</p>
            <p className="text-micro text-ink-faint uppercase tracking-wider">Alerts</p>
          </div>
        </div>

        {/* Last synced */}
        <div className="flex items-center gap-1.5 text-micro text-ink-faint">
          <Clock className="h-3 w-3" />
          {investor.last_synced_at
            ? `Synced ${new Date(investor.last_synced_at).toLocaleDateString()}`
            : "Never synced"}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 pt-1">
          <Link href={`/investors/${investor.id}`} className="flex-1">
            <Button
              variant="outline"
              size="sm"
              className="w-full gap-1.5 text-small border-line text-ink hover:text-signal hover:border-signal/40"
            >
              View Holdings →
            </Button>
          </Link>
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5 text-small text-ink-secondary hover:text-ink"
            onClick={onSync}
            disabled={isSyncing}
          >
            {isSyncing ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <RefreshCw className="h-3.5 w-3.5" />
            )}
            {isSyncing ? "Syncing…" : "Sync"}
          </Button>
          <Button
            variant="ghost"
            size="icon-sm"
            className="text-ink-faint hover:text-red-400"
            onClick={onDelete}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
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
            Name <span className="text-red-400">*</span>
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
          <div className="flex items-center gap-2 text-small text-red-400 mt-2">
            <AlertTriangle className="h-4 w-4" />
            <span>{(createMutation.error as Error)?.message || "Failed to create investor"}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
