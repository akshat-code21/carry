"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, Bell, Home, LayoutDashboard, Tv, Hash, TrendingUp, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "./ui/button";

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

const navItems = [
  { href: "/", label: "Search", icon: Home },
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/channels", label: "Channels", icon: Tv },
  { href: "/themes", label: "Themes", icon: Hash },
  { href: "/tickerflow", label: "TickerFlow", icon: BarChart3 },
  { href: "/activity", label: "Activity", icon: Bell },
];

export function Sidebar({ isOpen = false, onClose }: SidebarProps) {
  const pathname = usePathname();

  const isLinkActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <>
      {/* Mobile Drawer Overlay Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-xs md:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex h-full w-64 flex-col border-r bg-card/95 backdrop-blur-md transition-transform duration-200 ease-out md:static md:translate-x-0 md:bg-muted/40",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-14 items-center justify-between border-b px-6">
          <Link href="/" onClick={onClose} className="flex items-center gap-2 font-semibold">
            <TrendingUp className="h-6 w-6 text-primary" />
            <span className="font-heading text-base font-bold tracking-tight">YT Chatter</span>
          </Link>
          {onClose && (
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 md:hidden"
              onClick={onClose}
              aria-label="Close sidebar"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>

        <div className="flex-1 overflow-y-auto py-4">
          <nav className="grid items-start gap-1 px-3 text-sm font-medium">
            {navItems.map((item) => {
              const active = isLinkActive(item.href);
              const Icon = item.icon;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onClose}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                    active
                      ? "bg-primary/10 text-primary font-semibold"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  )}
                >
                  <Icon className={cn("h-4 w-4", active ? "text-primary" : "text-muted-foreground")} />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </aside>
    </>
  );
}
