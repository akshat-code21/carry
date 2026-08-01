import React from "react";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-md border border-dashed border-line-strong bg-panel px-6 py-10 text-center",
        className
      )}
    >
      {icon && (
        <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-md border border-line bg-panel-raised text-ink-faint">
          {icon}
        </div>
      )}
      <h3 className="font-display text-title font-semibold tracking-tight text-ink">
        {title}
      </h3>
      {description && (
        <p className="mt-1 max-w-sm text-small text-ink-secondary">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
