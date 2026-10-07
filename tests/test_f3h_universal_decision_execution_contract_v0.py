import hashlib
import os
import sys
from dataclasses import fields
from pathlib import Path

import pytest

from organizations.cssa.execution import build_action_proposal_v0
from organizations.cssa.execution.universal_bridge_v0 import (
    build_cssa_execution_surface_registry_v0,
    cssa_action_proposal_to_universal_v0,
)
from universal.execution import (
    EFFECT_COMMUNICATION,
    EFFECT_DATA_MUTATION,
    EFFECT_FINANCIAL,
    EFFECT_INTERNAL,
    EFFECT_PHYSICAL,
    ExecutionSurfaceRegistrationV0,
    UniversalActionProposalV0,
    UniversalExecutionContractError,
    UniversalExecutionSurfaceRegistryV0,
    assess_universal_execution_readiness_v0,
    build_universal_action_proposal_v0,
    build_universal_human_approval_v0,
    build_universal_provider_receipt_contract_v0,
    replay_universal_provider_receipt_v0,
    verify_universal_action_proposal_v0,
)


UPSTREAM = Path(os.environ["OBSIDIA_UPSTREAM_ROOT"]).resolve()
if str(UPSTREAM) not in sys.path:
    sys.path.insert(0, str(UPSTREAM))

from scripts.kernel.kx108_runtime_link_facts_v1 import runtime_link_facts  # noqa: E402


