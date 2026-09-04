"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useRedeemInvite } from "@/lib/hooks";
import { ApiError } from "@/lib/auth-client";

/**
 * Full-screen gate shown when the signed-in account has not redeemed an
 * invite yet (invite-only beta). Pre-fills from ?invite= or a stored code.
 */
function readPendingCode(): string {
  if (typeof window === "undefined") return "";
  const fromUrl = new URLSearchParams(window.location.search).get("invite");
  if (fromUrl) {
    // Strip ?invite= so the code doesn't linger in the address bar
    const params = new URLSearchParams(window.location.search);
    params.delete("invite");
    const next = params.toString();
    window.history.replaceState(
      {},
      "",
      `${window.location.pathname}${next ? `?${next}` : ""}`
    );
    window.localStorage.setItem("pending_invite_code", fromUrl);
    return fromUrl;
  }
  return window.localStorage.getItem("pending_invite_code") ?? "";
}

export function InviteGate({ email }: { email?: string | null }) {
  const redeem = useRedeemInvite();
  const [code, setCode] = useState(readPendingCode);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    setError(null);
    if (!code.trim()) return;
    try {
      await redeem.mutateAsync(code.trim());
      window.localStorage.removeItem("pending_invite_code");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Try again.");
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-canvas p-4">
      <div className="w-full max-w-md rounded-xl border border-line bg-panel p-8 shadow-lg">
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-signal font-display text-body font-bold text-black">
          C
        </div>
        <h1 className="mt-5 font-display text-title font-semibold tracking-tight text-ink">
          You&apos;re on the list
        </h1>
        <p className="mt-1.5 text-body leading-relaxed text-ink-secondary">
          Carry is currently invite-only
          {email ? (
            <> for <span className="font-medium text-ink">{email}</span></>
          ) : null}
          . Enter your invite code to unlock access.
        </p>

        <div className="mt-6 flex gap-2">
          <Input
            value={code}
            onChange={(e) => setCode(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit()}
            placeholder="Paste invite code"
            className="font-mono"
            autoFocus
          />
          <Button onClick={submit} disabled={redeem.isPending || !code.trim()}>
            {redeem.isPending ? "Checking…" : "Redeem"}
          </Button>
        </div>

        {error && <p className="mt-3 text-small text-bearish">{error}</p>}

        <p className="mt-6 font-mono text-micro leading-relaxed text-ink-faint">
          Don&apos;t have a code? Ask the team for an invite — each code is
          single-use and can be bound to your email.
        </p>
      </div>
    </div>
  );
}
