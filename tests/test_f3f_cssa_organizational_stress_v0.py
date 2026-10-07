import json
import os
import sys
from datetime import date
from pathlib import Path

import pytest

from organizations.cssa.field import field_runtime_adapter
from organizations.cssa.reporting import build_report_pack_v0
from organizations.cssa.season_simulation import build_full_season_corpus_v0
from organizations.cssa.stress import (
    assess_catalog_v0,
    catalog_summary_v0,
    season_workload_pressure_v0,
)
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
ROUTING = ROOT / "organizations" / "cssa" / "reporting" / "routing_v0.json"

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


def assessments():
    return assess_catalog_v0(load(CATALOG), load(RESOURCES))


def build_corpus():
    return build_full_season_corpus_v0(load(MODEL))


def test_catalog_has_12_stress_scenarios_with_balanced_gate_surface():
    rows = assessments()
    summary = catalog_summary_v0(rows)

    assert summary["scenario_count"] == 12
    assert summary["gate_counts"] == {
        "ALLOW": 2,
        "BLOCK": 5,
        "HOLD": 5,
    }
    assert summary["resource_conflict_count"] == 5
    assert summary["priority_orders_generated"] == 12


def test_vehicle_collision_is_hard_block_before_double_allocation():
    row = next(x for x in assessments() if x.scenario_id == "F3F_S01_VEHICLE_COLLISION")

    assert row.expected_gate == "BLOCK"
    assert len(row.conflicts) == 1
    conflict = row.conflicts[0]
    assert conflict.resource_id == "VEHICLE_EQUIVALENT_POOL"
    assert conflict.capacity == 2.0
    assert conflict.demand == 3.0
    assert conflict.overload == 1.0
    assert "CAPACITY_EXCEEDED:VEHICLE_EQUIVALENT_POOL" in row.contradictions
    assert "DOUBLE_ALLOCATION_RISK:VEHICLE_EQUIVALENT_POOL" in row.contradictions


def test_budget_pressure_holds_without_inventing_real_cssa_budget():
    row = next(x for x in assessments() if x.scenario_id == "F3F_S03_TRAVEL_BUDGET_PRESSURE")

    assert row.expected_gate == "HOLD"
    assert row.conflicts[0].resource_id == "TRAVEL_MONTHLY_ENVELOPE"
    assert "SIMULATED_BUDGET_PRESSURE" in row.risk_flags
    assert "OVERRUN_APPROVAL_UNKNOWN" in row.unknowns
    assert row.simulation_status == "SIMULATED_NOT_OBSERVED"


def test_safety_priority_beats_partner_activation_but_does_not_authorize_reallocation():
    row = next(x for x in assessments() if x.scenario_id == "F3F_S11_SAFETY_VS_PARTNER_PRIORITY")

    assert row.priority_order[0] == "SAFETY_ACCESS"
    assert row.expected_gate == "HOLD"
    assert "HUMAN_REALLOCATION_APPROVAL_UNKNOWN" in row.unknowns
    assert any(
        c.resource_id == "MATCHDAY_ORGANIZER_DAILY"
        for c in row.conflicts
    )


def test_home_match_priority_beats_commercial_event_on_same_venue_slot():
    row = next(x for x in assessments() if x.scenario_id == "F3F_S12_VENUE_DOUBLE_BOOKING")

    assert row.priority_order[0] == "HOME_MATCH"
    assert row.expected_gate == "BLOCK"
    assert row.conflicts[0].resource_id == "MAIN_STADIUM_SLOT"


def test_twenty_valid_cases_are_prioritized_without_false_block():
    row = next(x for x in assessments() if x.scenario_id == "F3F_S09_TWENTY_VALID_CASES")

    assert len(row.items) == 20
    assert len(row.priority_order) == 20
    assert len(set(row.priority_order)) == 20
    assert row.expected_gate == "ALLOW"
    assert row.priority_order[0] in {"CASE_01", "CASE_02"}


