#!/usr/bin/env bash
# Apply, promote, or delete the OpenChoreo resources for this project.
#
# Reads:
#   SRX_REPO_URL       Default: https://github.com/your-org/sovereign-revenue-exchange
#                      The OpenChoreo build pulls source from this URL. The
#                      workload.yaml files must be reachable at the configured
#                      appPath inside that repo.
#   SRX_REPO_REVISION  Default: main
#   SRX_NAMESPACE      Default: default
#
# Subcommands:
#   apply            Apply project + all three components in order.
#   apply-project    Apply just the Project resource.
#   apply-components Apply just the three Components + WorkflowRuns.
#   status           Show component, releasebinding, and httproute state.
#   promote          Promote the components from one environment to the next.
#                    promote dev->staging | promote staging->production
#   delete           Delete components, then project.
set -euo pipefail

SRX_REPO_URL="${SRX_REPO_URL:-https://github.com/your-org/sovereign-revenue-exchange}"
SRX_REPO_REVISION="${SRX_REPO_REVISION:-main}"
SRX_NAMESPACE="${SRX_NAMESPACE:-default}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

render() {
  # Substitute placeholders in a manifest. Avoids envsubst (not on all hosts).
  local src="$1"
  sed \
    -e "s|__SRX_REPO_URL__|${SRX_REPO_URL}|g" \
    -e "s|__SRX_REPO_REVISION__|${SRX_REPO_REVISION}|g" \
    "$src"
}

require_kubectl() {
  if ! command -v kubectl >/dev/null 2>&1; then
    echo "kubectl is required. Did you run scripts/local-up.sh first?" >&2
    exit 2
  fi
}

apply_project() {
  require_kubectl
  echo "Applying project resource…"
  kubectl apply -n "$SRX_NAMESPACE" -f "${ROOT}/openchoreo/project.yaml"
}

apply_components() {
  require_kubectl
  echo "Applying components from ${SRX_REPO_URL}@${SRX_REPO_REVISION}…"
  for c in taxpayer-registry returns exchange-gateway; do
    echo "  • $c"
    render "${ROOT}/openchoreo/components/${c}.yaml" | kubectl apply -n "$SRX_NAMESPACE" -f -
  done
}

cmd_apply() {
  apply_project
  apply_components
  echo
  echo "Apply complete. Watch build progress with:"
  echo "  kubectl get workflowrun -n ${SRX_NAMESPACE}"
  echo "  kubectl get pods -n workflows-${SRX_NAMESPACE}"
}

cmd_status() {
  require_kubectl
  echo "--- Components ---"
  kubectl get component -n "$SRX_NAMESPACE" -l openchoreo.dev/project=sovereign-revenue-exchange
  echo
  echo "--- ReleaseBindings ---"
  kubectl get releasebinding -n "$SRX_NAMESPACE" -l openchoreo.dev/project=sovereign-revenue-exchange
  echo
  echo "--- HTTPRoutes (gateway-exposed) ---"
  kubectl get httproute -A -l openchoreo.dev/project=sovereign-revenue-exchange
}

cmd_promote() {
  require_kubectl
  local arg="${1:-}"
  local src dst
  case "$arg" in
    "dev->staging"|"development->staging")
      src=development; dst=staging
      ;;
    "staging->production"|"staging->prod")
      src=staging; dst=production
      ;;
    *)
      echo "usage: deploy.sh promote dev->staging|staging->production" >&2
      exit 2
      ;;
  esac
  echo "Promoting components ${src} -> ${dst}…"
  for c in taxpayer-registry returns exchange-gateway; do
    echo "  • $c"
    # OpenChoreo's default DeploymentPipeline declares the promotion path
    # (development -> staging -> production); promotion is triggered by
    # creating a ReleaseBinding for the target environment. The exact
    # promotion CLI/CRD evolves between releases — this command surfaces
    # the canonical kubectl approach. Override by piping yaml of your choice.
    cat <<YAML | kubectl apply -n "$SRX_NAMESPACE" -f -
apiVersion: openchoreo.dev/v1alpha1
kind: ReleaseBinding
metadata:
  name: ${c}-${dst}
  namespace: ${SRX_NAMESPACE}
spec:
  owner:
    projectName: sovereign-revenue-exchange
    componentName: ${c}
  environment: ${dst}
YAML
  done
  echo
  echo "Watch with: kubectl get releasebinding -n ${SRX_NAMESPACE}"
}

cmd_delete() {
  require_kubectl
  echo "Deleting components and project…"
  for c in exchange-gateway returns taxpayer-registry; do
    render "${ROOT}/openchoreo/components/${c}.yaml" \
      | kubectl delete -n "$SRX_NAMESPACE" --ignore-not-found -f - || true
  done
  kubectl delete -n "$SRX_NAMESPACE" --ignore-not-found -f "${ROOT}/openchoreo/project.yaml" || true
}

case "${1:-}" in
  apply)            cmd_apply ;;
  apply-project)    apply_project ;;
  apply-components) apply_components ;;
  status)           cmd_status ;;
  promote)          shift; cmd_promote "$@" ;;
  delete)           cmd_delete ;;
  *)
    cat <<EOF
usage: deploy.sh <subcommand>

subcommands:
  apply               apply project + components (uses SRX_REPO_URL, SRX_REPO_REVISION)
  apply-project       apply only the Project resource
  apply-components    apply only the Components + WorkflowRuns
  status              show component / releasebinding / httproute state
  promote dev->staging
  promote staging->production
  delete              delete components, then project

environment:
  SRX_REPO_URL=${SRX_REPO_URL}
  SRX_REPO_REVISION=${SRX_REPO_REVISION}
  SRX_NAMESPACE=${SRX_NAMESPACE}
EOF
    exit 2 ;;
esac
