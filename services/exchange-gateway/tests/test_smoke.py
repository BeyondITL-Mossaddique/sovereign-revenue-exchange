from __future__ import annotations

import os

import pytest
import respx
from fastapi.testclient import TestClient
from httpx import Response

REGISTRY_URL = "http://registry-stub:8000"
RETURNS_URL = "http://returns-stub:8000"

os.environ["TAXPAYER_REGISTRY_URL"] = REGISTRY_URL
os.environ["RETURNS_URL"] = RETURNS_URL


@pytest.fixture(scope="module")
def client() -> TestClient:
    from app.main import app

    with TestClient(app) as c:
        yield c


TAXPAYER_900000000001 = {
    "tin": "900000000001",
    "nid": "1000000001",
    "name": "Test Taxpayer 001",
    "phone": "+880-1700000001",
    "address": "Test Address 1, Dhaka",
    "registered_on": "2024-01-15",
}

RETURNS_900000000001 = [
    {
        "id": "R001",
        "tin": "900000000001",
        "period": "2024",
        "figures": {
            "gross_income": "1200000.00",
            "deductions": "150000.00",
            "tax_payable": "120000.00",
            "currency": "BDT",
        },
        "status": "accepted",
        "submitted_at": "2025-01-15T09:30:00Z",
    }
]


def test_healthz(client: TestClient) -> None:
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["service"] == "exchange-gateway"


def test_dashboard_root(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    body = r.text
    # The React entry HTML carries the title and the BeyondITL reference
    # description; the rest of the page (TIN default, endpoint URLs) lives
    # in the bundled JS that is served from /assets/.
    assert "Sovereign Revenue Data Exchange" in body
    assert "BeyondITL" in body
    assert '<div id="root"></div>' in body


@respx.mock
def test_taxpayer_profile_happy_path(client: TestClient) -> None:
    respx.get(f"{REGISTRY_URL}/taxpayers/900000000001").mock(
        return_value=Response(200, json=TAXPAYER_900000000001)
    )
    respx.get(f"{RETURNS_URL}/returns").mock(
        return_value=Response(200, json=RETURNS_900000000001)
    )

    r = client.get(
        "/exchange/taxpayer-profile/900000000001",
        headers={"X-Requesting-Agency": "customs"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["taxpayer"]["tin"] == "900000000001"
    assert body["served_to_agency"] == "customs"
    assert len(body["returns"]) == 1
    assert body["returns"][0]["id"] == "R001"


@respx.mock
def test_taxpayer_profile_not_found(client: TestClient) -> None:
    respx.get(f"{REGISTRY_URL}/taxpayers/900000099999").mock(
        return_value=Response(404, json={"detail": "not found"})
    )
    r = client.get("/exchange/taxpayer-profile/900000099999")
    assert r.status_code == 404


@respx.mock
def test_taxpayer_profile_upstream_failure(client: TestClient) -> None:
    respx.get(f"{REGISTRY_URL}/taxpayers/900000000001").mock(
        return_value=Response(500)
    )
    r = client.get("/exchange/taxpayer-profile/900000000001")
    assert r.status_code == 502


@respx.mock
def test_verify_match(client: TestClient) -> None:
    respx.get(f"{REGISTRY_URL}/taxpayers/900000000001").mock(
        return_value=Response(200, json=TAXPAYER_900000000001)
    )
    respx.get(f"{RETURNS_URL}/returns").mock(
        return_value=Response(200, json=RETURNS_900000000001)
    )
    r = client.post(
        "/exchange/verify",
        json={"tin": "900000000001", "period": "2024", "claimed_status": "accepted"},
        headers={"X-Requesting-Agency": "audit-office"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["verified"] is True
    assert body["actual_status"] == "accepted"
    assert body["served_to_agency"] == "audit-office"


@respx.mock
def test_verify_mismatch(client: TestClient) -> None:
    respx.get(f"{REGISTRY_URL}/taxpayers/900000000001").mock(
        return_value=Response(200, json=TAXPAYER_900000000001)
    )
    respx.get(f"{RETURNS_URL}/returns").mock(
        return_value=Response(200, json=RETURNS_900000000001)
    )
    r = client.post(
        "/exchange/verify",
        json={"tin": "900000000001", "period": "2024", "claimed_status": "rejected"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["verified"] is False
    assert body["actual_status"] == "accepted"


@respx.mock
def test_verify_period_missing(client: TestClient) -> None:
    respx.get(f"{REGISTRY_URL}/taxpayers/900000000001").mock(
        return_value=Response(200, json=TAXPAYER_900000000001)
    )
    respx.get(f"{RETURNS_URL}/returns").mock(return_value=Response(200, json=[]))
    r = client.post(
        "/exchange/verify",
        json={"tin": "900000000001", "period": "2099", "claimed_status": "accepted"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["verified"] is False
    assert body["actual_status"] is None
