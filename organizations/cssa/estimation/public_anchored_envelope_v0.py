"""F3G-C — public-anchored estimated operating envelope V0.

Public facts remain facts. Unknown private values remain unknown.
Approximate capacity is represented only through replaceable ESTIMATED profiles.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping

from organizations.cssa.calibration import override_resource_capacities_v0
from organizations.cssa.stress import (
    assess_catalog_v0,
    season_workload_pressure_v0,
)


STATUS = "ESTIMATED_PUBLIC_ANCHORED"


@dataclass(frozen=True)
class EnvelopeProfileResultV0:
    profile_id: str
    truth_class: str
    gate_counts: tuple[tuple[str, int], ...]
    resource_conflict_count: int
    season_pressure_point_count: int
    season_max_overload: float
    blind_spot_pressure: tuple[tuple[str, bool], ...]
    status: str = STATUS

    def __post_init__(self) -> None:
        if self.truth_class != "ESTIMATED":
            raise ValueError("OPERATING_PROFILE_MUST_REMAIN_ESTIMATED")
        if self.status != STATUS:
            raise ValueError("PUBLIC_ANCHORED_STATUS_REQUIRED")


def validate_envelope_v0(
    envelope: Mapping[str, Any],
    base_resources: Mapping[str, Any],
) -> None:
    if envelope.get("status") != STATUS:
        raise ValueError("INVALID_PUBLIC_ANCHORED_ENVELOPE_STATUS")

    base_ids = {str(row["id"]) for row in base_resources["resources"]}
    for profile_id, profile in envelope["profiles"].items():
        if profile.get("truth_class") != "ESTIMATED":
            raise ValueError(f"PROFILE_NOT_ESTIMATED:{profile_id}")
        capacities = profile["capacities"]
        if set(capacities) != base_ids:
            missing = sorted(base_ids - set(capacities))
            extra = sorted(set(capacities) - base_ids)
            raise ValueError(
                f"PROFILE_RESOURCE_SET_MISMATCH:{profile_id}:"
                f"missing={missing}:extra={extra}"
            )
        for resource_id, raw in capacities.items():
            value = float(raw)
            if value < 0:
                raise ValueError(
                    f"NEGATIVE_ESTIMATED_CAPACITY:{profile_id}:{resource_id}"
                )


def build_profile_resources_v0(
    envelope: Mapping[str, Any],
    base_resources: Mapping[str, Any],
    profile_id: str,
) -> dict[str, Any]:
    validate_envelope_v0(envelope, base_resources)
    profile = envelope["profiles"].get(profile_id)
    if profile is None:
        raise ValueError(f"UNKNOWN_OPERATING_PROFILE:{profile_id}")

    model = override_resource_capacities_v0(
        base_resources,
        profile["capacities"],
    )
    model["status"] = STATUS
    model["profile_id"] = profile_id
    model["truth_class"] = "ESTIMATED"
    return model


def _blind_spot_pressure_v0(
    envelope: Mapping[str, Any],
    resources: Mapping[str, Any],
) -> dict[str, bool]:
    capacities = {
        str(row["id"]): float(row["capacity"])
        for row in resources["resources"]
    }
    results = {}
    for case in envelope["new_public_anchored_stress_cases"]:
        demand_by_resource: dict[str, float] = {}
        for resource_id, amount in case["items"]:
            resource_id = str(resource_id)
            demand_by_resource[resource_id] = (
                demand_by_resource.get(resource_id, 0.0)
                + float(amount)
            )
        overloaded = any(
            demand > capacities[resource_id]
            for resource_id, demand in demand_by_resource.items()
        )
        results[str(case["id"])] = overloaded
    return results


def evaluate_operating_profile_v0(
    envelope: Mapping[str, Any],
    base_resources: Mapping[str, Any],
    stress_catalog: Mapping[str, Any],
    season_events: tuple[Any, ...],
    profile_id: str,
) -> EnvelopeProfileResultV0:
    resources = build_profile_resources_v0(
        envelope,
        base_resources,
        profile_id,
    )
    assessments = assess_catalog_v0(
        _catalog_without_fixture_assertions(stress_catalog),
        resources,
    )
    gate_counts: dict[str, int] = {}
    resource_conflict_count = 0
    for assessment in assessments:
        gate_counts[assessment.expected_gate] = (
            gate_counts.get(assessment.expected_gate, 0) + 1
        )
        resource_conflict_count += len(assessment.conflicts)

    pressure = season_workload_pressure_v0(
        season_events,
        resources,
    )
    blind = _blind_spot_pressure_v0(
        envelope,
        resources,
    )

    return EnvelopeProfileResultV0(
        profile_id=profile_id,
        truth_class="ESTIMATED",
        gate_counts=tuple(sorted(gate_counts.items())),
        resource_conflict_count=resource_conflict_count,
        season_pressure_point_count=pressure["pressure_point_count"],
        season_max_overload=float(pressure["max_overload"]),
        blind_spot_pressure=tuple(sorted(blind.items())),
    )


def _catalog_without_fixture_assertions(
    catalog: Mapping[str, Any],
) -> dict[str, Any]:
    out = deepcopy(catalog)
    for row in out["scenarios"]:
        row.pop("expected_gate", None)
        row.pop("expected_priority_first", None)
    return out


def evaluate_all_profiles_v0(
    envelope: Mapping[str, Any],
    base_resources: Mapping[str, Any],
    stress_catalog: Mapping[str, Any],
    season_events: tuple[Any, ...],
) -> tuple[EnvelopeProfileResultV0, ...]:
    return tuple(
        evaluate_operating_profile_v0(
            envelope,
            base_resources,
            stress_catalog,
            season_events,
            profile_id,
        )
        for profile_id in envelope["profiles"]
    )


def robust_vs_fragile_v0(
    envelope: Mapping[str, Any],
    base_resources: Mapping[str, Any],
    stress_catalog: Mapping[str, Any],
    season_events: tuple[Any, ...],
) -> dict[str, Any]:
    results = evaluate_all_profiles_v0(
        envelope,
        base_resources,
        stress_catalog,
        season_events,
    )

    gates_by_profile = {
        row.profile_id: dict(row.gate_counts)
        for row in results
    }
    pressure_by_profile = {
        row.profile_id: row.season_pressure_point_count
        for row in results
    }
    blind_by_profile = {
        row.profile_id: dict(row.blind_spot_pressure)
        for row in results
    }

    return {
        "status": STATUS,
        "truth_class": "ESTIMATED",
        "profiles": [
            {
                "profile_id": row.profile_id,
                "gate_counts": dict(row.gate_counts),
                "resource_conflict_count": row.resource_conflict_count,
                "season_pressure_point_count": row.season_pressure_point_count,
                "season_max_overload": row.season_max_overload,
                "blind_spot_pressure": dict(row.blind_spot_pressure),
            }
            for row in results
        ],
        "gate_counts_by_profile": gates_by_profile,
        "pressure_points_by_profile": pressure_by_profile,
        "blind_spot_pressure_by_profile": blind_by_profile,
        "assumptions_kept_unknown": list(
            envelope["assumptions_kept_unknown"]
        ),
        "public_anchor_count": len(envelope["anchors"]),
        "replaceable_parameter_count": len(
            next(iter(envelope["profiles"].values()))["capacities"]
        ),
        "external_action": False,
        "authority": "KX108_ONLY",
    }
