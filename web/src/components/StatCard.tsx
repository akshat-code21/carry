import React from "react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface StatCardProps {
  title: string;
  value: string | number;
  icon?: React.ReactNode;
  description?: string;
  trend?: {
    value: string | number;
    positive?: boolean;
  };
  className?: string;
}

export function StatCard({
  title,
  value,
  icon,
  description,
  trend,
  className,
}: StatCardProps) {
  return (
    <Card size="sm" className={cn("p-0", className)}>
      <div className="flex items-center justify-between px-4 pt-3">
        <span className="label-overline">{title}</span>
        {icon && <span className="text-ink-faint">{icon}</span>}
      </div>
      <div className="px-4 pb-3 pt-1.5">
        <div className="font-mono text-display font-semibold tracking-tight tabular-nums text-ink">
          {value}
        </div>
        {(description || trend) && (
          <div className="mt-1 flex items-center gap-2 text-small text-ink-faint">
            {trend && (
              <span
                className={cn(
                  "font-mono font-semibold tabular-nums",
                  trend.positive ? "text-bullish" : "text-bearish"
                )}
              >
                {trend.positive ? "+" : ""}
                {trend.value}
              </span>
            )}
            {description && <span>{description}</span>}
          </div>
        )}
      </div>
    </Card>
  );
}
