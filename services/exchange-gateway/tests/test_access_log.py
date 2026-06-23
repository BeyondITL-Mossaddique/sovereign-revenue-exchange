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


@pytest.fixture()
def client():
    from app import rules
    from app.main import app

    rules.clear()
    with TestClient(app) as c:
        yield c


TAXPAYER = {
    "tin": "900000000001",
    "nid": "1000000001",
    "name": "Test Taxpayer 001",
    "phone": "+880-1700000001",
    "address": "Test Address 1, Dhaka",
    "registered_on": "2024-01-15",
    "data_classification": "Restricted",
}

RETURNS = [
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
        "submitted_at": "2024-10-15T09:30:00Z",
        "filer_category": "general",
        "late_filing": False,
        "computed": {
            "taxable_income": "1050000.00",
            "threshold": "375000",
            "computed_tax": "110000.00",
            "no_tax_due": False,
            "minimum_tax_applied": False,
            "filer_category": "general",
        },
        "data_classification": "Confidential",
    }
]


@respx.mock
def test_taxpayer_profile_surfaces_classification_and_computed_tax(client: TestClient) -> None:
    respx.get(f"{REGISTRY_URL}/taxpayers/900000000001").mock(
        return_value=Response(200, json=TAXPAYER)
    )
    respx.get(f"{RETURNS_URL}/returns").mock(
        return_value=Response(200, json=RETURNS)
    )
    r = client.get(
        "/exchange/taxpayer-profile/900000000001",
        headers={"X-Requesting-Agency": "customs"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["taxpayer"]["data_classification"] == "Restricted"
    assert body["returns"][0]["computed"]["computed_tax"] == "110000.00"
    assert body["returns"][0]["late_filing"] is False


@respx.mock
def test_access_log_records_calls(client: TestClient) -> None:
    respx.get(f"{REGISTRY_URL}/taxpayers/900000000001").mock(
        return_value=Response(200, json=TAXPAYER)
    )
    respx.get(f"{RETURNS_URL}/returns").mock(
        return_value=Response(200, json=RETURNS)
    )
    client.get(
        "/exchange/taxpayer-profile/900000000001",
        headers={"X-Requesting-Agency": "customs"},
    )
    r = client.get("/exchange/access-log")
    assert r.status_code == 200
    entries = r.json()
    # Most-recent-first ordering: the access-log call would itself not be
    # logged (the audit recorder runs inside the exchange handlers only).
    assert any(
        e["path"] == "/exchange/taxpayer-profile/900000000001"
        and e["agency"] == "customs"
        and e["status_code"] == 200
        and e["target_tin"] == "900000000001"
        for e in entries
    )


@respx.mock
def test_duplicates_by_nid_returns_group(client: TestClient) -> None:
    pair = [
        {**TAXPAYER, "tin": "900000000020", "name": "Test Taxpayer 020"},
        {**TAXPAYER, "tin": "900000000021", "name": "Test  Taxpayer 020"},
    ]
    respx.get(f"{REGISTRY_URL}/taxpayers", params={"nid": "1000000020"}).mock(
        return_value=Response(200, json=pair)
    )
    r = client.get(
        "/exchange/duplicates/by-nid/1000000020",
        headers={"X-Requesting-Agency": "auditor"},
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 2
    assert {b["tin"] for b in body} == {"900000000020", "900000000021"}


@respx.mock
def test_access_log_records_404(client: TestClient) -> None:
    respx.get(f"{REGISTRY_URL}/taxpayers/900000099999").mock(
        return_value=Response(404, json={"detail": "not found"})
    )
    client.get(
        "/exchange/taxpayer-profile/900000099999",
        headers={"X-Requesting-Agency": "audit-office"},
    )
    r = client.get("/exchange/access-log")
    entries = r.json()
    assert any(
        e["agency"] == "audit-office"
        and e["status_code"] == 404
        and e["target_tin"] == "900000099999"
        for e in entries
    )
