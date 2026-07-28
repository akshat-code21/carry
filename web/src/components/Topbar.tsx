"use client";

import { Bell, Moon, Sun } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { api, type ActivityEvent } from "@/lib/api";
import { Button } from "./ui/button";

function eventLabel(type: string): string {
  switch (type) {
    case "video_detected":
      return "Detected";
    case "video_processed":
      return "Ready";
    case "video_failed":
      return "Failed";
    default:
      return type;
  }
}

function eventBadgeClass(type: string): string {
  switch (type) {
    case "video_detected":
      return "bg-blue-500/15 text-blue-600 dark:text-blue-400";
    case "video_processed":
      return "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400";
    case "video_failed":
      return "bg-red-500/15 text-red-600 dark:text-red-400";
    default:
      return "bg-muted text-muted-foreground";
  }
}

function timeAgo(iso: string): string {
  const then = new Date(iso).getTime();
  const sec = Math.max(0, Math.floor((Date.now() - then) / 1000));
  if (sec < 60) return `${sec}s ago`;
  if (sec < 3600) return `${Math.floor(sec / 60)}m ago`;
  if (sec < 86400) return `${Math.floor(sec / 3600)}h ago`;
  return `${Math.floor(sec / 86400)}d ago`;
}

export function Topbar() {
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [unread, setUnread] = useState(0);
  const [open, setOpen] = useState(false);
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const isDark = document.documentElement.classList.contains("dark");
    setTheme(isDark ? "dark" : "light");
  }, []);

  const refreshUnread = useCallback(async () => {
    try {
      const res = await api.getActivityUnreadCount();
      setUnread(res.count);
    } catch {
      // API may be down during local boot — ignore
    }
  }, []);

  useEffect(() => {
    refreshUnread();
    const id = setInterval(refreshUnread, 30_000);
    return () => clearInterval(id);
  }, [refreshUnread]);

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, [open]);

  const toggleTheme = () => {
    const newTheme = theme === "light" ? "dark" : "light";
    setTheme(newTheme);
    if (newTheme === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  };

  const openPanel = async () => {
    const next = !open;
    setOpen(next);
    if (!next) return;
    setLoading(true);
    try {
      const list = await api.getActivity({ limit: 15 });
      setEvents(list);
      await refreshUnread();
    } catch {
      setEvents([]);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAll = async () => {
    try {
      await api.markAllActivityRead();
      setEvents((prev) =>
        prev.map((e) => ({ ...e, read_at: e.read_at ?? new Date().toISOString() }))
      );
      setUnread(0);
    } catch {
      // ignore
    }
  };

  const handleClickEvent = async (event: ActivityEvent) => {
    if (!event.read_at) {
      try {
        await api.markActivityRead(event.id);
        setEvents((prev) =>
          prev.map((e) =>
            e.id === event.id ? { ...e, read_at: new Date().toISOString() } : e
          )
        );
        setUnread((c) => Math.max(0, c - 1));
      } catch {
        // ignore
      }
    }
    setOpen(false);
  };

  return (
    <header className="flex h-14 items-center gap-4 border-b bg-muted/40 px-6 lg:h-[60px]">
      <div className="w-full flex-1" />

      <div className="relative" ref={panelRef}>
        <Button variant="ghost" size="icon" onClick={openPanel} className="relative">
          <Bell className="h-5 w-5" />
          {unread > 0 && (
            <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-semibold text-primary-foreground">
              {unread > 99 ? "99+" : unread}
            </span>
          )}
          <span className="sr-only">Activity notifications</span>
        </Button>

        {open && (
          <div className="absolute right-0 z-50 mt-2 w-[360px] max-w-[calc(100vw-2rem)] overflow-hidden rounded-lg border bg-background shadow-lg">
            <div className="flex items-center justify-between border-b px-3 py-2">
              <span className="text-sm font-semibold">Activity</span>
              <div className="flex items-center gap-2">
                {unread > 0 && (
                  <button
                    type="button"
                    onClick={handleMarkAll}
                    className="text-xs text-muted-foreground hover:text-foreground"
                  >
                    Mark all read
                  </button>
                )}
                <Link
                  href="/activity"
                  onClick={() => setOpen(false)}
                  className="text-xs text-primary hover:underline"
                >
                  View all
                </Link>
              </div>
            </div>
            <div className="max-h-80 overflow-y-auto">
              {loading && (
                <p className="px-3 py-6 text-center text-sm text-muted-foreground">
                  Loading…
                </p>
              )}
              {!loading && events.length === 0 && (
                <p className="px-3 py-6 text-center text-sm text-muted-foreground">
                  No activity yet. New channel videos will show up here.
                </p>
              )}
              {!loading &&
                events.map((event) => {
                  const href = event.video_id
                    ? `/videos/${event.video_id}`
                    : `/channels/${event.channel_id}`;
                  return (
                    <Link
                      key={event.id}
                      href={href}
                      onClick={() => handleClickEvent(event)}
                      className={`block border-b px-3 py-2.5 transition-colors hover:bg-muted/50 ${
                        event.read_at ? "opacity-70" : ""
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <span
                          className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${eventBadgeClass(
                            event.event_type
                          )}`}
                        >
                          {eventLabel(event.event_type)}
                        </span>
                        <span className="shrink-0 text-[10px] text-muted-foreground">
                          {timeAgo(event.created_at)}
                        </span>
                      </div>
                      <p className="mt-1 line-clamp-2 text-sm leading-snug">
                        {event.message}
                      </p>
                    </Link>
                  );
                })}
            </div>
          </div>
        )}
      </div>

      <Button variant="ghost" size="icon" onClick={toggleTheme}>
        {theme === "light" ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
        <span className="sr-only">Toggle theme</span>
      </Button>
    </header>
  );
}
