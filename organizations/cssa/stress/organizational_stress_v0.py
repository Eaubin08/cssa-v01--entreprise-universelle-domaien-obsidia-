"""F3F — organizational stress engine V0.

Non-sovereign organizational analysis only.

This layer detects shared-resource conflicts, workload pressure, budget pressure,
deadline cascades and prioritization needs. It does NOT authorize execution.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable, Mapping


SIMULATION_STATUS = "SIMULATED_NOT_OBSERVED"


@dataclass(frozen=True)
class StressItemV0:
    item_id: str
    family: str
    deadline_days: int
    regulatory: bool
    safety: bool
    resource_demands: tuple[tuple[str, float], ...]
    team_id: str | None = None

    def priority_score(self) -> int:
        score = 0
        if self.safety:
            score += 100
        if self.regulatory:
            score += 60
        if self.deadline_days <= 0:
            score += 50
        elif self.deadline_days == 1:
            score += 35
        elif self.deadline_days <= 3:
            score += 20
        elif self.deadline_days <= 7:
            score += 10

        if self.family == "PROOF_AUDIT":
            score += 15
        elif self.family == "COMPETITIONS":
            score += 10
        return score


@dataclass(frozen=True)
class ResourceConflictV0:
    resource_id: str
    capacity: float
    demand: float
    overload: float
    item_ids: tuple[str, ...]


@dataclass(frozen=True)
class StressAssessmentV0:
    scenario_id: str
    event_date: str
    title: str
    items: tuple[StressItemV0, ...]
    conflicts: tuple[ResourceConflictV0, ...]
    priority_order: tuple[str, ...]
    unknowns: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    risk_flags: tuple[str, ...] = ()
    expected_gate_fixture: str | None = None
    simulation_status: str = SIMULATION_STATUS
    family: str = "ORGANIZATIONAL_STRESS"
    case_type: str = "organizational_stress_assessment"
    team_id: str | None = None

    @property
    def event_id(self) -> str:
        return self.scenario_id

    @property
    def source_ids(self) -> tuple[str, ...]:
        return tuple(f"sim:stress:{item.item_id}" for item in self.items)

    @property
    def expected_gate(self) -> str:
        if len(self.contradictions) >= 2:
            return "BLOCK"
        if len(self.unknowns) > 1:
            return "HOLD"
        return "ALLOW"

    @property
    def expected_provider_invoked(self) -> bool:
        return self.expected_gate == "ALLOW"

    def to_runtime_mapping(self, *, confidence: float = 0.92) -> dict[str, Any]:
        return {
            "case_ref": f"cssa-stress:{self.scenario_id}",
            "valid_at": f"{self.event_date}T12:00:00Z",
            "source_ref": f"cssa-stress-source:{self.scenario_id}",
            "unknowns": self.unknowns,
            "contradictions": self.contradictions,
            "risk_flags": self.risk_flags,
            "evidence_refs": self.source_ids,
            "provenance_refs": ("F3F_SIMULATION_ONLY",),
            "confidence": float(confidence),
            "simulation_status": self.simulation_status,
            "priority_order": self.priority_order,
            "resource_conflicts": tuple(
                {
                    "resource_id": c.resource_id,
                    "capacity": c.capacity,
                    "demand": c.demand,
                    "overload": c.overload,
                }
                for c in self.conflicts
            ),
        }


def _resource_capacity_map(resource_model: Mapping[str, Any]) -> dict[str, float]:
    return {
        str(r["id"]): float(r["capacity"])
        for r in resource_model["resources"]
    }


def _parse_items(raw_items: Iterable[Mapping[str, Any]]) -> tuple[StressItemV0, ...]:
    items = []
    for raw in raw_items:
        items.append(
            StressItemV0(
                item_id=str(raw["id"]),
                family=str(raw["family"]),
                team_id=raw.get("team_id"),
                deadline_days=int(raw.get("deadline_days", 7)),
                regulatory=bool(raw.get("regulatory", False)),
                safety=bool(raw.get("safety", False)),
                resource_demands=tuple(
                    (str(resource_id), float(amount))
                    for resource_id, amount in raw.get("resource_demands", ())
                ),
            )
        )
    return tuple(items)


def detect_resource_conflicts_v0(
    items: Iterable[StressItemV0],
    resource_model: Mapping[str, Any],
) -> tuple[ResourceConflictV0, ...]:
    capacities = _resource_capacity_map(resource_model)
    demands: dict[str, float] = defaultdict(float)
    item_ids: dict[str, list[str]] = defaultdict(list)

    for item in items:
        for resource_id, amount in item.resource_demands:
            if resource_id not in capacities:
                raise ValueError(f"UNKNOWN_RESOURCE:{resource_id}")
            if amount < 0:
                raise ValueError("RESOURCE_DEMAND_MUST_BE_NONNEGATIVE")
            demands[resource_id] += amount
            item_ids[resource_id].append(item.item_id)

    conflicts = []
    for resource_id, demand in sorted(demands.items()):
        capacity = capacities[resource_id]
        if demand > capacity:
            conflicts.append(
                ResourceConflictV0(
                    resource_id=resource_id,
                    capacity=capacity,
                    demand=round(demand, 4),
                    overload=round(demand - capacity, 4),
                    item_ids=tuple(sorted(item_ids[resource_id])),
                )
            )
    return tuple(conflicts)


def priority_order_v0(items: Iterable[StressItemV0]) -> tuple[str, ...]:
    return tuple(
        item.item_id
        for item in sorted(
            items,
            key=lambda item: (
                -item.priority_score(),
                item.deadline_days,
                item.item_id,
            ),
        )
    )


def assess_stress_scenario_v0(
    raw: Mapping[str, Any],
    resource_model: Mapping[str, Any],
) -> StressAssessmentV0:
    items = _parse_items(raw["items"])
    conflicts = detect_resource_conflicts_v0(items, resource_model)

    unknowns = list(str(v) for v in raw.get("forced_unknowns", ()))
    contradictions = list(str(v) for v in raw.get("forced_contradictions", ()))
    risk_flags = []

    for conflict in conflicts:
        risk_flags.append(f"RESOURCE_OVERLOAD:{conflict.resource_id}")
        # A hard double allocation is represented as two structural
        # contradictions so the real GuardX108 fails closed to BLOCK.
        if conflict.resource_id in {
            "VEHICLE_EQUIVALENT_POOL",
            "HOSPITALITY_SPACE",
            "MAIN_STADIUM_SLOT",
        }:
            contradictions.extend(
                (
                    f"CAPACITY_EXCEEDED:{conflict.resource_id}",
                    f"DOUBLE_ALLOCATION_RISK:{conflict.resource_id}",
                )
            )
        elif conflict.resource_id == "TRAVEL_MONTHLY_ENVELOPE":
            risk_flags.append("SIMULATED_BUDGET_PRESSURE")
        else:
            risk_flags.append("WORKLOAD_CAPACITY_PRESSURE")

    assessment = StressAssessmentV0(
        scenario_id=str(raw["id"]),
        event_date=str(raw["date"]),
        title=str(raw["title"]),
        items=items,
        conflicts=conflicts,
        priority_order=priority_order_v0(items),
        unknowns=tuple(dict.fromkeys(unknowns)),
        contradictions=tuple(dict.fromkeys(contradictions)),
        risk_flags=tuple(dict.fromkeys(risk_flags)),
        expected_gate_fixture=raw.get("expected_gate"),
    )

    if assessment.expected_gate_fixture and (
        assessment.expected_gate != assessment.expected_gate_fixture
    ):
        raise ValueError(
            f"SCENARIO_GATE_MISMATCH:{assessment.scenario_id}:"
            f"{assessment.expected_gate}!={assessment.expected_gate_fixture}"
        )

    expected_first = raw.get("expected_priority_first")
    if expected_first and assessment.priority_order[0] != expected_first:
        raise ValueError(
            f"PRIORITY_MISMATCH:{assessment.scenario_id}:"
            f"{assessment.priority_order[0]}!={expected_first}"
        )

    return assessment


def assess_catalog_v0(
    catalog: Mapping[str, Any],
    resource_model: Mapping[str, Any],
) -> tuple[StressAssessmentV0, ...]:
    return tuple(
        assess_stress_scenario_v0(raw, resource_model)
        for raw in catalog["scenarios"]
    )


def season_workload_pressure_v0(
    events: Iterable[Any],
    resource_model: Mapping[str, Any],
) -> dict[str, Any]:
    """Scan all season events against simulated daily role capacity.

    This is a capacity pressure observation, not an operational decision.
    """
    capacities = _resource_capacity_map(resource_model)
    workload_map = resource_model["family_workload_map"]

    usage: dict[tuple[str, str], float] = defaultdict(float)
    contributing: dict[tuple[str, str], int] = defaultdict(int)
    event_count = 0

    for event in events:
        event_count += 1
        for resource_id, amount in workload_map.get(event.family, ()):
            key = (event.event_date, str(resource_id))
            usage[key] += float(amount)
            contributing[key] += 1

    pressure = []
    for (event_date, resource_id), demand in sorted(usage.items()):
        capacity = capacities[resource_id]
        if demand > capacity:
            pressure.append(
                {
                    "date": event_date,
                    "resource_id": resource_id,
                    "capacity": capacity,
                    "demand": round(demand, 4),
                    "overload": round(demand - capacity, 4),
                    "contributing_events": contributing[(event_date, resource_id)],
                }
            )

    return {
        "simulation_status": SIMULATION_STATUS,
        "event_count": event_count,
        "resource_day_observations": len(usage),
        "pressure_points": pressure,
        "pressure_point_count": len(pressure),
        "max_overload": max((p["overload"] for p in pressure), default=0.0),
    }


def catalog_summary_v0(
    assessments: Iterable[StressAssessmentV0],
) -> dict[str, Any]:
    rows = tuple(assessments)
    gate_counts: dict[str, int] = defaultdict(int)
    conflict_count = 0
    for row in rows:
        gate_counts[row.expected_gate] += 1
        conflict_count += len(row.conflicts)

    return {
        "simulation_status": SIMULATION_STATUS,
        "scenario_count": len(rows),
        "gate_counts": dict(sorted(gate_counts.items())),
        "resource_conflict_count": conflict_count,
        "priority_orders_generated": len(rows),
    }
