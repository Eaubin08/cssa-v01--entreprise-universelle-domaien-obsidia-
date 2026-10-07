import json
import math
import os
import sys
from pathlib import Path

import pytest

from organizations.cssa.calibration import (
    adversarial_summary_v0,
    apply_resolved_assumptions_v0,
    evaluate_profile_v0,
    exhaustive_assumption_grid_v0,
    exhaustive_resource_grid_v0,
    named_profile_results_v0,
    one_at_a_time_assumption_sensitivity_v0,
    one_at_a_time_resource_sensitivity_v0,
    override_resource_capacities_v0,
    pressure_sensitivity_v0,
)
from organizations.cssa.field import field_runtime_adapter
from organizations.cssa.season_simulation import build_full_season_corpus_v0
from organizations.cssa.stress import assess_stress_scenario_v0
from universal.registry.portable_v0 import (
    PortableDomainRegistrationV0,
    PortableDomainRegistryV0,
)
from universal.runtime.resolver_v0 import (
    CanonicalCompatibleResolverV0,
    PortableRuntimeBindingV0,
)


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "organizations" / "cssa" / "season" / "public_model_v0.json"
RESOURCES = ROOT / "organizations" / "cssa" / "stress" / "resources_v0.json"
CATALOG = ROOT / "organizations" / "cssa" / "stress" / "stress_scenarios_v0.json"
SPACE = ROOT / "organizations" / "cssa" / "calibration" / "sensitivity_space_v0.json"

