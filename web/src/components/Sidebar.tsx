"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Search,
  LayoutDashboard,
  Tv,
  Hash,
  Activity,
  PanelLeftClose,
  PanelLeftOpen,
  CandlestickChart,
  Gauge,
  ShieldCheck,
  Briefcase,
  Scale,
  GitCompareArrows,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "./ui/button";
import { useChannels } from "@/lib/hooks";

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
  isAdmin?: boolean;
}

const navItems = [
  { href: "/search", label: "Search", icon: Search },
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/channels", label: "Channels", icon: Tv },
  { href: "/themes", label: "Themes", icon: Hash },
  { href: "/tickerflow", label: "Tickerflow", icon: CandlestickChart },
  { href: "/investors", label: "Investors", icon: Briefcase },
  { href: "/consensus", label: "Consensus", icon: Scale },
  // { href: "/compare", label: "Compare", icon: GitCompareArrows },
  { href: "/activity", label: "Activity", icon: Activity },
];

const adminItems = [
  { href: "/usage", label: "Usage", icon: Gauge },
  { href: "/admin", label: "Admin", icon: ShieldCheck },
];

export function Sidebar({
  isOpen = false,
  onClose,
  isCollapsed = false,
  onToggleCollapse,
  isAdmin,
}: SidebarProps) {
  const pathname = usePathname();
  const { data: channels = [] } = useChannels();

  const items = isAdmin ? [...navItems, ...adminItems] : navItems;

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
          "fixed inset-y-0 left-0 z-50 flex h-full shrink-0 flex-col border-r border-line bg-canvas transition-all duration-200 ease-out md:static md:translate-x-0",
          isOpen ? "translate-x-0 w-52" : "-translate-x-full",
          isCollapsed ? "md:w-14" : "md:w-52"
        )}
      >
        {/* Brand Header */}
        <div
          className={cn(
            "flex h-12 items-center border-b border-line",
            isCollapsed ? "justify-center px-2" : "justify-between px-4"
          )}
        >
          {!isCollapsed ? (
            <>
              <Link
                href="/"
                onClick={onClose}
                className="flex items-center gap-2.5 overflow-hidden"
              >
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-signal font-display text-body font-bold tracking-tight text-signal-foreground">
                  C
                </span>
                <span className="flex flex-col leading-none">
                  <span className="font-display text-title font-semibold tracking-tight text-ink">
                    Carry
                  </span>
                </span>
              </Link>
              <Button
                variant="ghost"
                size="icon-sm"
                className="text-ink-faint hover:text-ink"
                onClick={() => {
                  if (isOpen && onClose) {
                    onClose();
                  } else if (onToggleCollapse) {
                    onToggleCollapse();
                  } else if (onClose) {
                    onClose();
                  }
                }}
                aria-label="Close sidebar"
                title="Close sidebar"
              >
                <PanelLeftClose className="h-4 w-4" />
              </Button>
            </>
          ) : (
            <Button
              variant="ghost"
              size="icon-sm"
              className="text-ink-faint hover:text-ink"
              onClick={onToggleCollapse}
              aria-label="Expand sidebar"
              title="Expand sidebar"
            >
              <PanelLeftOpen className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* Nav */}
        <div className="flex-1 overflow-y-auto py-3">
          <nav className={cn("grid items-start gap-px", isCollapsed ? "px-1.5" : "px-2")}>
            {items.map((item) => {
              const active = isLinkActive(item.href);
              const Icon = item.icon;
              const isAdminItem = adminItems.some((a) => a.href === item.href);

              return (
                <div key={item.href}>
                  {/* Section divider — admin tools live under their own overline */}
                  {isAdminItem && adminItems[0].href === item.href && (
                    isCollapsed ? (
                      <div className="my-2 border-t border-line/60 mx-1" />
                    ) : (
                      <p className="label-overline mt-4 mb-1 px-2.5">admin</p>
                    )
                  )}
                  <Link
                    href={item.href}
                    onClick={onClose}
                    title={isCollapsed ? item.label : undefined}
                    className={cn(
                      "group relative flex items-center rounded transition-colors",
                      isCollapsed
                        ? "justify-center px-2 py-2 text-body font-medium"
                        : "gap-2 px-2.5 py-1.5 text-body font-medium",
                      active
                        ? "bg-panel text-ink"
                        : "text-ink-secondary hover:bg-panel hover:text-ink"
                    )}
                  >
                    {active && (
                      <span
                        className={cn(
                          "absolute left-0 w-0.5 rounded-full bg-signal",
                          isCollapsed ? "inset-y-1.5" : "inset-y-0.5"
                        )}
                      />
                    )}
                    <Icon
                      className={cn(
                        "shrink-0",
                        isCollapsed ? "h-4 w-4" : "h-3.5 w-3.5",
                        active ? "text-signal" : "text-ink-faint group-hover:text-ink-secondary"
                      )}
                    />
                    {!isCollapsed && (
                      <span className="truncate">{item.label}</span>
                    )}
                  </Link>
                </div>
              );
            })}
          </nav>
        </div>

        {/* Watch status — live tape line */}
        <div
          className={cn(
            "border-t border-line",
            isCollapsed ? "py-3 flex justify-center" : "px-4 py-3"
          )}
          title={isCollapsed ? `${channels.length} channel${channels.length === 1 ? "" : "s"} · live` : undefined}
        >
          {!isCollapsed ? (
            <>
              <p className="font-mono text-micro uppercase tracking-[0.12em] text-ink-faint">
                watching
              </p>
              <p className="mt-0.5 flex items-center gap-1.5 font-mono text-small text-ink-secondary">
                <span className="h-1.5 w-1.5 rounded-full bg-signal" aria-hidden="true" />
                {channels.length} channel{channels.length === 1 ? "" : "s"} · live
              </p>
            </>
          ) : (
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-signal opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-signal" />
            </span>
          )}
        </div>
      </aside>
    </>
  );
}
