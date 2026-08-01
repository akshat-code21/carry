import { cn } from "@/lib/utils";

interface MetricProps {
  value: string | number;
  prefix?: string;
  suffix?: string;
  decimals?: number;
  className?: string;
}

export function Metric({
  value,
  prefix = "",
  suffix = "",
  decimals,
  className,
}: MetricProps) {
  let formattedValue: string;

  if (typeof value === "number") {
    formattedValue = decimals !== undefined ? value.toFixed(decimals) : value.toLocaleString();
  } else {
    formattedValue = value;
  }

  return (
    <span className={cn("font-mono tabular-nums tracking-tight", className)}>
      {prefix}
      {formattedValue}
      {suffix}
    </span>
  );
}
