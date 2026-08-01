import React from "react";
import { AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title = "Signal interrupted",
  message,
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-md border border-bearish/25 bg-bearish/5 px-6 py-10 text-center",
        className
      )}
    >
      <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-md border border-bearish/30 bg-bearish/10 text-bearish">
        <AlertCircle className="h-4 w-4" />
      </div>
      <h3 className="font-display text-title font-semibold tracking-tight text-ink">
        {title}
      </h3>
      <p className="mt-1 max-w-md text-small text-ink-secondary">{message}</p>
      {onRetry && (
        <Button
          onClick={onRetry}
          variant="outline"
          size="sm"
          className="mt-4 gap-2 border-bearish/30 text-bearish hover:bg-bearish/10"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Try Again
        </Button>
      )}
    </div>
  );
}
