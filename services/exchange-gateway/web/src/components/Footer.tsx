export function Footer() {
  return (
    <footer className="border-t border-hairline bg-white">
      <div className="mx-auto flex max-w-page flex-col gap-4 px-6 py-8 text-sm text-muted sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <img
            src="./brand/beyond-emblem.svg"
            alt=""
            aria-hidden
            className="h-6 w-6 opacity-80"
          />
          <div>
            <div className="text-ink">A BeyondITL reference implementation</div>
            <p className="mt-1 max-w-prose text-xs leading-relaxed">
              All data is synthetic. Independent reference implementation. Not
              affiliated with or endorsed by the National Board of Revenue or
              any government body.
            </p>
          </div>
        </div>
        <div className="text-xs text-muted/80">
          <a
            href="./docs"
            className="underline decoration-hairline underline-offset-4 hover:text-brand-dark"
          >
            API docs
          </a>
        </div>
      </div>
    </footer>
  );
}