def h(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def registry():
    r = UniversalExecutionSurfaceRegistryV0()
    for item in (
        ExecutionSurfaceRegistrationV0(
            surface_id="MAIL",
            operation_ids=("DRAFT_NOTIFICATION",),
            effect_class=EFFECT_COMMUNICATION,
            connector_id="MAIL_CONNECTOR",
        ),
        ExecutionSurfaceRegistrationV0(
            surface_id="CALENDAR",
            operation_ids=("PROPOSE_UPDATE_EVENT",),
            effect_class=EFFECT_DATA_MUTATION,
            connector_id="CALENDAR_CONNECTOR",
        ),
        ExecutionSurfaceRegistrationV0(
            surface_id="CRM",
            operation_ids=("PROPOSE_UPDATE_RECORD",),
            effect_class=EFFECT_DATA_MUTATION,
            connector_id="CRM_CONNECTOR",
        ),
        ExecutionSurfaceRegistrationV0(
            surface_id="TASKS",
            operation_ids=("PROPOSE_CREATE_TASK",),
            effect_class=EFFECT_DATA_MUTATION,
            connector_id="TASK_CONNECTOR",
        ),
        ExecutionSurfaceRegistrationV0(
            surface_id="PAYMENT",
            operation_ids=("PROPOSE_PAYMENT",),
            effect_class=EFFECT_FINANCIAL,
            connector_id="PAYMENT_CONNECTOR",
        ),
        ExecutionSurfaceRegistrationV0(
            surface_id="DEVICE",
            operation_ids=("PROPOSE_DEVICE_COMMAND",),
            effect_class=EFFECT_PHYSICAL,
            connector_id="DEVICE_CONNECTOR",
        ),
        ExecutionSurfaceRegistrationV0(
            surface_id="LOCAL_WORK",
            operation_ids=("RUN_INTERNAL_ANALYSIS",),
            effect_class=EFFECT_INTERNAL,
            connector_id=None,
            requires_human_approval=False,
        ),
    ):
        r.register(item)
    return r


CASES = (
    ("administration", "MAIL", "DRAFT_NOTIFICATION"),
    ("trading", "TASKS", "PROPOSE_CREATE_TASK"),
    ("ecom", "CRM", "PROPOSE_UPDATE_RECORD"),
    ("gps_defense_aviation", "DEVICE", "PROPOSE_DEVICE_COMMAND"),
    ("logistics", "CALENDAR", "PROPOSE_UPDATE_EVENT"),
    ("finance_ops", "PAYMENT", "PROPOSE_PAYMENT"),
)


def universal_proposal(domain_id, surface_id, operation_id):
    return build_universal_action_proposal_v0(
        registry=registry(),
        proposal_id=f"proposal-{domain_id}",
        domain_id=domain_id,
        surface_id=surface_id,
        operation_id=operation_id,
        target_ref=f"target:{domain_id}:001",
        payload={"intent": "fixture-action", "domain_value": domain_id},
        source_case_refs=(f"case:{domain_id}:001",),
        evidence_refs=(f"evidence:{domain_id}:001",),
        expected_target_state_hash=h(f"state:{domain_id}:001"),
    )


@pytest.mark.parametrize("domain_id,surface_id,operation_id", CASES)
def test_same_universal_contract_accepts_many_business_domains(
    domain_id,
    surface_id,
    operation_id,
):
    p = universal_proposal(domain_id, surface_id, operation_id)

    assert p.domain_id == domain_id
    assert p.surface_id == surface_id
    assert p.operation_id == operation_id
    assert p.decision_authority == "KX108_ONLY"
    assert p.allowed_to_decide is False
    assert p.allowed_to_act is False
    assert p.emits_act is False
    assert verify_universal_action_proposal_v0(
        registry=registry(),
        proposal=p,
    ) == (True, None)


def test_universal_contract_has_no_business_specific_field_names():
    names = {f.name.lower() for f in fields(UniversalActionProposalV0)}
    forbidden = {
        "match",
        "ticket",
        "referee",
        "supplier",
        "portfolio",
        "broker",
        "rinex",
        "satellite",
        "shipment",
        "product",
    }
    assert names.isdisjoint(forbidden)


@pytest.mark.parametrize(
    "mutation",
    [
        {"decision_authority": "DOMAIN"},
        {"allowed_to_decide": True},
        {"allowed_to_act": True},
        {"emits_act": True},
        {"kernel_mutation": True},
        {"memory_write": True},
    ],
)
def test_surface_registration_cannot_grant_authority(mutation):
    kwargs = dict(
        surface_id="X",
        operation_ids=("OP",),
        effect_class=EFFECT_DATA_MUTATION,
        connector_id="X_CONNECTOR",
    )
    kwargs.update(mutation)
    with pytest.raises(UniversalExecutionContractError):
        ExecutionSurfaceRegistrationV0(**kwargs)


def test_external_surface_requires_connector_but_internal_surface_does_not():
    with pytest.raises(
        UniversalExecutionContractError,
        match="external surface requires connector_id",
    ):
        ExecutionSurfaceRegistrationV0(
            surface_id="EXTERNAL",
            operation_ids=("OP",),
            effect_class=EFFECT_COMMUNICATION,
            connector_id=None,
        )

    internal = ExecutionSurfaceRegistrationV0(
        surface_id="INTERNAL",
        operation_ids=("OP",),
        effect_class=EFFECT_INTERNAL,
        connector_id=None,
        requires_human_approval=False,
    )
    assert internal.connector_id is None


def test_unknown_surface_and_unknown_operation_fail_closed():
    with pytest.raises(
        UniversalExecutionContractError,
        match="UNREGISTERED_EXECUTION_SURFACE",
    ):
        build_universal_action_proposal_v0(
            registry=registry(),
            proposal_id="p",
            domain_id="new_domain",
            surface_id="UNKNOWN",
            operation_id="OP",
            target_ref="target",
            payload={},
            source_case_refs=("case",),
            evidence_refs=("evidence",),
            expected_target_state_hash=h("state"),
        )

    with pytest.raises(
        UniversalExecutionContractError,
        match="UNREGISTERED_SURFACE_OPERATION",
    ):
        build_universal_action_proposal_v0(
            registry=registry(),
            proposal_id="p",
            domain_id="new_domain",
            surface_id="MAIL",
            operation_id="SEND_WITHOUT_REGISTRATION",
            target_ref="target",
            payload={},
            source_case_refs=("case",),
            evidence_refs=("evidence",),
            expected_target_state_hash=h("state"),
        )


def test_human_approval_is_bound_to_exact_domain_proposal():
    admin = universal_proposal(
        "administration",
        "MAIL",
        "DRAFT_NOTIFICATION",
    )
    trading = universal_proposal(
        "trading",
        "TASKS",
        "PROPOSE_CREATE_TASK",
    )
    approval = build_universal_human_approval_v0(
        approval_id="approval-1",
        approved_by="HUMAN:REVIEWER",
        approval_reference="review:1",
        proposal=admin,
    )

    readiness = assess_universal_execution_readiness_v0(
        proposal=trading,
        approval=approval,
        current_target_state_hash=trading.expected_target_state_hash,
        kx108_gate="ALLOW",
        kx108_decision_record_verified=True,
        upstream_world_action_activated=False,
        upstream_missing_runtime_links=(),
    )
    assert readiness["status"] == "EXECUTION_NOT_READY"
    assert readiness["reason"] == "HUMAN_APPROVAL_PROPOSAL_ID_MISMATCH"


@pytest.mark.parametrize("domain_id,surface_id,operation_id", CASES)
def test_all_external_domains_fail_closed_on_real_upstream_world_action_blocker(
    domain_id,
    surface_id,
    operation_id,
):
    facts = runtime_link_facts()
    p = universal_proposal(domain_id, surface_id, operation_id)
    approval = build_universal_human_approval_v0(
        approval_id=f"approval-{domain_id}",
        approved_by="HUMAN:REVIEWER",
        approval_reference=f"review:{domain_id}",
        proposal=p,
    )

    readiness = assess_universal_execution_readiness_v0(
        proposal=p,
        approval=approval,
        current_target_state_hash=p.expected_target_state_hash,
        kx108_gate="ALLOW",
        kx108_decision_record_verified=True,
        upstream_world_action_activated=facts["world_action_runtime_activated"],
        upstream_missing_runtime_links=tuple(facts["missing_runtime_links"]),
    )

    assert readiness["status"] == "EXECUTION_NOT_READY"
    assert readiness["reason"] == "EXTERNAL_WORLD_ACTUATION_NOT_ACTIVATED"
    assert readiness["execution_performed"] is False


def test_internal_bounded_surface_can_be_ready_without_world_actuation():
    r = registry()
    p = build_universal_action_proposal_v0(
        registry=r,
        proposal_id="internal-analysis-1",
        domain_id="research",
        surface_id="LOCAL_WORK",
        operation_id="RUN_INTERNAL_ANALYSIS",
        target_ref="local:analysis:001",
        payload={"job": "analyze"},
        source_case_refs=("case:research:1",),
        evidence_refs=("evidence:research:1",),
        expected_target_state_hash=h("local-state"),
    )

    readiness = assess_universal_execution_readiness_v0(
        proposal=p,
        approval=None,
        current_target_state_hash=p.expected_target_state_hash,
        kx108_gate="ALLOW",
        kx108_decision_record_verified=True,
        upstream_world_action_activated=False,
        upstream_missing_runtime_links=(
            "EXTERNAL_WORLD_ACTUATION_NOT_ACTIVATED",
        ),
    )

    assert readiness["status"] == "READY_FOR_REGISTERED_EXECUTION_SURFACE"
    assert readiness["effect_class"] == EFFECT_INTERNAL
    assert readiness["execution_performed"] is False


def test_kx108_hold_and_unverified_record_fail_before_execution():
    p = universal_proposal(
        "administration",
        "MAIL",
        "DRAFT_NOTIFICATION",
    )
    approval = build_universal_human_approval_v0(
        approval_id="a",
        approved_by="HUMAN:REVIEWER",
        approval_reference="review:a",
        proposal=p,
    )

    hold = assess_universal_execution_readiness_v0(
        proposal=p,
        approval=approval,
        current_target_state_hash=p.expected_target_state_hash,
        kx108_gate="HOLD",
        kx108_decision_record_verified=True,
        upstream_world_action_activated=True,
        upstream_missing_runtime_links=(),
    )
    assert hold["reason"] == "KX108_NOT_ALLOW:HOLD"

    unverified = assess_universal_execution_readiness_v0(
        proposal=p,
        approval=approval,
        current_target_state_hash=p.expected_target_state_hash,
        kx108_gate="ALLOW",
        kx108_decision_record_verified=False,
        upstream_world_action_activated=True,
        upstream_missing_runtime_links=(),
    )
    assert unverified["reason"] == "KX108_DECISION_RECORD_NOT_VERIFIED"


def test_target_prestate_change_invalidates_approval_for_any_domain():
    p = universal_proposal(
        "ecom",
        "CRM",
        "PROPOSE_UPDATE_RECORD",
    )
    approval = build_universal_human_approval_v0(
        approval_id="a",
        approved_by="HUMAN:REVIEWER",
        approval_reference="review:a",
        proposal=p,
    )

    readiness = assess_universal_execution_readiness_v0(
        proposal=p,
        approval=approval,
        current_target_state_hash=h("changed-state"),
        kx108_gate="ALLOW",
        kx108_decision_record_verified=True,
        upstream_world_action_activated=True,
        upstream_missing_runtime_links=(),
    )
    assert readiness["reason"] == "TARGET_PRESTATE_HASH_MISMATCH"


def test_universal_receipt_contract_and_replay_work_for_any_domain():
    p = universal_proposal(
        "logistics",
        "CALENDAR",
        "PROPOSE_UPDATE_EVENT",
    )
    receipt = build_universal_provider_receipt_contract_v0(
        proposal=p,
        execution_call_hash=h("call"),
        provider_result_identity={
            "provider_id": "sim-provider",
            "result_id": "sim-result-1",
        },
        real_execution_proven=False,
    )

    replay = replay_universal_provider_receipt_v0(
        proposal=p,
        receipt=receipt,
    )
    assert replay["status"] == "PASS"
    assert replay["real_execution_proven"] is False


@pytest.mark.parametrize(
    "surface,operation",
    [
        ("MAIL", "DRAFT_NOTIFICATION"),
        ("CALENDAR", "PROPOSE_UPDATE_EVENT"),
        ("CRM", "PROPOSE_UPDATE_RECORD"),
        ("TASKS", "PROPOSE_CREATE_TASK"),
    ],
)
def test_cssa_existing_action_proposals_map_losslessly_to_universal(
    surface,
    operation,
):
    cssa = build_action_proposal_v0(
        proposal_id=f"cssa-{surface}",
        surface=surface,
        operation=operation,
        target_ref=f"sim:{surface.lower()}:1",
        payload={"fixture": surface},
        source_case_refs=("cssa:case:1",),
        evidence_refs=("cssa:evidence:1",),
        expected_target_state_hash=h(f"cssa:{surface}:state"),
    )
    r, universal = cssa_action_proposal_to_universal_v0(cssa)

    assert universal.domain_id == "administration"
    assert universal.proposal_id == cssa.proposal_id
    assert universal.surface_id == cssa.surface
    assert universal.operation_id == cssa.operation
    assert universal.target_ref == cssa.target_ref
    assert universal.payload == cssa.payload
    assert universal.source_case_refs == cssa.source_case_refs
    assert universal.evidence_refs == cssa.evidence_refs
    assert universal.expected_target_state_hash == cssa.expected_target_state_hash
    assert verify_universal_action_proposal_v0(
        registry=r,
        proposal=universal,
    ) == (True, None)


def test_cssa_bridge_registry_is_non_sovereign():
    r = build_cssa_execution_surface_registry_v0()
    assert r.surfaces() == ("CALENDAR", "CRM", "MAIL", "TASKS")
    for surface_id in r.surfaces():
        item = r.get(surface_id)
        assert item.decision_authority == "KX108_ONLY"
        assert item.allowed_to_decide is False
        assert item.allowed_to_act is False
        assert item.emits_act is False
