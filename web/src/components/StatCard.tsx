import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
    <Card className={cn("", className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        {icon && <div className="text-muted-foreground">{icon}</div>}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold font-mono tabular-nums tracking-tight text-foreground">
          {value}
        </div>
        {(description || trend) && (
          <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
            {trend && (
              <span
                className={cn(
                  "font-semibold font-mono",
                  trend.positive ? "text-success" : "text-danger"
                )}
              >
                {trend.positive ? "+" : ""}{trend.value}
              </span>
            )}
            {description && <span>{description}</span>}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
