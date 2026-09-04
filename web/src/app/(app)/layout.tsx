"use client";

import { useMe } from "@/lib/hooks";
import { AppShell } from "@/components/AppShell";
import { InviteGate } from "@/components/InviteGate";

export default function AppLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const { data: me, isLoading, isError, inviteRequired, error } = useMe();

  // Signed in but hasn't redeemed an invite → show the gate.
  if (inviteRequired) {
    return <InviteGate email={me?.email ?? null} />;
  }

  // Transient failure (network blip / expired session) - render the shell
  // anyway; Clerk's proxy redirects unauthenticated page loads to sign-in.
  if (isError && !inviteRequired && !(error instanceof Error && error.message === "Network request failed")) {
    return <AppShell>{children}</AppShell>;
  }

  return (
    <AppShell fullName={me?.full_name ?? me?.email ?? null} isAdmin={me?.role === "admin"} loading={isLoading}>
      {children}
    </AppShell>
  );
}
