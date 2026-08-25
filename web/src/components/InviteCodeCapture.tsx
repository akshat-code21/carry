"use client";

import { useEffect } from "react";

/**
 * Captures ?invite=CODE on the sign-in/sign-up pages and stashes it in
 * localStorage, because Clerk's post-signup redirect drops query params.
 * The InviteGate picks it up from localStorage after signup.
 */
export function InviteCodeCapture() {
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("invite");
    if (!code) return;
    window.localStorage.setItem("pending_invite_code", code);
    params.delete("invite");
    const next = params.toString();
    window.history.replaceState(
      {},
      "",
      `${window.location.pathname}${next ? `?${next}` : ""}`
    );
  }, []);
  return null;
}
