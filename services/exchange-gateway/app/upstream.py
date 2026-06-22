"""Typed HTTP client wrappers for the upstream services.

The wrappers intentionally do not retry. Retries belong in the gateway
mediation layer (OpenChoreo) and would otherwise mask upstream failures
during smoke tests.
"""
from __future__ import annotations

from typing import Any, Optional

import httpx
from fastapi import HTTPException

from .config import Settings


class UpstreamError(HTTPException):
    """Raised when an upstream call fails in a way the caller should see."""


def _client(timeout: float) -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=httpx.Timeout(timeout))


async def fetch_taxpayer(settings: Settings, tin: str) -> Optional[dict[str, Any]]:
    url = f"{settings.taxpayer_registry_url}/taxpayers/{tin}"
    async with _client(settings.upstream_timeout_s) as c:
        try:
            r = await c.get(url)
        except httpx.HTTPError as exc:
            raise UpstreamError(
                status_code=502,
                detail=f"taxpayer-registry unreachable: {exc.__class__.__name__}",
            ) from exc
    if r.status_code == 404:
        return None
    if r.status_code != 200:
        raise UpstreamError(
            status_code=502,
            detail=f"taxpayer-registry returned {r.status_code}",
        )
    return r.json()


async def fetch_returns_for_tin(settings: Settings, tin: str) -> list[dict[str, Any]]:
    url = f"{settings.returns_url}/returns"
    async with _client(settings.upstream_timeout_s) as c:
        try:
            r = await c.get(url, params={"tin": tin})
        except httpx.HTTPError as exc:
            raise UpstreamError(
                status_code=502,
                detail=f"returns unreachable: {exc.__class__.__name__}",
            ) from exc
    if r.status_code != 200:
        raise UpstreamError(
            status_code=502, detail=f"returns returned {r.status_code}"
        )
    return r.json()
