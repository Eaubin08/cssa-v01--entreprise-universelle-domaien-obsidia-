import json
import os
import sys
from datetime import date
from pathlib import Path

import pytest

from organizations.cssa.annual import build_one_year_corpus_v0
from organizations.cssa.dependency import (
    build_fixture_dependency_index_v0,
    cascade_summary_v0,
    run_cascade_campaign_v0,
)
from organizations.cssa.field import field_runtime_adapter
from organizations.cssa.reporting import build_report_pack_v0
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
GRAPH = (
    ROOT
    / "organizations"
    / "cssa"
    / "dependency"
    / "fixture_dependency_graph_v0.json"
)
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


def events():
    return build_one_year_corpus_v0(load(MODEL))


def graph():
    return load(GRAPH)


def campaign(mode):
    return run_cascade_campaign_v0(
        events(),
        graph(),
        mode_name=mode,
    )


def test_fixture_dependency_index_covers_all_330_season_fixtures():
    index = build_fixture_dependency_index_v0(events(), graph())

    assert len(index) == 330
    assert all(row["root"] is not None for row in index.values())
    assert all(
        row["root"].case_type == "fixture_state"
        for row in index.values()
    )


def test_dependency_graph_explicitly_models_downstream_layers_and_proof():
    cfg = graph()

    node_ids = {
        row["id"] for row in cfg["node_types"].values()
    }
    assert {
        "TRANSPORT_PLAN",
        "TRAVEL_RECONCILIATION",
        "FMI",
        "TICKETING",
        "MATCHDAY",
        "PARTNER_HOSPITALITY",
        "COMMUNICATION",
        "VOLUNTEERS",
    } <= node_ids
    assert cfg["virtual_nodes"][0]["id"] == "PROOF_RECEIPT"
    assert "NO_SILENT_PARTIAL_PROPAGATION" in cfg["rules"]


def test_normal_hard_breaker_campaigns_cover_same_330_fixture_roots():
    rows = {
        mode: campaign(mode)
        for mode in ("NORMAL", "HARD", "BREAKER")
    }

    assert all(len(value) == 330 for value in rows.values())
    assert {
        row.fixture_ref for row in rows["NORMAL"]
    } == {
        row.fixture_ref for row in rows["HARD"]
    } == {
        row.fixture_ref for row in rows["BREAKER"]
    }


def test_any_detected_stale_state_never_silently_allows():
    for mode in ("NORMAL", "HARD", "BREAKER"):
        rows = campaign(mode)
        assert all(
            not row.stale_nodes or row.expected_gate != "ALLOW"
            for row in rows
        )
        assert cascade_summary_v0(rows)["silent_stale_allow_count"] == 0


def test_single_stale_dependent_becomes_hold_not_allow():
    row = next(
        item
        for item in campaign("HARD")
        if len([
            node for node in item.stale_nodes
            if node != "PROOF_RECEIPT"
        ]) == 1
        and not item.root_conflict
    )

    assert row.expected_gate == "HOLD"
    assert len(row.unknowns) >= 2
    assert "SINGLE_STALE_DEPENDENT" in row.risk_flags


def test_multi_layer_stale_state_becomes_block():
    row = next(
        item
        for item in campaign("BREAKER")
        if len([
            node for node in item.stale_nodes
            if node != "PROOF_RECEIPT"
        ]) >= 2
        and not item.root_conflict
    )

    assert row.expected_gate == "BLOCK"
    assert len(row.contradictions) >= 2
    assert "MULTIPLE_DEPENDENTS_ON_OLD_FIXTURE_VERSION" in row.risk_flags


def test_root_conflict_blocks_propagation_assessment():
    row = next(
        item for item in campaign("BREAKER")
        if item.root_conflict
    )

    assert row.expected_gate == "BLOCK"
    assert any(
        contradiction.startswith("ROOT_FIXTURE_STATE_CONFLICT:")
        for contradiction in row.contradictions
    )
    assert "UPSTREAM_ROOT_UNRESOLVED" in row.risk_flags


