"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import { api } from "@/lib/api";

/**
 * Fire-and-forget product analytics. Events are attributed server-side to the
 * authenticated user; failures are swallowed so tracking never breaks the UI.
 */
export function track(type: string, data: Record<string, unknown> = {}): void {
  if (typeof window === "undefined") return;
  // Dedupe rapid double-fires of identical events (React strict-mode effects)
  const key = `${type}:${JSON.stringify(data)}`;
  const now = Date.now();
  const last = (lastFired.get(key) ?? 0);
  lastFired.set(key, now);
  if (now - last < 400) return;

  void api.sendClientEvents([{ type, data }]);
}

const lastFired = new Map<string, number>();

/** Tracks route changes as page views - mount once inside the app shell. */
export function usePageViewTracking(): void {
  const pathname = usePathname();
  useEffect(() => {
    if (!pathname) return;
    track("page_viewed", { route: pathname });
  }, [pathname]);
}
