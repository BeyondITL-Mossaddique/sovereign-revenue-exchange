# Sovereign Revenue Data Exchange — an OpenChoreo reference

This repository is an independent reference implementation of one platform
shape a national revenue authority can adopt: a governed, observable
internal developer platform for taxpayer identity, return filing and
inter-agency data exchange, delivered on a fully open-source, on-premises
stack with no vendor lock-in.

Bangladesh already has the building blocks this kind of programme depends
on. NBR's e-services portal validates a TIN against National ID through
the e-tin / e-VAT services and against company data via RJSC. The TIN
itself has been the unified taxpayer ID across income tax and VAT for
some time. The national interoperability plumbing exists too — the
National e-Service Bus (NESB), National API Connect (NAC) and the
National Data Exchange (NDX) under BNDA, with the World Bank's SDRMP
programme funding the next wave of revenue-administration modernisation.

**This reference does not invent or replace any of that.** What it
demonstrates, in running code, is the platform pattern that *complements*
it:

1. **Open-source, no vendor lock-in.** State-owned and extensible by its
   own teams — every CRD and component is reviewable, replaceable and
   under Apache-2.0.
2. **Provably on-premises.** Restricted data (NID, banking) stays in
   country. Classification is recorded on every record so PDPO 2025
   localisation can be enforced rather than asserted.
3. **One consistent, auditable internal developer platform.** Governed
   APIs, dev → staging → production promotion, observability, and an
   access log on every gateway call.
4. **A reference pattern that fits the e-Service Bus / NDX / BNDA
   direction.** It is one example of how a governed, observable service
   layer can be built so that it interoperates with the national
   interoperability backbone — not an attempt to substitute for it.

