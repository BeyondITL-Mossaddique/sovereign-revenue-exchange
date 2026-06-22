# Sovereign Revenue Data Exchange — top-level Make targets.
#
# Two layers:
#   * Local compose stack (up, down, smoke) — for fast iteration without OpenChoreo.
#   * OpenChoreo deploy (deploy, status, promote-*, delete) — wraps scripts/deploy.sh.

SHELL := /usr/bin/env bash
COMPOSE ?= docker compose
SRX_REPO_URL ?= https://github.com/your-org/sovereign-revenue-exchange
SRX_REPO_REVISION ?= main

.PHONY: help up down smoke test build clean deploy status promote-staging promote-production delete openchoreo-up

help:
	@awk 'BEGIN {FS = ":.*##"; printf "usage: make <target>\n\ntargets:\n"} /^[a-zA-Z_\-]+:.*##/ { printf "  %-22s %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

# --- Local compose stack -------------------------------------------------

build: ## Build all three service images
	$(COMPOSE) build

up: ## Start the compose stack (builds first)
	$(COMPOSE) up -d --build

down: ## Stop the compose stack
	$(COMPOSE) down

smoke: ## End-to-end curl smoke tests against the local stack
	scripts/smoke.sh

test: ## Run each service's pytest suite inside its Docker test stage
	@for s in taxpayer-registry returns exchange-gateway; do \
	  echo "=== $$s ==="; \
	  (cd services/$$s && docker build --target test -t srx-$$s:test . >/dev/null && docker run --rm srx-$$s:test) || exit 1; \
	done

clean: down ## Stop and remove built dev images
	@docker image rm -f srx-taxpayer-registry:dev srx-returns:dev srx-exchange-gateway:dev 2>/dev/null || true
	@docker image rm -f srx-taxpayer-registry:test srx-returns:test srx-exchange-gateway:test 2>/dev/null || true

# --- OpenChoreo (assumes quick-start cluster is up and kubectl is configured) ---

openchoreo-up: ## Print + (with --run) launch the OpenChoreo quick-start dev container
	scripts/local-up.sh

deploy: ## Apply project + components to the OpenChoreo cluster
	SRX_REPO_URL=$(SRX_REPO_URL) SRX_REPO_REVISION=$(SRX_REPO_REVISION) scripts/deploy.sh apply

status: ## Show OpenChoreo component / releasebinding / httproute state
	scripts/deploy.sh status

promote-staging: ## Promote all three components development -> staging
	scripts/deploy.sh promote dev->staging

promote-production: ## Promote all three components staging -> production
	scripts/deploy.sh promote staging->production

delete: ## Delete components and project from the cluster
	scripts/deploy.sh delete
