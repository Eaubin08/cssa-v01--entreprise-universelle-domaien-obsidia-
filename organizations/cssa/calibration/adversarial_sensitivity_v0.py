"""F3G-A — adversarial sensitivity and calibration-prep engine V0.

Purpose:
- attack synthetic organizational assumptions;
- identify which parameters actually change governance outcomes;
- separate resource sensitivity from missing-authority/data sensitivity;
- produce a ranked list of field facts worth calibrating later.

This module has no execution authority.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from itertools import product
from math import isfinite
from typing import Any, Iterable, Mapping

from organizations.cssa.stress import (
    assess_stress_scenario_v0,
    season_workload_pressure_v0,
)


SIMULATION_STATUS = "SIMULATED_NOT_OBSERVED"


@dataclass(frozen=True)
class SensitivityProfileResultV0:
    profile_id: str
    resource_overrides: tuple[tuple[str, float], ...]
    resolved_assumptions: tuple[str, ...]
    scenario_gates: tuple[tuple[str, str], ...]
    gate_counts: tuple[tuple[str, int], ...]
    resource_conflict_count: int
    priority_fingerprint: tuple[tuple[str, str], ...]
    simulation_status: str = SIMULATION_STATUS

    def __post_init__(self) -> None:
        if self.simulation_status != SIMULATION_STATUS:
            raise ValueError("sensitivity profile must remain simulated")

    def gate_for(self, scenario_id: str) -> str:
        return dict(self.scenario_gates)[scenario_id]


def _resource_ids(resource_model: Mapping[str, Any]) -> set[str]:
    return {str(row["id"]) for row in resource_model["resources"]}


def override_resource_capacities_v0(
    resource_model: Mapping[str, Any],
    overrides: Mapping[str, float],
) -> dict[str, Any]:
    """Return a validated copy with capacity overrides.

    Zero is valid and intentionally adversarial.
    Negative, non-finite and unknown resources fail closed.
    """
    known = _resource_ids(resource_model)
    unknown = set(overrides) - known
    if unknown:
        raise ValueError(f"UNKNOWN_RESOURCE_OVERRIDE:{sorted(unknown)}")

    clean: dict[str, float] = {}
    for resource_id, raw_value in overrides.items():
        value = float(raw_value)
        if not isfinite(value):
            raise ValueError(f"NON_FINITE_RESOURCE_CAPACITY:{resource_id}")
        if value < 0:
            raise ValueError(f"NEGATIVE_RESOURCE_CAPACITY:{resource_id}")
        clean[resource_id] = value

    mutated = deepcopy(resource_model)
    for row in mutated["resources"]:
        resource_id = str(row["id"])
        if resource_id in clean:
            row["capacity"] = clean[resource_id]
    mutated["status"] = SIMULATION_STATUS
    return mutated


def _assumption_index(space: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    rows = {
        str(row["id"]): row
        for row in space["assumption_dimensions"]
    }
    if len(rows) != len(space["assumption_dimensions"]):
        raise ValueError("DUPLICATE_ASSUMPTION_ID")
    return rows


def apply_resolved_assumptions_v0(
    raw_scenario: Mapping[str, Any],
    space: Mapping[str, Any],
    resolved_assumptions: Iterable[str],
) -> dict[str, Any]:
    """Remove only the explicit unknown/contradiction tokens tied to a resolved fact."""
    assumption_index = _assumption_index(space)
    resolved = tuple(sorted(set(str(v) for v in resolved_assumptions)))
    unknown_assumptions = set(resolved) - set(assumption_index)
    if unknown_assumptions:
        raise ValueError(
            f"UNKNOWN_RESOLVED_ASSUMPTION:{sorted(unknown_assumptions)}"
        )

    out = deepcopy(raw_scenario)

    # Fixture assertions belong to F3F baseline and are intentionally removed
    # during sensitivity sweeps because the point is to let verdicts change.
    out.pop("expected_gate", None)
    out.pop("expected_priority_first", None)

    unknowns = list(str(v) for v in out.get("forced_unknowns", ()))
    contradictions = list(str(v) for v in out.get("forced_contradictions", ()))

    remove_unknowns: set[str] = set()
    remove_contradictions: set[str] = set()
    for assumption_id in resolved:
        row = assumption_index[assumption_id]
        remove_unknowns.update(
            str(v) for v in row.get("removes_unknowns", ())
        )
        remove_contradictions.update(
            str(v) for v in row.get("removes_contradictions", ())
        )

    out["forced_unknowns"] = [
        value for value in unknowns if value not in remove_unknowns
    ]
    out["forced_contradictions"] = [
        value
        for value in contradictions
        if value not in remove_contradictions
    ]
    return out


def evaluate_profile_v0(
    catalog: Mapping[str, Any],
    base_resources: Mapping[str, Any],
    space: Mapping[str, Any],
    *,
    profile_id: str,
    resource_overrides: Mapping[str, float] | None = None,
    resolved_assumptions: Iterable[str] = (),
) -> SensitivityProfileResultV0:
    resources = override_resource_capacities_v0(
        base_resources,
        resource_overrides or {},
    )
    resolved = tuple(sorted(set(str(v) for v in resolved_assumptions)))

    gates: list[tuple[str, str]] = []
    priorities: list[tuple[str, str]] = []
    conflict_count = 0
    gate_counts: dict[str, int] = {}

    for raw in catalog["scenarios"]:
        mutated = apply_resolved_assumptions_v0(
            raw,
            space,
            resolved,
        )
        assessment = assess_stress_scenario_v0(mutated, resources)
        gates.append((assessment.scenario_id, assessment.expected_gate))
        if assessment.priority_order:
            priorities.append(
                (assessment.scenario_id, assessment.priority_order[0])
            )
        conflict_count += len(assessment.conflicts)
        gate_counts[assessment.expected_gate] = (
            gate_counts.get(assessment.expected_gate, 0) + 1
        )

    return SensitivityProfileResultV0(
        profile_id=profile_id,
        resource_overrides=tuple(
            sorted(
                (str(k), float(v))
                for k, v in (resource_overrides or {}).items()
            )
        ),
        resolved_assumptions=resolved,
        scenario_gates=tuple(sorted(gates)),
        gate_counts=tuple(sorted(gate_counts.items())),
        resource_conflict_count=conflict_count,
        priority_fingerprint=tuple(sorted(priorities)),
    )


def named_profile_results_v0(
    catalog: Mapping[str, Any],
    resources: Mapping[str, Any],
    space: Mapping[str, Any],
) -> tuple[SensitivityProfileResultV0, ...]:
    return tuple(
        evaluate_profile_v0(
            catalog,
            resources,
            space,
            profile_id=str(profile["id"]),
            resource_overrides=profile["overrides"],
        )
        for profile in space["named_operating_profiles"]
    )


def one_at_a_time_resource_sensitivity_v0(
    catalog: Mapping[str, Any],
    resources: Mapping[str, Any],
    space: Mapping[str, Any],
) -> dict[str, Any]:
    baseline = evaluate_profile_v0(
        catalog,
        resources,
        space,
        profile_id="BASELINE",
    )
    baseline_gates = dict(baseline.scenario_gates)

    rows: list[dict[str, Any]] = []
    for dimension in space["resource_dimensions"]:
        resource_id = str(dimension["id"])
        changed_scenarios: set[str] = set()
        gate_sets: dict[str, set[str]] = {
            scenario_id: {gate}
            for scenario_id, gate in baseline.scenario_gates
        }

        for value in dimension["values"]:
            result = evaluate_profile_v0(
                catalog,
                resources,
                space,
                profile_id=f"{resource_id}={value}",
                resource_overrides={resource_id: float(value)},
            )
            for scenario_id, gate in result.scenario_gates:
                gate_sets.setdefault(scenario_id, set()).add(gate)
                if gate != baseline_gates[scenario_id]:
                    changed_scenarios.add(scenario_id)

        rows.append(
            {
                "parameter_id": resource_id,
                "levels": list(dimension["values"]),
                "scenario_gate_flip_count": len(changed_scenarios),
                "changed_scenarios": sorted(changed_scenarios),
                "scenario_gate_sets": {
                    scenario_id: sorted(gates)
                    for scenario_id, gates in sorted(gate_sets.items())
                    if len(gates) > 1
                },
                "field_question": dimension["field_question"],
            }
        )

    rows.sort(
        key=lambda row: (
            -row["scenario_gate_flip_count"],
            row["parameter_id"],
        )
    )
    return {
        "simulation_status": SIMULATION_STATUS,
        "baseline_gate_counts": dict(baseline.gate_counts),
        "parameters": rows,
    }


def one_at_a_time_assumption_sensitivity_v0(
    catalog: Mapping[str, Any],
    resources: Mapping[str, Any],
    space: Mapping[str, Any],
) -> dict[str, Any]:
    baseline = evaluate_profile_v0(
        catalog,
        resources,
        space,
        profile_id="BASELINE",
    )
    baseline_gates = dict(baseline.scenario_gates)
    baseline_priorities = dict(baseline.priority_fingerprint)

    rows: list[dict[str, Any]] = []
    for dimension in space["assumption_dimensions"]:
        assumption_id = str(dimension["id"])
        result = evaluate_profile_v0(
            catalog,
            resources,
            space,
            profile_id=f"ASSUMPTION:{assumption_id}",
            resolved_assumptions=(assumption_id,),
        )
        changed_gates = [
            scenario_id
            for scenario_id, gate in result.scenario_gates
            if gate != baseline_gates[scenario_id]
        ]
        changed_priorities = [
            scenario_id
            for scenario_id, first_item in result.priority_fingerprint
            if first_item != baseline_priorities.get(scenario_id)
        ]
        rows.append(
            {
                "assumption_id": assumption_id,
                "scenario_gate_flip_count": len(changed_gates),
                "changed_scenarios": sorted(changed_gates),
                "priority_change_count": len(changed_priorities),
                "priority_changed_scenarios": sorted(changed_priorities),
                "field_question": dimension["field_question"],
            }
        )

    rows.sort(
        key=lambda row: (
            -row["scenario_gate_flip_count"],
            -row["priority_change_count"],
            row["assumption_id"],
        )
    )
    return {
        "simulation_status": SIMULATION_STATUS,
        "baseline_gate_counts": dict(baseline.gate_counts),
        "assumptions": rows,
    }


def exhaustive_resource_grid_v0(
    catalog: Mapping[str, Any],
    resources: Mapping[str, Any],
    space: Mapping[str, Any],
) -> dict[str, Any]:
    """Exhaustively attack the six configured resource dimensions."""
    dimensions = list(space["resource_dimensions"])
    ids = [str(row["id"]) for row in dimensions]
    values = [tuple(row["values"]) for row in dimensions]

    scenario_gate_counts: dict[str, dict[str, int]] = {
        str(raw["id"]): {}
        for raw in catalog["scenarios"]
    }
    profiles_with_block = 0
    profiles_with_hold = 0
    profiles_all_allow = 0
    profile_count = 0

    for combo in product(*values):
        overrides = {
            resource_id: float(value)
            for resource_id, value in zip(ids, combo)
        }
        result = evaluate_profile_v0(
            catalog,
            resources,
            space,
            profile_id=f"GRID:{profile_count}",
            resource_overrides=overrides,
        )
        profile_count += 1
        gates = dict(result.scenario_gates)
        if "BLOCK" in gates.values():
            profiles_with_block += 1
        if "HOLD" in gates.values():
            profiles_with_hold += 1
        if set(gates.values()) == {"ALLOW"}:
            profiles_all_allow += 1

        for scenario_id, gate in result.scenario_gates:
            bucket = scenario_gate_counts[scenario_id]
            bucket[gate] = bucket.get(gate, 0) + 1

    return {
        "simulation_status": SIMULATION_STATUS,
        "profile_count": profile_count,
        "dimension_count": len(ids),
        "dimensions": {
            resource_id: list(levels)
            for resource_id, levels in zip(ids, values)
        },
        "profiles_with_block": profiles_with_block,
        "profiles_with_hold": profiles_with_hold,
        "profiles_all_allow": profiles_all_allow,
        "scenario_gate_counts": {
            scenario_id: dict(sorted(counts.items()))
            for scenario_id, counts in sorted(scenario_gate_counts.items())
        },
        "resource_fragile_scenarios": sorted(
            scenario_id
            for scenario_id, counts in scenario_gate_counts.items()
            if len(counts) > 1
        ),
    }


def exhaustive_assumption_grid_v0(
    catalog: Mapping[str, Any],
    resources: Mapping[str, Any],
    space: Mapping[str, Any],
) -> dict[str, Any]:
    assumptions = [
        str(row["id"])
        for row in space["assumption_dimensions"]
    ]
    scenario_gate_sets: dict[str, set[str]] = {
        str(raw["id"]): set()
        for raw in catalog["scenarios"]
    }
    all_allow_count = 0
    profile_count = 0

    for bits in product((False, True), repeat=len(assumptions)):
        resolved = tuple(
            assumption_id
            for assumption_id, enabled in zip(assumptions, bits)
            if enabled
        )
        result = evaluate_profile_v0(
            catalog,
            resources,
            space,
            profile_id=f"ASSUMPTION_GRID:{profile_count}",
            resolved_assumptions=resolved,
        )
        profile_count += 1
        gates = dict(result.scenario_gates)
        if set(gates.values()) == {"ALLOW"}:
            all_allow_count += 1
        for scenario_id, gate in result.scenario_gates:
            scenario_gate_sets[scenario_id].add(gate)

    return {
        "simulation_status": SIMULATION_STATUS,
        "profile_count": profile_count,
        "assumption_count": len(assumptions),
        "all_allow_profile_count": all_allow_count,
        "assumption_sensitive_scenarios": sorted(
            scenario_id
            for scenario_id, gates in scenario_gate_sets.items()
            if len(gates) > 1
        ),
        "scenario_gate_sets": {
            scenario_id: sorted(gates)
            for scenario_id, gates in sorted(scenario_gate_sets.items())
        },
    }


def pressure_sensitivity_v0(
    season_events: Iterable[Any],
    resources: Mapping[str, Any],
    space: Mapping[str, Any],
) -> dict[str, Any]:
    """One-at-a-time pressure scan across ROLE_CAPACITY resources."""
    base_capacities = {
        str(row["id"]): float(row["capacity"])
        for row in resources["resources"]
        if row["kind"] == "ROLE_CAPACITY"
    }
    multipliers = [float(v) for v in space["pressure_multipliers"]]

    rows: list[dict[str, Any]] = []
    events = tuple(season_events)
    for resource_id, base_capacity in sorted(base_capacities.items()):
        observations = []
        for multiplier in multipliers:
            model = override_resource_capacities_v0(
                resources,
                {resource_id: base_capacity * multiplier},
            )
            result = season_workload_pressure_v0(events, model)
            observations.append(
                {
                    "multiplier": multiplier,
                    "capacity": base_capacity * multiplier,
                    "pressure_point_count": result["pressure_point_count"],
                    "max_overload": result["max_overload"],
                }
            )

        counts = [row["pressure_point_count"] for row in observations]
        rows.append(
            {
                "resource_id": resource_id,
                "base_capacity": base_capacity,
                "pressure_point_min": min(counts),
                "pressure_point_max": max(counts),
                "pressure_point_range": max(counts) - min(counts),
                "observations": observations,
            }
        )

    rows.sort(
        key=lambda row: (
            -row["pressure_point_range"],
            row["resource_id"],
        )
    )
    return {
        "simulation_status": SIMULATION_STATUS,
        "multipliers": multipliers,
        "resources": rows,
    }


def build_calibration_priorities_v0(
    resource_sensitivity: Mapping[str, Any],
    assumption_sensitivity: Mapping[str, Any],
    pressure_sensitivity: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Rank what real-world facts are worth asking for first."""
    pressure_by_resource = {
        row["resource_id"]: row
        for row in pressure_sensitivity["resources"]
    }

    priorities = []
    for row in resource_sensitivity["parameters"]:
        pressure = pressure_by_resource.get(row["parameter_id"], {})
        priorities.append(
            {
                "calibration_id": row["parameter_id"],
                "kind": "RESOURCE",
                "scenario_gate_flip_count": row["scenario_gate_flip_count"],
                "pressure_point_range": int(
                    pressure.get("pressure_point_range", 0)
                ),
                "field_question": row["field_question"],
            }
        )

    for row in assumption_sensitivity["assumptions"]:
        priorities.append(
            {
                "calibration_id": row["assumption_id"],
                "kind": "ASSUMPTION",
                "scenario_gate_flip_count": row["scenario_gate_flip_count"],
                "pressure_point_range": 0,
                "field_question": row["field_question"],
            }
        )

    priorities.sort(
        key=lambda row: (
            -row["scenario_gate_flip_count"],
            -row["pressure_point_range"],
            row["calibration_id"],
        )
    )
    return priorities



