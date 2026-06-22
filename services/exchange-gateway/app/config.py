"""Runtime configuration for the exchange gateway.

In a local docker-compose stack these resolve to the compose service DNS names.
In OpenChoreo, the project's service component DNS is injected by the platform
(see openchoreo/components/exchange-gateway.yaml for the env wiring).
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    taxpayer_registry_url: str
    returns_url: str
    upstream_timeout_s: float
    requesting_agency_header: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            taxpayer_registry_url=os.environ.get(
                "TAXPAYER_REGISTRY_URL", "http://taxpayer-registry:8000"
            ).rstrip("/"),
            returns_url=os.environ.get(
                "RETURNS_URL", "http://returns:8000"
            ).rstrip("/"),
            upstream_timeout_s=float(os.environ.get("UPSTREAM_TIMEOUT_S", "5.0")),
            requesting_agency_header=os.environ.get(
                "REQUESTING_AGENCY_HEADER", "X-Requesting-Agency"
            ),
        )


def get_settings() -> Settings:
    return Settings.from_env()
