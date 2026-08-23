"use client";

import { Bell, Menu, Moon, Sun, Search } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { UserButton, useUser } from "@clerk/nextjs";
import { api, type ActivityEvent } from "@/lib/api";
import { Button } from "./ui/button";
import { useTheme } from "./ThemeProvider";
import { useUnreadCount } from "@/lib/hooks";

import { eventLabel, eventBadgeClass, timeAgo } from "@/lib/activity";

interface TopbarProps {
  onMenuClick?: () => void;
  onOpenCommandPalette?: () => void;
  fullName?: string | null;
  loadingUser?: boolean;
}

export function Topbar({ onMenuClick, onOpenCommandPalette, fullName, loadingUser }: TopbarProps) {
  const { theme, setTheme } = useTheme();
  const { isSignedIn } = useUser();
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
    <header className="flex h-12 shrink-0 items-center justify-between gap-4 border-b border-line bg-canvas px-3 md:px-5">
      <div className="flex items-center gap-2">
        {onMenuClick && (
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={onMenuClick}
            className="md:hidden text-ink-faint hover:text-ink"
            aria-label="Open sidebar menu"
          >
            <Menu className="h-4 w-4" />
          </Button>
        )}

        {/* ⌘K Search Palette Trigger */}
        <Button
          variant="outline"
          size="sm"
          onClick={onOpenCommandPalette}
          className="hidden sm:flex h-8 w-72 items-center justify-between rounded-md border-line bg-panel px-3 text-small text-ink-faint hover:bg-panel-raised hover:text-ink"
        >
          <div className="flex items-center gap-2">
            <Search className="h-3.5 w-3.5 text-ink-faint" />
            <span className="font-mono text-caption">Search...</span>
          </div>
          <kbd className="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border border-line bg-canvas px-1.5 font-mono text-micro font-medium text-ink-faint">
            <span className="text-caption">⌘</span>K
          </kbd>
        </Button>
      </div>

      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={onOpenCommandPalette}
          className="sm:hidden text-ink-faint hover:text-ink"
          aria-label="Search"
        >
          <Search className="h-4 w-4" />
        </Button>

        <div className="relative" ref={panelRef}>
          <Button variant="ghost" size="icon-sm" onClick={openPanel} className="relative text-ink-faint hover:text-ink">
            <Bell className="h-4 w-4" />
            {unread > 0 && (
              <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-signal px-1 font-mono text-micro font-semibold text-black">
                {unread > 99 ? "99+" : unread}
              </span>
            )}
            <span className="sr-only">Activity notifications</span>
          </Button>

          {open && (
            <div className="absolute right-0 z-50 mt-2 w-[360px] max-w-[calc(100vw-2rem)] overflow-hidden rounded-lg border border-line bg-panel shadow-xl">
              <div className="flex items-center justify-between border-b border-line px-3 py-2">
                <span className="font-display text-small font-semibold text-ink">
                  Activity
                </span>
                <div className="flex items-center gap-3">
                  {unread > 0 && (
                    <button
                      type="button"
                      onClick={handleMarkAll}
                      className="font-mono text-micro text-ink-faint hover:text-ink"
                    >
                      Mark all read
                    </button>
                  )}
                  <Link
                    href="/activity"
                    onClick={() => setOpen(false)}
                    className="font-mono text-micro text-signal hover:underline"
                  >
                    View all
                  </Link>
                </div>
              </div>
              <div className="max-h-80 overflow-y-auto">
                {loading && (
                  <p className="px-3 py-6 text-center text-small text-ink-faint">
                    Loading…
                  </p>
                )}
                {!loading && events.length === 0 && (
                  <p className="px-3 py-6 text-center text-small text-ink-faint">
                    Nothing to flag yet — new uploads and processing results land here.
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
                        className={`block border-b border-line px-3 py-2.5 transition-colors hover:bg-panel-raised ${event.read_at ? "opacity-70" : ""
                          }`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <span
                            className={`rounded px-1.5 py-0.5 font-mono text-micro font-medium ${eventBadgeClass(
                              event.event_type
                            )}`}
                          >
                            {eventLabel(event.event_type)}
                          </span>
                          <span className="shrink-0 font-mono text-micro text-ink-faint">
                            {timeAgo(event.created_at)}
                          </span>
                        </div>
                        <p className="mt-1 line-clamp-2 text-body leading-snug">
                          {event.message}
                        </p>
                      </Link>
                    );
                  })}
              </div>
            </div>
          )}
        </div>

        <Button variant="ghost" size="icon-sm" onClick={toggleTheme} className="text-ink-faint hover:text-ink">
          {theme === "light" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
          <span className="sr-only">Toggle theme</span>
        </Button>

        {/* Account */}
        {loadingUser ? (
          <div className="ml-1 h-6 w-6 animate-pulse rounded-full bg-panel-raised" />
        ) : isSignedIn ? (
          <div className="ml-1 flex items-center gap-2">
            {fullName && (
              <span className="hidden font-mono text-micro text-ink-secondary sm:block">
                {fullName}
              </span>
            )}
            <UserButton />
          </div>
        ) : null}
      </div>
    </header>
  );
}