def resource_coverage_audit_v0(
    catalog: Mapping[str, Any],
    resources: Mapping[str, Any],
) -> dict[str, Any]:
    """Find modeled resources that the current simulator never exercises."""
    all_resources = {
        str(row["id"])
        for row in resources["resources"]
    }
    workload_refs = {
        str(resource_id)
        for demands in resources["family_workload_map"].values()
        for resource_id, _amount in demands
    }
    scenario_refs = {
        str(resource_id)
        for scenario in catalog["scenarios"]
        for item in scenario["items"]
        for resource_id, _amount in item.get("resource_demands", ())
    }
    exercised = workload_refs | scenario_refs
    unknown_refs = exercised - all_resources
    if unknown_refs:
        raise ValueError(
            f"RESOURCE_REFERENCE_WITHOUT_DEFINITION:{sorted(unknown_refs)}"
        )

    return {
        "simulation_status": SIMULATION_STATUS,
        "resource_count": len(all_resources),
        "workload_referenced_count": len(workload_refs),
        "scenario_referenced_count": len(scenario_refs),
        "exercised_resource_count": len(exercised),
        "unexercised_resources": sorted(all_resources - exercised),
    }

def adversarial_summary_v0(
    catalog: Mapping[str, Any],
    resources: Mapping[str, Any],
    space: Mapping[str, Any],
    season_events: Iterable[Any],
) -> dict[str, Any]:
    resource_sensitivity = one_at_a_time_resource_sensitivity_v0(
        catalog, resources, space
    )
    assumption_sensitivity = one_at_a_time_assumption_sensitivity_v0(
        catalog, resources, space
    )
    pressure = pressure_sensitivity_v0(
        season_events, resources, space
    )
    resource_grid = exhaustive_resource_grid_v0(
        catalog, resources, space
    )
    assumption_grid = exhaustive_assumption_grid_v0(
        catalog, resources, space
    )
    named_profiles = named_profile_results_v0(
        catalog, resources, space
    )
    coverage = resource_coverage_audit_v0(
        catalog, resources
    )

    return {
        "simulation_status": SIMULATION_STATUS,
        "named_profiles": [
            {
                "profile_id": row.profile_id,
                "gate_counts": dict(row.gate_counts),
                "resource_conflict_count": row.resource_conflict_count,
            }
            for row in named_profiles
        ],
        "resource_sensitivity": resource_sensitivity,
        "assumption_sensitivity": assumption_sensitivity,
        "pressure_sensitivity": pressure,
        "resource_grid": resource_grid,
        "assumption_grid": assumption_grid,
        "resource_coverage": coverage,
        "calibration_priorities": build_calibration_priorities_v0(
            resource_sensitivity,
            assumption_sensitivity,
            pressure,
        ),
        "authority": "KX108_ONLY",
        "external_action": False,
    }
