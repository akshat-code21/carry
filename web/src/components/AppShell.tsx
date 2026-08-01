"use client";

import { useState, useEffect, type ReactNode } from "react";
import { Sidebar } from "@/components/Sidebar";
import { Topbar } from "@/components/Topbar";
import { CommandPalette } from "@/components/CommandPalette";

export function AppShell({ children }: { children: ReactNode }) {
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);

  // Global ⌘K / Ctrl+K listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setCommandPaletteOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div className="flex h-full overflow-hidden bg-background">
      <Sidebar
        isOpen={mobileSidebarOpen}
        onClose={() => setMobileSidebarOpen(false)}
      />

      <div className="flex flex-1 flex-col overflow-hidden">
        <Topbar
          onMenuClick={() => setMobileSidebarOpen(true)}
          onOpenCommandPalette={() => setCommandPaletteOpen(true)}
        />
        <main className="flex-1 overflow-y-auto bg-muted/10 p-4 md:p-6 lg:p-8">
          {children}
        </main>
      </div>

      <CommandPalette
        isOpen={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
      />
    </div>
  );
}
