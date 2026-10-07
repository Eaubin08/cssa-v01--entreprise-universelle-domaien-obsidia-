import json
from pathlib import Path

import pytest

from organizations.cssa.estimation import (
    build_profile_resources_v0,
    evaluate_all_profiles_v0,
    robust_vs_fragile_v0,
    validate_envelope_v0,
)
from organizations.cssa.season_simulation import build_full_season_corpus_v0


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "organizations" / "cssa" / "season" / "public_model_v0.json"
RESOURCES = ROOT / "organizations" / "cssa" / "stress" / "resources_v0.json"
CATALOG = ROOT / "organizations" / "cssa" / "stress" / "stress_scenarios_v0.json"
ENVELOPE = (
    ROOT
    / "organizations"
    / "cssa"
    / "estimation"
    / "public_anchored_envelope_v0.json"
)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def corpus():
    return build_full_season_corpus_v0(load(MODEL))


def test_envelope_is_explicitly_estimated_not_real_cssa_capacity():
    envelope = load(ENVELOPE)
    resources = load(RESOURCES)
    validate_envelope_v0(envelope, resources)

    assert envelope["status"] == "ESTIMATED_PUBLIC_ANCHORED"
    assert envelope["capacity_semantics"]["unit"] == "SIMULATION_CAPACITY_UNIT"
    assert "not number of employees" in envelope["capacity_semantics"]["note"]
    assert set(envelope["profiles"]) == {
        "LOW_CONSTRAINED",
        "CENTRAL_WORKING",
        "HIGH_CAPACITY",
    }
    assert all(
        row["truth_class"] == "ESTIMATED"
        for row in envelope["profiles"].values()
    )


def test_each_profile_replaces_exactly_the_same_15_resource_parameters():
    envelope = load(ENVELOPE)
    resources = load(RESOURCES)
    resource_ids = {row["id"] for row in resources["resources"]}

    assert len(resource_ids) == 15
    for profile in envelope["profiles"].values():
        assert set(profile["capacities"]) == resource_ids


def test_unknown_private_values_are_preserved_as_unknown():
    envelope = load(ENVELOPE)

    assert {
        "REAL_EMPLOYEE_HEADCOUNT_BY_ROLE",
        "REAL_VEHICLE_FLEET",
        "REAL_TRAVEL_BUDGET",
        "REAL_VOLUNTEER_COUNT_PER_MATCH",
        "REAL_DELEGATION_AND_SIGNATURE_SCOPE",
        "REAL_ASSOCIATION_SAS_OPERATING_SPLIT",
    } <= set(envelope["assumptions_kept_unknown"])


def test_low_central_high_capacity_profiles_are_monotonic():
    envelope = load(ENVELOPE)
    low = envelope["profiles"]["LOW_CONSTRAINED"]["capacities"]
    central = envelope["profiles"]["CENTRAL_WORKING"]["capacities"]
    high = envelope["profiles"]["HIGH_CAPACITY"]["capacities"]

    for resource_id in low:
        assert low[resource_id] <= central[resource_id] <= high[resource_id]


def test_invalid_profile_resource_set_fails_closed():
    envelope = load(ENVELOPE)
    resources = load(RESOURCES)
    broken = json.loads(json.dumps(envelope))
    broken["profiles"]["CENTRAL_WORKING"]["capacities"].pop(
        "VEHICLE_EQUIVALENT_POOL"
    )

    with pytest.raises(ValueError, match="PROFILE_RESOURCE_SET_MISMATCH"):
        validate_envelope_v0(broken, resources)


def test_profile_build_does_not_mutate_f3f_base_resources():
    envelope = load(ENVELOPE)
    resources = load(RESOURCES)
    base_vehicle = next(
        row["capacity"]
        for row in resources["resources"]
        if row["id"] == "VEHICLE_EQUIVALENT_POOL"
    )

    high = build_profile_resources_v0(
        envelope,
        resources,
        "HIGH_CAPACITY",
    )

    high_vehicle = next(
        row["capacity"]
        for row in high["resources"]
        if row["id"] == "VEHICLE_EQUIVALENT_POOL"
    )
    assert high_vehicle == 3
    assert base_vehicle == 2
    assert high["truth_class"] == "ESTIMATED"


def test_public_anchored_profiles_reduce_pressure_without_erasing_unknowns():
    result = robust_vs_fragile_v0(
        load(ENVELOPE),
        load(RESOURCES),
        load(CATALOG),
        corpus().events,
    )

    pressure = result["pressure_points_by_profile"]
    assert (
        pressure["LOW_CONSTRAINED"]
        >= pressure["CENTRAL_WORKING"]
        >= pressure["HIGH_CAPACITY"]
    )
    assert len(result["assumptions_kept_unknown"]) == 8
    assert result["truth_class"] == "ESTIMATED"
    assert result["external_action"] is False
    assert result["authority"] == "KX108_ONLY"


def test_more_capacity_never_increases_hard_block_count():
    rows = {
        row.profile_id: row
        for row in evaluate_all_profiles_v0(
            load(ENVELOPE),
            load(RESOURCES),
            load(CATALOG),
            corpus().events,
        )
    }

    low_blocks = dict(rows["LOW_CONSTRAINED"].gate_counts).get("BLOCK", 0)
    central_blocks = dict(rows["CENTRAL_WORKING"].gate_counts).get("BLOCK", 0)
    high_blocks = dict(rows["HIGH_CAPACITY"].gate_counts).get("BLOCK", 0)

    assert low_blocks >= central_blocks >= high_blocks


def test_public_shadow_blind_spots_are_now_exercised_as_estimated_pressure():
    rows = {
        row.profile_id: dict(row.blind_spot_pressure)
        for row in evaluate_all_profiles_v0(
            load(ENVELOPE),
            load(RESOURCES),
            load(CATALOG),
            corpus().events,
        )
    }

    assert rows["LOW_CONSTRAINED"] == {
        "F3GC_TECHNICAL_DIRECTION_CRUNCH": True,
        "F3GC_VOLUNTEER_MATCHDAY_PRESSURE": True,
    }
    assert rows["CENTRAL_WORKING"] == {
        "F3GC_TECHNICAL_DIRECTION_CRUNCH": False,
        "F3GC_VOLUNTEER_MATCHDAY_PRESSURE": True,
    }
    assert rows["HIGH_CAPACITY"] == {
        "F3GC_TECHNICAL_DIRECTION_CRUNCH": False,
        "F3GC_VOLUNTEER_MATCHDAY_PRESSURE": False,
    }


def test_public_anchor_count_and_replaceable_parameters_are_explicit():
    result = robust_vs_fragile_v0(
        load(ENVELOPE),
        load(RESOURCES),
        load(CATALOG),
        corpus().events,
    )

    assert result["public_anchor_count"] == 6
    assert result["replaceable_parameter_count"] == 15