def test_full_904_event_season_is_scanned_for_daily_role_pressure():
    corpus = build_corpus()
    result = season_workload_pressure_v0(corpus.events, load(RESOURCES))

    assert result["event_count"] == 904
    assert result["resource_day_observations"] > 0
    assert result["pressure_point_count"] > 0
    assert result["max_overload"] > 0


def test_stress_findings_route_into_existing_weekly_reporting_cockpit():
    routing = load(ROUTING)
    rows = assessments()
    pack = build_report_pack_v0(
        rows,
        routing,
        cadence="WEEKLY",
        as_of=date(2026, 10, 20),
        truth_class="SIMULATED_NOT_OBSERVED",
    )

    assert len(pack.items) > 0
    assert "MANAGER_GENERAL" in pack.persona_views
    assert "RESP_ADMIN" in pack.persona_views
    assert "TECHNICAL_DIRECTOR" in pack.persona_views
    assert all(item.family == "ORGANIZATIONAL_STRESS" for item in pack.items)


def make_resolver():
    registry = PortableDomainRegistryV0()
    registry.register(
        PortableDomainRegistrationV0(
            domain_id="administration",
            adapter_id="cssa.organizational-stress.v0",
            schema_ref="organizations/cssa/stress/organizational_stress_v0.py",
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
            confidence_provider_id="cssa.organizational-stress.confidence.v0",
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
            "runtime_id": "cssa-organizational-stress-readonly",
            "provider": "cssa_organizational_stress_readonly",
        }


def run_assessment(tmp_path, row):
    raw = row.to_runtime_mapping(confidence=0.92)

    flow = CanonicalRuntimeReceiptFlow()
    provider = CountingProvider()
    flow.register_provider("cssa_organizational_stress_readonly", provider)

    action = ActionCandidate(
        action_id=f"f3f-{row.scenario_id.lower()}",
        domain="administration",
        actor_id="f3f-stress-simulation",
        intent="evaluate_organizational_stress",
        action_type="analysis",
        irreversible=False,
        timestamp_plan="",
        payload={
            "freshness_score": 1.0,
            "source_count": max(2, len(row.source_ids)),
            "clean_json_ready": True,
            "critical": False,
        },
    )

    result = upstream_runtime.run_governed_runtime_cycle(
        AGENT_ID,
        action,
        raw,
        execution_surface=flow,
        mission_id=f"mission-{row.scenario_id.lower()}",
        provider_id="cssa_organizational_stress_readonly",
        capability="analysis",
        execution_payload={
            "mode": "READONLY_ORGANIZATIONAL_STRESS",
            "scenario_id": row.scenario_id,
        },
        agent_context_store_dir=tmp_path / row.scenario_id / "contexts",
        decision_store_dir=tmp_path / row.scenario_id / "decisions",
        domain_extension_resolver=make_resolver(),
    )
    return result, provider


@pytest.mark.parametrize("gate", ["ALLOW", "HOLD", "BLOCK"])
def test_representative_stress_assessments_cross_real_guard(tmp_path, gate):
    row = next(x for x in assessments() if x.expected_gate == gate)
    result, provider = run_assessment(tmp_path, row)

    assert result.x108_gate == gate
    assert result.decision_record_verified is True
    assert result.decision_authority == "KX108_ONLY"
    assert result.memory_write is False
    assert result.kernel_mutation is False
    assert result.emits_act is False
    assert result.world_action_allowed is False

    if gate == "ALLOW":
        assert result.provider_invoked is True
        assert provider.invocations == 1
        assert result.receipt["status"] == "COMPLETED"
    else:
        assert result.provider_invoked is False
        assert provider.invocations == 0
        assert result.receipt is None


def test_stress_layer_has_no_execution_authority():
    row = assessments()[0]
    raw = row.to_runtime_mapping()

    assert raw["simulation_status"] == "SIMULATED_NOT_OBSERVED"
    assert raw["provenance_refs"] == ("F3F_SIMULATION_ONLY",)
    assert "decision" not in raw
    assert "authorized_action" not in raw
