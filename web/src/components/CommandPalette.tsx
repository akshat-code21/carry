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
    handleNavigate(`/search?q=${encodeURIComponent(query.trim())}`);
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

  const allThemesFlat = Array.isArray(themes)
    ? themes.flatMap((sector) => {
        const items: { id: string; name: string; level: string }[] = [{ id: sector.id, name: sector.name, level: sector.level }];
        for (const ind of sector.industries || []) {
          items.push({ id: ind.id, name: ind.name, level: ind.level });
          for (const th of ind.themes || []) {
            items.push({ id: th.id, name: th.name, level: th.level });
          }
        }
        return items;
      })
    : [];

  const filteredThemes = query.trim()
    ? allThemesFlat.filter((th) => th.name.toLowerCase().includes(query.toLowerCase())).slice(0, 4)
    : allThemesFlat.slice(0, 4);


  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-scrim p-4 pt-16 sm:pt-24">
      <div
        className="relative w-full max-w-xl overflow-hidden rounded-lg border border-line-strong bg-panel shadow-2xl text-ink"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Bar Input */}
        <form onSubmit={handleSearchSubmit} className="flex items-center border-b border-line px-4 py-3">
          <Search className="mr-3 h-5 w-5 shrink-0 text-ink-faint" />
          <input
            type="text"
            autoFocus
            placeholder="Search tickers, channels, themes, or full text (Press Enter)..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 bg-transparent text-base text-ink placeholder:text-ink-faint focus:outline-none"
          />
          {query ? (
            <button
              type="button"
              onClick={() => setQuery("")}
              className="p-1 text-ink-faint hover:text-ink"
            >
              <X className="h-4 w-4" />
            </button>
          ) : (
            <kbd className="hidden h-5 select-none items-center rounded border border-line bg-panel-raised px-1.5 font-mono text-micro text-ink-faint sm:inline-flex">
              ESC
            </kbd>
          )}
        </form>

        {/* Results Body */}
        <div className="max-h-96 overflow-y-auto p-2">
          {/* Direct Search Action */}
          {query.trim() && (
            <div
              onClick={() => handleNavigate(`/search?q=${encodeURIComponent(query.trim())}`)}
              className="mb-2 flex cursor-pointer items-center justify-between rounded-md bg-signal/10 px-3 py-2 text-body font-medium text-signal transition-colors hover:bg-signal/20"
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
              <span className="label-overline block px-3 py-1">Tickers &amp; ETFs</span>
              {filteredTickers.map((t) => (
                <div
                  key={t.ticker}
                  onClick={() => handleNavigate(`/tickers/${t.ticker}`)}
                  className="flex cursor-pointer items-center justify-between rounded-md px-3 py-2 text-body transition-colors hover:bg-panel-raised"
                >
                  <div className="flex items-center gap-2.5">
                    <TrendingUp className="h-4 w-4 shrink-0 text-signal" />
                    <span className="font-mono font-semibold">${t.ticker}</span>
                    {t.is_etf && (
                      <Badge variant="outline" className="px-1 text-micro text-info">
                        ETF
                      </Badge>
                    )}
                  </div>
                  <span className="font-mono text-small text-ink-secondary tabular-nums">
                    {t.total_mentions} mentions
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Channels Section */}
          {filteredChannels.length > 0 && (
            <div className="mb-3">
              <span className="label-overline block px-3 py-1">Channels</span>
              {filteredChannels.map((c) => (
                <div
                  key={c.id}
                  onClick={() => handleNavigate(`/channels/${c.id}`)}
                  className="flex cursor-pointer items-center justify-between rounded-md px-3 py-2 text-body transition-colors hover:bg-panel-raised"
                >
                  <div className="flex items-center gap-2.5">
                    <Tv className="h-4 w-4 shrink-0 text-ink-faint" />
                    <span className="max-w-[320px] truncate font-medium">{c.title}</span>
                  </div>
                  <span className="text-small text-ink-faint">View Channel →</span>
                </div>
              ))}
            </div>
          )}

          {/* Themes Section */}
          {filteredThemes.length > 0 && (
            <div>
              <span className="label-overline block px-3 py-1">Themes &amp; Sectors</span>
              {filteredThemes.map((th) => (
                <div
                  key={th.id}
                  onClick={() => handleNavigate(`/themes/${th.id}`)}
                  className="flex cursor-pointer items-center justify-between rounded-md px-3 py-2 text-body transition-colors hover:bg-panel-raised"
                >
                  <div className="flex items-center gap-2.5">
                    <Hash className="h-4 w-4 shrink-0 text-ink-faint" />
                    <span className="max-w-[320px] truncate font-medium">{th.name}</span>
                  </div>
                  <Badge variant="outline" className="font-mono text-micro uppercase">
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