UPSTREAM = Path(os.environ["OBSIDIA_UPSTREAM_ROOT"]).resolve()
for candidate in (UPSTREAM, UPSTREAM / "scripts"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from periphery.common import ActionCandidate  # noqa: E402
from scripts.providers.canonical_runtime_receipt_flow_v1 import (  # noqa: E402
    CanonicalRuntimeReceiptFlow,
)
import obsidia_governed_runtime_cycle_v1 as upstream_runtime  # noqa: E402


AGENT_ID = "DATA_PURITY_AGENT"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def corpus():
    return build_full_season_corpus_v0(load(MODEL))


def scenario(scenario_id):
    return next(
        raw for raw in load(CATALOG)["scenarios"]
        if raw["id"] == scenario_id
    )


def test_parameter_space_is_explicitly_synthetic_and_has_attack_extremes():
    space = load(SPACE)

    assert space["status"] == "SIMULATED_NOT_OBSERVED"
    assert len(space["resource_dimensions"]) == 6
    assert len(space["assumption_dimensions"]) == 6

    by_id = {row["id"]: row for row in space["resource_dimensions"]}
    assert 0 in by_id["RESP_ADMIN_DAILY"]["values"]
    assert 0 in by_id["VEHICLE_EQUIVALENT_POOL"]["values"]
    assert 15000 in by_id["TRAVEL_MONTHLY_ENVELOPE"]["values"]

    profile_ids = {
        row["id"] for row in space["named_operating_profiles"]
    }
    assert profile_ids == {
        "CRUSHED",
        "TIGHT",
        "BASE_F3F",
        "COMFORTABLE",
        "ABUNDANT",
    }


def test_invalid_resource_overrides_fail_closed():
    resources = load(RESOURCES)

    with pytest.raises(ValueError, match="UNKNOWN_RESOURCE_OVERRIDE"):
        override_resource_capacities_v0(
            resources,
            {"DOES_NOT_EXIST": 1},
        )

    with pytest.raises(ValueError, match="NEGATIVE_RESOURCE_CAPACITY"):
        override_resource_capacities_v0(
            resources,
            {"VEHICLE_EQUIVALENT_POOL": -1},
        )

    with pytest.raises(ValueError, match="NON_FINITE_RESOURCE_CAPACITY"):
        override_resource_capacities_v0(
            resources,
            {"RESP_ADMIN_DAILY": math.inf},
        )

    with pytest.raises(ValueError, match="NON_FINITE_RESOURCE_CAPACITY"):
        override_resource_capacities_v0(
            resources,
            {"RESP_ADMIN_DAILY": math.nan},
        )


def test_zero_capacity_is_valid_adversarial_input_without_mutating_baseline():
    resources = load(RESOURCES)
    original = next(
        r["capacity"] for r in resources["resources"]
        if r["id"] == "VEHICLE_EQUIVALENT_POOL"
    )

    mutated = override_resource_capacities_v0(
        resources,
        {"VEHICLE_EQUIVALENT_POOL": 0},
    )

    assert next(
        r["capacity"] for r in mutated["resources"]
        if r["id"] == "VEHICLE_EQUIVALENT_POOL"
    ) == 0
    assert next(
        r["capacity"] for r in resources["resources"]
        if r["id"] == "VEHICLE_EQUIVALENT_POOL"
    ) == original == 2


def test_unknown_assumption_fails_closed():
    with pytest.raises(ValueError, match="UNKNOWN_RESOLVED_ASSUMPTION"):
        apply_resolved_assumptions_v0(
            scenario("F3F_S02_ADMIN_ABSENCE_LGEF_URGENT"),
            load(SPACE),
            ("FAKE_ASSUMPTION",),
        )


def test_vehicle_capacity_threshold_flips_hard_collision_gate():
    catalog = load(CATALOG)
    resources = load(RESOURCES)
    space = load(SPACE)

    blocked = evaluate_profile_v0(
        catalog,
        resources,
        space,
        profile_id="vehicle-2",
        resource_overrides={"VEHICLE_EQUIVALENT_POOL": 2},
    )
    allowed = evaluate_profile_v0(
        catalog,
        resources,
        space,
        profile_id="vehicle-3",
        resource_overrides={"VEHICLE_EQUIVALENT_POOL": 3},
    )

    assert blocked.gate_for("F3F_S01_VEHICLE_COLLISION") == "BLOCK"
    assert allowed.gate_for("F3F_S01_VEHICLE_COLLISION") == "ALLOW"


def test_resolving_delegation_changes_two_hold_scenarios_without_guessing():
    result = one_at_a_time_assumption_sensitivity_v0(
        load(CATALOG),
        load(RESOURCES),
        load(SPACE),
    )
    delegation = next(
        row for row in result["assumptions"]
        if row["assumption_id"] == "DELEGATION_RESOLVED"
    )

    assert delegation["scenario_gate_flip_count"] == 2
    assert delegation["changed_scenarios"] == [
        "F3F_S02_ADMIN_ABSENCE_LGEF_URGENT",
        "F3F_S08_NO_DELEGATION_FOR_ABSENCE",
    ]


def test_resource_sensitivity_identifies_only_hard_shared_assets_as_gate_fragile():
    result = one_at_a_time_resource_sensitivity_v0(
        load(CATALOG),
        load(RESOURCES),
        load(SPACE),
    )
    changed = {
        row["parameter_id"]: row["changed_scenarios"]
        for row in result["parameters"]
        if row["scenario_gate_flip_count"] > 0
    }

    assert changed == {
        "HOSPITALITY_SPACE": ["F3F_S05_HOSPITALITY_DOUBLE_COMMITMENT"],
        "MAIN_STADIUM_SLOT": ["F3F_S12_VENUE_DOUBLE_BOOKING"],
        "VEHICLE_EQUIVALENT_POOL": ["F3F_S01_VEHICLE_COLLISION"],
    }


def test_exhaustive_resource_grid_attacks_15120_capacity_profiles():
    result = exhaustive_resource_grid_v0(
        load(CATALOG),
        load(RESOURCES),
        load(SPACE),
    )

    assert result["profile_count"] == 15120
    assert result["dimension_count"] == 6
    assert result["profiles_all_allow"] == 0
    assert result["resource_fragile_scenarios"] == [
        "F3F_S01_VEHICLE_COLLISION",
        "F3F_S05_HOSPITALITY_DOUBLE_COMMITMENT",
        "F3F_S12_VENUE_DOUBLE_BOOKING",
    ]


def test_exhaustive_assumption_grid_attacks_all_64_truth_states():
    result = exhaustive_assumption_grid_v0(
        load(CATALOG),
        load(RESOURCES),
        load(SPACE),
    )

    assert result["profile_count"] == 64
    assert result["assumption_count"] == 6
    assert result["all_allow_profile_count"] == 0
    assert result["assumption_sensitive_scenarios"] == [
        "F3F_S02_ADMIN_ABSENCE_LGEF_URGENT",
        "F3F_S03_TRAVEL_BUDGET_PRESSURE",
        "F3F_S04_LATE_MATCH_CHANGE_CASCADE",
        "F3F_S06_FMI_BACKLOG_DEADLINE_CASCADE",
        "F3F_S07_STALE_SOURCE_CONFLICT",
        "F3F_S08_NO_DELEGATION_FOR_ABSENCE",
        "F3F_S11_SAFETY_VS_PARTNER_PRIORITY",
    ]


def test_named_profiles_show_resource_relief_cannot_fix_authority_or_stale_truth():
    rows = {
        row.profile_id: row
        for row in named_profile_results_v0(
            load(CATALOG),
            load(RESOURCES),
            load(SPACE),
        )
    }

    assert dict(rows["BASE_F3F"].gate_counts) == {
        "ALLOW": 2,
        "BLOCK": 5,
        "HOLD": 5,
    }
    assert dict(rows["ABUNDANT"].gate_counts) == {
        "ALLOW": 5,
        "BLOCK": 2,
        "HOLD": 5,
    }

    # Throwing resources at the system cannot resolve stale facts or missing authority.
    assert rows["ABUNDANT"].gate_for("F3F_S07_STALE_SOURCE_CONFLICT") == "BLOCK"
    assert rows["ABUNDANT"].gate_for("F3F_S08_NO_DELEGATION_FOR_ABSENCE") == "HOLD"


def test_full_season_pressure_is_attacked_across_role_capacity_multipliers():
    result = pressure_sensitivity_v0(
        corpus().events,
        load(RESOURCES),
        load(SPACE),
    )

    assert result["multipliers"] == [0.0, 0.25, 0.5, 1.0, 2.0, 4.0]
    assert len(result["resources"]) == 10
    assert any(
        row["pressure_point_range"] > 0
        for row in result["resources"]
    )

    admin = next(
        row for row in result["resources"]
        if row["resource_id"] == "RESP_ADMIN_DAILY"
    )
    assert admin["observations"][0]["capacity"] == 0
    assert admin["observations"][0]["pressure_point_count"] > 0


def test_adversarial_summary_ranks_real_field_questions_instead_of_fake_precision():
    summary = adversarial_summary_v0(
        load(CATALOG),
        load(RESOURCES),
        load(SPACE),
        corpus().events,
    )

    assert summary["authority"] == "KX108_ONLY"
    assert summary["external_action"] is False
    assert summary["resource_grid"]["profile_count"] == 15120
    assert summary["assumption_grid"]["profile_count"] == 64

    priorities = summary["calibration_priorities"]
    assert priorities[0]["calibration_id"] == "DELEGATION_RESOLVED"
    assert priorities[0]["scenario_gate_flip_count"] == 2
    assert "?" in priorities[0]["field_question"]


def make_resolver():
    registry = PortableDomainRegistryV0()
    registry.register(
        PortableDomainRegistrationV0(
            domain_id="administration",
            adapter_id="cssa.sensitivity.v0",
            schema_ref="organizations/cssa/calibration/adversarial_sensitivity_v0.py",
            capabilities=("read", "classify", "detect", "propose"),
        ),
        field_runtime_adapter,
    )
    resolver = CanonicalCompatibleResolverV0(
        source_root=UPSTREAM,
        registry=registry,
    )
    resolver.bind_portable_runtime(
        PortableRuntimeBindingV0(
            domain_id="administration",
            confidence_provider_id="cssa.sensitivity.confidence.v0",
        ),
        lambda raw: raw["confidence"],
    )
    return resolver


class CountingProvider:
    def __init__(self):
        self.invocations = 0

    def __call__(self, **kwargs):
        self.invocations += 1
        return {
            "runtime_id": "cssa-sensitivity-readonly",
            "provider": "cssa_sensitivity_readonly",
        }


def run_assessment(tmp_path, assessment):
    raw = assessment.to_runtime_mapping(confidence=0.92)

    flow = CanonicalRuntimeReceiptFlow()
    provider = CountingProvider()
    flow.register_provider("cssa_sensitivity_readonly", provider)

    action = ActionCandidate(
        action_id=f"f3ga-{assessment.scenario_id.lower()}",
        domain="administration",
        actor_id="f3g-a-sensitivity",
        intent="evaluate_sensitivity_flip",
        action_type="analysis",
        irreversible=False,
        timestamp_plan="",
        payload={
            "freshness_score": 1.0,
            "source_count": max(2, len(assessment.source_ids)),
            "clean_json_ready": True,
            "critical": False,
        },
    )

    result = upstream_runtime.run_governed_runtime_cycle(
        AGENT_ID,
        action,
        raw,
        execution_surface=flow,
        mission_id=f"mission-{assessment.scenario_id.lower()}",
        provider_id="cssa_sensitivity_readonly",
        capability="analysis",
        execution_payload={
            "mode": "READONLY_ADVERSARIAL_SENSITIVITY",
            "scenario_id": assessment.scenario_id,
        },
        agent_context_store_dir=tmp_path / assessment.scenario_id / "contexts",
        decision_store_dir=tmp_path / assessment.scenario_id / "decisions",
        domain_extension_resolver=make_resolver(),
    )
    return result, provider


@pytest.mark.parametrize(
    "vehicle_capacity,expected_gate,expected_provider",
    [
        (2, "BLOCK", False),
        (3, "ALLOW", True),
    ],
)
def test_capacity_flip_still_crosses_real_guard(
    tmp_path,
    vehicle_capacity,
    expected_gate,
    expected_provider,
):
    raw = apply_resolved_assumptions_v0(
        scenario("F3F_S01_VEHICLE_COLLISION"),
        load(SPACE),
        (),
    )
    resources = override_resource_capacities_v0(
        load(RESOURCES),
        {"VEHICLE_EQUIVALENT_POOL": vehicle_capacity},
    )
    assessment = assess_stress_scenario_v0(raw, resources)
    result, provider = run_assessment(tmp_path, assessment)

    assert result.x108_gate == expected_gate
    assert result.provider_invoked is expected_provider
    assert provider.invocations == (1 if expected_provider else 0)
    assert result.decision_authority == "KX108_ONLY"
    assert result.memory_write is False
    assert result.kernel_mutation is False
    assert result.emits_act is False
    assert result.world_action_allowed is False
