import * as React from "react";
import { ChevronDown, ChevronUp, ShieldCheck } from "lucide-react";
import { Skeleton } from "./ui";
import type { AccessLogEntry } from "@/lib/types";
import { fetchAccessLog, formatDateTime } from "@/lib/api";

export function GovernanceStrip() {
  const [open, setOpen] = React.useState(false);
  const [entries, setEntries] = React.useState<AccessLogEntry[] | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!open || entries !== null) return;
    setLoading(true);
    setError(null);
    fetchAccessLog(25)
      .then(setEntries)
      .catch((e) => setError(String(e.message || e)))
      .finally(() => setLoading(false));
  }, [open, entries]);

  return (
    <section
      aria-label="Gateway governance"
      className="animate-fade-up rounded-card border border-hairline bg-brand-tint/40 px-5 py-4"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <span className="mt-0.5 flex h-7 w-7 items-center justify-center rounded-full bg-brand text-white">
            <ShieldCheck className="h-4 w-4" />
          </span>
          <div>
            <div className="text-sm font-medium text-ink">
              Retrieved through the governed gateway
            </div>
            <div className="text-xs text-muted">
              Authenticated · rate-limited · logged · runs on-premises
            </div>
          </div>
        </div>
        <button
          type="button"
          className="btn-ghost text-xs"
          aria-expanded={open}
          aria-controls="access-log-panel"
          onClick={() => {
            setOpen((v) => !v);
            setEntries(null);
          }}
        >
          {open ? (
            <>
              Hide access log <ChevronUp className="h-4 w-4" />
            </>
          ) : (
            <>
              View access log <ChevronDown className="h-4 w-4" />
            </>
          )}
        </button>
      </div>
      {open && (
        <div
          id="access-log-panel"
          className="mt-4 overflow-x-auto rounded-md border border-hairline bg-white"
        >
          {loading && (
            <div className="space-y-2 p-4">
              <Skeleton className="h-3 w-2/3" />
              <Skeleton className="h-3 w-1/2" />
              <Skeleton className="h-3 w-3/4" />
            </div>
          )}
          {error && (
            <div className="p-4 text-sm text-status-red">
              Could not load the access log: {error}
            </div>
          )}
          {!loading && !error && entries && entries.length === 0 && (
            <div className="p-4 text-sm text-muted">
              No calls have been recorded yet.
            </div>
          )}
          {!loading && !error && entries && entries.length > 0 && (
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-hairline text-left uppercase tracking-[0.06em] text-muted">
                  <th className="py-2 pl-4 pr-3 font-medium">When (UTC)</th>
                  <th className="px-3 py-2 font-medium">Agency</th>
                  <th className="px-3 py-2 font-medium">Method</th>
                  <th className="px-3 py-2 font-medium">Path</th>
                  <th className="py-2 pl-3 pr-4 text-right font-medium">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody>
                {entries.map((e, i) => (
                  <tr
                    key={i}
                    className="border-b border-hairline last:border-b-0"
                  >
                    <td className="whitespace-nowrap py-2 pl-4 pr-3 font-mono tabular text-[11px] text-ink/80">
                      {formatDateTime(e.at)}
                    </td>
                    <td className="px-3 py-2 text-ink/80">
                      {e.agency || (
                        <span className="text-muted">—</span>
                      )}
                    </td>
                    <td className="px-3 py-2 font-mono text-[11px]">
                      {e.method}
                    </td>
                    <td className="px-3 py-2 font-mono text-[11px] text-ink/80">
                      {e.path}
                    </td>
                    <td className="py-2 pl-3 pr-4 text-right font-mono text-[11px]">
                      <span
                        className={
                          e.status_code >= 400
                            ? "text-status-red"
                            : "text-brand-dark"
                        }
                      >
                        {e.status_code}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </section>
  );
}
