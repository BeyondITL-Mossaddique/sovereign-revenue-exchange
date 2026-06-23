import type {
  AccessLogEntry,
  TaxpayerProfile,
  TaxpayerSummary,
} from "./types";

// Build a URL relative to the page's baseURI so the dashboard works whether
// it is served from "/" locally or from "/exchange-gateway-http/" through
// the OpenChoreo gateway. Vite is configured with `base: './'`, so static
// asset paths and these API calls all resolve against `document.baseURI`.
function apiUrl(path: string): string {
  return new URL(path.replace(/^\/+/, ""), document.baseURI).toString();
}

const HEADERS: HeadersInit = {
  Accept: "application/json",
  "X-Requesting-Agency": "minister-dashboard",
};

export class NotFoundError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "NotFoundError";
  }
}

export async function fetchTaxpayerProfile(
  tin: string,
): Promise<TaxpayerProfile> {
  const res = await fetch(apiUrl(`exchange/taxpayer-profile/${tin}`), {
    headers: HEADERS,
  });
  if (res.status === 404) {
    throw new NotFoundError(`No taxpayer is registered with TIN ${tin}.`);
  }
  if (!res.ok) {
    throw new Error(`Gateway responded with HTTP ${res.status}.`);
  }
  return res.json();
}

export async function fetchAccessLog(
  limit = 25,
): Promise<AccessLogEntry[]> {
  const res = await fetch(apiUrl(`exchange/access-log?limit=${limit}`), {
    headers: HEADERS,
  });
  if (!res.ok) {
    throw new Error(`Gateway responded with HTTP ${res.status}.`);
  }
  return res.json();
}

export async function fetchDuplicatesByNid(
  nid: string,
): Promise<TaxpayerSummary[]> {
  const res = await fetch(apiUrl(`exchange/duplicates/by-nid/${nid}`), {
    headers: HEADERS,
  });
  if (!res.ok) {
    throw new Error(`Gateway responded with HTTP ${res.status}.`);
  }
  return res.json();
}

export function formatBdt(amount: string | number, currency = "BDT"): string {
  const n = typeof amount === "string" ? Number(amount) : amount;
  if (!Number.isFinite(n)) return `${amount} ${currency}`;
  return (
    n.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }) +
    " " +
    currency
  );
}

export function formatDate(iso: string): string {
  // YYYY-MM-DD or full ISO string
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
  });
}

export function formatDateTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}
