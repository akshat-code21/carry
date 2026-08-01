"use client";

import { Bell, Menu, Moon, Sun, Search } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { api, type ActivityEvent } from "@/lib/api";
import { Button } from "./ui/button";
import { useTheme } from "./ThemeProvider";
import { useUnreadCount } from "@/lib/hooks";

import { eventLabel, eventBadgeClass, timeAgo } from "@/lib/activity";

interface TopbarProps {
  onMenuClick?: () => void;
  onOpenCommandPalette?: () => void;
}

export function Topbar({ onMenuClick, onOpenCommandPalette }: TopbarProps) {
  const { theme, setTheme } = useTheme();
  const { data: unreadData, refetch: refetchUnread } = useUnreadCount();
  const unread = unreadData?.count || 0;
  const [open, setOpen] = useState(false);
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

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
    setTheme(theme === "light" ? "dark" : "light");
  };

  const openPanel = async () => {
    const next = !open;
    setOpen(next);
    if (!next) return;
    setLoading(true);
    try {
      const list = await api.getActivity({ limit: 15 });
      setEvents(list);
      await refetchUnread();
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
      await refetchUnread();
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
        await refetchUnread();
      } catch {
        // ignore
      }
    }
    setOpen(false);
  };

  return (
    <header className="flex h-14 items-center justify-between gap-4 border-b bg-background/95 backdrop-blur-md px-4 md:px-6 lg:h-[60px]">
      <div className="flex items-center gap-2">
        {onMenuClick && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onMenuClick}
            className="md:hidden text-muted-foreground hover:text-foreground"
            aria-label="Open sidebar menu"
          >
            <Menu className="h-5 w-5" />
          </Button>
        )}

        {/* ⌘K Search Palette Trigger */}
        <Button
          variant="outline"
          size="sm"
          onClick={onOpenCommandPalette}
          className="hidden sm:flex h-9 w-64 items-center justify-between rounded-lg border-input bg-muted/30 px-3 text-xs text-muted-foreground hover:bg-muted/60 hover:text-foreground"
        >
          <div className="flex items-center gap-2">
            <Search className="h-3.5 w-3.5 text-muted-foreground" />
            <span>Search or command...</span>
          </div>
          <kbd className="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground opacity-100">
            <span className="text-xs">⌘</span>K
          </kbd>
        </Button>
      </div>

      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={onOpenCommandPalette}
          className="sm:hidden text-muted-foreground hover:text-foreground"
          aria-label="Search"
        >
          <Search className="h-5 w-5" />
        </Button>

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
      </div>
    </header>
  );
}
