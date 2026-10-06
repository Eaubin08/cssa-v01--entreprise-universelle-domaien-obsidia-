from dataclasses import fields

import pytest

from universal.contracts.domain_v0 import (
    DomainStateRefV0,
    GovernancePayloadV0,
    domain_state_to_governance_payload,
)


def state() -> DomainStateRefV0:
    return DomainStateRefV0(
        domain_id="administration",
        state_ref="case:123",
        valid_at="2026-10-06T20:00:00Z",
        upstream_state_ref="source:mail:456",
        unknowns=("sender_role_unknown",),
        contradictions=("deadline_conflict",),
        risk_flags=("late_request_possible",),
        evidence_refs=("doc:rule:20.7",),
        provenance_refs=("source:lgef",),
    )


def test_translation_conserves_required_information():
    s = state()
    p = domain_state_to_governance_payload(s, proposed_action_ref="proposal:789")
    assert p.domain_id == s.domain_id
    assert p.domain_state_ref == s.state_ref
    assert p.upstream_state_ref == s.upstream_state_ref
    assert p.unknowns == s.unknowns
    assert p.contradictions == s.contradictions
    assert p.risk_flags == s.risk_flags
    assert p.evidence_refs == s.evidence_refs
    assert p.provenance_refs == s.provenance_refs
    assert p.proposed_action_ref == "proposal:789"


def test_translation_never_creates_authority():
    p = domain_state_to_governance_payload(state(), proposed_action_ref="proposal:789")
    assert p.decision is None
    assert p.binder_permission is False
    assert p.allowed_to_act is False
    assert p.decision_authority == "KX108_ONLY"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"decision": "ACT"},
        {"binder_permission": True},
        {"allowed_to_act": True},
        {"decision_authority": "DOMAIN"},
    ],
)
def test_governance_payload_rejects_authority_leak(kwargs):
    data = {"domain_id": "administration", "domain_state_ref": "case:123"}
    data.update(kwargs)
    with pytest.raises(ValueError):
        GovernancePayloadV0(**data)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"allowed_to_decide": True},
        {"allowed_to_act": True},
        {"decision_authority": "DOMAIN"},
    ],
)
def test_domain_state_rejects_authority_leak(kwargs):
    data = {
        "domain_id": "administration",
        "state_ref": "case:123",
        "valid_at": "2026-10-06T20:00:00Z",
    }
    data.update(kwargs)
    with pytest.raises(ValueError):
        DomainStateRefV0(**data)


def test_contract_does_not_hardcode_cssa_or_existing_domain_business_semantics():
    names = {f.name.lower() for cls in (DomainStateRefV0, GovernancePayloadV0) for f in fields(cls)}
    forbidden = {
        "match",
        "referee",
        "official",
        "licence",
        "payment",
        "broker",
        "portfolio",
        "gnss",
        "rinex",
        "shipment",
    }
    assert names.isdisjoint(forbidden)


def test_upstream_world_state_is_optional_not_mandatory():
    s = DomainStateRefV0(
        domain_id="administration",
        state_ref="case:1",
        valid_at="2026-10-06T20:00:00Z",
    )
    p = domain_state_to_governance_payload(s)
    assert s.upstream_state_ref is None
    assert p.upstream_state_ref is None
