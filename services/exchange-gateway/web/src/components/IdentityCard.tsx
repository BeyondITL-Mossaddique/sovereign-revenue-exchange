import { Lock, ShieldAlert } from "lucide-react";
import { Badge, Card, CardBody, CardHeader, CardTitle, KeyValue } from "./ui";
import type { DataClassification, TaxpayerSummary } from "@/lib/types";
import { formatDate } from "@/lib/api";

function classificationTone(c: DataClassification) {
  switch (c) {
    case "Restricted":
      return "restricted" as const;
    case "Confidential":
      return "amber" as const;
    case "Internal":
      return "neutral" as const;
    default:
      return "neutral" as const;
  }
}

export function IdentityCard({
  taxpayer,
  servedToAgency,
}: {
  taxpayer: TaxpayerSummary;
  servedToAgency: string | null;
}) {
  return (
    <Card className="animate-fade-up">
      <CardHeader>
        <CardTitle>
          Identity <span lang="bn" className="ml-1.5 text-muted/80">করদাতা</span>
        </CardTitle>
        <Badge
          tone={classificationTone(taxpayer.data_classification)}
          icon={
            taxpayer.data_classification === "Restricted" ? (
              <Lock className="h-3.5 w-3.5" />
            ) : (
              <ShieldAlert className="h-3.5 w-3.5" />
            )
          }
        >
          {taxpayer.data_classification}
        </Badge>
      </CardHeader>
      <CardBody>
        <dl className="divide-y divide-hairline">
          <KeyValue
            label="TIN"
            altLabel="টিআইএন"
            value={taxpayer.tin}
            mono
          />
          <KeyValue
            label="National ID"
            value={
              <span className="font-mono tabular">{taxpayer.nid}</span>
            }
          />
          <KeyValue label="Name" altLabel="করদাতা" value={taxpayer.name} />
          <KeyValue
            label="Registered on"
            value={formatDate(taxpayer.registered_on)}
          />
          <KeyValue
            label="Served to agency"
            value={
              <span className="rounded bg-brand-tint px-1.5 py-0.5 text-xs font-medium text-brand-dark">
                {servedToAgency || "—"}
              </span>
            }
          />
        </dl>
      </CardBody>
    </Card>
  );
}
