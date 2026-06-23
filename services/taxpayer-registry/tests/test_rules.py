from __future__ import annotations

from app.rules import (
    DataClassification,
    TAXPAYER_FIELD_CLASSIFICATION,
    record_classification,
)


def test_nid_is_restricted() -> None:
    assert TAXPAYER_FIELD_CLASSIFICATION["nid"] is DataClassification.restricted


def test_banking_fields_are_restricted() -> None:
    assert TAXPAYER_FIELD_CLASSIFICATION["bank_account"] is DataClassification.restricted
    assert TAXPAYER_FIELD_CLASSIFICATION["bank_routing"] is DataClassification.restricted


def test_record_classification_picks_highest_level() -> None:
    record = {
        "tin": "900000000001",
        "nid": "1000000001",
        "name": "Test Taxpayer 001",
        "address": "Test Address 1",
    }
    assert record_classification(record) is DataClassification.restricted


def test_record_classification_without_nid_drops_to_confidential() -> None:
    record = {
        "tin": "900000000001",
        "name": "Test Taxpayer 001",
        "address": "Test Address 1",
        "nid": None,
    }
    assert record_classification(record) is DataClassification.confidential
