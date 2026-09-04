"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Check, Copy, Link2 as LinkIcon, Plus, ShieldCheck } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import { Skeleton } from "@/components/Skeleton";
import { ErrorState } from "@/components/ErrorState";
import { useMe } from "@/lib/hooks";
import { useChartColors } from "@/lib/useChartColors";
import { api, type InviteDto } from "@/lib/api";

export default function AdminPage() {
  const { isAdmin, isLoading: meLoading } = useMe();

  if (meLoading) return <Skeleton className="h-96" />;
  if (!isAdmin) {
    return (
      <div className="space-y-6">
        <PageHeader title="Admin" description="Restricted area." />
        <ErrorState message="You need admin privileges to view this page." />
      </div>
    );
  }
  return <AdminDashboard />;
}

function AdminDashboard() {
  const [days, setDays] = useState<7 | 30>(30);
  const c = useChartColors();
  const overview = useQuery({
    queryKey: ["platformOverview", days],
    queryFn: () => api.getPlatformOverview(days),
  });
  const data = overview.data;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Admin"
        description="Invite management and platform-wide usage metrics."
      >
        <div className="flex rounded-md border border-line p-0.5">
          {([7, 30] as const).map((r) => (
            <button
              key={r}
              onClick={() => setDays(r)}
              className={`rounded px-2.5 py-1 font-mono text-micro transition-colors ${
                days === r ? "bg-panel text-signal" : "text-ink-faint hover:text-ink"
              }`}
            >
              {r}d
            </button>
          ))}
        </div>
      </PageHeader>

      {overview.isLoading && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      )}
      {overview.isError && (
        <ErrorState message="Failed to load platform metrics." onRetry={() => overview.refetch()} />
      )}

      {data && (
        <>
          {/* Users & engagement */}
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard title="Total users" value={data.users.total} description={`${data.users.pending_invite} pending invite`} />
            <StatCard title="DAU / WAU / MAU" value={`${data.users.dau} / ${data.users.wau} / ${data.users.mau}`} description="Distinct active users" />
            <StatCard title={`Searches (${data.activity.window_days}d)`} value={data.searches.total} description={`${(data.searches.zero_result_rate * 100).toFixed(1)}% zero-result`} />
            <StatCard title={`LLM tokens (${data.activity.window_days}d)`} value={fmt(data.llm.input_tokens + data.llm.output_tokens)} description={`${fmt(data.activity.expensive_ops)} expensive ops`} />
          </div>

          {/* DAU chart */}
          <Card>
            <CardContent className="pt-5">
              <h2 className="font-display text-title font-semibold text-ink">Daily active users</h2>
              <div className="mt-4 h-56">
                {data.daily_active.length === 0 ? (
                  <p className="font-mono text-small text-ink-faint">No activity recorded yet.</p>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data.daily_active} margin={{ top: 8, right: 8, left: -22, bottom: 0 }}>
                      <defs>
                        <linearGradient id="gDau" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor={c.success} stopOpacity={0.35} />
                          <stop offset="100%" stopColor={c.success} stopOpacity={0.02} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke={c.line} vertical={false} />
                      <XAxis dataKey="day" tick={{ fontSize: 10, fill: c.mutedForeground }} tickFormatter={(v: string) => v.slice(5)} tickLine={false} axisLine={false} />
                      <YAxis tick={{ fontSize: 10, fill: c.mutedForeground }} tickLine={false} axisLine={false} allowDecimals={false} />
                      <Tooltip contentStyle={{ backgroundColor: c.canvas, border: `1px solid ${c.line}`, borderRadius: 4, fontSize: 12 }} />
                      <Area type="monotone" dataKey="users" name="Active users" stroke={c.success} fill="url(#gDau)" strokeWidth={1.5} />
                    </AreaChart>
                  </ResponsiveContainer>
                )}
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-4 lg:grid-cols-2">
            {/* Top users */}
            <Card>
              <CardContent className="pt-5">
                <h2 className="font-display text-title font-semibold text-ink">Most active users</h2>
                {data.top_users.length === 0 ? (
                  <p className="mt-3 font-mono text-small text-ink-faint">No user activity yet.</p>
                ) : (
                  <ul className="mt-3 space-y-2">
                    {data.top_users.slice(0, 8).map((u) => (
                      <li key={u.id} className="flex items-center justify-between gap-3 border-b border-line pb-2 last:border-0">
                        <div className="min-w-0">
                          <span className="block truncate text-small text-ink">{u.full_name || u.email}</span>
                          <span className="font-mono text-micro text-ink-faint">{u.email}</span>
                        </div>
                        <div className="shrink-0 text-right font-mono text-micro text-ink-secondary">
                          <div>{u.api_calls} calls</div>
                          <div>{u.searches} searches</div>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>

            {/* Top features + queries */}
            <div className="space-y-4">
              <Card>
                <CardContent className="pt-5">
                  <h2 className="font-display text-title font-semibold text-ink">Feature adoption</h2>
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {data.top_features.length === 0 && (
                      <p className="font-mono text-small text-ink-faint">No page views yet.</p>
                    )}
                    {data.top_features.map((f) => (
                      <Badge key={f.route} variant="secondary" className="font-mono">
                        {f.route} · {f.views}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-5">
                  <h2 className="font-display text-title font-semibold text-ink">Top queries</h2>
                  {data.top_queries.length === 0 ? (
                    <p className="mt-3 font-mono text-small text-ink-faint">No searches yet.</p>
                  ) : (
                    <ul className="mt-3 space-y-1.5">
                      {data.top_queries.slice(0, 6).map((q, i) => (
                        <li key={i} className="flex items-center justify-between gap-3 border-b border-line pb-1.5 last:border-0">
                          <span className="truncate font-mono text-small text-ink-secondary">{q.query}</span>
                          <span className="shrink-0 rounded bg-panel px-1.5 py-0.5 font-mono text-micro tabular-nums text-signal">{q.count}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </>
      )}

      {/* Invites */}
      <InvitesSection />
    </div>
  );
}

function InvitesSection() {
  const queryClient = useQueryClient();
  const invites = useQuery({ queryKey: ["invites"], queryFn: () => api.listInvites() });

  const [email, setEmail] = useState("");
  const [maxUses, setMaxUses] = useState("1");
  const [copied, setCopied] = useState<string | null>(null);

  const create = useMutation({
    mutationFn: () =>
      api.createInvite({
        invited_email: email.trim() || null,
        max_uses: Math.max(1, parseInt(maxUses, 10) || 1),
      }),
    onSuccess: () => {
      setEmail("");
      void queryClient.invalidateQueries({ queryKey: ["invites"] });
    },
  });

  const revoke = useMutation({
    mutationFn: (id: string) => api.revokeInvite(id),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["invites"] }),
  });

  const copy = async (code: string) => {
    await navigator.clipboard.writeText(code);
    setCopied(code);
    setTimeout(() => setCopied(null), 1500);
  };

  const copyLink = async (code: string) => {
    const url = `${window.location.origin}/sign-up?invite=${code}`;
    await navigator.clipboard.writeText(url);
    setCopied(`link:${code}`);
    setTimeout(() => setCopied(null), 1500);
  };

  return (
    <Card>
      <CardContent className="pt-5">
        <h2 className="flex items-center gap-2 font-display text-title font-semibold text-ink">
          <ShieldCheck className="h-4 w-4 text-ink-faint" /> Invites
        </h2>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <Input
            placeholder="Email (optional — binds the code)"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-64"
          />
          <Input
            type="number"
            min={1}
            value={maxUses}
            onChange={(e) => setMaxUses(e.target.value)}
            className="w-20"
            aria-label="Max uses"
          />
          <Button onClick={() => create.mutate()} disabled={create.isPending}>
            <Plus className="mr-1 h-3.5 w-3.5" />
            {create.isPending ? "Creating…" : "Create invite"}
          </Button>
        </div>
        {create.isError && (
          <p className="mt-2 text-small text-bearish">Failed to create invite.</p>
        )}
        <p className="mt-2 font-mono text-micro text-ink-faint">
          Invites grant regular-user access only — promote admins via Clerk
          public metadata (see docs/authentication.md).
        </p>

        <div className="mt-5 overflow-hidden rounded-lg border border-line">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-line bg-panel/50 font-mono text-micro uppercase tracking-wider text-ink-faint">
                <th className="px-3 py-2 font-medium">Code</th>
                <th className="px-3 py-2 font-medium">Bound to</th>
                <th className="px-3 py-2 font-medium">Uses</th>
                <th className="px-3 py-2 font-medium">Status</th>
                <th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody>
              {(invites.data ?? []).map((inv) => (
                <InviteRow
                  key={inv.id}
                  invite={inv}
                  copied={copied === inv.code}
                  copiedLink={copied === `link:${inv.code}`}
                  onCopy={() => copy(inv.code)}
                  onCopyLink={() => copyLink(inv.code)}
                  onRevoke={() => revoke.mutate(inv.id)}
                />
              ))}
              {invites.data?.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-3 py-6 text-center font-mono text-small text-ink-faint">
                    No invites created yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

function InviteRow({
  invite,
  copied,
  copiedLink,
  onCopy,
  onCopyLink,
  onRevoke,
}: {
  invite: InviteDto;
  copied: boolean;
  copiedLink: boolean;
  onCopy: () => void;
  onCopyLink: () => void;
  onRevoke: () => void;
}) {
  const status =
    invite.revoked_at ? "revoked" :
    invite.expires_at && new Date(invite.expires_at) < new Date() ? "expired" :
    invite.uses_count >= invite.max_uses ? "fully used" : "active";

  return (
    <tr className="border-b border-line last:border-0">
      <td className="px-3 py-2">
        <div className="flex items-center gap-2.5">
          <button onClick={onCopy} className="group flex items-center gap-1.5 font-mono text-small text-ink hover:text-signal" title="Copy code">
            {invite.code}
            {copied ? <Check className="h-3 w-3 text-signal" /> : <Copy className="h-3 w-3 opacity-0 transition-opacity group-hover:opacity-60" />}
          </button>
          <button onClick={onCopyLink} className="flex items-center gap-1 font-mono text-micro text-ink-faint hover:text-signal" title="Copy signup link (auto-applies the code)">
            {copiedLink ? <Check className="h-3 w-3 text-signal" /> : <LinkIcon className="h-3 w-3" />}
            link
          </button>
        </div>
      </td>
      <td className="px-3 py-2 font-mono text-small text-ink-secondary">{invite.invited_email ?? "—"}</td>
      <td className="px-3 py-2 font-mono text-small tabular-nums text-ink-secondary">
        {invite.uses_count}/{invite.max_uses}
      </td>
      <td className="px-3 py-2">
        <span
          className={`rounded px-1.5 py-0.5 font-mono text-micro ${
            status === "active" ? "bg-signal/10 text-signal" : "bg-warning/10 text-warning"
          }`}
        >
          {status}
        </span>
      </td>
      <td className="px-3 py-2 text-right">
        {!invite.revoked_at && status !== "fully used" && (
          <Button variant="ghost" size="sm" onClick={onRevoke} className="font-mono text-micro text-ink-faint hover:text-bearish">
            Revoke
          </Button>
        )}
      </td>
    </tr>
  );
}

function fmt(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n ?? 0);
}
