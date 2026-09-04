"use client";

import { useEffect, useMemo, useRef } from "react";
import {
  AreaSeries,
  CandlestickSeries,
  ColorType,
  CrosshairMode,
  HistogramSeries,
  LineSeries,
  LineStyle,
  createChart,
  type CandlestickData,
  type HistogramData,
  type IChartApi,
  type IChartApiBase,
  type IPrimitivePaneRenderer,
  type IPrimitivePaneView,
  type ISeriesApi,
  type ISeriesPrimitive,
  type LineData,
  type MouseEventParams,
  type PrimitivePaneViewZOrder,
  type SeriesAttachedParameter,
  type SeriesType,
  type Time,
  type UTCTimestamp,
  type WhitespaceData,
} from "lightweight-charts";
import type { CanvasRenderingTarget2D } from "fancy-canvas";
import { toRgbaColor } from "@/lib/oklchToRgba";
import { useChartColors, type ChartColors } from "@/lib/useChartColors";

/* ------------------------------------------------------------------ */
/* Types                                                               */
/* ------------------------------------------------------------------ */

export interface TvPricePoint {
  /** ISO date string, e.g. `2025-01-15` */
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
}

export type TvChartSeriesType = "line" | "area" | "candlestick";

export interface TvSignalMarker {
  date: string;
  /** B = bullish (buy), S = bearish (sell), N = neutral. */
  signal: "B" | "S" | "N";
  label?: string;
  /** Optional color override (defaults to success/danger/muted per signal). */
  color?: string;
}

export interface TvMetricPoint {
  date: string;
  value: number | null;
}

/** Optional second line overlaid in the main pane (e.g. "Price 1W Later"). */
export interface TvSecondaryLine {
  label: string;
  points: { date: string; value: number }[];
}

interface TradingViewPriceChartProps {
  points: TvPricePoint[];
  seriesType?: TvChartSeriesType;
  /** B/S markers anchored to the price series directly on the line. */
  markers?: TvSignalMarker[];
  /** Optional second pane with a histogram metric (e.g. mentions / buzz score). */
  metrics?: TvMetricPoint[];
  metricLabel?: string;
  secondaryLine?: TvSecondaryLine;
  showLegend?: boolean;
  height?: number;
}

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

/** `2025-01-15` → UTC-noon UTCTimestamp (noon avoids DST edge-cases). */
function toUtcTimestamp(dateStr: string): UTCTimestamp {
  return Math.floor(new Date(`${dateStr}T12:00:00Z`).getTime() / 1000) as UTCTimestamp;
}

const MONO_FONT =
  'var(--font-geist-mono), ui-monospace, SFMono-Regular, Menlo, monospace';

function drawRoundedPill(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number
) {
  if (ctx.roundRect) {
    ctx.beginPath();
    ctx.roundRect(x, y, w, h, r);
  } else {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }
}

/* ------------------------------------------------------------------ */
/* Signal Badges Primitive (Draws B / S badges directly on the line)  */
/* ------------------------------------------------------------------ */

interface BadgeItem {
  x: number;
  y: number;
  text: string;
  color: string;
}

class SignalBadgesRenderer implements IPrimitivePaneRenderer {
  private _items: BadgeItem[] = [];
  private _canvasBg: string = "#ffffff";
  private _fontFamily: string = MONO_FONT;

  setData(items: BadgeItem[], canvasBg: string, fontFamily: string) {
    this._items = items;
    this._canvasBg = canvasBg;
    this._fontFamily = fontFamily;
  }

  draw(target: CanvasRenderingTarget2D) {
    target.useMediaCoordinateSpace(({ context: ctx }) => {
      ctx.save();
      for (const item of this._items) {
        const { x, y, text, color } = item;

        if (text.length <= 1) {
          const radius = 8.5;

          // 1. Halo / cutout border
          ctx.beginPath();
          ctx.arc(x, y, radius + 2, 0, Math.PI * 2);
          ctx.fillStyle = this._canvasBg;
          ctx.fill();

          // 2. Badge circle
          ctx.beginPath();
          ctx.arc(x, y, radius, 0, Math.PI * 2);
          ctx.fillStyle = color;
          ctx.fill();

          // 3. Centered letter "B" / "S" / "N"
          ctx.fillStyle = "#FFFFFF";
          ctx.font = `bold 10px ${this._fontFamily}`;
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(text, x, y + 0.5);
        } else {
          ctx.font = `bold 9.5px ${this._fontFamily}`;
          const textMetrics = ctx.measureText(text);
          const w = Math.max(20, textMetrics.width + 10);
          const h = 17;
          const r = 8.5;

          // 1. Halo / cutout pill
          drawRoundedPill(ctx, x - w / 2 - 2, y - h / 2 - 2, w + 4, h + 4, r + 2);
          ctx.fillStyle = this._canvasBg;
          ctx.fill();

          // 2. Badge pill
          drawRoundedPill(ctx, x - w / 2, y - h / 2, w, h, r);
          ctx.fillStyle = color;
          ctx.fill();

          // 3. Text
          ctx.fillStyle = "#FFFFFF";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(text, x, y + 0.5);
        }
      }
      ctx.restore();
    });
  }
}

