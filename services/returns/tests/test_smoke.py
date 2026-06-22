from __future__ import annotations

import os
import tempfile

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client() -> TestClient:
    fd, path = tempfile.mkstemp(suffix=".sqlite", prefix="returns-test-")
    os.close(fd)
    os.environ["SRX_DB_PATH"] = path

    from app.main import app

    with TestClient(app) as c:
        yield c

    os.unlink(path)


def test_healthz(client: TestClient) -> None:
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["service"] == "returns"


def test_get_seed_return(client: TestClient) -> None:
    r = client.get("/returns/R001")
    assert r.status_code == 200
    body = r.json()
    assert body["tin"] == "900000001"
    assert body["period"] == "2024"
    assert body["status"] == "accepted"


def test_list_returns_for_tin(client: TestClient) -> None:
    r = client.get("/returns", params={"tin": "900000001"})
    assert r.status_code == 200
    rows = r.json()
    # Seed data has 2 returns for 900000001.
    assert len(rows) == 2
    assert all(row["tin"] == "900000001" for row in rows)


def test_submit_return_roundtrip(client: TestClient) -> None:
    payload = {
        "tin": "900000004",
        "period": "2024",
        "figures": {
            "gross_income": "800000.00",
            "deductions": "75000.00",
            "tax_payable": "72500.00",
            "currency": "BDT",
        },
    }
    r = client.post("/returns", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "submitted"
    return_id = body["id"]

    r2 = client.get(f"/returns/{return_id}")
    assert r2.status_code == 200
    assert r2.json()["tin"] == "900000004"


def test_submit_return_duplicate_period(client: TestClient) -> None:
    payload = {
        "tin": "900000005",
        "period": "2024",
        "figures": {
            "gross_income": "500000.00",
            "deductions": "40000.00",
            "tax_payable": "46000.00",
            "currency": "BDT",
        },
    }
    r1 = client.post("/returns", json=payload)
    assert r1.status_code == 201
    r2 = client.post("/returns", json=payload)
    assert r2.status_code == 409


def test_submit_return_rejects_real_looking_tin(client: TestClient) -> None:
    payload = {
        "tin": "123456789",
        "period": "2024",
        "figures": {
            "gross_income": "100000.00",
            "deductions": "0",
            "tax_payable": "10000.00",
        },
    }
    r = client.post("/returns", json=payload)
    assert r.status_code == 422


def test_period_validation(client: TestClient) -> None:
    payload = {
        "tin": "900000005",
        "period": "Jan-2024",
        "figures": {
            "gross_income": "100000.00",
            "deductions": "0",
            "tax_payable": "10000.00",
        },
    }
    r = client.post("/returns", json=payload)
    assert r.status_code == 422