def test_receipt_mismatch_alone_is_hold_and_not_silently_accepted():
    row = next(
        item
        for item in campaign("HARD")
        if item.receipt_mismatch
        and not item.root_conflict
        and not [
            node for node in item.stale_nodes
            if node != "PROOF_RECEIPT"
        ]
    )

    assert row.expected_gate == "HOLD"
    assert "PROOF_NOT_BOUND_TO_CURRENT_ROOT_VERSION" in row.risk_flags
    assert any(
        value.startswith("PROOF_RECEIPT_VERSION_MISMATCH:")
        for value in row.unknowns
    )


def test_full_propagation_of_changed_fixture_can_allow():
    row = next(
        item
        for item in campaign("HARD")
        if item.root_version == 2
        and not item.root_conflict
        and not item.stale_nodes
    )

    assert row.propagation_completeness == 1.0
    assert row.expected_gate == "ALLOW"


def test_breaker_exposes_at_least_as_many_failures_as_hard_and_normal():
    normal = cascade_summary_v0(campaign("NORMAL"))
    hard = cascade_summary_v0(campaign("HARD"))
    breaker = cascade_summary_v0(campaign("BREAKER"))

    assert normal["failure_count"] <= hard["failure_count"] <= breaker["failure_count"]
    assert normal["changed_fixture_count"] < hard["changed_fixture_count"] < breaker["changed_fixture_count"]
    assert breaker["root_conflict_count"] >= hard["root_conflict_count"]
    assert breaker["mean_changed_propagation_completeness"] <= hard["mean_changed_propagation_completeness"]


def test_dependency_failures_route_into_existing_persona_cockpit():
    rows = tuple(
        row
        for row in campaign("BREAKER")
        if row.expected_gate != "ALLOW"
    )
    as_of = date.fromisoformat(rows[0].event_date)
    pack = build_report_pack_v0(
        rows,
        load(ROUTING),
        cadence="MONTHLY",
        as_of=as_of,
        truth_class="SIMULATED_NOT_OBSERVED",
    )

    assert len(pack.items) > 0
    assert "MANAGER_GENERAL" in pack.persona_views
    assert "RESP_ADMIN" in pack.persona_views
    assert "COMMUNICATION" in pack.persona_views
    assert pack.external_delivery_enabled is False


def make_resolver():
    registry = PortableDomainRegistryV0()
    registry.register(
        PortableDomainRegistrationV0(
            domain_id="administration",
            adapter_id="cssa.fixture-cascade.v0",
            schema_ref="organizations/cssa/dependency/fixture_cascade_v0.py",
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
            confidence_provider_id="cssa.fixture-cascade.confidence.v0",
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
            "runtime_id": "cssa-fixture-cascade-readonly",
            "provider": "cssa_fixture_cascade_readonly",
        }


def run_assessment(tmp_path, row):
    raw = row.to_runtime_mapping(confidence=0.92)

    flow = CanonicalRuntimeReceiptFlow()
    provider = CountingProvider()
    flow.register_provider("cssa_fixture_cascade_readonly", provider)

    action = ActionCandidate(
        action_id=f"f3i-{row.event_id.lower()}",
        domain="administration",
        actor_id="f3i-cascade-simulation",
        intent="evaluate_fixture_dependency_cascade",
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
        mission_id=f"mission-{row.event_id.lower()}",
        provider_id="cssa_fixture_cascade_readonly",
        capability="analysis",
        execution_payload={
            "mode": "READONLY_FIXTURE_DEPENDENCY_CASCADE",
            "fixture_ref": row.fixture_ref,
        },
        agent_context_store_dir=tmp_path / row.event_id / "contexts",
        decision_store_dir=tmp_path / row.event_id / "decisions",
        domain_extension_resolver=make_resolver(),
    )
    return result, provider


@pytest.mark.parametrize("gate", ["ALLOW", "HOLD", "BLOCK"])
def test_representative_dependency_assessments_cross_real_guard(tmp_path, gate):
    source = campaign("BREAKER")
    row = next(item for item in source if item.expected_gate == gate)

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
    else:
        assert result.provider_invoked is False
        assert provider.invocations == 0


def test_dependency_layer_has_no_execution_authority():
    row = campaign("BREAKER")[0]
    raw = row.to_runtime_mapping()

    assert raw["simulation_status"] == "SIMULATED_NOT_OBSERVED"
    assert raw["provenance_refs"] == ("F3I_SIMULATION_ONLY",)
    assert "authorized_action" not in raw
    assert "decision" not in raw