class SignalBadgesPaneView implements IPrimitivePaneView {
  private _renderer = new SignalBadgesRenderer();
  private _source: SignalBadgesPrimitive;

  constructor(source: SignalBadgesPrimitive) {
    this._source = source;
  }

  zOrder(): PrimitivePaneViewZOrder {
    return "top";
  }

  renderer(): IPrimitivePaneRenderer | null {
    if (!this._source.chart || !this._source.series || !this._source.colors) return null;
    const timeScale = this._source.chart.timeScale();
    const series = this._source.series;
    const markers = this._source.markers;
    const pointsMap = this._source.pointsMap;
    const colors = this._source.colors;

    if (!markers.length || !pointsMap.size) return null;

    // Group markers by date to handle multiple signals on the same day without collision
    const markersByDate = new Map<string, TvSignalMarker[]>();
    for (const m of markers) {
      const list = markersByDate.get(m.date) || [];
      list.push(m);
      markersByDate.set(m.date, list);
    }

    const items: BadgeItem[] = [];

    for (const [date, dateMarkers] of markersByDate.entries()) {
      const pt = pointsMap.get(date);
      if (!pt) continue;

      const time = toUtcTimestamp(date);
      const rawX = timeScale.timeToCoordinate(time);
      if (rawX === null) continue;

      const rawY = series.priceToCoordinate(pt.close);
      if (rawY === null) continue;

      const count = dateMarkers.length;
      dateMarkers.forEach((m, idx) => {
        const xOffset = count > 1 ? (idx - (count - 1) / 2) * 18 : 0;
        const badgeColor =
          m.color ??
          (m.signal === "B"
            ? colors.success
            : m.signal === "S"
              ? colors.danger
              : colors.mutedForeground);

        items.push({
          x: rawX + xOffset,
          y: rawY,
          text: m.label ?? m.signal,
          color: toRgbaColor(badgeColor),
        });
      });
    }

    this._renderer.setData(
      items,
      toRgbaColor(colors.canvas),
      MONO_FONT
    );
    return this._renderer;
  }
}

class SignalBadgesPrimitive implements ISeriesPrimitive<Time> {
  private _paneView: SignalBadgesPaneView;
  chart: IChartApiBase<Time> | null = null;
  series: ISeriesApi<SeriesType, Time> | null = null;
  requestUpdate: (() => void) | null = null;
  markers: TvSignalMarker[] = [];
  pointsMap: Map<string, TvPricePoint> = new Map();
  colors: ChartColors | null = null;

  constructor() {
    this._paneView = new SignalBadgesPaneView(this);
  }

  attached(param: SeriesAttachedParameter<Time, SeriesType>) {
    this.chart = param.chart;
    this.series = param.series;
    this.requestUpdate = param.requestUpdate;
    this.requestUpdate?.();
  }

  detached() {
    this.chart = null;
    this.series = null;
    this.requestUpdate = null;
  }

  updateAllViews() {
    this.requestUpdate?.();
  }

  paneViews() {
    return [this._paneView];
  }

  setData(
    markers: TvSignalMarker[],
    points: TvPricePoint[],
    colors: ChartColors
  ) {
    this.markers = markers;
    this.pointsMap = new Map(points.map((p) => [p.date, p]));
    this.colors = colors;
    this.requestUpdate?.();
  }
}

/* ------------------------------------------------------------------ */
/* Component                                                           */
/* ------------------------------------------------------------------ */

