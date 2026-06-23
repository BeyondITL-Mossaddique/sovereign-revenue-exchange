"""Illustrative tax-rule figures for the returns service.

Illustrative figures — verify against the current Finance Act / NBR before any
real use. The numbers here are anchored to publicly stated FY2025-26 figures
but are presented as a configurable reference, not a binding interpretation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Final, Optional


class FilerCategory(str, Enum):
    general = "general"
    woman_or_senior = "woman_or_senior"
    person_with_disability = "person_with_disability"
    war_wounded_freedom_fighter = "war_wounded_freedom_fighter"


# FY2025-26 tax-free thresholds (BDT). Illustrative.
TAX_FREE_THRESHOLD: Final[dict[FilerCategory, Decimal]] = {
    FilerCategory.general: Decimal("375000"),
    FilerCategory.woman_or_senior: Decimal("425000"),
    FilerCategory.person_with_disability: Decimal("475000"),
    FilerCategory.war_wounded_freedom_fighter: Decimal("500000"),
}


@dataclass(frozen=True)
class Slab:
    width: Optional[Decimal]  # None for the top slab (open-ended)
    rate: Decimal             # decimal rate, e.g. 0.10 for 10%


# Slab widths above the tax-free threshold, FY2025-26 (illustrative).
# Top band over 3,575,000 BDT is taxed at 30%.
SLABS: Final[list[Slab]] = [
    Slab(width=Decimal("300000"),  rate=Decimal("0.10")),
    Slab(width=Decimal("400000"),  rate=Decimal("0.15")),
    Slab(width=Decimal("500000"),  rate=Decimal("0.20")),
    Slab(width=Decimal("2000000"), rate=Decimal("0.25")),
    Slab(width=None,               rate=Decimal("0.30")),
]


# Minimum income tax if the taxable income exceeds the tax-free threshold.
MINIMUM_TAX: Final[Decimal] = Decimal("5000")


# VAT registration threshold (turnover). Above this, regular VAT registration
# applies. Below, the turnover-tax / enlistment track applies.
VAT_REGISTRATION_THRESHOLD: Final[Decimal] = Decimal("5000000")


# Filing window. Late submission outside this window is flagged.
FILING_WINDOW_START_MONTH: Final[int] = 7   # 1 July
FILING_WINDOW_START_DAY: Final[int] = 1
FILING_WINDOW_END_MONTH: Final[int] = 11    # 30 November
FILING_WINDOW_END_DAY: Final[int] = 30


@dataclass(frozen=True)
class TaxComputation:
    taxable_income: Decimal
    threshold: Decimal
    computed_tax: Decimal
    minimum_tax_applied: bool
    no_tax_due: bool
    category: FilerCategory


def compute_tax(
    gross_income: Decimal,
    deductions: Decimal,
    category: FilerCategory = FilerCategory.general,
) -> TaxComputation:
    """Income-tax liability from the figures and filer category.

    Returns a TaxComputation describing the result. If the taxable income is
    at or below the tax-free threshold the result is `no_tax_due=True` and
    `computed_tax=0`. Otherwise the slab schedule is applied and the result
    is the higher of the slab total and `MINIMUM_TAX`.
    """
    threshold = TAX_FREE_THRESHOLD[category]
    taxable = (gross_income - deductions)
    if taxable < 0:
        taxable = Decimal("0")

    if taxable <= threshold:
        return TaxComputation(
            taxable_income=taxable,
            threshold=threshold,
            computed_tax=Decimal("0"),
            minimum_tax_applied=False,
            no_tax_due=True,
            category=category,
        )

    over = taxable - threshold
    tax = Decimal("0")
    for slab in SLABS:
        if over <= 0:
            break
        if slab.width is None:
            tax += over * slab.rate
            over = Decimal("0")
        else:
            chunk = min(over, slab.width)
            tax += chunk * slab.rate
            over -= chunk

    minimum_applied = False
    if tax < MINIMUM_TAX:
        tax = MINIMUM_TAX
        minimum_applied = True

    return TaxComputation(
        taxable_income=taxable,
        threshold=threshold,
        computed_tax=tax.quantize(Decimal("0.01")),
        minimum_tax_applied=minimum_applied,
        no_tax_due=False,
        category=category,
    )


def is_late_filing(period: str, submitted_on: date) -> bool:
    """True if the filing falls outside the 1 July–30 November window for its
    fiscal year. A period like '2024' is taken to mean the income year ending
    30 June 2024 — the window then runs 1 July 2024 to 30 November 2024.
    Quarterly periods (e.g. '2024-Q3') are not subject to the annual window
    and never flagged as late here.
    """
    if "-Q" in period:
        return False
    try:
        year = int(period)
    except ValueError:
        return False
    window_start = date(year, FILING_WINDOW_START_MONTH, FILING_WINDOW_START_DAY)
    window_end = date(year, FILING_WINDOW_END_MONTH, FILING_WINDOW_END_DAY)
    return submitted_on > window_end or submitted_on < window_start


def needs_vat_registration(turnover: Decimal) -> bool:
    """True if turnover exceeds the VAT registration threshold."""
    return turnover > VAT_REGISTRATION_THRESHOLD
