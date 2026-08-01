import { cn } from "@/lib/utils";

interface SectionLabelProps {
  children: string;
  className?: string;
  dotColor?: string;
}

export function SectionLabel({
  children,
  className,
  dotColor = "#d8f36a",
}: SectionLabelProps) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <span
        className="h-1.5 w-1.5 rounded-full"
        style={{ backgroundColor: dotColor }}
      />
      <span className="text-[11px] font-semibold uppercase tracking-[0.11em] text-tf-muted">
        {children}
      </span>
    </div>
  );
}
