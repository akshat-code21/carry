interface MCFooterProps {
  quotaRemaining?: number | null;
}

export function MCFooter({ quotaRemaining }: MCFooterProps) {
  return (
    <footer className="mt-16 border-t border-tf-stroke py-8">
      <div className="flex items-start justify-between gap-8 max-md:flex-col">
        <p className="max-w-[680px] text-[12px] leading-5 text-tf-faint">
          TickerFlow aggregates third-party sentiment signals for research.
          It is not investment, legal, or tax advice. Always verify source data
          before making financial decisions.
        </p>

        <div className="flex shrink-0 items-center gap-4 text-[12px] text-tf-faint">
          {quotaRemaining !== null && quotaRemaining !== undefined && (
            <span className="font-mono tabular-nums">
              {quotaRemaining} requests left
            </span>
          )}
          <span aria-hidden="true" className="h-3 w-px bg-tf-stroke" />
          <span>TickerFlow · 2026</span>
        </div>
      </div>
    </footer>
  );
}