The platform target is [OpenChoreo](https://openchoreo.dev) `v1.1.x`,
the CNCF/Linux Foundation internal developer platform that originated as
WSO2 Choreo.

## Not affiliated with NBR. Synthetic data only.

This project is independent. It is **not** affiliated with, endorsed by, or
sponsored by the National Board of Revenue (NBR) of Bangladesh, the
Government of the People's Republic of Bangladesh, or any other government
body. The service names and capabilities are modelled loosely on the kinds
of systems found in national revenue ecosystems (eTIN, eReturn, e-VAT,
EFDMS) purely to make the demonstration concrete. They do not represent,
replicate, or interoperate with any real production system.

All data is synthetic. Bangladesh TINs are 12 digits for both individuals
and companies; this reference uses a reserved 12-digit test range
(`900000000001`–`999999999999`) that is not issued in any real-world TIN
scheme. Names follow the pattern `Test Taxpayer N`. See
[`NOTICE`](./NOTICE) for the full disclaimer.

## What the three services illustrate

Each service stands in for a class of system that already exists in some
form inside the national revenue ecosystem. The point is the *shape* of
the platform around them — not to replace them.

| Demo service        | Class of system it illustrates                                                 | What this reference adds to the conversation                                                   |
| ------------------- | ------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------- |
| `taxpayer-registry` | The taxpayer master — TIN lookup, NID reverse-lookup, deduplication            | Data classification per field; Restricted (PDPO 2025) stays on-premises by construction.       |
| `returns`           | The system of record for filings (income tax, VAT, EFDMS-shaped)               | Tax liability computed from current illustrative figures + filer category; late filings flagged. |
| `exchange-gateway`  | A governed inter-agency read surface (Customs, AML, Land, Court use cases)     | One auditable entry point; every call logged with requesting agency + timestamp.               |
| platform pattern    | Governed APIs, dev/staging/prod promotion, observability, on-prem, no lock-in  | A complete reference of how this fits an internal developer platform built on open components. |

## Architecture

```mermaid
flowchart LR
  subgraph external["External agencies / clients"]
    A1[Requesting agency]
  end

  subgraph plane_ctl["OpenChoreo control plane"]
    direction TB
    cp1[(Project<br/>Component<br/>Workload<br/>WorkflowRun)]
  end

  subgraph plane_data["OpenChoreo data plane"]
    direction TB
    gw["External gateway<br/>(Envoy Gateway)<br/>:19080 / :19443"]
    subgraph proj["Project: sovereign-revenue-exchange"]
      direction LR
      eg["exchange-gateway<br/>(visibility: external)"]
      tr["taxpayer-registry<br/>(visibility: project)"]
      rt["returns<br/>(visibility: project)"]
    end
    gw --> eg
    eg --> tr
    eg --> rt
  end

  subgraph plane_obs["OpenChoreo observability plane"]
    obs[(Logs / metrics / traces)]
  end

  subgraph plane_wf["OpenChoreo workflow plane"]
    wf[[dockerfile-builder<br/>(per-component build)]]
  end

  A1 -->|TLS, agency header| gw
  cp1 -.->|reconciles| plane_data
  wf -.->|emits Workload + image| plane_data
  plane_data -.->|telemetry| plane_obs
```

The three planes shown are how OpenChoreo organises its responsibilities:
the control plane reconciles project and component declarations; the data
plane hosts the running services and their gateway; the observability plane
collects telemetry; the workflow plane runs builds. The user-facing surface
in this reference is the external gateway — `taxpayer-registry` and
`returns` are not directly reachable from outside the Project.

## Repository layout

```
sovereign-revenue-exchange/
├── services/
│   ├── taxpayer-registry/        # FastAPI, SQLite, Dockerfile, pytest
│   ├── returns/
│   └── exchange-gateway/         # composes the two above
├── openchoreo/
│   ├── project.yaml              # Project CR
│   └── components/               # one Component + WorkflowRun per service
├── scripts/
│   ├── local-up.sh               # wraps the OpenChoreo quick-start
│   ├── deploy.sh                 # apply / promote / delete in the cluster
│   ├── smoke.sh                  # end-to-end curl checks
│   └── ec2-bootstrap.sh          # Ubuntu host setup runbook
├── docs/
│   └── architecture.md           # longer write-up + mapping table
├── docker-compose.yml            # local stack for development without OpenChoreo
├── Makefile
├── README.md
├── CONTRIBUTING.md
├── NOTICE
└── LICENSE                       # Apache-2.0
```

## Run locally with docker compose

For day-to-day development, the three services run as plain containers under
`docker compose`. This validates the application code before anything
OpenChoreo-specific.

```sh
make up         # docker compose up -d --build
make smoke      # end-to-end curl checks against the gateway
make down
```

The compose stack publishes:

- `http://127.0.0.1:18000` — exchange-gateway (the public surface)
- `http://127.0.0.1:18001` — taxpayer-registry (exposed for inspection only)
- `http://127.0.0.1:18002` — returns (exposed for inspection only)

The two upstream services are exposed on the host **only** under compose —
under OpenChoreo they have `visibility: project` and are unreachable from
outside the Project.

Per-service tests:

```sh
make test       # builds each service's Dockerfile --target test and runs pytest
```

## Run under OpenChoreo

Targeting OpenChoreo `v1.1.1`. Requires Docker on the host (the install
runs everything else in containers).

```sh
scripts/local-up.sh           # prints what's about to happen
scripts/local-up.sh --run     # launches the openchoreo/quick-start dev container
```

Inside the dev container:

```sh
./install.sh --version v1.1.1 --with-build --with-observability
```

The install takes 5–10 minutes on first run. When it finishes:

- Gateway: `http://<env-name>-default.<gateway-host>:19080` (HTTP) / `:19443` (HTTPS)
- Backstage UI: `http://openchoreo.localhost:8080/`
  · user: `admin@openchoreo.dev` · pass: `Admin@123`

Then deploy this project's components:

```sh
# Defaults already point at this repo's published URL; override if you fork.
scripts/deploy.sh apply       # applies Project + 3 Components + 3 WorkflowRuns
scripts/deploy.sh status      # shows component / releasebinding / httproute state
```

Promote across the environments that the default DeploymentPipeline
provisions (development → staging → production):

```sh
scripts/deploy.sh promote dev->staging
scripts/deploy.sh promote staging->production
```

Once the build workflow completes and the ReleaseBinding goes ready, hit
the gateway-exposed endpoint:

```sh
GATEWAY_URL="http://<env-name>-default.<gateway-host>:19080/exchange-gateway-http" \
  scripts/smoke.sh
```

## Run on an EC2 host

`scripts/ec2-bootstrap.sh` is a runbook for Ubuntu 22.04 / 24.04. It
installs Docker (engine + compose plugin) from the official apt repo, adds
the current user to the `docker` group, and prints the follow-up steps for
the OpenChoreo quick-start and an optional nginx + Let's Encrypt frontend
for a public subdomain.

A `t3.large` (2 vCPU / 8 GB) is the minimum that comfortably runs the
quick-start install with build and observability enabled.

```sh
scp -r ./sovereign-revenue-exchange ubuntu@<host>:/home/ubuntu/
ssh ubuntu@<host>
cd ~/sovereign-revenue-exchange
./scripts/ec2-bootstrap.sh           # add --dry-run first to inspect
# log out and back in for the docker group change to apply
./scripts/local-up.sh --run
```

## What this reference is, and what it is not

It is one concrete shape for an internal developer platform that a
revenue authority can run itself, that fits next to the national
interoperability backbone (NESB / NAC / NDX), and that gives engineering
teams a consistent, observable, governed surface to build on.

It is not:

- **An NBR system.** This project is not affiliated with the National
  Board of Revenue or any government body. Service names borrow from the
  domain (eTIN, eReturn, e-VAT) only to make the demonstration concrete.
- **A replacement for TIN–NID verification.** NBR's portal already
  validates TIN against National ID through live NID and RJSC APIs.
- **A new national exchange.** The national exchange layer exists in the
  e-Service Bus, National API Connect and NDX under BNDA.

The genuine deltas of this reference are the four points in the intro:
open-source, on-premises by construction, one consistent developer
platform, and a pattern that *complements* the existing national
direction rather than competing with it.

## License

Apache-2.0. See [`LICENSE`](./LICENSE).
