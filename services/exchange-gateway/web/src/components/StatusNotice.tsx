import { AlertCircle, SearchX } from "lucide-react";

export function NotFoundNotice({ tin }: { tin: string }) {
  return (
    <div className="animate-fade-up rounded-card border border-hairline bg-white p-6">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 flex h-9 w-9 items-center justify-center rounded-full bg-amber-50 text-status-amber">
          <SearchX className="h-5 w-5" />
        </span>
        <div>
          <h3 className="text-base font-semibold text-ink">
            No taxpayer registered with TIN{" "}
            <span className="font-mono tabular">{tin}</span>
          </h3>
          <p className="mt-1 text-sm text-muted">
            Double-check the number, or try the default seeded value to see a
            populated profile.
          </p>
        </div>
      </div>
    </div>
  );
}

export function ErrorNotice({ message }: { message: string }) {
  return (
    <div className="animate-fade-up rounded-card border border-status-red/30 bg-red-50 p-5">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 text-status-red">
          <AlertCircle className="h-5 w-5" />
        </span>
        <div>
          <h3 className="text-sm font-semibold text-status-red">
            The gateway could not complete this lookup
          </h3>
          <p className="mt-1 text-xs text-status-red/80">{message}</p>
        </div>
      </div>
    </div>
  );
}
