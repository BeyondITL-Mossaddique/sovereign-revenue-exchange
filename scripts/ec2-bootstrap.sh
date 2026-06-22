#!/usr/bin/env bash
# Bootstrap an Ubuntu 22.04/24.04 host (e.g. an AWS EC2 instance) for the
# OpenChoreo quick-start install.
#
# Run as a user with sudo. Do not run as root unless your image expects it.
# Run with --dry-run to print the steps without executing.
#
# Recommended instance: 4 vCPU / 8 GB RAM, 30 GB gp3 root volume,
# security group allowing 22 (SSH), 80, 443. Open 19080/19443 only if you
# want to hit the OpenChoreo gateway directly without nginx in front.
set -euo pipefail

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
fi

run() {
  echo "+ $*"
  if [[ "$DRY_RUN" -eq 0 ]]; then
    eval "$@"
  fi
}

require_ubuntu() {
  if ! grep -qE '^(NAME|ID)=.*[Uu]buntu' /etc/os-release 2>/dev/null; then
    echo "This script targets Ubuntu. /etc/os-release does not look like Ubuntu." >&2
    exit 2
  fi
  local v
  v=$(. /etc/os-release && echo "$VERSION_ID")
  case "$v" in
    22.04|24.04) : ;;
    *) echo "Ubuntu ${v} is untested. Continuing anyway." >&2 ;;
  esac
}

require_ubuntu

echo "==> apt update + base packages"
run sudo apt-get update -y
run sudo apt-get install -y ca-certificates curl gnupg jq git make

echo
echo "==> Docker Engine (official apt repo)"
run sudo install -m 0755 -d /etc/apt/keyrings
run "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg"
run sudo chmod a+r /etc/apt/keyrings/docker.gpg
run 'echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null'
run sudo apt-get update -y
run sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
run sudo usermod -aG docker "$USER"

echo
echo "==> OpenChoreo quick-start (will run as the current user after re-login)"
cat <<'EOF'

After this script finishes, log out and back in (so the docker group takes
effect), then run:

    cd ~/sovereign-revenue-exchange
    scripts/local-up.sh --run

That launches the OpenChoreo dev container. Inside it, run:

    ./install.sh --version v1.1.1 --with-build --with-observability

The install takes ~5-10 minutes the first time. When it finishes the
gateway is listening on host ports 19080 (HTTP) and 19443 (HTTPS).

EOF

cat <<'EOF'

--- Optional: nginx + TLS in front of the OpenChoreo gateway -------------

If you want a public subdomain (e.g. api.example.gov.bd) terminating TLS and
proxying to the OpenChoreo gateway, do roughly this. The exact commands are
left for you to run because they assume you own a domain, a DNS record, and
have decided which agency / hostname to publish under.

  sudo apt-get install -y nginx certbot python3-certbot-nginx

  sudo tee /etc/nginx/sites-available/srx.conf >/dev/null <<NGINX
  server {
      listen 80;
      server_name api.example.gov.bd;
      location / {
          proxy_pass http://127.0.0.1:19080;
          proxy_set_header Host $host;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
      }
  }
  NGINX
  sudo ln -sf /etc/nginx/sites-available/srx.conf /etc/nginx/sites-enabled/srx.conf
  sudo nginx -t && sudo systemctl reload nginx
  sudo certbot --nginx -d api.example.gov.bd  # issues + auto-renews a cert

Make sure your security group / firewall opens 80 and 443 inbound for the
Let's Encrypt HTTP-01 challenge to succeed.
EOF

echo
echo "Bootstrap complete."
