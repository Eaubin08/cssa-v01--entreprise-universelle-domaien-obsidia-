"""F3D — CSSA public-price simulation helpers.

These helpers intentionally require explicit quantities/product mix.
They never derive private club revenue from public audience/partner counts.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


LICENSE_PACK_PRICES_EUR = {
    "U6_U9": 180.0,
    "U10_U18": 240.0,
    "U20_SENIORS": 300.0,
}

SUBSCRIPTION_FULL_PRICES_EUR = {
    "HONNEUR": 55.0,
    "SALON_DES_LEGENDES": 195.0,
    "CLUB_1919": 550.0,
}

SUBSCRIPTION_REDUCED_PRICES_EUR = {
    "HONNEUR": 40.0,
    "SALON_DES_LEGENDES": 145.0,
    "CLUB_1919": 400.0,
}


@dataclass(frozen=True)
class LicencePackScenarioV0:
    u6_u9: int
    u10_u18: int
    u20_seniors: int
    family_discount_events: int = 0
    female_discount_events: int = 0
    pass_sport_events: int = 0

    def __post_init__(self) -> None:
        values = (
            self.u6_u9,
            self.u10_u18,
            self.u20_seniors,
            self.family_discount_events,
            self.female_discount_events,
            self.pass_sport_events,
        )
        if any(v < 0 for v in values):
            raise ValueError("scenario quantities must be >= 0")

    @property
    def licence_holders(self) -> int:
        return self.u6_u9 + self.u10_u18 + self.u20_seniors

    @property
    def gross_pack_value_eur(self) -> float:
        return round(
            self.u6_u9 * LICENSE_PACK_PRICES_EUR["U6_U9"]
            + self.u10_u18 * LICENSE_PACK_PRICES_EUR["U10_U18"]
            + self.u20_seniors * LICENSE_PACK_PRICES_EUR["U20_SENIORS"],
            2,
        )

    @property
    def modeled_discount_value_eur(self) -> float:
        """Raw scenario discount events, not a CSSA accounting claim.

        Actual eligibility/stacking must be validated case-by-case.
        """
        return round(
            self.family_discount_events * 25.0
            + self.female_discount_events * 25.0
            + self.pass_sport_events * 70.0,
            2,
        )


def subscription_gross_from_explicit_mix_v0(
    *,
    full: Mapping[str, int],
    reduced: Mapping[str, int],
) -> float:
    """Compute only when product mix is explicitly supplied."""
    total = 0.0
    for product, price in SUBSCRIPTION_FULL_PRICES_EUR.items():
        qty = int(full.get(product, 0))
        if qty < 0:
            raise ValueError("subscription quantity must be >= 0")
        total += qty * price

    for product, price in SUBSCRIPTION_REDUCED_PRICES_EUR.items():
        qty = int(reduced.get(product, 0))
        if qty < 0:
            raise ValueError("subscription quantity must be >= 0")
        total += qty * price

    unknown_products = (set(full) | set(reduced)) - set(
        SUBSCRIPTION_FULL_PRICES_EUR
    )
    if unknown_products:
        raise ValueError(f"unknown subscription product(s): {sorted(unknown_products)}")

    return round(total, 2)


def revenue_from_subscriber_count_only_v0(count: int) -> float:
    """Forbidden inference: public subscriber count has no known product mix."""
    raise ValueError(
        "SUBSCRIBER_COUNT_ONLY_CANNOT_ESTIMATE_REVENUE:"
        "partners/product_mix/discount_mix_unknown"
    )


def revenue_from_partner_count_only_v0(count: int) -> float:
    """Forbidden inference: +50 partners does not expose contract values."""
    raise ValueError(
        "PARTNER_COUNT_ONLY_CANNOT_ESTIMATE_REVENUE:"
        "contract_tiers_and_commitments_unknown"
    )
