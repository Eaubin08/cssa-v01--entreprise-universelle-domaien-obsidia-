import json
import os
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest

from organizations.cssa.annual import build_one_year_corpus_v0
from organizations.cssa.dependency import (
    annual_propagation_campaign_v0,
    assess_revision_state_v0,
    build_fixture_dependency_graphs_v0,
    compare_campaigns_v0,
    validate_graph_coverage_v0,
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
RULES = ROOT / "organizations" / "cssa" / "dependency" / "dependency_rules_v0.json"
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


def annual_events():
    return build_one_year_corpus_v0(load(MODEL))


def graphs():
    return build_fixture_dependency_graphs_v0(annual_events())


def r1_home_graph():
    return next(
        graph for graph in graphs()
        if graph.root.team_id == "SENIORS_R1"
        and int(graph.fixture_ref.rsplit(":", 1)[1]) % 2 == 1
    )


def test_one_year_dependency_graph_covers_all_330_fixture_roots():
    rows = graphs()
    audit = validate_graph_coverage_v0(rows, load(RULES))

    assert len(rows) == 330
    assert audit["fixture_count"] == 330
    assert audit["dependency_count"] == 478
    assert audit["missing_required"] == []
    assert audit["unruled_case_types"] == []


def test_r1_home_fixture_has_six_downstream_surfaces():
    graph = r1_home_graph()
    assert {node.case_type for node in graph.dependents} == {
        "fmi_post_match",
        "match_publication_candidate",
        "venue_configuration",
        "hospitality_activation",
        "matchday_volunteer_assignment",
        "home_match_ticketing_state",
    }


def test_clean_revision_propagation_is_allow_and_fully_current():
    graph = r1_home_graph()
    assessment = assess_revision_state_v0(
        graph=graph,
        rules=load(RULES),
        assessment_id="CLEAN-R1-HOME",
        root_revision=2,
        root_final_authority=True,
        surface_revisions={
            node.case_type: 2 for node in graph.dependents
        },
        surface_delays_hours={
            node.case_type: 0 for node in graph.dependents
        },
    )

    assert assessment.expected_gate == "ALLOW"
    assert assessment.unknowns == ()
    assert assessment.contradictions == ()
    assert assessment.silent_inconsistency_count == 0
    assert all(surface.ready for surface in assessment.surfaces)


def test_single_stale_required_surface_is_hold_not_allow():
    graph = r1_home_graph()
    revisions = {node.case_type: 2 for node in graph.dependents}
    revisions["home_match_ticketing_state"] = 1

    assessment = assess_revision_state_v0(
        graph=graph,
        rules=load(RULES),
        assessment_id="STALE-TICKETING",
        root_revision=2,
        root_final_authority=True,
        surface_revisions=revisions,
        surface_delays_hours={
            node.case_type: 0 for node in graph.dependents
        },
    )

    assert assessment.expected_gate == "HOLD"
    assert "DEPENDENT_REFRESH_PENDING:home_match_ticketing_state" in assessment.unknowns
    assert "DEPENDENT_STATE_NOT_CURRENT:home_match_ticketing_state" in assessment.unknowns
    ticketing = next(
        surface for surface in assessment.surfaces
        if surface.case_type == "home_match_ticketing_state"
    )
    assert ticketing.ready is False
    assert ticketing.stale_reason == "STALE_REVISION"
    assert assessment.silent_inconsistency_count == 0


def test_nonfinal_upstream_authority_blocks_downstream_public_readiness():
    graph = r1_home_graph()
    assessment = assess_revision_state_v0(
        graph=graph,
        rules=load(RULES),
        assessment_id="NOT-FINAL",
        root_revision=2,
        root_final_authority=False,
        surface_revisions={
            node.case_type: 2 for node in graph.dependents
        },
    )

    assert assessment.expected_gate == "BLOCK"
    assert any(
        value.startswith("AUTHORITY_NOT_FINAL:")
        for value in assessment.contradictions
    )
    assert all(surface.ready is False for surface in assessment.surfaces)
    assert assessment.silent_inconsistency_count == 0


def test_dependent_ahead_of_root_is_structural_block():
    graph = r1_home_graph()
    revisions = {node.case_type: 2 for node in graph.dependents}
    revisions["match_publication_candidate"] = 3

    assessment = assess_revision_state_v0(
        graph=graph,
        rules=load(RULES),
        assessment_id="AHEAD-OF-ROOT",
        root_revision=2,
        root_final_authority=True,
        surface_revisions=revisions,
    )

    assert assessment.expected_gate == "BLOCK"
    assert "DEPENDENT_AHEAD_OF_ROOT:match_publication_candidate" in assessment.contradictions
    assert "ILLEGAL_REVISION_ORDER:match_publication_candidate" in assessment.contradictions


def test_missing_required_surface_holds_and_is_never_silent():
    graph = r1_home_graph()
    assessment = assess_revision_state_v0(
        graph=graph,
        rules=load(RULES),
        assessment_id="MISSING-COMM",
        root_revision=2,
        root_final_authority=True,
        surface_revisions={
            node.case_type: 2 for node in graph.dependents
        },
        missing_surfaces=("match_publication_candidate",),
    )

    assert assessment.expected_gate == "HOLD"
    assert "MISSING_DEPENDENT:match_publication_candidate" in assessment.unknowns
    assert "PROPAGATION_STATUS_UNKNOWN:match_publication_candidate" in assessment.unknowns
    assert assessment.silent_inconsistency_count == 0


def test_orphan_dependent_without_fixture_root_fails_closed():
    orphan = SimpleNamespace(
        event_id="ORPHAN",
        event_date="2026-10-01",
        family="COMMUNICATION",
        case_type="match_publication_candidate",
        team_id="SENIORS_R1",
        target_refs=("fixture:SENIORS_R1:999",),
    )

    with pytest.raises(ValueError, match="FIXTURE_ROOT_CARDINALITY"):
        build_fixture_dependency_graphs_v0((orphan,))


def test_all_three_annual_campaigns_have_zero_silent_inconsistency():
    result = compare_campaigns_v0(graphs(), load(RULES))

    assert result["fixture_count"] == 330
    assert result["silent_inconsistency_count"] == 0
    assert set(result["campaigns"]) == {"NORMAL", "HARD", "BREAKER"}
    for campaign in result["campaigns"].values():
        assert campaign["fixture_count"] == 330
        assert campaign["silent_inconsistency_count"] == 0


def test_attack_strength_increases_non_allow_surface():
    rules = load(RULES)
    normal = annual_propagation_campaign_v0(graphs(), rules, mode="NORMAL")
    hard = annual_propagation_campaign_v0(graphs(), rules, mode="HARD")
    breaker = annual_propagation_campaign_v0(graphs(), rules, mode="BREAKER")

    def non_allow(row):
        return row["gate_counts"].get("HOLD", 0) + row["gate_counts"].get("BLOCK", 0)

    assert non_allow(normal) > 0
    assert non_allow(hard) >= non_allow(normal)
    assert non_allow(breaker) >= non_allow(hard)
    assert breaker["stale_or_blocked_surface_count"] >= hard["stale_or_blocked_surface_count"]


def test_dependency_failures_route_into_existing_persona_cockpit():
    graph = r1_home_graph()
    revisions = {node.case_type: 2 for node in graph.dependents}
    revisions["home_match_ticketing_state"] = 1

    assessment = assess_revision_state_v0(
        graph=graph,
        rules=load(RULES),
        assessment_id="REPORT-STALE-TICKETING",
        root_revision=2,
        root_final_authority=True,
        surface_revisions=revisions,
    )

    routing = load(ROUTING)
    pack = build_report_pack_v0(
        (assessment,),
        routing,
        cadence="WEEKLY",
        as_of=date.fromisoformat(assessment.event_date),
        truth_class=None,
    )

    assert len(pack.items) == 1
    assert pack.items[0].family == "DEPENDENCY_PROPAGATION"
    assert pack.items[0].expected_gate == "HOLD"
    assert "MANAGER_GENERAL" in pack.persona_views
    assert "RESP_ADMIN" in pack.persona_views
    assert "TICKETING_BOUTIQUE" in pack.persona_views
    assert "COMMUNICATION" in pack.persona_views
    assert pack.external_delivery_enabled is False


def make_resolver():
    registry = PortableDomainRegistryV0()
    registry.register(
        PortableDomainRegistrationV0(
            domain_id="administration",
            adapter_id="cssa.dependency-propagation.v0",
            schema_ref="organizations/cssa/dependency/dependency_propagation_v0.py",
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
            confidence_provider_id="cssa.dependency-propagation.confidence.v0",
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
            "runtime_id": "cssa-dependency-readonly",
            "provider": "cssa_dependency_readonly",
        }


def run_assessment(tmp_path, assessment):
    raw = assessment.to_runtime_mapping(confidence=0.92)

    flow = CanonicalRuntimeReceiptFlow()
    provider = CountingProvider()
    flow.register_provider("cssa_dependency_readonly", provider)

    action = ActionCandidate(
        action_id=f"f3i-{assessment.assessment_id.lower()}",
        domain="administration",
        actor_id="f3i-dependency-propagation",
        intent="evaluate_dependency_propagation",
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
        mission_id=f"mission-{assessment.assessment_id.lower()}",
        provider_id="cssa_dependency_readonly",
        capability="analysis",
        execution_payload={
            "mode": "READONLY_DEPENDENCY_PROPAGATION",
            "fixture_ref": assessment.fixture_ref,
        },
        agent_context_store_dir=tmp_path / assessment.assessment_id / "contexts",
        decision_store_dir=tmp_path / assessment.assessment_id / "decisions",
        domain_extension_resolver=make_resolver(),
    )
    return result, provider


@pytest.mark.parametrize("gate", ["ALLOW", "HOLD", "BLOCK"])
def test_representative_dependency_assessments_cross_real_guard(tmp_path, gate):
    graph = r1_home_graph()
    revisions = {node.case_type: 2 for node in graph.dependents}

    if gate == "ALLOW":
        assessment = assess_revision_state_v0(
            graph=graph,
            rules=load(RULES),
            assessment_id="REAL-GUARD-ALLOW",
            root_revision=2,
            root_final_authority=True,
            surface_revisions=revisions,
        )
    elif gate == "HOLD":
        revisions["home_match_ticketing_state"] = 1
        assessment = assess_revision_state_v0(
            graph=graph,
            rules=load(RULES),
            assessment_id="REAL-GUARD-HOLD",
            root_revision=2,
            root_final_authority=True,
            surface_revisions=revisions,
        )
    else:
        assessment = assess_revision_state_v0(
            graph=graph,
            rules=load(RULES),
            assessment_id="REAL-GUARD-BLOCK",
            root_revision=2,
            root_final_authority=False,
            surface_revisions=revisions,
        )

    result, provider = run_assessment(tmp_path, assessment)

    assert result.x108_gate == gate
    assert result.decision_authority == "KX108_ONLY"
    assert result.decision_record_verified is True
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
