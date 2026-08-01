import { cn } from "@/lib/utils";

interface SectionLabelProps {
  children: string;
  className?: string;
  dotClassName?: string;
}

export function SectionLabel({
  children,
  className,
  dotClassName,
}: SectionLabelProps) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <span
        className={cn("h-1.5 w-1.5 rounded-full bg-tf-signal", dotClassName)}
      />
      <span className="font-mono text-caption font-semibold uppercase tracking-[0.1em] text-tf-muted">
        {children}
      </span>
    </div>
  );
}
