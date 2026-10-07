"""F3D — season-scale travel simulation helpers.

All monetary outputs are scenario estimates, never CSSA accounting facts.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TravelCostScenarioV0:
    name: str
    team_route_km: float
    vehicle_equivalents: float
    eur_per_vehicle_km: float

    def __post_init__(self) -> None:
        if self.team_route_km < 0:
            raise ValueError("team_route_km must be >= 0")
        if self.vehicle_equivalents <= 0:
            raise ValueError("vehicle_equivalents must be > 0")
        if self.eur_per_vehicle_km < 0:
            raise ValueError("eur_per_vehicle_km must be >= 0")

    @property
    def vehicle_km(self) -> float:
        return self.team_route_km * self.vehicle_equivalents

    @property
    def estimated_vehicle_cost_eur(self) -> float:
        return self.vehicle_km * self.eur_per_vehicle_km


LOW = TravelCostScenarioV0(
    name="LOW_SIMULATION",
    team_route_km=22_000,
    vehicle_equivalents=2.0,
    eur_per_vehicle_km=0.35,
)

BASE = TravelCostScenarioV0(
    name="BASE_SIMULATION",
    team_route_km=(22_000 + 36_250) / 2,
    vehicle_equivalents=2.5,
    eur_per_vehicle_km=0.45,
)

HIGH = TravelCostScenarioV0(
    name="HIGH_SIMULATION",
    team_route_km=36_250,
    vehicle_equivalents=3.0,
    eur_per_vehicle_km=0.60,
)


def season_cost_envelope_v0() -> dict[str, float]:
    """Return explicit simulation envelope, not an observed CSSA budget."""
    return {
        "low_eur": round(LOW.estimated_vehicle_cost_eur, 2),
        "base_eur": round(BASE.estimated_vehicle_cost_eur, 2),
        "high_eur": round(HIGH.estimated_vehicle_cost_eur, 2),
    }


def fuel_only_reference_v0(
    team_route_km: float,
    *,
    vehicle_equivalents: float = 2.5,
    eur_per_vehicle_km: float = 0.11,
) -> float:
    """Fuel-only reference parameter for simulations.

    This excludes depreciation, maintenance, reimbursement policy, tolls,
    parking, hired coach, hotels and meals.
    """
    if team_route_km < 0 or vehicle_equivalents <= 0 or eur_per_vehicle_km < 0:
        raise ValueError("invalid travel reference parameter")
    return round(team_route_km * vehicle_equivalents * eur_per_vehicle_km, 2)
