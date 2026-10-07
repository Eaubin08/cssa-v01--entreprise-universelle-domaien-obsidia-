import json
import os
import sys
from collections import Counter
from pathlib import Path

import pytest

from organizations.cssa.field import field_runtime_adapter
from organizations.cssa.season_simulation import (
    FIXTURE_COUNTS_V0,
    SIMULATION_STATUS,
    build_full_season_corpus_v0,
    corpus_summary_v0,
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


def load_model():
    return json.loads(MODEL.read_text(encoding="utf-8"))


def build():
    return build_full_season_corpus_v0(load_model())


def test_full_season_has_19_teams_and_904_events():
    corpus = build()
    summary = corpus_summary_v0(corpus)

    assert corpus.simulation_status == SIMULATION_STATUS
    assert corpus.start_date == "2026-08-01"
    assert corpus.end_date == "2027-06-15"
    assert len(corpus.team_ids) == 19
    assert set(corpus.team_ids) == set(FIXTURE_COUNTS_V0)
    assert summary["event_count"] == 904


def test_fixture_counts_match_simulation_profile_for_every_team():
    corpus = build()
    fixture_counts = Counter(
        event.team_id
        for event in corpus.events
        if event.case_type == "fixture_state"
    )

    assert dict(fixture_counts) == FIXTURE_COUNTS_V0
    assert sum(fixture_counts.values()) == 330


def test_first_team_has_full_matchday_commercial_and_communication_lifecycle():
    corpus = build()

    assert len([
        e for e in corpus.events
        if e.team_id == "SENIORS_R1" and e.case_type == "fixture_state"
    ]) == 26
    assert len([
        e for e in corpus.events
        if e.team_id == "SENIORS_R1" and e.case_type == "away_trip_plan"
    ]) == 13
    assert len([
        e for e in corpus.events
        if e.team_id == "SENIORS_R1" and e.case_type == "venue_configuration"
    ]) == 13
    assert len([
        e for e in corpus.events
        if e.team_id == "SENIORS_R1" and e.case_type == "hospitality_activation"
    ]) == 13
    assert len([
        e for e in corpus.events
        if e.team_id == "SENIORS_R1" and e.case_type == "home_match_ticketing_state"
    ]) == 13
    assert len([
        e for e in corpus.events
        if e.team_id == "SENIORS_R1" and e.case_type == "match_publication_candidate"
    ]) == 26


def test_simulated_route_kilometres_stay_inside_f3d_season_envelope():
    corpus = build()
    km = corpus.total_estimated_team_route_km

    assert km == 24_500.00
    assert 22_000 <= km <= 36_250


def test_whole_club_operating_families_are_concurrent_in_one_corpus():
    corpus = build()
    families = {e.family for e in corpus.events}

    assert {
        "ACADEMY_MEMBERSHIP",
        "COMPETITIONS",
        "TRAVEL_LOGISTICS",
        "FINANCE_ACCOUNTING",
        "PARTNERS_COMMERCIAL",
        "SUPPORTERS_TICKETING",
        "MATCHDAY",
        "COMMUNICATION",
        "PEOPLE_HR_VOLUNTEERS",
        "EDUCATION",
        "PROOF_AUDIT",
        "PRIVACY_SENSITIVE",
    } <= families


def test_corpus_contains_allow_hold_block_and_pre_runtime_privacy_stop():
    corpus = build()
    summary = corpus_summary_v0(corpus)

    assert summary["gate_counts"]["ALLOW"] > 700
    assert summary["gate_counts"]["HOLD"] > 10
    assert summary["gate_counts"]["BLOCK"] > 10
    assert summary["gate_counts"]["PRE_RUNTIME_BLOCK"] == 2


def test_no_event_is_field_evidence_or_cssa_validation():
    corpus = build()

    for event in corpus.events:
        assert event.simulation_status == SIMULATION_STATUS
        assert "F3E_SIMULATION_ONLY" in event.provenance_refs


def test_sensitive_youth_and_payroll_events_stop_before_runtime():
    corpus = build()
    blocked = corpus.by_gate("PRE_RUNTIME_BLOCK")

    assert {e.event_id for e in blocked} == {
        "STRESS-YOUTH-HEALTH",
        "STRESS-PAYROLL",
    }

    for event in blocked:
        with pytest.raises(ValueError, match="PRIVACY_BLOCKED_BEFORE_RUNTIME"):
            event.to_runtime_mapping()


def test_management_vacancy_and_public_staleness_are_explicit_stress_cases():
    corpus = build()
    by_id = {e.event_id: e for e in corpus.events}

    assert by_id["STRESS-MANAGER-VACANCY"].expected_gate == "HOLD"
    assert by_id["STRESS-SOURCE-STALE"].expected_gate == "BLOCK"
    assert "CSSA_MANAGER_DEPARTURE_2026_09_10" in (
        by_id["STRESS-MANAGER-VACANCY"].evidence_refs
    )


def make_resolver():
    registry = PortableDomainRegistryV0()
    registry.register(
        PortableDomainRegistrationV0(
            domain_id="administration",
            adapter_id="cssa.full-season.sim.v0",
            schema_ref="organizations/cssa/season_simulation/full_season_v0.py",
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
            confidence_provider_id="cssa.full-season.confidence.v0",
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
            "runtime_id": "cssa-full-season-readonly",
            "provider": "cssa_full_season_readonly",
        }


def run_event(tmp_path, event):
    raw = event.to_runtime_mapping(confidence=0.92)

    flow = CanonicalRuntimeReceiptFlow()
    provider = CountingProvider()
    flow.register_provider("cssa_full_season_readonly", provider)

    action = ActionCandidate(
        action_id=f"f3e-{event.event_id.lower()}",
        domain="administration",
        actor_id="f3e-season-simulation",
        intent="evaluate_simulated_season_event",
        action_type="analysis",
        irreversible=False,
        timestamp_plan="",
        payload={
            "freshness_score": 1.0,
            "source_count": max(2, len(event.source_ids)),
            "clean_json_ready": True,
            "critical": False,
        },
    )

    result = upstream_runtime.run_governed_runtime_cycle(
        AGENT_ID,
        action,
        raw,
        execution_surface=flow,
        mission_id=f"mission-{event.event_id.lower()}",
        provider_id="cssa_full_season_readonly",
        capability="analysis",
        execution_payload={
            "mode": "READONLY_FULL_SEASON_SIMULATION",
            "event_id": event.event_id,
        },
        agent_context_store_dir=tmp_path / event.event_id / "contexts",
        decision_store_dir=tmp_path / event.event_id / "decisions",
        domain_extension_resolver=make_resolver(),
    )
    return result, provider


@pytest.mark.parametrize("gate", ["ALLOW", "HOLD", "BLOCK"])
def test_representative_season_events_cross_real_runtime(tmp_path, gate):
    corpus = build()
    event = next(e for e in corpus.events if e.expected_gate == gate)
    result, provider = run_event(tmp_path, event)

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
