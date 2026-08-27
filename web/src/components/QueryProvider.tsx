"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";

export function QueryProvider({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 2 * 60 * 1000, // 2 minute stale time for snappier back-nav
            refetchOnWindowFocus: false,
            retry: (failureCount, error) => {
              // Never retry on auth failures — avoids doubling cold-load time
              const apiErr = error as { status?: number; code?: string };
              if (apiErr?.status === 401 || apiErr?.code === "unauthorized") {
                return false;
              }
              return failureCount < 1;
            },
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