export function TradingViewPriceChart({
  points,
  seriesType = "line",
  markers = [],
  metrics,
  metricLabel,
  secondaryLine,
  showLegend = true,
  height = 420,
}: TradingViewPriceChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const priceSeriesRef = useRef<ISeriesApi<"Line" | "Area" | "Candlestick"> | null>(null);
  const secondarySeriesRef = useRef<ISeriesApi<"Line"> | null>(null);
  const metricSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const badgesPluginRef = useRef<SignalBadgesPrimitive | null>(null);

  const colors = useChartColors();

  /* ---- data (memoised so effect deps stay stable) ----------------- */
  const barData = useMemo<CandlestickData<Time>[]>(
    () =>
      points.map((p) => ({
        time: toUtcTimestamp(p.date),
        open: p.open,
        high: p.high,
        low: p.low,
        close: p.close,
      })),
    [points]
  );

  const lineData = useMemo<LineData<Time>[]>(
    () => points.map((p) => ({ time: toUtcTimestamp(p.date), value: p.close })),
    [points]
  );

  const secondaryData = useMemo<LineData<Time>[]>(
    () =>
      secondaryLine
        ? secondaryLine.points
          .filter((p) => p.value !== null && p.value !== undefined)
          .map((p) => ({ time: toUtcTimestamp(p.date), value: p.value }))
        : [],
    [secondaryLine]
  );

  const metricData = useMemo<(HistogramData<Time> | WhitespaceData<Time>)[]>(() => {
    if (!metrics) return [];
    // Interleave whitespace entries so gaps break the histogram cleanly.
    return metrics.flatMap((m) =>
      m.value === null || m.value === undefined
        ? [{ time: toUtcTimestamp(m.date) }]
        : [{ time: toUtcTimestamp(m.date), value: m.value }]
    );
  }, [metrics]);

  const hasMetrics =
    metrics !== undefined &&
    metricData.some((d) => (d as HistogramData<Time>).value !== undefined);
  const hasSecondary = secondaryLine !== undefined && secondaryData.length > 0;

  /* ---- chart lifecycle -------------------------------------------- */
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: toRgbaColor(colors.inkSecondary),
        fontFamily: MONO_FONT,
        fontSize: 11,
        attributionLogo: true, // Apache-2.0 attribution (required by license)
        panes: {
          separatorColor: toRgbaColor(colors.line),
          separatorHoverColor: toRgbaColor(colors.primary),
          enableResize: true,
        },
      },
      grid: {
        vertLines: { visible: false },
        horzLines: { color: toRgbaColor(colors.line), style: LineStyle.Dotted },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          color: toRgbaColor(colors.primary),
          width: 1,
          style: LineStyle.Dashed,
          labelBackgroundColor: toRgbaColor(colors.primary),
        },
        horzLine: {
          color: toRgbaColor(colors.primary),
          width: 1,
          style: LineStyle.Dashed,
          labelBackgroundColor: toRgbaColor(colors.primary),
        },
      },
      rightPriceScale: {
        borderColor: toRgbaColor(colors.line),
        autoScale: true,
        scaleMargins: {
          top: 0.18,
          bottom: 0.15,
        },
      },
      timeScale: { borderColor: toRgbaColor(colors.line), rightOffset: 4, barSpacing: 8 },
    });
    chartRef.current = chart;

    /* -- price series (main pane) -- */
    let priceSeries: ISeriesApi<"Line" | "Area" | "Candlestick">;
    if (seriesType === "candlestick") {
      priceSeries = chart.addSeries(CandlestickSeries, {
        upColor: toRgbaColor(colors.success),
        downColor: toRgbaColor(colors.danger),
        borderUpColor: toRgbaColor(colors.success),
        borderDownColor: toRgbaColor(colors.danger),
        wickUpColor: toRgbaColor(colors.success),
        wickDownColor: toRgbaColor(colors.danger),
      });
    } else if (seriesType === "area") {
      priceSeries = chart.addSeries(AreaSeries, {
        lineColor: toRgbaColor(colors.signal),
        topColor: toRgbaColor(colors.signal, 0.28),
        bottomColor: toRgbaColor(colors.signal, 0.02),
        lineWidth: 2,
      });
    } else {
      priceSeries = chart.addSeries(LineSeries, {
        color: toRgbaColor(colors.signal),
        lineWidth: 2,
        priceLineVisible: true,
        lastValueVisible: true,
      });
    }
    priceSeriesRef.current = priceSeries;

    /* -- signal badges primitive (draws B/S directly on the line) -- */
    const badgesPlugin = new SignalBadgesPrimitive();
    priceSeries.attachPrimitive(badgesPlugin);
    badgesPluginRef.current = badgesPlugin;

    /* -- optional secondary line (main pane) -- */
    if (secondaryLine) {
      secondarySeriesRef.current = chart.addSeries(LineSeries, {
        color: toRgbaColor(colors.chart2),
        lineWidth: 2,
        lineStyle: LineStyle.Dashed,
        priceLineVisible: false,
        lastValueVisible: false,
        crosshairMarkerVisible: false,
      });
    }

    /* -- optional metric pane (paneIndex 1) -- */
    if (metrics && metrics.length > 0) {
      const metricSeries = chart.addSeries(
        HistogramSeries,
        {
          priceScaleId: "metric-pane",
          priceFormat: { type: "volume" },
          priceLineVisible: false,
          lastValueVisible: false,
        },
        1
      );
      metricSeriesRef.current = metricSeries;
      chart.panes()[0]?.setStretchFactor(0.75);
      chart.panes()[1]?.setStretchFactor(0.25);
    }

    return () => {
      if (priceSeriesRef.current && badgesPluginRef.current) {
        priceSeriesRef.current.detachPrimitive(badgesPluginRef.current);
      }
      badgesPluginRef.current = null;
      chart.remove();
      chartRef.current = null;
      priceSeriesRef.current = null;
      secondarySeriesRef.current = null;
      metricSeriesRef.current = null;
    };
    // Recreate only when the structural shape changes; data/colors/markers
    // are applied by the reactive effects below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seriesType, hasMetrics, hasSecondary]);

  /* ---- reactive data updates --------------------------------------- */
  useEffect(() => {
    const chart = chartRef.current;
    const priceSeries = priceSeriesRef.current;
    if (!chart || !priceSeries) return;

    priceSeries.setData(seriesType === "candlestick" ? barData : lineData);
    if (secondarySeriesRef.current) {
      secondarySeriesRef.current.setData(hasSecondary ? secondaryData : []);
    }
    if (metricSeriesRef.current) {
      metricSeriesRef.current.setData(metricData);
      metricSeriesRef.current.applyOptions({ color: toRgbaColor(colors.primary, 0.55) });
    }
    chart.timeScale().fitContent();
  }, [barData, lineData, secondaryData, hasSecondary, metricData, seriesType, colors.primary]);

  /* ---- signal badges update ---------------------------------------- */
  useEffect(() => {
    badgesPluginRef.current?.setData(markers, points, colors);
  }, [markers, points, colors]);

  /* ---- theme change → applyOptions ---------------------------------- */
  useEffect(() => {
    const chart = chartRef.current;
    const priceSeries = priceSeriesRef.current;
    if (!chart || !priceSeries) return;

    chart.applyOptions({
      layout: {
        textColor: toRgbaColor(colors.inkSecondary),
        panes: {
          separatorColor: toRgbaColor(colors.line),
          separatorHoverColor: toRgbaColor(colors.primary),
          enableResize: true,
        },
      },
      grid: {
        vertLines: { visible: false },
        horzLines: { color: toRgbaColor(colors.line), style: LineStyle.Dotted },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          color: toRgbaColor(colors.primary),
          width: 1,
          style: LineStyle.Dashed,
          labelBackgroundColor: toRgbaColor(colors.primary),
        },
        horzLine: {
          color: toRgbaColor(colors.primary),
          width: 1,
          style: LineStyle.Dashed,
          labelBackgroundColor: toRgbaColor(colors.primary),
        },
      },
      rightPriceScale: { borderColor: toRgbaColor(colors.line) },
      timeScale: { borderColor: toRgbaColor(colors.line) },
    });

    if (seriesType === "candlestick") {
      priceSeries.applyOptions({
        upColor: toRgbaColor(colors.success),
        downColor: toRgbaColor(colors.danger),
        borderUpColor: toRgbaColor(colors.success),
        borderDownColor: toRgbaColor(colors.danger),
        wickUpColor: toRgbaColor(colors.success),
        wickDownColor: toRgbaColor(colors.danger),
      });
    } else if (seriesType === "area") {
      priceSeries.applyOptions({
        lineColor: toRgbaColor(colors.signal),
        topColor: toRgbaColor(colors.signal, 0.28),
        bottomColor: toRgbaColor(colors.signal, 0.02),
      });
    } else {
      priceSeries.applyOptions({ color: toRgbaColor(colors.signal) });
    }

    if (secondarySeriesRef.current) {
      secondarySeriesRef.current.applyOptions({ color: toRgbaColor(colors.chart2) });
    }
    if (metricSeriesRef.current) {
      metricSeriesRef.current.applyOptions({ color: toRgbaColor(colors.primary, 0.55) });
    }
  }, [colors, seriesType]);

  /* ---- crosshair tooltip (custom, positioned absolutely) ------------ */
  useEffect(() => {
    const chart = chartRef.current;
    const container = containerRef.current;
    if (!chart || !container) return;

    const tooltip = document.createElement("div");
    tooltip.style.position = "absolute";
    tooltip.style.display = "none";
    tooltip.style.pointerEvents = "none";
    tooltip.style.zIndex = "50";
    tooltip.style.minWidth = "140px";
    tooltip.style.padding = "8px 12px";
    tooltip.style.borderRadius = "8px";
    tooltip.style.fontSize = "11px";
    tooltip.style.fontFamily = MONO_FONT;
    tooltip.style.backgroundColor = toRgbaColor(colors.canvas);
    tooltip.style.border = `1px solid ${toRgbaColor(colors.line)}`;
    tooltip.style.color = colors.ink;
    tooltip.style.boxShadow = "0 4px 12px rgba(0,0,0,0.18)";
    container.appendChild(tooltip);

    const fmtDate = (t: Time) => {
      if (typeof t === "number") {
        return new Date(t * 1000).toLocaleDateString(undefined, {
          month: "short",
          day: "numeric",
          year: "numeric",
        });
      }
      return String(t);
    };

    const handler = (param: MouseEventParams<Time>) => {
      if (!param.point || !param.time || !param.seriesData.size) {
        tooltip.style.display = "none";
        return;
      }

      const pData = param.seriesData.get(priceSeriesRef.current!) as
        | { close?: number; value?: number; open?: number; high?: number; low?: number }
        | undefined;
      const mData = metricSeriesRef.current
        ? (param.seriesData.get(metricSeriesRef.current) as { value?: number } | undefined)
        : undefined;

      const dateStr = fmtDate(param.time);
      let content = `<div style="font-weight:600;margin-bottom:4px;color:${toRgbaColor(colors.ink)}">${dateStr}</div>`;

      if (pData) {
        if (seriesType === "candlestick" && pData.open != null) {
          content += `
            <div style="display:flex;justify-content:space-between;gap:8px;color:${toRgbaColor(colors.inkSecondary)}">
              <span>Open:</span><span style="font-weight:600;color:${toRgbaColor(colors.ink)}">$${pData.open.toFixed(2)}</span>
            </div>
            <div style="display:flex;justify-content:space-between;gap:8px;color:${toRgbaColor(colors.inkSecondary)}">
              <span>High:</span><span style="font-weight:600;color:${toRgbaColor(colors.ink)}">$${pData.high?.toFixed(2)}</span>
            </div>
            <div style="display:flex;justify-content:space-between;gap:8px;color:${toRgbaColor(colors.inkSecondary)}">
              <span>Low:</span><span style="font-weight:600;color:${toRgbaColor(colors.ink)}">$${pData.low?.toFixed(2)}</span>
            </div>
            <div style="display:flex;justify-content:space-between;gap:8px;color:${toRgbaColor(colors.inkSecondary)}">
              <span>Close:</span><span style="font-weight:600;color:${toRgbaColor(colors.ink)}">$${pData.close?.toFixed(2)}</span>
            </div>`;
        } else {
          const val = pData.value ?? pData.close;
          if (val != null) {
            content += `
              <div style="display:flex;justify-content:space-between;gap:8px;color:${toRgbaColor(colors.inkSecondary)}">
                <span>Close:</span><span style="font-weight:600;color:${toRgbaColor(colors.ink)}">$${val.toFixed(2)}</span>
              </div>`;
          }
        }
      }

      if (mData?.value != null) {
        content += `
          <div style="display:flex;justify-content:space-between;gap:8px;color:${toRgbaColor(colors.inkSecondary)};margin-top:2px;">
            <span>${metricLabel ?? "Metric"}:</span><span style="font-weight:600;color:${toRgbaColor(colors.primary)}">${mData.value}</span>
          </div>`;
      }

      // Check for signal marker on this date
      const marker = markers.find((m) => m.date === String(param.time));
      if (marker) {
        const sigColor =
          marker.signal === "B"
            ? toRgbaColor(colors.success)
            : marker.signal === "S"
              ? toRgbaColor(colors.danger)
              : toRgbaColor(colors.inkSecondary);
        const sigName =
          marker.signal === "B" ? "Bullish (B)" : marker.signal === "S" ? "Bearish (S)" : "Neutral";
        content += `
          <div style="margin-top:4px;padding-top:4px;border-top:1px solid ${toRgbaColor(colors.line)};font-weight:600;color:${sigColor}">
            ● ${marker.label ?? sigName}
          </div>`;
      }

      tooltip.innerHTML = content;
      tooltip.style.display = "block";

      const toolWidth = 160;
      const toolHeight = 100;
      let left = param.point.x + 16;
      let top = param.point.y + 16;

      if (left + toolWidth > container.clientWidth) {
        left = param.point.x - toolWidth - 16;
      }
      if (top + toolHeight > container.clientHeight) {
        top = param.point.y - toolHeight - 16;
      }
      tooltip.style.left = `${Math.max(8, left)}px`;
      tooltip.style.top = `${Math.max(8, top)}px`;
    };

    chart.subscribeCrosshairMove(handler);

    return () => {
      chart.unsubscribeCrosshairMove(handler);
      tooltip.remove();
    };
  }, [colors, seriesType, metricLabel, markers]);

  const hasBullish = markers.some((m) => m.signal === "B");
  const hasBearish = markers.some((m) => m.signal === "S");

  /* ---- render -------------------------------------------------------- */
  return (
    <div className="relative w-full" style={{ height }}>
      <div ref={containerRef} className="h-full w-full" />
      {showLegend && (
        <div className="pointer-events-none absolute left-3 top-2.5 z-20 flex flex-wrap items-center gap-x-3.5 gap-y-1.5 rounded-md border border-line/70 bg-panel/90 px-2.5 py-1 font-mono text-micro shadow-xs backdrop-blur-sm">
          {seriesType !== "candlestick" && (
            <span className="flex items-center gap-1.5 text-ink-secondary">
              <span
                className="inline-block h-[3px] w-3 rounded-full"
                style={{
                  backgroundColor: toRgbaColor(colors.signal),
                }}
              />
              Close Price
            </span>
          )}
          {seriesType === "candlestick" && (
            <>
              <span className="flex items-center gap-1.5 text-ink-secondary">
                <span
                  className="inline-block h-2.5 w-2 rounded-sm"
                  style={{ backgroundColor: toRgbaColor(colors.success) }}
                />
                Up
              </span>
              <span className="flex items-center gap-1.5 text-ink-secondary">
                <span
                  className="inline-block h-2.5 w-2 rounded-sm"
                  style={{ backgroundColor: toRgbaColor(colors.danger) }}
                />
                Down
              </span>
            </>
          )}
          {hasSecondary && secondaryLine && (
            <span className="flex items-center gap-1.5 text-ink-secondary">
              <span
                className="inline-block h-[3px] w-3 rounded-full"
                style={{
                  backgroundColor: toRgbaColor(colors.chart2),
                  opacity: 0.9,
                }}
              />
              {secondaryLine.label}
            </span>
          )}
          {markers.length > 0 && (
            <>
              {hasBullish && (
                <span className="flex items-center gap-1.5 text-ink-secondary">
                  <span
                    className="flex h-3.5 w-3.5 items-center justify-center rounded-full text-[9px] font-bold text-white shadow-2xs"
                    style={{ backgroundColor: toRgbaColor(colors.success) }}
                  >
                    B
                  </span>
                  B (Bullish)
                </span>
              )}
              {hasBearish && (
                <span className="flex items-center gap-1.5 text-ink-secondary">
                  <span
                    className="flex h-3.5 w-3.5 items-center justify-center rounded-full text-[9px] font-bold text-white shadow-2xs"
                    style={{ backgroundColor: toRgbaColor(colors.danger) }}
                  >
                    S
                  </span>
                  S (Bearish)
                </span>
              )}
            </>
          )}
          {hasMetrics && metricLabel && (
            <span className="flex items-center gap-1.5 text-ink-secondary">
              <span
                className="inline-block h-2.5 w-3 rounded-sm"
                style={{ backgroundColor: toRgbaColor(colors.primary, 0.55) }}
              />
              {metricLabel}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
