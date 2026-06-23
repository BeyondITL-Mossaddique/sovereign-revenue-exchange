from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.rules import (
    FilerCategory,
    MINIMUM_TAX,
    TAX_FREE_THRESHOLD,
    VAT_REGISTRATION_THRESHOLD,
    compute_tax,
    is_late_filing,
    needs_vat_registration,
)


def test_threshold_general_no_tax_due() -> None:
    # Income at the general threshold (after deductions) is below the cut-off.
    result = compute_tax(Decimal("375000"), Decimal("0"), FilerCategory.general)
    assert result.no_tax_due is True
    assert result.computed_tax == Decimal("0")
    assert result.threshold == TAX_FREE_THRESHOLD[FilerCategory.general]


def test_threshold_woman_or_senior_is_higher() -> None:
    # A woman/senior at 400k is still below threshold; a man at the same
    # income is above the general threshold and owes the minimum tax.
    woman = compute_tax(Decimal("400000"), Decimal("0"), FilerCategory.woman_or_senior)
    assert woman.no_tax_due is True

    man = compute_tax(Decimal("400000"), Decimal("0"), FilerCategory.general)
    assert man.no_tax_due is False
    assert man.computed_tax == MINIMUM_TAX
    assert man.minimum_tax_applied is True


def test_war_wounded_freedom_fighter_threshold() -> None:
    result = compute_tax(Decimal("500000"), Decimal("0"), FilerCategory.war_wounded_freedom_fighter)
    assert result.no_tax_due is True


def test_slab_application_first_band() -> None:
    # 100,000 BDT into the first 10% band on top of the general threshold.
    result = compute_tax(Decimal("475000"), Decimal("0"), FilerCategory.general)
    # 100000 * 0.10 = 10000, well above the minimum tax.
    assert result.no_tax_due is False
    assert result.computed_tax == Decimal("10000.00")
    assert result.minimum_tax_applied is False


def test_top_slab_30_percent() -> None:
    # 4,000,000 BDT income: 375k free + 300k@10 + 400k@15 + 500k@20 + 2,000k@25
    # leaves 425k in the 30% band.
    income = Decimal("4000000")
    result = compute_tax(income, Decimal("0"), FilerCategory.general)
    expected = (
        Decimal("300000") * Decimal("0.10")
        + Decimal("400000") * Decimal("0.15")
        + Decimal("500000") * Decimal("0.20")
        + Decimal("2000000") * Decimal("0.25")
        + Decimal("425000") * Decimal("0.30")
    ).quantize(Decimal("0.01"))
    assert result.computed_tax == expected


def test_deductions_reduce_taxable_income() -> None:
    base = compute_tax(Decimal("600000"), Decimal("0"), FilerCategory.general)
    with_deductions = compute_tax(Decimal("600000"), Decimal("100000"), FilerCategory.general)
    assert with_deductions.taxable_income == Decimal("500000")
    assert with_deductions.computed_tax < base.computed_tax


def test_minimum_tax_applies_just_above_threshold() -> None:
    # Income only 10,000 above the threshold yields 1,000 in tax — below
    # the 5,000 minimum, so the minimum applies.
    result = compute_tax(Decimal("385000"), Decimal("0"), FilerCategory.general)
    assert result.computed_tax == MINIMUM_TAX
    assert result.minimum_tax_applied is True


def test_negative_taxable_income_is_clamped_to_zero() -> None:
    result = compute_tax(Decimal("100000"), Decimal("200000"), FilerCategory.general)
    assert result.taxable_income == Decimal("0")
    assert result.no_tax_due is True


def test_filing_window_late_after_november() -> None:
    assert is_late_filing("2024", date(2024, 12, 1)) is True


def test_filing_window_on_time() -> None:
    assert is_late_filing("2024", date(2024, 10, 30)) is False
    assert is_late_filing("2024", date(2024, 7, 1)) is False
    assert is_late_filing("2024", date(2024, 11, 30)) is False


def test_filing_window_quarterly_never_late() -> None:
    # Quarterly periods are out of scope for the annual income-tax window.
    assert is_late_filing("2024-Q4", date(2025, 6, 30)) is False


def test_vat_registration_threshold() -> None:
    assert needs_vat_registration(VAT_REGISTRATION_THRESHOLD + Decimal("1")) is True
    assert needs_vat_registration(VAT_REGISTRATION_THRESHOLD) is False
    assert needs_vat_registration(Decimal("3000000")) is False


@pytest.mark.parametrize(
    "category",
    list(FilerCategory),
)
def test_thresholds_are_configured_for_every_category(category: FilerCategory) -> None:
    # Catches accidental config drift between FilerCategory and TAX_FREE_THRESHOLD.
    assert category in TAX_FREE_THRESHOLD
