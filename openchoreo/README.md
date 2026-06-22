# OpenChoreo resources for the Sovereign Revenue Data Exchange

These manifests are written for OpenChoreo `v1.1.x` and adapted from the
upstream samples at:

- [`samples/from-source/projects/url-shortener/`](https://github.com/openchoreo/openchoreo/tree/release-v1.1/samples/from-source/projects/url-shortener)
- [`samples/from-source/services/go-docker-greeter/`](https://github.com/openchoreo/openchoreo/tree/release-v1.1/samples/from-source/services/go-docker-greeter)
- [`samples/component-types/component-http-service/`](https://github.com/openchoreo/openchoreo/tree/release-v1.1/samples/component-types/component-http-service)

If you need to update these resources for a different OpenChoreo version,
re-read the matching upstream samples first. Do not invent CRD fields.

## Layout

```
openchoreo/
├── project.yaml                          # Project: sovereign-revenue-exchange
└── components/
    ├── taxpayer-registry.yaml            # Component + WorkflowRun (build)
    ├── returns.yaml
    └── exchange-gateway.yaml             # The only externally-exposed component
```

The workload-level endpoint definitions (port, type, visibility, dependencies,
env) live next to each service's source code:

```
services/
├── taxpayer-registry/workload.yaml       # visibility: project
├── returns/workload.yaml                 # visibility: project
└── exchange-gateway/workload.yaml        # visibility: external, with deps
```

This split mirrors how the upstream `sample-workloads` repo organises its
components: the `Component` CR references a repo + path; the build emits a
`Workload` from the `workload.yaml` it finds at that path.

## Visibility model

| Component         | Visibility | Reachable from                          |
| ----------------- | ---------- | --------------------------------------- |
| taxpayer-registry | `project`  | other components in the same Project    |
| returns           | `project`  | other components in the same Project    |
| exchange-gateway  | `external` | the platform's external HTTP gateway    |

This is the zero-trust / mediation pattern: the upstream services have no
externally-reachable endpoint. Every cross-boundary call enters through the
gateway, where the platform applies its policies.

## Auth and rate limiting

The OpenChoreo v1.1 sample set exposes external endpoints by rendering an
`HTTPRoute` against the data plane's `ingress.external` gateway. Authentication
(JWT / OAuth2) and rate limiting at the API layer are platform-level
concerns configured on the gateway itself (Envoy Gateway in the reference
install). The samples do not surface a per-component policy trait for these
in this release, so this reference does not invent one. See
`docs/architecture.md` for where in the request path policies attach and how
to add them when your data plane is configured for it.

## Apply

The `scripts/deploy.sh` script substitutes the `__SRX_REPO_URL__` and
`__SRX_REPO_REVISION__` placeholders in the component manifests and applies
them in order:

```
scripts/deploy.sh apply
```
