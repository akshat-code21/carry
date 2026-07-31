"use client";

import {
  type FormEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  AlertCircle,
  AtSign,
  Clock,
  Database,
  MessageCircle,
  Newspaper,
  RefreshCw,
  Search,
} from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { AnimatedCounter } from "@/components/market-chatter/AnimatedCounter";
import { MCFooter } from "@/components/market-chatter/MCFooter";
import { GlowCard } from "@/components/market-chatter/GlowCard";
import { GradientText } from "@/components/market-chatter/GradientText";
import { SectionLabel } from "@/components/market-chatter/SectionLabel";
import { StatusBadge } from "@/components/market-chatter/StatusBadge";
import { cn } from "@/lib/utils";

type Source = "reddit" | "x" | "news";

type SourceCard = {
  source: Source;
  status: string;
  as_of?: string | null;
  sentiment_score?: number | null;
  buzz_score?: number | null;
  mentions?: number | null;
  bullish_pct?: number | null;
  bearish_pct?: number | null;
  trend?: string | null;
  coverage_count?: number | null;
  daily_mentions_available: boolean;
  message?: string | null;
};

type TickerData = {
  symbol: string;
  company_name?: string | null;
  data_status: string;
  as_of?: string | null;
  signal: {
    score?: number | null;
    sentiment?: number | null;
    attention?: number | null;
    confidence: number;
    source_count: number;
  };
  sources: SourceCard[];
  chart_source: Source;
  chart_metric: "mentions" | "buzz_score";
  chart_period_days: number;
  chart: Array<{
    date: string;
    mentions?: number | null;
    buzz_score?: number | null;
    close?: number | null;
  }>;
  quota_remaining?: number | null;
};

type TooltipEntry = {
  color?: string;
  dataKey?: string | number;
  name?: string | number;
  value?: number | string;
};

/* Uses the Next.js rewrite proxy — /api/v1/* → backend:8000/api/v1/* */
const API_BASE = "/api/v1";

const QUICK_TICKERS = ["NVDA", "TSLA", "AAPL", "MSFT"] as const;

const sourceLabels: Record<Source, string> = {
  reddit: "Reddit",
  x: "X / FinTwit",
  news: "News",
};

const sourceDescriptions: Record<Source, string> = {
  reddit: "Retail discussion",
  x: "Real-time market talk",
  news: "Editorial coverage",
};

function formatNumber(value?: number | null, digits = 0) {
  if (value === undefined || value === null) return "—";
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  }).format(value);
}

