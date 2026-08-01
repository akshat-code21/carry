import React from "react";
import { cn } from "@/lib/utils";

interface PageHeaderProps {
  title: string;
  description?: string;
  children?: React.ReactNode;
  className?: string;
}

export function PageHeader({
  title,
  description,
  children,
  className,
}: PageHeaderProps) {
  return (
    <div className={cn("flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between", className)}>
      <div className="flex-1 min-w-0">
        <h1 className="font-display text-display font-bold tracking-tight text-ink">
          {title}
        </h1>
        {description && (
          <p className="mt-1 line-clamp-2 max-w-3xl text-small text-ink-secondary">
            {description}
          </p>
        )}
      </div>
      {children && <div className="mt-3 flex shrink-0 items-center gap-2.5 sm:mt-0 sm:ml-4">{children}</div>}
    </div>
  );
}
