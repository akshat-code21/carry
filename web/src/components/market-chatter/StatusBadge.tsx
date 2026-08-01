import { cn } from "@/lib/utils";

interface StatusBadgeProps {
  status: string;
  className?: string;
}

const statusConfig: Record<
  string,
  { classes: string; dot: string; label?: string }
> = {
  unavailable: {
    classes: "border-tf-negative/20 bg-tf-negative/10 text-tf-negative",
    dot: "bg-tf-negative",
  },
  partial: {
    classes: "border-tf-warning/20 bg-tf-warning/10 text-tf-warning",
    dot: "bg-tf-warning",
  },
  stale_budget_limited: {
    classes: "border-tf-warning/20 bg-tf-warning/10 text-tf-warning",
    dot: "bg-tf-warning",
    label: "Budget limited",
  },
};

const defaultConfig = {
  classes: "border-tf-positive/20 bg-tf-positive/10 text-tf-positive",
  dot: "bg-tf-positive",
};

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusConfig[status] ?? defaultConfig;
  const label = config.label ?? status.replaceAll("_", " ");

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-micro font-semibold uppercase tracking-[0.07em]",
        config.classes,
        className,
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", config.dot)} />
      {label}
    </span>
  );
}
