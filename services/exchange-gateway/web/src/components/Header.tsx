import { ShieldCheck } from "lucide-react";

export function Header() {
  return (
    <header className="border-b border-hairline bg-white">
      <div className="mx-auto flex max-w-page items-center justify-between gap-6 px-6 py-3.5">
        <div className="flex items-center gap-3">
          <img
            src="./brand/beyond-emblem.svg"
            alt="BeyondITL emblem"
            className="h-8 w-8"
          />
          <div className="text-[15px] font-semibold tracking-[-0.005em] text-ink">
            Sovereign Revenue Data Exchange
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="hidden text-xs text-muted sm:inline">
            Runs on-premises · Restricted data localized (PDPO 2025)
          </span>
          <span className="pill border-brand/25 bg-brand-tint text-brand-dark">
            <ShieldCheck className="h-3.5 w-3.5" /> Demo · synthetic data
          </span>
        </div>
      </div>
    </header>
  );
}
