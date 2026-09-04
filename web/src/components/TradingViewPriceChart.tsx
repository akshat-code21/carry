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
  radius?: number;
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
        const radius = item.radius ?? 8.0;

        if (text.length <= 1) {
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
          const fontSize = radius <= 7.5 ? "9px" : "10px";
          ctx.font = `bold ${fontSize} ${this._fontFamily}`;
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(text, x, y + 0.5);
        } else {
          const fontSize = radius <= 7.5 ? "8.5px" : "9.5px";
          ctx.font = `bold ${fontSize} ${this._fontFamily}`;
          const textMetrics = ctx.measureText(text);
          const w = Math.max(radius * 2 + 4, textMetrics.width + 8);
          const h = radius * 2;
          const r = radius;

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

    // Group markers by date
    const markersByDate = new Map<string, TvSignalMarker[]>();
    for (const m of markers) {
      const list = markersByDate.get(m.date) || [];
      list.push(m);
      markersByDate.set(m.date, list);
    }

    // Sort dates chronologically
    const sortedDates = Array.from(markersByDate.keys()).sort((a, b) => a.localeCompare(b));

    interface MarkerCandidate {
      date: string;
      rawX: number;
      rawY: number;
      markers: TvSignalMarker[];
    }

    const candidates: MarkerCandidate[] = [];
    for (const date of sortedDates) {
      const pt = pointsMap.get(date);
      if (!pt) continue;

      const time = toUtcTimestamp(date);
      const rawX = timeScale.timeToCoordinate(time);
      if (rawX === null) continue;

      const rawY = series.priceToCoordinate(pt.close);
      if (rawY === null) continue;

      candidates.push({
        date,
        rawX,
        rawY,
        markers: markersByDate.get(date) || [],
      });
    }

    if (!candidates.length) return null;

    // Detect density & adapt spacing / badge size
    const span = Math.abs(candidates[candidates.length - 1].rawX - candidates[0].rawX);
    const avgDeltaX = candidates.length > 1 ? span / (candidates.length - 1) : 50;
    const isDense = avgDeltaX < 24;
    const badgeRadius = isDense ? 7.5 : 8.5;
    const minSpacing = isDense ? 19 : 23; // Minimum px between badges to prevent overlapping blobs

    const items: BadgeItem[] = [];
    let lastPlacedX = -9999;
    let lastPlacedSignal: string | null = null;

    for (let i = 0; i < candidates.length; i++) {
      const c = candidates[i];
      const primaryMarker = c.markers[0];
      const sig = primaryMarker.signal;
      const isReversal = lastPlacedSignal !== null && sig !== lastPlacedSignal;
      const dist = Math.abs(c.rawX - lastPlacedX);

      // Prioritize placing marker if:
      // 1. Ample distance between badges
      // 2. Trend reversal (direction change B <-> S)
      // 3. First or last point in the visible series
      if (dist >= minSpacing || isReversal || i === 0 || i === candidates.length - 1) {
        const count = c.markers.length;
        c.markers.forEach((m, idx) => {
          const xOffset = count > 1 ? (idx - (count - 1) / 2) * (badgeRadius * 2 + 2) : 0;
          const badgeColor =
            m.color ??
            (m.signal === "B"
              ? colors.success
              : m.signal === "S"
                ? colors.danger
                : colors.mutedForeground);

          items.push({
            x: c.rawX + xOffset,
            y: c.rawY,
            text: m.label ?? m.signal,
            color: toRgbaColor(badgeColor),
            radius: badgeRadius,
          });
        });
        lastPlacedX = c.rawX;
        lastPlacedSignal = sig;
      }
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

  /* ---- data lookups ----------------------------------------------- */
  const pointsByTime = useMemo(() => {
    const map = new Map<number, { point: TvPricePoint; prev?: TvPricePoint }>();
    points.forEach((p, idx) => {
      map.set(toUtcTimestamp(p.date), { point: p, prev: points[idx - 1] });
    });
    return map;
  }, [points]);

  const markersByDate = useMemo(() => {
    const map = new Map<string, TvSignalMarker>();
    markers.forEach((m) => map.set(m.date, m));
    return map;
  }, [markers]);

  const metricsByDate = useMemo(() => {
    const map = new Map<string, number>();
    metrics?.forEach((m) => {
      if (m.value !== null && m.value !== undefined) {
        map.set(m.date, m.value);
      }
    });
    return map;
  }, [metrics]);

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
        entireTextOnly: true,
        scaleMargins: {
          top: 0.10,
          bottom: 0.10,
        },
      },
      timeScale: {
        borderColor: toRgbaColor(colors.line),
        rightOffset: 3,
        barSpacing: 10,
        minBarSpacing: 3,
      },
      handleScroll: {
        mouseWheel: true,
        pressedMouseMove: true,
        horzTouchDrag: true,
        vertTouchDrag: false, // Ensures natural vertical page scrolling on mobile touch screens
      },
      handleScale: {
        axisPressedMouseMove: true,
        mouseWheel: true,
        pinch: true, // Allows smooth pinch-to-zoom on mobile
      },
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
      chart.panes()[0]?.setStretchFactor(0.72);
      chart.panes()[1]?.setStretchFactor(0.28);
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

  /* ---- crosshair tooltip near cursor ------------------------------- */
  useEffect(() => {
    const chart = chartRef.current;
    const container = containerRef.current;
    if (!chart || !container) return;

    const tooltip = document.createElement("div");
    tooltip.style.position = "absolute";
    tooltip.style.display = "none";
    tooltip.style.pointerEvents = "none";
    tooltip.style.zIndex = "50";
    tooltip.style.minWidth = "150px";
    tooltip.style.maxWidth = "260px";
    tooltip.style.padding = "8px 12px";
    tooltip.style.borderRadius = "8px";
    tooltip.style.fontSize = "11px";
    tooltip.style.fontFamily = MONO_FONT;
    tooltip.style.backgroundColor = toRgbaColor(colors.canvas, 0.95);
    tooltip.style.border = `1px solid ${toRgbaColor(colors.line)}`;
    tooltip.style.color = colors.ink;
    tooltip.style.boxShadow = "0 8px 24px rgba(0,0,0,0.22)";
    tooltip.style.backdropFilter = "blur(8px)";
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

      const timeNum = typeof param.time === "number" ? param.time : null;
      const lookup = timeNum !== null ? pointsByTime.get(timeNum) : undefined;
      const dateKey = lookup?.point.date ?? (typeof param.time === "string" ? param.time : "");
      const dateStr = fmtDate(param.time);

      let content = `<div style="font-weight:600;margin-bottom:4px;color:${toRgbaColor(colors.ink)}">${dateStr}</div>`;

      if (pData) {
        if (seriesType === "candlestick" && pData.open != null) {
          content += `
            <div style="display:flex;justify-content:space-between;gap:12px;color:${toRgbaColor(colors.inkSecondary)}">
              <span>Open:</span><span style="font-weight:600;color:${toRgbaColor(colors.ink)}">$${pData.open.toFixed(2)}</span>
            </div>
            <div style="display:flex;justify-content:space-between;gap:12px;color:${toRgbaColor(colors.inkSecondary)}">
              <span>High:</span><span style="font-weight:600;color:${toRgbaColor(colors.ink)}">$${pData.high?.toFixed(2)}</span>
            </div>
            <div style="display:flex;justify-content:space-between;gap:12px;color:${toRgbaColor(colors.inkSecondary)}">
              <span>Low:</span><span style="font-weight:600;color:${toRgbaColor(colors.ink)}">$${pData.low?.toFixed(2)}</span>
            </div>
            <div style="display:flex;justify-content:space-between;gap:12px;color:${toRgbaColor(colors.inkSecondary)}">
              <span>Close:</span><span style="font-weight:600;color:${toRgbaColor(colors.ink)}">$${pData.close?.toFixed(2)}</span>
            </div>`;
        } else {
          const val = pData.value ?? pData.close;
          if (val != null) {
            const prev = lookup?.prev;
            const changePct = prev && prev.close > 0 ? ((val - prev.close) / prev.close) * 100 : undefined;
            const changeColor = changePct !== undefined
              ? (changePct >= 0 ? toRgbaColor(colors.success) : toRgbaColor(colors.danger))
              : toRgbaColor(colors.ink);
            const changeText = changePct !== undefined
              ? `<span style="font-size:10px;font-weight:600;color:${changeColor}">(${changePct >= 0 ? "+" : ""}${changePct.toFixed(2)}%)</span>`
              : "";

            content += `
              <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;color:${toRgbaColor(colors.inkSecondary)}">
                <span>Price:</span>
                <span style="font-weight:600;color:${toRgbaColor(colors.ink)}">$${val.toFixed(2)} ${changeText}</span>
              </div>`;
          }
        }
      }

      if (mData?.value != null) {
        content += `
          <div style="display:flex;justify-content:space-between;gap:10px;color:${toRgbaColor(colors.inkSecondary)};margin-top:2px;">
            <span>${metricLabel ?? "Metric"}:</span>
            <span style="font-weight:600;color:${toRgbaColor(colors.primary)}">${mData.value}</span>
          </div>`;
      }

      // Check for signal marker on this date
      const marker = dateKey ? markersByDate.get(dateKey) : undefined;
      if (marker) {
        const sigColor =
          marker.signal === "B"
            ? toRgbaColor(colors.success)
            : marker.signal === "S"
              ? toRgbaColor(colors.danger)
              : toRgbaColor(colors.mutedForeground);
        const sigName =
          marker.signal === "B" ? "Buy" : marker.signal === "S" ? "Sell" : "Neutral";
        content += `
          <div style="margin-top:6px;padding-top:4px;border-top:1px solid ${toRgbaColor(colors.line)};font-weight:600;color:${sigColor};display:flex;align-items:center;gap:4px;">
            <!-- <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background-color:${sigColor}"></span> -->
            ${sigName}
          </div>`;
      }

      tooltip.innerHTML = content;
      tooltip.style.display = "block";

      const toolWidth = 175;
      const toolHeight = 90;
      let left = param.point.x + 14;
      let top = param.point.y + 14;

      if (left + toolWidth > container.clientWidth) {
        left = param.point.x - toolWidth - 14;
      }
      if (top + toolHeight > container.clientHeight) {
        top = param.point.y - toolHeight - 14;
      }
      tooltip.style.left = `${Math.max(6, left)}px`;
      tooltip.style.top = `${Math.max(6, top)}px`;
    };

    chart.subscribeCrosshairMove(handler);

    return () => {
      chart.unsubscribeCrosshairMove(handler);
      tooltip.remove();
    };
  }, [colors, seriesType, metricLabel, pointsByTime, markersByDate]);

  const hasBullish = markers.some((m) => m.signal === "B");
  const hasBearish = markers.some((m) => m.signal === "S");

  /* ---- render -------------------------------------------------------- */
  return (
    <div className="flex w-full flex-col gap-2">
      {/* Top Header Strip: Legend */}
      {showLegend && (
        <div className="flex flex-wrap items-center gap-x-3.5 gap-y-1.5 rounded-md border border-line/60 bg-panel/75 px-3 py-1.5 font-mono text-micro shadow-2xs backdrop-blur-xs text-ink-secondary">
          {seriesType !== "candlestick" && (
            <span className="flex items-center gap-1.5">
              <span
                className="inline-block h-[3px] w-3 rounded-full"
                style={{ backgroundColor: toRgbaColor(colors.signal) }}
              />
              Price
            </span>
          )}
          {seriesType === "candlestick" && (
            <>
              <span className="flex items-center gap-1.5">
                <span
                  className="inline-block h-2.5 w-2 rounded-xs"
                  style={{ backgroundColor: toRgbaColor(colors.success) }}
                />
                Up
              </span>
              <span className="flex items-center gap-1.5">
                <span
                  className="inline-block h-2.5 w-2 rounded-xs"
                  style={{ backgroundColor: toRgbaColor(colors.danger) }}
                />
                Down
              </span>
            </>
          )}
          {hasSecondary && secondaryLine && (
            <span className="flex items-center gap-1.5">
              <span
                className="inline-block h-[3px] w-3 rounded-full opacity-90"
                style={{ backgroundColor: toRgbaColor(colors.chart2) }}
              />
              {secondaryLine.label}
            </span>
          )}
          {markers.length > 0 && (
            <>
              {hasBullish && (
                <span className="flex items-center gap-1">
                  <span
                    className="flex h-3.5 w-3.5 items-center justify-center rounded-full text-[9px] font-bold text-white shadow-2xs"
                    style={{ backgroundColor: toRgbaColor(colors.success) }}
                  >
                    B
                  </span>
                  Buy
                </span>
              )}
              {hasBearish && (
                <span className="flex items-center gap-1">
                  <span
                    className="flex h-3.5 w-3.5 items-center justify-center rounded-full text-[9px] font-bold text-white shadow-2xs"
                    style={{ backgroundColor: toRgbaColor(colors.danger) }}
                  >
                    S
                  </span>
                  Sell
                </span>
              )}
            </>
          )}
          {hasMetrics && metricLabel && (
            <span className="flex items-center gap-1.5">
              <span
                className="inline-block h-2.5 w-2.5 rounded-xs"
                style={{ backgroundColor: toRgbaColor(colors.primary, 0.55) }}
              />
              {metricLabel}
            </span>
          )}
        </div>
      )}

      {/* Chart Canvas with Cursor-Anchored Tooltip */}
      <div className="relative w-full rounded-md border border-line/40 bg-canvas/30" style={{ height }}>
        <div ref={containerRef} className="h-full w-full" />
      </div>
    </div>
  );
}
