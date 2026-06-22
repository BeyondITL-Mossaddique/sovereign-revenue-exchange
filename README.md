# Sovereign Revenue Data Exchange — an OpenChoreo reference

This repository is a reference implementation of the platform pattern a
national revenue authority needs — taxpayer identity lookup and
deduplication, return filing, and governed inter-agency data exchange —
delivered on a fully open-source, on-premises-capable stack with no
proprietary lock-in. The platform target is
[OpenChoreo](https://openchoreo.dev) `v1.1.x`, the CNCF/Linux Foundation
internal developer platform that originated as WSO2 Choreo.

## Not affiliated with NBR. Synthetic data only.

This project is independent. It is **not** affiliated with, endorsed by, or
sponsored by the National Board of Revenue (NBR) of Bangladesh, the
Government of the People's Republic of Bangladesh, or any other government
body. The service names and capabilities are modelled loosely on the kinds
of systems found in national revenue ecosystems (eTIN, eReturn, e-VAT,
EFDMS) purely to make the demonstration concrete. They do not represent,
replicate, or interoperate with any real production system.

All data is synthetic. TINs use a reserved test range
(`900000001`–`999999999`) that is not issued in any real-world TIN scheme.
Names follow the pattern `Test Taxpayer N`. See [`NOTICE`](./NOTICE) for the
full disclaimer.

## What this maps to in a real revenue programme

| Demo service        | Real-world analogue                                            | Why it matters for a revenue authority                                                          |
| ------------------- | -------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `taxpayer-registry` | eTIN registry + NID verification + duplicate-taxpayer cleanup  | Identity is the foundation. Without one canonical taxpayer record, every other system drifts.   |
| `returns`           | eReturn (and the per-period filing layer behind e-VAT/EFDMS)   | The system of record for what was filed when. Audit, refund, and assessment all read from this. |
| `exchange-gateway`  | Inter-agency exchange (Customs, Bank/AML, Land, Court) and bilateral data-exchange treaties | Other agencies must reach taxpayer truth through a governed surface, not direct DB queries.     |
| platform pattern    | Governed APIs, multi-env promotion (dev/staging/prod), observability, on-prem deployment, open-source / no vendor lock-in | Sovereignty + accountability: tax data stays in-country, every change is reviewable, the stack is auditable. |

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
export SRX_REPO_URL=https://github.com/<your-org>/sovereign-revenue-exchange
export SRX_REPO_REVISION=main
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

## Why OpenChoreo for sovereign government workloads

- **Kubernetes-native.** The substrate is standard, replaceable, and
  understood. Operators do not need vendor-specific certifications. The
  whole stack is reviewable and auditable.
- **Runs fully on-premises.** OpenChoreo installs into your own cluster —
  in-country, in your own data centre, behind your own firewall. Tax data
  never leaves the jurisdiction by default.
- **Open governance.** OpenChoreo is open-source under Apache-2.0 and lives
  under Linux Foundation governance. No single vendor controls the roadmap
  or can withdraw the runtime.
- **No proprietary black-box layer.** Every CRD is published. There is no
  encrypted control-plane component you cannot inspect.
- **Modular.** Build, observability, workflow, and the control plane are
  separate installable units. Disable what you don't need.

## License

Apache-2.0. See [`LICENSE`](./LICENSE).
