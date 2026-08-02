"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Search, LayoutDashboard, Tv, Hash, Activity, AudioLines, X, CandlestickChart } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "./ui/button";
import { useChannels } from "@/lib/hooks";

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

const navItems = [
  { href: "/search", label: "Search", icon: Search },
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/channels", label: "Channels", icon: Tv },
  { href: "/themes", label: "Themes", icon: Hash },
  { href: "/tickerflow", label: "Tickerflow", icon: CandlestickChart },
  { href: "/activity", label: "Activity", icon: Activity },
];

export function Sidebar({ isOpen = false, onClose }: SidebarProps) {
  const pathname = usePathname();
  const { data: channels = [] } = useChannels();

  const isLinkActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <>
      {/* Mobile Drawer Overlay Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-scrim md:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex h-full w-60 flex-col border-r border-line bg-canvas transition-transform duration-200 ease-out md:static md:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Brand — a ticker plate, not an icon + word */}
        <div className="flex h-12 items-center justify-between border-b border-line px-4">
          <Link href="/" onClick={onClose} className="flex items-center gap-2.5">
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-signal font-display text-body font-bold tracking-tight text-black">
              C
            </span>
            <span className="flex flex-col leading-none">
              <span className="font-display text-title font-semibold tracking-tight text-ink">
                Carry
              </span>
              {/* <span className="mt-1 font-mono text-micro uppercase tracking-[0.12em] text-ink-faint">
                market commentary
              </span> */}
            </span>
          </Link>
          {onClose && (
            <Button
              variant="ghost"
              size="icon-sm"
              className="md:hidden text-ink-faint"
              onClick={onClose}
              aria-label="Close sidebar"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* Nav */}
        <div className="flex-1 overflow-y-auto py-3">
          <nav className="grid items-start gap-0.5 px-2.5">
            {navItems.map((item) => {
              const active = isLinkActive(item.href);
              const Icon = item.icon;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onClose}
                  className={cn(
                    "group relative flex items-center gap-2.5 rounded-md px-2.5 py-[7px] text-body font-medium transition-colors",
                    active
                      ? "bg-panel text-signal"
                      : "text-ink-secondary hover:bg-panel hover:text-ink"
                  )}
                >
                  {active && (
                    <span className="absolute inset-y-1 left-0 w-0.5 rounded-full bg-signal" />
                  )}
                  <Icon
                    className={cn(
                      "h-4 w-4",
                      active ? "text-signal" : "text-ink-faint group-hover:text-ink-secondary"
                    )}
                  />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Watch status — live tape line */}
        <div className="border-t border-line px-4 py-3">
          <p className="font-mono text-micro uppercase tracking-[0.12em] text-ink-faint">
            watching
          </p>
          <p className="mt-0.5 flex items-center gap-1.5 font-mono text-small text-ink-secondary">
            <span className="h-1.5 w-1.5 rounded-full bg-signal" aria-hidden="true" />
            {channels.length} channel{channels.length === 1 ? "" : "s"} · live
          </p>
        </div>
      </aside>
    </>
  );
}
