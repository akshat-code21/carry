import React from "react";
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";

export interface Column<T> {
  key: string;
  header: string;
  render: (row: T, index: number) => React.ReactNode;
  numeric?: boolean;
  className?: string;
  headerClassName?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (row: T, index: number) => string;
  onRowClick?: (row: T) => void;
  emptyState?: React.ReactNode;
  className?: string;
  tableLayout?: "auto" | "fixed";
  /**
   * Dense-table pattern: sticky table header inside the scroll container.
   * Pair with a max-height via className (e.g. "max-h-[480px] overflow-y-auto").
   */
  stickyHeader?: boolean;
  /**
   * Dense-table pattern: keep the first (identity) column pinned during
   * horizontal scroll on narrow viewports.
   */
  stickyFirstColumn?: boolean;
}

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  onRowClick,
  emptyState,
  className,
  tableLayout = "fixed",
  stickyHeader = false,
  stickyFirstColumn = false,
}: DataTableProps<T>) {
  if (data.length === 0 && emptyState) {
    return <>{emptyState}</>;
  }

  const firstColStickyClasses =
    "sticky left-0 z-10 bg-panel group-hover/row:bg-panel-raised";

  return (
    <div className={cn("w-full overflow-x-auto rounded-md border border-line bg-panel", className)}>
      <Table className={cn(tableLayout === "fixed" && "table-fixed")}>
        <TableHeader>
          <TableRow
            className={cn(
              "bg-panel-raised hover:bg-panel-raised",
              stickyHeader && "[&_th]:sticky [&_th]:top-0 [&_th]:z-10"
            )}
          >
            {columns.map((col, i) => (
              <TableHead
                key={col.key}
                className={cn(
                  "px-3 py-2",
                  col.numeric && "text-right",
                  stickyFirstColumn && i === 0 && firstColStickyClasses,
                  stickyHeader && "bg-panel-raised",
                  col.headerClassName
                )}
              >
                {col.header}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((row, idx) => (
            <TableRow
              key={keyExtractor(row, idx)}
              onClick={() => onRowClick?.(row)}
              className={cn(
                "transition-colors group/row",
                onRowClick && "cursor-pointer hover:bg-panel-raised"
              )}
            >
              {columns.map((col, i) => (
                <TableCell
                  key={col.key}
                  className={cn(
                    "px-3 py-2.5 text-body text-ink align-top",
                    col.numeric && "text-right font-mono tabular-nums",
                    stickyFirstColumn && i === 0 && firstColStickyClasses,
                    col.className
                  )}
                >
                  {col.render(row, idx)}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
