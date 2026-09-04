import rgba from "color-rgba";

/**
 * Convert CSS colors (oklch, lab, oklab, lch, hex, rgb, hsl, named, etc.)
 * to `rgba(...)` strings accepted by Lightweight Charts and canvas/SVG renderers.
 */

export interface RgbaColor {
  r: number;
  g: number;
  b: number;
  a: number;
}

/**
 * Parse any CSS color into `{ r, g, b, a }` with channels in 0..255 and alpha in 0..1.
 */
export function parseColor(value: string | undefined | null): RgbaColor | null {
  if (!value) return null;
  const result = rgba(value);
  if (
    !result ||
    result.length < 4 ||
    result[0] === undefined ||
    result[1] === undefined ||
    result[2] === undefined ||
    result[3] === undefined
  ) {
    return null;
  }
  const [r, g, b, a] = result;
  return {
    r: Math.round(r),
    g: Math.round(g),
    b: Math.round(b),
    a: Math.round(a * 1000) / 1000,
  };
}

/** Backward compatibility alias for oklchToRgba */
export function oklchToRgba(value: string): RgbaColor | null {
  return parseColor(value);
}

/**
 * Convert any CSS color into an `rgba(r, g, b, a)` string accepted by
 * Lightweight Charts. Non-parseable strings pass through as fallbacks.
 */
export function toRgbaColor(value: string | undefined | null, alphaOverride?: number): string {
  if (!value) return "rgba(0, 0, 0, 1)";
  const trimmed = value.trim();
  if (trimmed === "transparent") {
    const alpha = alphaOverride !== undefined ? Math.max(0, Math.min(1, alphaOverride)) : 0;
    return `rgba(0, 0, 0, ${alpha})`;
  }
  const parsed = parseColor(trimmed);
  if (parsed) {
    const alpha = alphaOverride !== undefined ? Math.max(0, Math.min(1, alphaOverride)) : parsed.a;
    return `rgba(${parsed.r}, ${parsed.g}, ${parsed.b}, ${alpha})`;
  }
  if (trimmed.startsWith("#") || trimmed.startsWith("rgb") || trimmed.startsWith("hsl")) {
    return trimmed;
  }
  return trimmed;
}

/** Convenience: CSS color → `#rrggbb` hex (for SVG/HTML where supported). */
export function toHexColor(value: string): string {
  const parsed = parseColor(value);
  if (!parsed) return value;
  const hex = (n: number) => n.toString(16).padStart(2, "0");
  return `#${hex(parsed.r)}${hex(parsed.g)}${hex(parsed.b)}`;
}