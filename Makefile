# Sovereign Revenue Data Exchange — top-level Make targets.
#
# Two layers:
#   * Local compose stack (up, down, smoke) — for fast iteration without OpenChoreo.
#   * OpenChoreo deploy (deploy, status, promote-*, delete) — wraps scripts/deploy.sh.

SHELL := /usr/bin/env bash
COMPOSE ?= docker compose
SRX_REPO_URL ?= https://github.com/BeyondITL-Mossaddique/sovereign-revenue-exchange
SRX_REPO_REVISION ?= main

.PHONY: help up down smoke test build clean deploy status promote-staging promote-production delete openchoreo-up demo

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

demo: ## Build + start the compose stack, then print the demo URLs
	@$(COMPOSE) up -d --build
	@printf "\nWaiting for exchange-gateway to become healthy "
	@for i in $$(seq 1 30); do \
	  if curl -fsS http://127.0.0.1:18000/healthz >/dev/null 2>&1; then \
	    printf " ready.\n"; break; \
	  fi; \
	  printf "."; sleep 1; \
	  if [ $$i -eq 30 ]; then printf "\nTimed out waiting for gateway.\n"; exit 1; fi; \
	done
	@printf "\n\033[1mSovereign Revenue Data Exchange — demo stack is up.\033[0m\n\n"
	@printf "  \033[1mMinister-facing dashboard\033[0m (non-technical view)\n"
	@printf "    http://127.0.0.1:18000/\n\n"
	@printf "  \033[1mSwagger UI\033[0m (technical / engineering view)\n"
	@printf "    exchange-gateway:    http://127.0.0.1:18000/docs\n"
	@printf "    taxpayer-registry:   http://127.0.0.1:18001/docs\n"
	@printf "    returns:             http://127.0.0.1:18002/docs\n\n"
	@printf "  Stop the stack with:   make down\n"

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
