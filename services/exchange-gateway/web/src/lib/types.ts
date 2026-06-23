export type DataClassification =
  | "Public"
  | "Internal"
  | "Confidential"
  | "Restricted";

export interface TaxpayerSummary {
  tin: string;
  nid: string;
  name: string;
  registered_on: string;
  data_classification: DataClassification;
}

export interface TaxComputationSummary {
  taxable_income: string;
  threshold: string;
  computed_tax: string;
  no_tax_due: boolean;
  minimum_tax_applied: boolean;
  filer_category: string;
}

export interface ReturnSummary {
  id: string;
  period: string;
  status: "submitted" | "accepted" | "rejected" | string;
  tax_payable: string;
  currency: string;
  late_filing: boolean;
  computed: TaxComputationSummary | null;
}

export interface TaxpayerProfile {
  taxpayer: TaxpayerSummary;
  returns: ReturnSummary[];
  served_to_agency: string | null;
}

export interface AccessLogEntry {
  at: string;
  agency: string | null;
  method: string;
  path: string;
  target_tin: string | null;
  status_code: number;
}

export interface DuplicateCandidate {
  tin?: string | null;
  nid?: string | null;
  name: string;
  phone?: string | null;
}

export interface DuplicateGroup {
  key: string;
  members: DuplicateCandidate[];
}

export interface DeduplicateResponse {
  groups: DuplicateGroup[];
  unique_count: number;
  duplicate_count: number;
}
