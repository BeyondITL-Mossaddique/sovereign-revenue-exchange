#!/usr/bin/env bash
# Wraps the OpenChoreo v1.1 quick-start install.
#
# Prints the commands first, then runs them when invoked with `--run`.
# Without --run this script is a self-documenting reference you can paste.
set -euo pipefail

VERSION="${OPENCHOREO_VERSION:-v1.1.1}"
EXTRA_FLAGS="${OPENCHOREO_FLAGS:---with-build --with-observability}"

cat <<EOF
================================================================
  OpenChoreo quick-start — version $VERSION
================================================================

This will:
  1. Pull and run the openchoreo/quick-start dev container (privileged
     access to the host Docker socket; --network=host so the cluster
     gateway binds to host ports 19080 and 19443).
  2. Inside the dev container, run install.sh with these flags:
       $EXTRA_FLAGS

  After install completes (5-10 minutes on first run):
    • Gateway:    http://<env-name>-default.<gateway-host>:19080
    • Backstage:  http://openchoreo.localhost:8080/
                  user: admin@openchoreo.dev   pass: Admin@123

  Then deploy this project's components with:
    scripts/deploy.sh apply

EOF

cat <<'EOF'
--- 1. Dev container ---

docker run --rm -it --name openchoreo-quick-start \
  --pull always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --network=host \
  ghcr.io/openchoreo/quick-start:VERSION_PLACEHOLDER

--- 2. Inside the dev container ---

./install.sh --version VERSION_PLACEHOLDER FLAGS_PLACEHOLDER

--- 3. Outside the dev container, once install finishes ---

kubectl get nodes
kubectl get pods -A
EOF

if [[ "${1:-}" == "--run" ]]; then
  echo
  echo "Running the dev container now…"
  exec docker run --rm -it --name openchoreo-quick-start \
    --pull always \
    -v /var/run/docker.sock:/var/run/docker.sock \
    --network=host \
    "ghcr.io/openchoreo/quick-start:${VERSION}"
fi

echo
echo "Pass --run to launch the quick-start dev container now."
echo "Inside that container, you still have to invoke install.sh manually:"
echo "  ./install.sh --version ${VERSION} ${EXTRA_FLAGS}"