function formatDate(value?: string | null) {
  if (!value) return "Awaiting timestamp";
  return new Date(value).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function SourceIcon({ source }: { source: Source }) {
  const iconClassName = "h-4 w-4";
  if (source === "reddit") return <MessageCircle className={iconClassName} aria-hidden="true" />;
  if (source === "x") return <AtSign className={iconClassName} aria-hidden="true" />;
  return <Newspaper className={iconClassName} aria-hidden="true" />;
}

function LoadingSkeleton() {
  return (
    <div className="mt-8 space-y-4" aria-label="Loading ticker data">
      <div className="inline-flex items-center gap-2.5 rounded-full border border-tf-stroke bg-tf-panel/80 px-3.5 py-1.5 backdrop-blur-md shadow-sm">
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-tf-signal opacity-75" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-tf-signal" />
        </span>
        <span className="text-[12px] font-medium tracking-tight text-tf-muted animate-pulse">
          Analyzing market chatter...
        </span>
      </div>
      <div className="tf-skeleton-shimmer h-16 rounded-lg border border-tf-stroke bg-tf-panel" />
      <div className="grid grid-cols-4 gap-3 max-lg:grid-cols-2 max-sm:grid-cols-1">
        {Array.from({ length: 4 }, (_, index) => (
          <div
            key={`metric-skeleton-${index}`}
            className="tf-skeleton-shimmer h-40 rounded-lg border border-tf-stroke bg-tf-panel"
          />
        ))}
      </div>
      <div className="tf-skeleton-shimmer h-[430px] rounded-lg border border-tf-stroke bg-tf-panel" />
    </div>
  );
}

function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: readonly TooltipEntry[];
  label?: string;
}) {
  if (!active || !payload?.length || !label) return null;

  return (
    <div className="min-w-44 rounded-md border border-tf-stroke-strong bg-tf-panel-raised px-3 py-2.5 shadow-2xl shadow-black/30">
      <p className="mb-2 border-b border-tf-stroke pb-2 font-mono text-[10px] uppercase tracking-[0.08em] text-tf-muted">
        {new Date(`${label}T00:00:00`).toLocaleDateString(undefined, {
          month: "short",
          day: "numeric",
          year: "numeric",
        })}
      </p>
      <div className="space-y-1.5">
        {payload.map((entry) => (
          <div
            key={String(entry.dataKey)}
            className="flex items-center justify-between gap-6 text-[12px]"
          >
            <span className="flex items-center gap-2 text-tf-muted">
              <span
                className="h-1.5 w-1.5 rounded-full"
                style={{ backgroundColor: entry.color }}
              />
              {entry.name}
            </span>
            <span className="font-mono font-medium tabular-nums text-tf-ink">
              {entry.dataKey === "close" ? "$" : ""}
              {typeof entry.value === "number"
                ? formatNumber(entry.value, entry.dataKey === "close" ? 2 : 0)
                : "—"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function DualLineChart({
  data,
  metric,
}: {
  data: TickerData["chart"];
  metric: TickerData["chart_metric"];
}) {
  const chartData = data.filter(
    (point) => point.close !== null && point.close !== undefined,
  );
  const metricLabel = metric === "mentions" ? "Mentions" : "Buzz score";

  const formatXTick = useCallback((value: string) => {
    return new Date(`${value}T00:00:00`).toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
    });
  }, []);

  if (!chartData.length) {
    return (
      <div className="flex h-[340px] flex-col items-center justify-center gap-3 text-center">
        <Database className="h-5 w-5 text-tf-faint" aria-hidden="true" />
        <div>
          <p className="text-[13px] font-medium text-tf-ink-secondary">
            No chart history yet
          </p>
          <p className="mt-1 text-[12px] text-tf-muted">
            Historical activity will appear after the next collection cycle.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-[350px] w-full max-sm:h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={chartData}
          margin={{ top: 16, right: 4, bottom: 0, left: 4 }}
          accessibilityLayer
        >
          <CartesianGrid
            stroke="rgba(255,255,255,0.045)"
            strokeDasharray="2 4"
            vertical={false}
          />
          <XAxis
            dataKey="date"
            tickFormatter={formatXTick}
            tick={{ fill: "#747b71", fontSize: 10 }}
            axisLine={{ stroke: "#262b26" }}
            tickLine={false}
            minTickGap={36}
            dy={8}
          />
          <YAxis
            yAxisId="metric"
            orientation="left"
            tick={{ fill: "#7f897b", fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            width={42}
            allowDecimals={false}
          />
          <YAxis
            yAxisId="price"
            orientation="right"
            tick={{ fill: "#7f897b", fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            width={48}
            tickFormatter={(value: number) => `$${formatNumber(value, 0)}`}
            domain={["auto", "auto"]}
          />
          <Tooltip
            content={<ChartTooltip />}
            cursor={{
              stroke: "rgba(216,243,106,0.22)",
              strokeDasharray: "3 4",
            }}
          />
          <Line
            yAxisId="metric"
            type="monotone"
            dataKey={metric}
            name={metricLabel}
            stroke="#d8f36a"
            strokeWidth={2}
            dot={false}
            activeDot={{
              r: 4,
              fill: "#d8f36a",
              stroke: "#111411",
              strokeWidth: 2,
            }}
            connectNulls={false}
            animationDuration={550}
          />
          <Line
            yAxisId="price"
            type="monotone"
            dataKey="close"
            name="Closing price"
            stroke="#efb864"
            strokeWidth={1.5}
            dot={false}
            activeDot={{
              r: 4,
              fill: "#efb864",
              stroke: "#111411",
              strokeWidth: 2,
            }}
            connectNulls={false}
            animationDuration={550}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function MetricCard({
  label,
  value,
  detail,
  suffix,
  featured = false,
}: {
  label: string;
  value?: number | null;
  detail: string;
  suffix?: string;
  featured?: boolean;
}) {
  const boundedValue = Math.max(0, Math.min(value ?? 0, 100));

  return (
    <GlowCard
      glowColor={featured ? "signal" : "neutral"}
      className="min-h-40 p-5"
    >
      <div className="flex h-full flex-col justify-between gap-7">
        <div className="flex items-center justify-between gap-4">
          <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-tf-muted">
            {label}
          </span>
          {featured && (
            <span className="rounded border border-tf-signal/20 bg-tf-signal/10 px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-[0.08em] text-tf-signal">
              Composite
            </span>
          )}
        </div>

        <div>
          <AnimatedCounter
            value={value}
            decimals={1}
            suffix={suffix}
            className={cn(
              "text-[34px] font-medium leading-none tracking-[-0.06em] text-tf-ink",
              featured && "text-[42px] text-tf-signal",
            )}
          />
          <div className="mt-4 h-px overflow-hidden bg-tf-stroke">
            <div
              className={cn("h-full bg-tf-ink-secondary", featured && "bg-tf-signal")}
              style={{ width: `${boundedValue}%` }}
            />
          </div>
          <p className="mt-3 text-[11px] leading-4 text-tf-faint">{detail}</p>
        </div>
      </div>
    </GlowCard>
  );
}

function SourceMetric({
  label,
  value,
  digits = 1,
  suffix,
}: {
  label: string;
  value?: number | null;
  digits?: number;
  suffix?: string;
}) {
  return (
    <div>
      <p className="text-[10px] font-medium uppercase tracking-[0.08em] text-tf-faint">
        {label}
      </p>
      <AnimatedCounter
        value={value}
        decimals={digits}
        suffix={suffix}
        className="mt-1.5 block text-[19px] font-medium tracking-[-0.04em] text-tf-ink"
      />
    </div>
  );
}

export default function TickerFlowPage() {
  const [query, setQuery] = useState("");
  const [activeSymbol, setActiveSymbol] = useState("");
  const [source, setSource] = useState<Source>("reddit");
  const [period, setPeriod] = useState(7);
  const [data, setData] = useState<TickerData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const requestId = useRef(0);

  const fetchTicker = useCallback(
    async (requestedSymbol: string, refresh = false) => {
      const currentRequest = ++requestId.current;
      setLoading(true);
      setError(null);
      setData((prev) => (prev?.symbol === requestedSymbol ? prev : null));

      try {
        const params = new URLSearchParams({
          source,
          period_days: String(period),
          refresh: String(refresh),
        });
        const response = await fetch(
          `${API_BASE}/tickers/${requestedSymbol}?${params}`,
          {
            cache: "no-store",
            signal: AbortSignal.timeout(120000),
          },
        );
        const contentType = response.headers.get("content-type");
        let body: (TickerData & { detail?: string }) | null = null;
        let errorMessage = "Unable to load ticker data.";

        if (contentType && contentType.includes("application/json")) {
          body = (await response.json()) as TickerData & { detail?: string };
          if (!response.ok) {
            errorMessage = body.detail ?? errorMessage;
          }
        } else if (!response.ok) {
          const rawText = await response.text();
          errorMessage = rawText.length < 150 ? rawText : "Server processing error. Please try again.";
        }

        if (!response.ok || !body) {
          throw new Error(errorMessage);
        }

        if (currentRequest === requestId.current) {
          setData(body);
        }
      } catch (requestError) {
        if (currentRequest === requestId.current) {
          setError(
            requestError instanceof Error
              ? requestError.message
              : "Unable to load ticker data.",
          );
        }
      } finally {
        if (currentRequest === requestId.current) {
          setLoading(false);
        }
      }
    },
    [period, source],
  );

  useEffect(() => {
    if (activeSymbol) void fetchTicker(activeSymbol);
  }, [activeSymbol, fetchTicker]);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const normalized = query.trim().toUpperCase();
    if (!normalized) return;

    setQuery(normalized);
    if (normalized === activeSymbol) {
      void fetchTicker(normalized);
      return;
    }

    setActiveSymbol(normalized);
  };

  const chooseTicker = (ticker: string) => {
    setQuery(ticker);
    if (ticker === activeSymbol) {
      void fetchTicker(ticker);
      return;
    }
    setActiveSymbol(ticker);
  };

  return (
    <div className="tickerflow-theme">
      <div className="mx-auto max-w-[1240px] pb-10">
        <section aria-labelledby="tf-page-title">
          <div className="flex items-end justify-between gap-12 max-lg:flex-col max-lg:items-start max-lg:gap-5">
            <div>
              <SectionLabel>Market intelligence workspace</SectionLabel>
              <h1
                id="tf-page-title"
                className="mt-5 max-w-[720px] text-[clamp(2.25rem,5vw,3.5rem)] font-medium leading-[0.98] tracking-[-0.065em] text-tf-ink"
              >
                Market <GradientText>attention</GradientText>,<br />
                made legible.
              </h1>
            </div>
            <p className="max-w-[390px] border-l border-tf-stroke pl-5 text-[14px] leading-6 text-tf-muted max-lg:border-l-0 max-lg:border-t max-lg:pl-0 max-lg:pt-4">
              Compare source-level sentiment with price movement—without hiding
              where the signal came from.
            </p>
          </div>

          <div className="mt-10 rounded-lg border border-tf-stroke bg-tf-panel p-2 shadow-[0_18px_70px_rgba(0,0,0,0.18)]">
            <form
              onSubmit={handleSubmit}
              className="flex items-center gap-2 max-sm:flex-wrap"
            >
              <label htmlFor="tf-ticker" className="sr-only">
                Ticker symbol
              </label>
              <div className="relative min-w-0 flex-1">
                <span className="pointer-events-none absolute inset-y-0 left-4 flex items-center font-mono text-[15px] text-tf-signal">
                  $
                </span>
                <input
                  id="tf-ticker"
                  value={query}
                  onChange={(event) =>
                    setQuery(event.target.value.toUpperCase().replace(/[^A-Z.]/g, ""))
                  }
                  maxLength={6}
                  autoComplete="off"
                  spellCheck={false}
                  className="h-12 w-full rounded-md border border-transparent bg-tf-canvas pl-8 pr-4 font-mono text-[14px] font-semibold tracking-[0.08em] text-tf-ink outline-none transition-colors placeholder:text-tf-faint focus:border-tf-stroke-strong"
                  placeholder="ENTER TICKER"
                />
              </div>
              <button
                type="submit"
                disabled={loading && !data}
                className="inline-flex h-12 shrink-0 items-center justify-center gap-2 rounded-md bg-tf-signal px-5 text-[13px] font-semibold text-[#16190f] transition-colors hover:bg-[#e4f98b] disabled:opacity-50 max-sm:flex-1"
              >
                <Search className="h-3.5 w-3.5" aria-hidden="true" />
                Analyze ticker
              </button>
            </form>

            <div className="flex items-center gap-2 px-2 pb-1 pt-3 max-sm:overflow-x-auto">
              <span className="mr-1 shrink-0 text-[10px] font-semibold uppercase tracking-[0.09em] text-tf-faint">
                Quick look
              </span>
              {QUICK_TICKERS.map((ticker) => (
                <button
                  key={ticker}
                  type="button"
                  onClick={() => chooseTicker(ticker)}
                  aria-pressed={activeSymbol === ticker}
                  className={cn(
                    "shrink-0 rounded px-2 py-1 font-mono text-[10px] font-medium tracking-[0.06em] text-tf-muted transition-colors hover:bg-tf-panel-raised hover:text-tf-ink",
                    activeSymbol === ticker && "bg-tf-signal/10 text-tf-signal",
                  )}
                >
                  ${ticker}
                </button>
              ))}
            </div>
          </div>
        </section>

        <AnimatePresence initial={false}>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              role="alert"
              className="mt-5 flex items-start justify-between gap-5 rounded-lg border border-tf-negative/20 bg-tf-negative/10 px-4 py-3.5"
            >
              <div className="flex items-start gap-3">
                <AlertCircle
                  className="mt-0.5 h-4 w-4 shrink-0 text-tf-negative"
                  aria-hidden="true"
                />
                <div>
                  <p className="text-[12px] font-semibold text-tf-negative">
                    Market data is temporarily unavailable
                  </p>
                  <p className="mt-1 text-[12px] text-tf-negative/75">{error}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => void fetchTicker(activeSymbol)}
                className="shrink-0 rounded border border-tf-negative/20 px-2.5 py-1.5 text-[11px] font-semibold text-tf-negative transition-colors hover:bg-tf-negative/10"
              >
                Retry
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {loading && !data && <LoadingSkeleton />}

        <AnimatePresence mode="wait">
          {data && (
            <motion.section
              key={data.symbol}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.25 }}
              className="mt-12"
              aria-busy={loading}
            >
              <div className="mb-5 flex items-end justify-between gap-6 border-b border-tf-stroke pb-5 max-md:items-start">
                <div>
                  <div className="flex items-center gap-2.5">
                    <h2 className="font-mono text-[28px] font-medium tracking-[-0.05em] text-tf-ink">
                      ${data.symbol}
                    </h2>
                    <StatusBadge status={data.data_status} />
                  </div>
                  <p className="mt-1 text-[13px] text-tf-muted">
                    {data.company_name ?? "Company data unavailable"}
                  </p>
                </div>

                <div className="flex items-center gap-2 text-right text-[10px] uppercase tracking-[0.07em] text-tf-faint">
                  <Clock className="h-3.5 w-3.5" aria-hidden="true" />
                  <span className="max-sm:hidden">Updated </span>
                  <span className="font-mono normal-case tracking-normal">
                    {formatDate(data.as_of)}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-4 gap-3 max-lg:grid-cols-2 max-sm:grid-cols-1">
                <MetricCard
                  label="Signal score"
                  value={data.signal.score}
                  detail="Attention and sentiment composite · 0–100"
                  featured
                />
                <MetricCard
                  label="Sentiment"
                  value={data.signal.sentiment}
                  detail="Source-weighted conversation tone"
                />
                <MetricCard
                  label="Attention"
                  value={data.signal.attention}
                  detail="Relative discussion and coverage volume"
                />
                <MetricCard
                  label="Confidence"
                  value={Math.round(data.signal.confidence * 100)}
                  suffix="%"
                  detail={`${data.signal.source_count} of 3 sources reporting`}
                />
              </div>

              <GlowCard
                className="mt-5 overflow-hidden"
                hover={false}
                glowColor="signal"
              >
                <div className="flex items-start justify-between gap-6 border-b border-tf-stroke px-5 py-5 max-lg:flex-col">
                  <div>
                    <SectionLabel dotColor="#efb864">Price context</SectionLabel>
                    <h3 className="mt-2.5 text-[17px] font-semibold tracking-[-0.025em] text-tf-ink">
                      Conversation activity vs. closing price
                    </h3>
                    <div className="mt-3 flex items-center gap-5 text-[10px] uppercase tracking-[0.07em] text-tf-muted">
                      <span className="flex items-center gap-2">
                        <span className="h-1.5 w-4 rounded-full bg-tf-signal" />
                        {data.chart_metric === "mentions" ? "Mentions" : "Buzz"}
                      </span>
                      <span className="flex items-center gap-2">
                        <span className="h-1.5 w-4 rounded-full bg-tf-price" />
                        Closing price
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-2 max-sm:w-full">
                    <div
                      className="flex rounded-md border border-tf-stroke bg-tf-canvas p-1"
                      aria-label="Chart source"
                    >
                      {(Object.keys(sourceLabels) as Source[]).map((value) => (
                        <button
                          key={value}
                          type="button"
                          onClick={() => setSource(value)}
                          aria-pressed={source === value}
                          className={cn(
                            "rounded px-2.5 py-1.5 text-[11px] font-medium text-tf-muted transition-colors hover:text-tf-ink",
                            source === value &&
                            "bg-tf-panel-raised text-tf-ink shadow-sm shadow-black/20",
                          )}
                        >
                          {value === "x" ? "X" : sourceLabels[value]}
                        </button>
                      ))}
                    </div>
                    <div
                      className="flex rounded-md border border-tf-stroke bg-tf-canvas p-1"
                      aria-label="Chart period"
                    >
                      {[7, 30].map((value) => (
                        <button
                          key={value}
                          type="button"
                          onClick={() => setPeriod(value)}
                          aria-pressed={period === value}
                          className={cn(
                            "rounded px-2.5 py-1.5 font-mono text-[10px] text-tf-muted transition-colors hover:text-tf-ink",
                            period === value && "bg-tf-panel-raised text-tf-ink",
                          )}
                        >
                          {value}D
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="relative px-3 pb-4 pt-2 max-sm:px-0">
                  {loading && (
                    <div className="absolute right-5 top-4 z-10 flex items-center gap-2 rounded-full border border-tf-stroke bg-tf-panel-raised px-2.5 py-1 text-[10px] text-tf-muted">
                      <RefreshCw className="h-3 w-3 animate-spin" aria-hidden="true" />
                      Updating
                    </div>
                  )}
                  <DualLineChart data={data.chart} metric={data.chart_metric} />
                  {data.chart_metric === "buzz_score" && (
                    <p className="border-t border-tf-stroke px-3 pt-3 text-[11px] leading-5 text-tf-faint">
                      Daily mention history is not available for this source;
                      vendor buzz history is shown instead.
                    </p>
                  )}
                </div>
              </GlowCard>

              <section id="tf-sources" className="mt-12 scroll-mt-24">
                <div className="mb-5 flex items-end justify-between gap-6 max-sm:items-start">
                  <div>
                    <SectionLabel>Source coverage</SectionLabel>
                    <h3 className="mt-2.5 text-[21px] font-medium tracking-[-0.035em] text-tf-ink">
                      The signal, source by source
                    </h3>
                  </div>
                  <button
                    type="button"
                    onClick={() => void fetchTicker(activeSymbol, true)}
                    disabled={loading}
                    className="inline-flex h-9 shrink-0 items-center gap-2 rounded-md border border-tf-stroke bg-tf-panel px-3 text-[11px] font-semibold text-tf-ink-secondary transition-colors hover:border-tf-stroke-strong hover:bg-tf-panel-raised hover:text-tf-ink disabled:opacity-50"
                  >
                    <RefreshCw
                      className={cn("h-3.5 w-3.5", loading && "animate-spin")}
                      aria-hidden="true"
                    />
                    <span className="max-sm:hidden">Refresh data</span>
                    <span className="sm:hidden">Refresh</span>
                  </button>
                </div>

                <div className="grid grid-cols-3 gap-3 max-lg:grid-cols-1">
                  {data.sources.map((item) => (
                    <GlowCard
                      key={item.source}
                      className="overflow-hidden"
                      glowColor={
                        item.source === "reddit"
                          ? "negative"
                          : item.source === "news"
                            ? "signal"
                            : "neutral"
                      }
                    >
                      <div className="flex items-start justify-between gap-4 border-b border-tf-stroke px-5 py-4">
                        <div className="flex items-center gap-3">
                          <span className="flex h-8 w-8 items-center justify-center rounded-md border border-tf-stroke bg-tf-canvas text-tf-ink-secondary">
                            <SourceIcon source={item.source} />
                          </span>
                          <div>
                            <h4 className="text-[13px] font-semibold text-tf-ink">
                              {sourceLabels[item.source]}
                            </h4>
                            <p className="mt-0.5 text-[10px] text-tf-faint">
                              {sourceDescriptions[item.source]}
                            </p>
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-x-6 gap-y-5 px-5 py-5">
                        <SourceMetric
                          label="Sentiment"
                          value={item.sentiment_score}
                        />
                        <SourceMetric label="Buzz" value={item.buzz_score} />
                        <SourceMetric
                          label="Mentions"
                          value={item.mentions}
                          digits={0}
                        />
                        <SourceMetric
                          label="Bullish"
                          value={item.bullish_pct}
                          suffix="%"
                        />
                      </div>

                      <div className="min-h-[74px] border-t border-tf-stroke bg-tf-canvas/35 px-5 py-3.5">
                        <p className="text-[11px] leading-4 text-tf-muted">
                          {item.trend
                            ? `${item.trend} attention`
                            : "Trend not yet available"}
                          {item.coverage_count
                            ? ` · ${formatNumber(item.coverage_count)} coverage sources`
                            : ""}
                        </p>
                        {item.as_of && (
                          <p className="mt-1.5 font-mono text-[9px] uppercase tracking-[0.04em] text-tf-faint">
                            Updated {formatDate(item.as_of)}
                          </p>
                        )}
                        {item.message && (
                          <p className="mt-1.5 text-[10px] leading-4 text-tf-negative">
                            {item.message}
                          </p>
                        )}
                      </div>
                    </GlowCard>
                  ))}
                </div>
              </section>

              <MCFooter quotaRemaining={data.quota_remaining} />
            </motion.section>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
