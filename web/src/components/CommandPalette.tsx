"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Search, Tv, Hash, TrendingUp, X, Loader2, ArrowRight } from "lucide-react";
import { useTickers, useChannels, useThemes } from "@/lib/hooks";
import { Badge } from "@/components/ui/badge";

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");

  const { data: tickers = [] } = useTickers();
  const { data: channels = [] } = useChannels();
  const { data: themes = [] } = useThemes();

  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  const handleNavigate = useCallback(
    (path: string) => {
      onClose();
      setQuery("");
      router.push(path);
    },
    [onClose, router]
  );

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    handleNavigate(`/?q=${encodeURIComponent(query.trim())}`);
  };

  if (!isOpen) return null;

  const filteredTickers = query.trim()
    ? tickers.filter(
        (t) =>
          t.ticker.toLowerCase().includes(query.toLowerCase()) ||
          t.themes?.some((th) => th.toLowerCase().includes(query.toLowerCase()))
      ).slice(0, 5)
    : tickers.slice(0, 5);

  const filteredChannels = query.trim()
    ? channels.filter((c) => c.title.toLowerCase().includes(query.toLowerCase())).slice(0, 4)
    : channels.slice(0, 4);

  const filteredThemes = query.trim()
    ? themes.filter((th) => th.name.toLowerCase().includes(query.toLowerCase())).slice(0, 4)
    : themes.slice(0, 4);

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-16 sm:pt-24 p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-150">
      <div
        className="relative w-full max-w-xl overflow-hidden rounded-xl border bg-popover shadow-2xl text-popover-foreground animate-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Bar Input */}
        <form onSubmit={handleSearchSubmit} className="flex items-center border-b px-4 py-3">
          <Search className="mr-3 h-5 w-5 shrink-0 text-muted-foreground" />
          <input
            type="text"
            autoFocus
            placeholder="Search tickers, channels, themes, or full text (Press Enter)..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 bg-transparent text-base text-foreground placeholder:text-muted-foreground focus:outline-none"
          />
          {query ? (
            <button
              type="button"
              onClick={() => setQuery("")}
              className="p-1 text-muted-foreground hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </button>
          ) : (
            <kbd className="hidden sm:inline-flex h-5 select-none items-center rounded border bg-muted px-1.5 font-mono text-[10px] text-muted-foreground">
              ESC
            </kbd>
          )}
        </form>

        {/* Results Body */}
        <div className="max-h-96 overflow-y-auto p-2">
          {/* Direct Search Action */}
          {query.trim() && (
            <div
              onClick={() => handleNavigate(`/?q=${encodeURIComponent(query.trim())}`)}
              className="flex items-center justify-between rounded-lg px-3 py-2 text-sm cursor-pointer bg-primary/10 text-primary font-medium hover:bg-primary/20 transition-colors mb-2"
            >
              <div className="flex items-center gap-2">
                <Search className="h-4 w-4" />
                <span>Search full transcripts for &quot;{query}&quot;</span>
              </div>
              <ArrowRight className="h-4 w-4" />
            </div>
          )}

          {/* Tickers Section */}
          {filteredTickers.length > 0 && (
            <div className="mb-3">
              <span className="px-3 py-1 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider block">
                Tickers & ETFs
              </span>
              {filteredTickers.map((t) => (
                <div
                  key={t.ticker}
                  onClick={() => handleNavigate(`/tickers/${t.ticker}`)}
                  className="flex items-center justify-between rounded-lg px-3 py-2 text-sm cursor-pointer hover:bg-muted/60 transition-colors"
                >
                  <div className="flex items-center gap-2.5">
                    <TrendingUp className="h-4 w-4 text-primary shrink-0" />
                    <span className="font-bold font-mono">${t.ticker}</span>
                    {t.is_etf && (
                      <Badge variant="outline" className="text-[9px] text-warning border-warning/30 bg-warning/10 px-1 py-0">
                        ETF
                      </Badge>
                    )}
                  </div>
                  <span className="text-xs text-muted-foreground font-mono">
                    {t.total_mentions} mentions
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Channels Section */}
          {filteredChannels.length > 0 && (
            <div className="mb-3">
              <span className="px-3 py-1 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider block">
                Channels
              </span>
              {filteredChannels.map((c) => (
                <div
                  key={c.id}
                  onClick={() => handleNavigate(`/channels/${c.id}`)}
                  className="flex items-center justify-between rounded-lg px-3 py-2 text-sm cursor-pointer hover:bg-muted/60 transition-colors"
                >
                  <div className="flex items-center gap-2.5">
                    <Tv className="h-4 w-4 text-muted-foreground shrink-0" />
                    <span className="font-medium truncate max-w-[320px]">{c.title}</span>
                  </div>
                  <span className="text-xs text-muted-foreground">View Channel →</span>
                </div>
              ))}
            </div>
          )}

          {/* Themes Section */}
          {filteredThemes.length > 0 && (
            <div>
              <span className="px-3 py-1 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider block">
                Themes & Sectors
              </span>
              {filteredThemes.map((th) => (
                <div
                  key={th.id}
                  onClick={() => handleNavigate(`/themes/${th.id}`)}
                  className="flex items-center justify-between rounded-lg px-3 py-2 text-sm cursor-pointer hover:bg-muted/60 transition-colors"
                >
                  <div className="flex items-center gap-2.5">
                    <Hash className="h-4 w-4 text-muted-foreground shrink-0" />
                    <span className="font-medium truncate max-w-[320px]">{th.name}</span>
                  </div>
                  <Badge variant="outline" className="text-[10px] uppercase font-mono">
                    {th.level}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
