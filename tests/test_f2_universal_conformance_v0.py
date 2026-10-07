import pytest

from universal.compat.october_udip_v0 import october_udip_state_to_f1
from universal.conformance.v0 import (
    ConformanceError,
    conform_main_domain_snapshot,
)
from universal.contracts.domain_v0 import domain_state_to_governance_payload


MAIN_FIXTURES = {
    "bank": {
        "domain": "bank",
        "market_verdict": "AUTHORIZE",
        "confidence": 0.91,
        "unknowns": [],
        "contradictions": [],
        "risk_flags": [],
        "evidence_refs": ["bank:e1"],
        "agent_votes": [{"agent_id": "TransactionContextAgent"}],
        "decision_authority": "KX108_ONLY",
        "emits_act": False,
        "emits_verdict": False,
        "kernel_mutation": False,
        "memory_write": False,
    },
    "trading": {
        "domain": "trading",
        "market_verdict": "ALLOW",
        "confidence": 0.88,
        "unknowns": ["spread_future_unknown"],
        "contradictions": [],
        "risk_flags": ["event_risk"],
        "evidence_refs": ["trading:e1"],
        "symbol": "BTC/USDT",
        "decision_authority": "KX108_ONLY",
        "emits_act": False,
        "emits_verdict": False,
        "kernel_mutation": False,
    },
    "ecom": {
        "domain": "ecom",
        "market_verdict": "HOLD",
        "confidence": 0.50,
        "unknowns": ["x108_compliance_rate_missing"],
        "contradictions": [],
        "risk_flags": [],
        "evidence_refs": ["ecom:e1"],
        "session_id": "session-1",
        "decision_authority": "KX108_ONLY",
        "emits_act": False,
        "emits_verdict": False,
        "kernel_mutation": False,
    },
    "gps_defense_aviation": {
        "domain": "gps_defense_aviation",
        "market_verdict": "TRAJECTORY_VALID",
        "confidence": 0.94,
        "unknowns": [],
        "contradictions": ["sensor_disagreement"],
        "risk_flags": ["spoof_possible"],
        "evidence_refs": ["gps:e1", "gps:e2"],
        "satellites_count": 11,
        "decision_authority": "KX108_ONLY",
        "emits_act": False,
        "emits_verdict": False,
        "kernel_mutation": False,
    },
}


@pytest.mark.parametrize("domain_id", tuple(MAIN_FIXTURES))
def test_current_main_domain_profiles_conform_without_business_leak(domain_id):
    source = MAIN_FIXTURES[domain_id]
    state, payload, report = conform_main_domain_snapshot(
        source,
        profile_id=f"main:{domain_id}",
        state_ref=f"{domain_id}:fixture:1",
        valid_at="2026-10-06T20:00:00Z",
        provenance_refs=(f"main:{domain_id}",),
        proposed_action_ref=f"proposal:{domain_id}",
    )

    assert report.status == "PASS"
    assert state.domain_id == domain_id
    assert payload.domain_id == domain_id
    assert payload.decision is None
    assert payload.binder_permission is False
    assert payload.allowed_to_act is False
    assert payload.decision_authority == "KX108_ONLY"

    assert "market_verdict" in report.ignored_domain_fields
    assert "confidence" in report.ignored_domain_fields


def test_arbitrary_new_domain_is_accepted_by_universal_contract_only():
    source = {
        "domain": "administration",
        "unknowns": ["internal_role_unknown"],
        "contradictions": [],
        "risk_flags": [],
        "evidence_refs": ["public:rule:1"],
        "decision_authority": "KX108_ONLY",
        "emits_act": False,
        "emits_verdict": False,
        "kernel_mutation": False,
    }
    state, payload, report = conform_main_domain_snapshot(
        source,
        profile_id="synthetic:administration",
        state_ref="admin:case:1",
        valid_at="2026-10-06T20:00:00Z",
    )
    assert report.status == "PASS"
    assert state.domain_id == "administration"
    assert payload.domain_id == "administration"
    assert payload.decision is None


def test_domain_specific_fields_are_ignored_not_promoted():
    source = dict(MAIN_FIXTURES["gps_defense_aviation"])
    source.update(
        {
            "rinex_path": "x.rnx",
            "signal_noise_ratio": 42.0,
            "aircraft": "fixture",
        }
    )
    _, _, report = conform_main_domain_snapshot(
        source,
        profile_id="main:gps:business-field-isolation",
        state_ref="gps:fixture:2",
        valid_at="2026-10-06T20:00:00Z",
    )
    assert {"rinex_path", "signal_noise_ratio", "aircraft"}.issubset(
        set(report.ignored_domain_fields)
    )


@pytest.mark.parametrize(
    "mutation",
    [
        {"decision_authority": "DOMAIN"},
        {"allowed_to_decide": True},
        {"allowed_to_act": True},
        {"emits_act": True},
        {"emits_verdict": True},
        {"kernel_mutation": True},
        {"x108_mutation": True},
        {"memory_write": True},
        {"graphiti_write": True},
        {"neo4j_write": True},
    ],
)
def test_main_profile_authority_leak_fails_closed(mutation):
    source = dict(MAIN_FIXTURES["bank"])
    source.update(mutation)
    with pytest.raises(ConformanceError):
        conform_main_domain_snapshot(
            source,
            profile_id="main:authority-leak",
            state_ref="bank:fixture:bad",
            valid_at="2026-10-06T20:00:00Z",
        )


def test_october_udip_candidate_maps_without_semantic_loss():
    old = {
        "domain_id": "gps",
        "world_state_ref": "world-1",
        "valid_at": "2026-10-06T12:00:00Z",
        "unknowns": ("freshness_unknown",),
        "contradictions": ("sensor_disagreement",),
        "risk_flags": ("hostile_input_possible",),
        "evidence_refs": ("evidence-a",),
        "provenance_refs": ("capture-1", "sensor-a"),
        "decision_authority": "KX108_ONLY",
        "allowed_to_decide": False,
        "allowed_to_act": False,
    }
    state = october_udip_state_to_f1(old)
    payload = domain_state_to_governance_payload(
        state,
        proposed_action_ref="proposal-1",
    )
    assert state.state_ref == "gps:world-1:2026-10-06T12:00:00Z"
    assert state.upstream_state_ref == "world-1"
    assert payload.unknowns == old["unknowns"]
    assert payload.contradictions == old["contradictions"]
    assert payload.risk_flags == old["risk_flags"]
    assert payload.evidence_refs == old["evidence_refs"]
    assert payload.provenance_refs == old["provenance_refs"]
    assert payload.decision is None
    assert payload.binder_permission is False
    assert payload.allowed_to_act is False


@pytest.mark.parametrize(
    "mutation",
    [
        {"decision_authority": "DOMAIN"},
        {"allowed_to_decide": True},
        {"allowed_to_act": True},
    ],
)
def test_october_udip_authority_leak_rejected(mutation):
    old = {
        "domain_id": "gps",
        "world_state_ref": "world-1",
        "valid_at": "2026-10-06T12:00:00Z",
    }
    old.update(mutation)
    with pytest.raises(ValueError):
        october_udip_state_to_f1(old)


def test_market_verdict_act_never_becomes_universal_decision():
    source = dict(MAIN_FIXTURES["trading"])
    source["market_verdict"] = "ACT"
    _, payload, report = conform_main_domain_snapshot(
        source,
        profile_id="main:advisory-act-isolation",
        state_ref="trading:fixture:act",
        valid_at="2026-10-06T20:00:00Z",
    )
    assert "market_verdict" in report.ignored_domain_fields
    assert payload.decision is None
    assert payload.allowed_to_act is False
