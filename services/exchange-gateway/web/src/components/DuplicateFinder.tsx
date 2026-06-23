import * as React from "react";
import { GitMerge, Users } from "lucide-react";
import { Card, CardBody, CardHeader, CardTitle, Skeleton } from "./ui";
import type { TaxpayerSummary } from "@/lib/types";
import { fetchDuplicatesByNid, formatDate } from "@/lib/api";

const SEEDED_DUPLICATE_NID = "1000000020";

type Phase = "idle" | "loading" | "found" | "merged" | "empty" | "error";

export function DuplicateFinder() {
  const [phase, setPhase] = React.useState<Phase>("idle");
  const [candidates, setCandidates] = React.useState<TaxpayerSummary[]>([]);
  const [error, setError] = React.useState<string | null>(null);
  const [nid, setNid] = React.useState(SEEDED_DUPLICATE_NID);

  const start = async () => {
    setError(null);
    setPhase("loading");
    setCandidates([]);
    try {
      const rows = await fetchDuplicatesByNid(nid);
      if (rows.length <= 1) {
        setCandidates(rows);
        setPhase("empty");
        return;
      }
      setCandidates(rows);
      setPhase("found");
      // Pause briefly so the viewer sees the duplicates, then collapse.
      setTimeout(() => setPhase("merged"), 1400);
    } catch (e) {
      setError(String((e as Error).message || e));
      setPhase("error");
    }
  };

  const merged = phase === "merged" ? candidates[0] : null;

  return (
    <Card className="animate-fade-up">
      <CardHeader>
        <CardTitle>
          Find duplicates
          <span lang="bn" className="ml-1.5 text-muted/80">
            ডুপ্লিকেট
          </span>
        </CardTitle>
        <div className="flex items-center gap-2 text-xs text-muted">
          <Users className="h-3.5 w-3.5" /> Demo against the seeded duplicate pair
        </div>
      </CardHeader>
      <CardBody>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <label className="block flex-1">
            <span className="mb-1.5 block text-xs font-medium uppercase tracking-[0.08em] text-muted">
              National ID
            </span>
            <input
              className="input-base h-10 font-mono"
              value={nid}
              inputMode="numeric"
              spellCheck={false}
              onChange={(e) => setNid(e.target.value)}
            />
          </label>
          <button
            type="button"
            className="btn-primary h-10 px-4 text-xs"
            onClick={start}
            disabled={phase === "loading" || !/^\d{10}$/.test(nid)}
          >
            <GitMerge className="h-4 w-4" />
            {phase === "loading" ? "Searching…" : "Find duplicates"}
          </button>
        </div>

        <div className="mt-5">
          {phase === "loading" && (
            <div className="space-y-2">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          )}

          {phase === "error" && (
            <div className="rounded-md border border-status-red/30 bg-red-50 p-3 text-sm text-status-red">
              {error}
            </div>
          )}

          {phase === "empty" && (
            <div className="rounded-md border border-dashed border-hairline bg-white p-4 text-sm text-muted">
              {candidates.length === 0
                ? `No taxpayer records share NID ${nid}.`
                : `Only one taxpayer record carries NID ${nid}. Nothing to merge.`}
            </div>
          )}

          {(phase === "found" || phase === "merged") && (
            <div className="relative">
              <div
                className={`grid gap-3 transition-all duration-700 sm:grid-cols-2 ${
                  phase === "merged"
                    ? "pointer-events-none scale-95 opacity-0"
                    : "opacity-100"
                }`}
              >
                {candidates.map((c) => (
                  <DuplicateRow key={c.tin} t={c} />
                ))}
              </div>
              {merged && (
                <div className="-mt-12 sm:-mt-16">
                  <div className="rounded-md border border-brand/30 bg-brand-tint/60 p-4">
                    <div className="mb-1 text-xs font-medium uppercase tracking-[0.08em] text-brand-dark">
                      Merged identity
                    </div>
                    <div className="text-sm text-ink">
                      <span className="font-mono tabular">{merged.tin}</span>
                      <span className="mx-2 text-muted">·</span>
                      {merged.name}
                      <span className="mx-2 text-muted">·</span>
                      <span className="font-mono tabular text-muted">
                        NID {merged.nid}
                      </span>
                    </div>
                    <div className="mt-1 text-xs text-muted">
                      Registered {formatDate(merged.registered_on)} ·{" "}
                      {candidates.length - 1} duplicate record
                      {candidates.length - 1 === 1 ? "" : "s"} collapsed.
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </CardBody>
    </Card>
  );
}

function DuplicateRow({ t }: { t: TaxpayerSummary }) {
  return (
    <div className="rounded-md border border-hairline bg-white p-3">
      <div className="font-mono tabular text-sm text-ink">{t.tin}</div>
      <div className="mt-0.5 text-sm text-ink/80">{t.name}</div>
      <div className="mt-1 text-xs text-muted">
        NID <span className="font-mono">{t.nid}</span> · registered{" "}
        {formatDate(t.registered_on)}
      </div>
    </div>
  );
}
