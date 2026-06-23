# Architecture

This document expands on the high-level diagram in [`README.md`](../README.md)
and explains the design choices behind the three services and the
OpenChoreo resources that bind them together.

## Goals

1. Show, with running code, how a national revenue authority can put a
   governed API surface in front of identity, return-filing, and
   inter-agency data exchange — without proprietary middleware.
2. Use only OpenChoreo CRDs and conventions that exist in the published
   `release-v1.1` samples. Do not invent fields.
3. Keep the demo small enough to fit on a single 8 GB / 4 vCPU host
   running OpenChoreo's `--with-build --with-observability` profile.
4. Keep every line of generated data obviously synthetic.

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

### exchange-gateway

The only externally-exposed component. It composes the two upstream
services into a single governed read surface for other agencies, and it
verifies claims:

- `GET /exchange/taxpayer-profile/{tin}` — taxpayer + their returns, in
  one response. The `X-Requesting-Agency` header is echoed into a
  `served_to_agency` field so the upstream can attribute reads to a
  requesting party (the place an audit log would attach).
- `POST /exchange/verify` — confirm that a stated `(tin, period,
  claimed_status)` matches reality. This is the API a customs officer's
  workstation or a court system would call to verify whether a return was
  filed and accepted.

The gateway calls the upstreams over in-cluster DNS
(`http://taxpayer-registry:8000`, `http://returns:8000`). It does not
retry — retries belong in the mediation layer (OpenChoreo's gateway) and
masking them at the application layer hides upstream failures during smoke
tests.

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
