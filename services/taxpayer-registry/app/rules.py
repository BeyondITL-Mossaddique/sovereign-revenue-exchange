"""Illustrative regulatory figures used by the taxpayer-registry service.

These are reference figures intended to demonstrate the shape of the rules,
not a definitive interpretation. Illustrative figures — verify against the
current Finance Act / NBR before any real use.
"""
from __future__ import annotations

from enum import Enum
from typing import Final


class DataClassification(str, Enum):
    """PDPO 2025 sensitivity bands used to tag every stored field.

    Restricted data (NID, banking) must remain on-premises in country.
    """

    public = "Public"
    internal = "Internal"
    confidential = "Confidential"
    restricted = "Restricted"


# Field-level classification policy. Used by the API to attach a badge to
# each returned record and to enforce localisation of Restricted data.
TAXPAYER_FIELD_CLASSIFICATION: Final[dict[str, DataClassification]] = {
    "tin": DataClassification.confidential,
    "nid": DataClassification.restricted,
    "name": DataClassification.confidential,
    "phone": DataClassification.confidential,
    "address": DataClassification.confidential,
    "registered_on": DataClassification.internal,
    # Banking fields stay Restricted whenever they appear.
    "bank_account": DataClassification.restricted,
    "bank_routing": DataClassification.restricted,
}


def record_classification(fields: dict[str, object]) -> DataClassification:
    """The highest classification level present in a record's fields."""
    order = [
        DataClassification.public,
        DataClassification.internal,
        DataClassification.confidential,
        DataClassification.restricted,
    ]
    highest = DataClassification.public
    for name, value in fields.items():
        if value is None:
            continue
        level = TAXPAYER_FIELD_CLASSIFICATION.get(name, DataClassification.internal)
        if order.index(level) > order.index(highest):
            highest = level
    return highest
