import { CheckCircle2, Clock4, XCircle, AlertTriangle } from "lucide-react";
import { Badge, Card, CardBody, CardHeader, CardTitle } from "./ui";
import type { ReturnSummary } from "@/lib/types";
import { formatBdt } from "@/lib/api";

function statusBadge(status: ReturnSummary["status"]) {
  const s = status.toLowerCase();
  if (s === "accepted") {
    return (
      <Badge tone="green" icon={<CheckCircle2 className="h-3.5 w-3.5" />}>
        Accepted
      </Badge>
    );
  }
  if (s === "rejected") {
    return (
      <Badge tone="red" icon={<XCircle className="h-3.5 w-3.5" />}>
        Rejected
      </Badge>
    );
  }
  if (s === "submitted") {
    return (
      <Badge tone="amber" icon={<Clock4 className="h-3.5 w-3.5" />}>
        Submitted
      </Badge>
    );
  }
  return <Badge tone="neutral">{status}</Badge>;
}

export function ReturnsCard({ returns }: { returns: ReturnSummary[] }) {
  if (returns.length === 0) {
    return (
      <Card className="animate-fade-up">
        <CardHeader>
          <CardTitle>
            Returns <span lang="bn" className="ml-1.5 text-muted/80">রিটার্ন</span>
          </CardTitle>
        </CardHeader>
        <CardBody>
          <div className="rounded-md border border-dashed border-hairline bg-brand-tint/30 px-4 py-6 text-center text-sm text-muted">
            No returns on file for this taxpayer.
          </div>
        </CardBody>
      </Card>
    );
  }
  return (
    <Card className="animate-fade-up">
      <CardHeader>
        <CardTitle>
          Returns <span lang="bn" className="ml-1.5 text-muted/80">রিটার্ন</span>
        </CardTitle>
        <span className="text-xs text-muted">
          {returns.length} on file
        </span>
      </CardHeader>
      <CardBody className="overflow-x-auto p-0">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-hairline text-left text-xs uppercase tracking-[0.06em] text-muted">
              <th className="py-3 pl-5 pr-3 font-medium">ID</th>
              <th className="px-3 py-3 font-medium">Period</th>
              <th className="px-3 py-3 font-medium">Status</th>
              <th className="px-3 py-3 text-right font-medium">Tax filed</th>
              <th className="py-3 pl-3 pr-5 text-right font-medium">
                Tax computed
              </th>
            </tr>
          </thead>
          <tbody>
            {returns.map((r) => (
              <tr
                key={r.id}
                className="border-b border-hairline last:border-b-0 hover:bg-brand-tint/30"
              >
                <td className="whitespace-nowrap py-3 pl-5 pr-3 font-mono text-[13px] text-ink/80">
                  {r.id}
                </td>
                <td className="whitespace-nowrap px-3 py-3 font-mono text-[13px]">
                  {r.period}
                  {r.late_filing && (
                    <span className="ml-2 inline-flex items-center gap-1 rounded bg-amber-50 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-status-amber">
                      <AlertTriangle className="h-3 w-3" /> Late
                    </span>
                  )}
                </td>
                <td className="px-3 py-3">{statusBadge(r.status)}</td>
                <td className="px-3 py-3 text-right tabular font-mono text-[13px]">
                  {formatBdt(r.tax_payable, r.currency)}
                </td>
                <td className="py-3 pl-3 pr-5 text-right tabular font-mono text-[13px]">
                  {r.computed?.no_tax_due ? (
                    <span className="text-muted">no tax due</span>
                  ) : r.computed ? (
                    <>
                      {formatBdt(r.computed.computed_tax, r.currency)}
                      {r.computed.minimum_tax_applied && (
                        <span className="ml-1.5 text-[10px] uppercase text-muted">
                          min
                        </span>
                      )}
                    </>
                  ) : (
                    <span className="text-muted">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardBody>
    </Card>
  );
}
