# Architecture

This document expands on the high-level diagram in [`README.md`](../README.md)
and explains the design choices behind the three services and the
OpenChoreo resources that bind them together.

## Positioning

Bangladesh already has the building blocks this kind of programme depends
on:

- TIN–NID verification — NBR's e-services portal already validates TIN
  against National ID and against RJSC company data through live APIs.
- A unified income-tax/VAT taxpayer ID — the TIN serves both.
- National interoperability plumbing — the National e-Service Bus
  (NESB), National API Connect (NAC) and the National Data Exchange
  (NDX) under BNDA, with the World Bank's SDRMP funding the next wave of
  revenue-administration modernisation.

This reference is independent and **does not** present any of those as
new. It demonstrates a *complementary* shape: a governed, on-premises,
auditable internal developer platform that other state services can be
built on, in a way that fits cleanly next to the existing
interoperability backbone.

What is genuinely new here is the *pattern*, not the capability:

1. Open-source, no vendor lock-in — state-owned, extensible by its own
   teams, Apache-2.0 throughout.
2. Provably on-premises — Restricted data (NID, banking) is classified at
   the field level so PDPO 2025 localisation can be enforced.
3. One consistent, auditable internal developer platform — governed APIs,
   dev → staging → production promotion, observability, audit log of
   every gateway call.
4. A reference pattern for building governed, observable services that
   fit the e-Service Bus / NDX / BNDA direction — not an attempt to
   replace it.

## Goals

1. Show, with running code, how a state team can put a governed API
   surface in front of identity, return-filing and inter-agency data
   exchange, on a platform they own end-to-end.
2. Use only OpenChoreo CRDs and conventions that exist in the published
   `release-v1.1` samples. Do not invent fields.
3. Keep the demo small enough to fit on a single 8 GB / 4 vCPU host
   running OpenChoreo's `--with-build --with-observability` profile.
4. Keep every line of generated data obviously synthetic, and tag every
   field with its PDPO 2025 classification so the on-prem localisation
   guarantee is something the code itself can defend.

## Service boundaries

```
                          ┌──────────────────────────────┐
                          │   Project: sovereign-revenue │
                          │              -exchange       │
                          │                              │
       external           │  ┌────────────────────────┐  │
       gateway   ─────────┼─►│   exchange-gateway     │  │
       (Envoy)            │  │     (external)         │  │
                          │  └────────┬────────┬──────┘  │
                          │           │        │         │
                          │           ▼        ▼         │
                          │  ┌────────────┐ ┌────────┐   │
                          │  │ taxpayer-  │ │returns │   │
                          │  │ registry   │ │        │   │
                          │  │ (project)  │ │(project│   │
                          │  └────────────┘ └────────┘   │
                          └──────────────────────────────┘
```

Three services, one Project. The Project is the governance and isolation
boundary in OpenChoreo: components in the same Project can reach each
other when one declares the other in `workload.yaml -> dependencies`; the
external world can only reach what the platform exposes through the
gateway.

### taxpayer-registry

Holds taxpayer records keyed by TIN. The real-world analogue is the eTIN
registry plus the National ID (NID) verification surface and a duplicate-
taxpayer cleanup workflow. The endpoints exposed here are:

- `GET /taxpayers/{tin}` — single record lookup. 404 on miss.
- `GET /taxpayers?nid={nid}` — reverse lookup by national identity.
- `POST /taxpayers/deduplicate` — given a list of candidate records (the
  kind of feed an outside system might submit), return the groups that
  look like the same person.

Deduplication uses NID as the strongest identity signal and falls back to
normalised name + the trailing 9 digits of phone (which collapses local
`01…` and international `+880-1…` forms onto the same key). The algorithm
is intentionally simple — this is a reference, not a fuzzy-match library.

### returns

The system-of-record for filings. Tax authorities call this layer many
things (eReturn for income tax, the per-period filing layer behind e-VAT
and the EFDMS). The endpoints exposed here are:

- `POST /returns` — submit a return for a taxpayer + period.
- `GET /returns/{id}` — fetch a specific return.
- `GET /returns?tin={tin}` — list a taxpayer's returns, newest first.

Returns are uniquely scoped to `(tin, period)` — re-submitting the same
pair returns `409`. Period accepts annual (`YYYY`) and quarterly
(`YYYY-Q1..Q4`) forms only.

Tax liability is computed from a small, explicit table of illustrative
FY2025-26 figures in `services/returns/app/rules.py` (tax-free
thresholds by filer category, slabs at 10/15/20/25/30%, a 5,000 BDT
minimum tax, the 5,000,000 BDT VAT registration threshold). Every
figure is marked **illustrative — verify against the current Finance
Act / NBR before any real use.** Returns submitted outside the
1 July–30 November filing window are flagged `late_filing: true`.

### exchange-gateway

The only externally-exposed component. It composes the two upstream
services into a single governed read surface for other agencies, verifies
claims, and surfaces both a minister-facing dashboard and an access log:

- `GET /exchange/taxpayer-profile/{tin}` — taxpayer + their returns
  (with computed tax and `late_filing` flags), in one response. The
  `X-Requesting-Agency` header is echoed into `served_to_agency` and
  written to the audit trail.
- `POST /exchange/verify` — confirm that a stated `(tin, period,
  claimed_status)` matches reality.
- `GET /exchange/duplicates/by-nid/{nid}` — list of taxpayer records
  sharing the given NID (this is what the dashboard's "Find duplicates"
  panel calls to demonstrate dedupe end-to-end).
