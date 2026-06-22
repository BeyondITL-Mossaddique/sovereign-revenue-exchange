from __future__ import annotations

import os
import tempfile

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client() -> TestClient:
    # Isolate the test database to a tempfile so re-runs are deterministic.
    fd, path = tempfile.mkstemp(suffix=".sqlite", prefix="taxpayer-test-")
    os.close(fd)
    os.environ["SRX_DB_PATH"] = path

    from app.main import app

    with TestClient(app) as c:
        yield c

    os.unlink(path)


def test_healthz(client: TestClient) -> None:
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["service"] == "taxpayer-registry"


def test_get_known_taxpayer(client: TestClient) -> None:
    r = client.get("/taxpayers/900000001")
    assert r.status_code == 200
    body = r.json()
    assert body["tin"] == "900000001"
    assert body["nid"] == "1000000001"
    assert body["name"].startswith("Test Taxpayer")


def test_get_unknown_taxpayer(client: TestClient) -> None:
    r = client.get("/taxpayers/900099999")
    assert r.status_code == 404


def test_lookup_by_nid(client: TestClient) -> None:
    r = client.get("/taxpayers", params={"nid": "1000000003"})
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 1
    assert rows[0]["tin"] == "900000003"


def test_lookup_by_nid_validation(client: TestClient) -> None:
    # NID must be exactly 10 digits.
    r = client.get("/taxpayers", params={"nid": "abc"})
    assert r.status_code == 422


def test_deduplicate_groups_by_nid(client: TestClient) -> None:
    payload = {
        "candidates": [
            {"nid": "1000000001", "name": "Test Taxpayer 001"},
            {"nid": "1000000001", "name": "test  taxpayer 001"},
            {"nid": "1000000002", "name": "Test Taxpayer 002"},
            {"name": "Test Singleton", "phone": "+880-170-9999999"},
        ]
    }
    r = client.post("/taxpayers/deduplicate", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["duplicate_count"] == 2
    assert any(g["key"] == "nid:1000000001" and len(g["members"]) == 2 for g in body["groups"])


def test_deduplicate_groups_by_name_phone(client: TestClient) -> None:
    payload = {
        "candidates": [
            {"name": "Acme Test Co", "phone": "+880-170-1234567"},
            {"name": "acme test co", "phone": "01701234567"},
            {"name": "Other Test Co", "phone": "+880-170-7654321"},
        ]
    }
    r = client.post("/taxpayers/deduplicate", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert any(g["key"].startswith("np:") and len(g["members"]) == 2 for g in body["groups"])


def test_tin_validation_rejects_non_test_range() -> None:
    # Models reject TINs outside the reserved test range. Import here so the
    # validator runs on construction, not via the API.
    from app.models import Taxpayer
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Taxpayer(
            tin="123456789",
            nid="1234567890",
            name="Should Fail",
            registered_on="2024-01-01",
        )