- `GET /exchange/access-log?limit=N` — the most-recent-first audit
  trail of gateway calls (timestamp, requesting agency, method, path,
  target TIN, status code).

Every call into the exchange surface is appended to a bounded in-memory
audit log. The dashboard exposes it under the "Retrieved through the
governed gateway" strip. In production this log would be flushed to an
append-only store; the reference keeps the last 200 entries in memory.

The gateway calls the upstreams over in-cluster DNS
(`http://taxpayer-registry:8000`, `http://returns:8000`). It does not
retry — retries belong in the mediation layer (OpenChoreo's gateway) and
masking them at the application layer hides upstream failures during smoke
tests.

#### Dashboard

The minister-facing dashboard is built from `services/exchange-gateway/web`
(React + Vite + TypeScript + Tailwind + shadcn-style components + lucide
icons) and copied into the FastAPI static dir by the multi-stage docker
build. Asset paths are all relative, so the bundle works both at `/`
locally and behind the OpenChoreo gateway's `/exchange-gateway-http/`
prefix without rebuilding.

## OpenChoreo resources

### Project (`openchoreo/project.yaml`)

A single `Project` CR named `sovereign-revenue-exchange`, using the
`default` DeploymentPipeline that the quick-start install provisions
(promotion path: development → staging → production).

### Components (`openchoreo/components/*.yaml`)

Each service has a `Component` and a `WorkflowRun`. Both reference
`ClusterWorkflow/dockerfile-builder` with the per-service path inside this
repo. The `Component` is wired to the built-in
`ClusterComponentType/deployment/service`, which renders the standard
service deployment + `HTTPRoute` for any endpoint with
`visibility: external`.

### Workload descriptors (`services/*/workload.yaml`)

The `Workload` for each component is supplied by the `workload.yaml`
sitting next to the source code. The platform's build picks it up and
emits a `Workload` CR after the image is built. The descriptors here set:

| Service           | Endpoint port | Visibility | Dependencies                             |
| ----------------- | ------------- | ---------- | ---------------------------------------- |
| taxpayer-registry | 8000          | project    | —                                        |
| returns           | 8000          | project    | —                                        |
| exchange-gateway  | 8000          | external   | taxpayer-registry/http, returns/http     |

The exchange-gateway descriptor also defines a small `configurations.env`
block that injects the upstream URLs into the container. This mirrors the
`POSTGRES_DSN` pattern in the upstream
[`url-shortener` sample](https://github.com/openchoreo/sample-workloads/blob/main/project-url-shortener/api-service/workload.yaml).

## Where authentication and rate limiting attach

The published v1.1 sample set does not include a per-component trait for
JWT/OAuth2 enforcement or rate limiting on external endpoints. Rather than
invent CRD fields, this reference does the honest thing:

1. **Mediation is structural.** The upstream services have
   `visibility: project`. No external client can reach them at all. Every
   cross-boundary call enters the platform through the
   `exchange-gateway`'s external HTTPRoute, which is the natural place
   for the data plane's gateway (Envoy Gateway in the reference install)
   to attach JWT validation and rate-limit policies.
2. **Application-layer attribution is present.** The
   `X-Requesting-Agency` header is captured and surfaced in responses, so
   that once a token-issuing identity provider is in place, the agency
   claim can be tied to the gateway's authenticated principal.
3. **Where to wire it.** When your data plane is configured with an
   `EnvoyGateway` plus
   [SecurityPolicy](https://gateway.envoyproxy.io/latest/api/extension_types/#securitypolicy)
   and
   [BackendTrafficPolicy](https://gateway.envoyproxy.io/latest/api/extension_types/#backendtrafficpolicy)
   resources, target the `HTTPRoute` the platform generates for the
   exchange-gateway component (label selector:
   `openchoreo.dev/component=exchange-gateway,openchoreo.dev/endpoint-visibility=external`).

## Promotion across environments

The default DeploymentPipeline declares
`development → staging → production`. Each environment gets its own
`ReleaseBinding` per component. `scripts/deploy.sh promote dev->staging`
applies a `ReleaseBinding` resource for the target environment for each
of the three components. This is intentionally a thin wrapper: the
canonical OpenChoreo promotion flow lives in the cluster, and the script
is just the convenience surface.

## Observability

The quick-start install with `--with-observability` brings up the
observability plane (OpenTelemetry collector + dashboards) and labels the
HTTPRoutes the platform generates so logs/metrics/traces are correlatable
back to the Component. This reference does not add custom OTel
instrumentation to the FastAPI apps in order to stay small — adding it is
a matter of installing the `opentelemetry-instrumentation-fastapi` package
and setting the collector endpoint via env, similar to how the
`url-shortener` sample's `api-service/workload.yaml` sets
`OTEL_EXPORTER_ENDPOINT`.

## Data is synthetic and bounded

The seed fixtures live in:

- `services/taxpayer-registry/app/fixtures.py`
- `services/returns/app/fixtures.py`

Constraints enforced in code:

- Bangladesh TINs are 12 digits for both individuals and companies. Every
  TIN must satisfy `900000000001 ≤ tin ≤ 999999999999` (a reserved
  12-digit test range). The `taxpayer-registry` Pydantic model rejects
  anything outside this range at construction time; the `returns` service
  applies the same check on submission. The fixture module also asserts
  the constraint at import time so a real-looking TIN cannot sneak into
  seed data.
- Names start with `Test Taxpayer` or `Test Entity`.
- NIDs are synthetic 10-digit numerics in the `100000000X` family.

If you adapt this reference, keep these rails in place. The point of the
test range is that any record leaking out of a demo cannot be confused for
a real taxpayer.
