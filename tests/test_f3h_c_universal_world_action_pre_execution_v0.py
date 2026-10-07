import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

from organizations.cssa.execution import build_action_proposal_v0
from organizations.cssa.execution.mail_governed_execution_v0 import (
    build_mail_send_plan_v0,
)
from organizations.cssa.execution.world_action_bridge_v0 import (
    build_cssa_mail_world_action_request_v0,
)
from universal.execution import (
    ARC_EXTERNAL_API,
    ARC_FINANCIAL,
    ARC_IRREVERSIBLE,
    ARC_SENSITIVE,
    CANONICAL_WORLD_BLOCKER,
    EFFECT_COMMUNICATION,
    EFFECT_DATA_MUTATION,
    EFFECT_FINANCIAL,
    EFFECT_PHYSICAL,
    ExecutionSurfaceRegistrationV0,
    OUTCOME_CONFIRMED,
    OUTCOME_UNKNOWN,
    PRE_EXECUTION_BLOCKED,
    PRE_EXECUTION_READY,
    RETRY_IDEMPOTENT_AFTER_RECONCILIATION,
    RETRY_NEVER_ON_UNKNOWN,
    UniversalExecutionContractError,
    UniversalExecutionSurfaceRegistryV0,
    WCC_CRITICAL,
    WCC_IRREVERSIBLE,
    WCC_REVERSIBLE,
    WORLD_ACTION_PRE_PHASE,
    WorldActionOperationPolicyV0,
    WorldActionPolicyRegistryV0,
    assess_prior_attempts_v0,
    assess_world_action_pre_execution_v0,
    build_provider_outcome_v0,
    build_universal_action_proposal_v0,
    build_world_action_human_approval_v0,
    build_world_action_pre_context_v0,
    build_world_action_request_v0,
    canonical_sha256_v0,
    legacy_dry_run_ticket_input_v0,
    legacy_world_action_event_input_v0,
    replay_world_action_receipt_v0,
    verify_world_action_human_approval_v0,
    verify_world_action_pre_evidence_v0,
)

UPSTREAM = Path(os.environ["OBSIDIA_UPSTREAM_ROOT"]).resolve()
if str(UPSTREAM) not in sys.path:
    sys.path.insert(0, str(UPSTREAM))

from scripts.kernel.kx108_runtime_link_facts_v1 import runtime_link_facts  # noqa: E402
from periphery.world_calls.sovereign_ticket import issue_sovereign_ticket  # noqa: E402
from periphery.world_calls.obsidia_gateway import ObsidiaGateway  # noqa: E402
from periphery.world_calls.world_call_classifier import WorldCallClass  # noqa: E402
from periphery.world_calls.world_action_bus import publish_event  # noqa: E402
from periphery.world_calls.world_executor_dryrun import execute_dry_run  # noqa: E402


def h(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def surface_registry():
    r = UniversalExecutionSurfaceRegistryV0()
    specs = (
        ("MAIL", ("DRAFT_NOTIFICATION",), EFFECT_COMMUNICATION, "GMAIL"),
        (
            "CALENDAR",
            ("PROPOSE_UPDATE_EVENT",),
            EFFECT_DATA_MUTATION,
            "CALENDAR_CONNECTOR",
        ),
        (
            "CRM",
            ("PROPOSE_UPDATE_RECORD",),
            EFFECT_DATA_MUTATION,
            "CRM_CONNECTOR",
        ),
        (
            "TASKS",
            ("PROPOSE_CREATE_TASK",),
            EFFECT_DATA_MUTATION,
            "TASK_CONNECTOR",
        ),
        (
            "PAYMENT",
            ("PROPOSE_PAYMENT",),
            EFFECT_FINANCIAL,
            "PAYMENT_CONNECTOR",
        ),
        (
            "DEVICE",
            ("PROPOSE_DEVICE_COMMAND",),
            EFFECT_PHYSICAL,
            "DEVICE_CONNECTOR",
        ),
    )
    for surface_id, operations, effect_class, connector_id in specs:
        r.register(
            ExecutionSurfaceRegistrationV0(
                surface_id=surface_id,
                operation_ids=operations,
                effect_class=effect_class,
                connector_id=connector_id,
                requires_human_approval=True,
            )
        )
    return r


def policy_registry(r):
    p = WorldActionPolicyRegistryV0(surface_registry=r)
    policies = (
        WorldActionOperationPolicyV0(
            surface_id="MAIL",
            operation_id="DRAFT_NOTIFICATION",
            connector_id="GMAIL",
            connector_action="SEND_EMAIL",
            required_scope="gmail:send",
            world_call_class=WCC_IRREVERSIBLE,
            action_risk_class=ARC_IRREVERSIBLE,
            autonomy_level=5,
            retry_policy=RETRY_NEVER_ON_UNKNOWN,
            irreversible=True,
        ),
        WorldActionOperationPolicyV0(
            surface_id="CALENDAR",
            operation_id="PROPOSE_UPDATE_EVENT",
            connector_id="CALENDAR_CONNECTOR",
            connector_action="UPDATE_EVENT",
            required_scope="calendar:write",
            world_call_class=WCC_REVERSIBLE,
            action_risk_class=ARC_EXTERNAL_API,
            autonomy_level=4,
            retry_policy=RETRY_IDEMPOTENT_AFTER_RECONCILIATION,
            irreversible=False,
        ),
        WorldActionOperationPolicyV0(
            surface_id="CRM",
            operation_id="PROPOSE_UPDATE_RECORD",
            connector_id="CRM_CONNECTOR",
            connector_action="UPDATE_RECORD",
            required_scope="crm:write",
            world_call_class=WCC_REVERSIBLE,
            action_risk_class=ARC_EXTERNAL_API,
            autonomy_level=4,
            retry_policy=RETRY_IDEMPOTENT_AFTER_RECONCILIATION,
            irreversible=False,
        ),
        WorldActionOperationPolicyV0(
            surface_id="TASKS",
            operation_id="PROPOSE_CREATE_TASK",
            connector_id="TASK_CONNECTOR",
            connector_action="CREATE_TASK",
            required_scope="tasks:write",
            world_call_class=WCC_REVERSIBLE,
            action_risk_class=ARC_EXTERNAL_API,
            autonomy_level=4,
            retry_policy=RETRY_IDEMPOTENT_AFTER_RECONCILIATION,
            irreversible=False,
        ),
        WorldActionOperationPolicyV0(
            surface_id="PAYMENT",
            operation_id="PROPOSE_PAYMENT",
            connector_id="PAYMENT_CONNECTOR",
            connector_action="EXECUTE_PAYMENT",
            required_scope="payments:execute",
            world_call_class=WCC_IRREVERSIBLE,
            action_risk_class=ARC_FINANCIAL,
            autonomy_level=5,
            retry_policy=RETRY_NEVER_ON_UNKNOWN,
            irreversible=True,
        ),
        WorldActionOperationPolicyV0(
            surface_id="DEVICE",
            operation_id="PROPOSE_DEVICE_COMMAND",
            connector_id="DEVICE_CONNECTOR",
            connector_action="EXECUTE_DEVICE_COMMAND",
            required_scope="device:control",
            world_call_class=WCC_CRITICAL,
            action_risk_class=ARC_SENSITIVE,
            autonomy_level=5,
            retry_policy=RETRY_NEVER_ON_UNKNOWN,
            irreversible=False,
        ),
    )
    for item in policies:
        p.register(item)
    return p


CASES = (
    (
        "administration",
        "MAIL",
        "DRAFT_NOTIFICATION",
        "SEND_EMAIL",
        {"to": "supporter@example.invalid", "body": "Info match"},
    ),
    (
        "logistics",
        "CALENDAR",
        "PROPOSE_UPDATE_EVENT",
        "UPDATE_EVENT",
        {"event_id": "evt-1", "start": "2026-10-08T18:00:00+02:00"},
    ),
    (
        "ecom",
        "CRM",
        "PROPOSE_UPDATE_RECORD",
        "UPDATE_RECORD",
        {"record_id": "cust-1", "status": "confirmed"},
    ),
    (
        "trading",
        "TASKS",
        "PROPOSE_CREATE_TASK",
        "CREATE_TASK",
        {"title": "Review risk", "owner": "risk"},
    ),
    (
        "finance_ops",
        "PAYMENT",
        "PROPOSE_PAYMENT",
        "EXECUTE_PAYMENT",
        {"payment_ref": "pay-1", "amount_minor": 1000, "currency": "EUR"},
    ),
    (
        "gps_defense_aviation",
        "DEVICE",
        "PROPOSE_DEVICE_COMMAND",
        "EXECUTE_DEVICE_COMMAND",
        {"device_ref": "sim-device", "command": "fixture-command"},
    ),
)


def proposal_for(domain_id, surface_id, operation_id):
    r = surface_registry()
    return build_universal_action_proposal_v0(
        registry=r,
        proposal_id=f"proposal-{domain_id}",
        domain_id=domain_id,
        surface_id=surface_id,
        operation_id=operation_id,
        target_ref=f"target:{domain_id}:001",
        payload={"intent": "fixture"},
        source_case_refs=(f"case:{domain_id}:001",),
        evidence_refs=(f"evidence:{domain_id}:001",),
        expected_target_state_hash=h(f"state:{domain_id}:001"),
    )


def request_for(domain_id, surface_id, operation_id, connector_action, args):
    r = surface_registry()
    policies = policy_registry(r)
    proposal = build_universal_action_proposal_v0(
        registry=r,
        proposal_id=f"proposal-{domain_id}",
        domain_id=domain_id,
        surface_id=surface_id,
        operation_id=operation_id,
        target_ref=f"target:{domain_id}:001",
        payload={"intent": "fixture"},
        source_case_refs=(f"case:{domain_id}:001",),
        evidence_refs=(f"evidence:{domain_id}:001",),
        expected_target_state_hash=h(f"state:{domain_id}:001"),
    )
    request = build_world_action_request_v0(
        surface_registry=r,
        policy_registry=policies,
        proposal=proposal,
        request_id=f"world-action-{domain_id}",
        connector_action=connector_action,
        connector_args=args,
        current_target_state_hash=proposal.expected_target_state_hash,
    )
    return r, policies, proposal, request


def approval_for(request):
    return build_world_action_human_approval_v0(
        approval_id=f"approval-{request.request_id}",
        approved_by="HUMAN:REVIEWER",
        approval_reference=f"review:{request.request_id}",
        request=request,
    )


def synthetic_pre_evidence(request, approval):
    data = {
        "schema": "UNIVERSAL_WORLD_ACTION_PRE_EVIDENCE_V0",
        "decision_phase": WORLD_ACTION_PRE_PHASE,
        "decision_authority": "KX108_ONLY",
        "x108_gate": "ALLOW",
        "proposal_hash": request.proposal_hash,
        "world_action_request_hash": request.request_hash,
        "connector_call_hash": request.connector_call_hash,
        "target_prestate_hash": request.target_prestate_hash,
        "world_action_approval_hash": approval["approval_hash"],
        "required_scope": request.required_scope,
        "world_call_class": request.world_call_class,
        "action_risk_class": request.action_risk_class,
        "autonomy_level": request.autonomy_level,
        "idempotency_key": request.idempotency_key,
        "decision_record_id": "sim-world-pre-decision",
        "decision_record_hash": h("sim-world-pre-decision"),
        "sovereign_ticket_id": "sim-live-ticket",
        "dry_run_only": False,
        "egress_allowed": True,
    }
    data["evidence_hash"] = canonical_sha256_v0(data)
    return data


def synthetic_activated_runtime():
    return {
        "decision_authority": "KX108_ONLY",
        "world_action_runtime_activated": True,
        "missing_runtime_links": (),
    }


@pytest.mark.parametrize(
    "domain_id,surface_id,operation_id,connector_action,args",
    CASES,
)
def test_same_world_action_rail_builds_exact_requests_across_domains(
    domain_id,
    surface_id,
    operation_id,
    connector_action,
    args,
):
    _, _, proposal, request = request_for(
        domain_id,
        surface_id,
        operation_id,
        connector_action,
        args,
    )
    request.assert_non_sovereign()
    assert request.domain_id == domain_id
    assert request.proposal_hash == proposal.proposal_hash
    assert request.connector_action == connector_action
    assert len(request.connector_call_hash) == 64
    assert len(request.idempotency_key) == 64
    assert len(request.request_hash) == 64
    assert request.allowed_to_act is False


def test_exact_world_action_human_approval_changes_with_connector_args():
    _, _, _, first = request_for(*CASES[0])
    changed_case = list(CASES[0])
    changed_case[4] = {"to": "other@example.invalid", "body": "Info match"}
    _, _, _, second = request_for(*changed_case)

    assert first.request_hash != second.request_hash
    assert first.connector_call_hash != second.connector_call_hash
    assert approval_for(first)["approval_hash"] != approval_for(second)["approval_hash"]


def test_tampered_world_action_approval_fails():
    _, _, _, request = request_for(*CASES[1])
    approval = approval_for(request)
    approval["connector_call_hash"] = h("tampered")

    ok, reason = verify_world_action_human_approval_v0(
        approval=approval,
        request=request,
    )
    assert ok is False
    assert reason == "WORLD_ACTION_HUMAN_APPROVAL_CONNECTOR_CALL_HASH_MISMATCH"


def test_secret_fields_are_rejected_before_world_action_request_exists():
    r = surface_registry()
    p = policy_registry(r)
    proposal = proposal_for("administration", "MAIL", "DRAFT_NOTIFICATION")

    with pytest.raises(
        UniversalExecutionContractError,
        match="SECRET_FIELD_FORBIDDEN_IN_ACTION_PAYLOAD",
    ):
        build_world_action_request_v0(
            surface_registry=r,
            policy_registry=p,
            proposal=proposal,
            request_id="secret-test",
            connector_action="SEND_EMAIL",
            connector_args={
                "to": "x@example.invalid",
                "authorization_token": "must-never-enter-action-payload",
            },
            current_target_state_hash=proposal.expected_target_state_hash,
        )


def test_target_state_drift_rejects_before_request_binding():
    r = surface_registry()
    p = policy_registry(r)
    proposal = proposal_for("ecom", "CRM", "PROPOSE_UPDATE_RECORD")

    with pytest.raises(
        UniversalExecutionContractError,
        match="TARGET_PRESTATE_HASH_MISMATCH",
    ):
        build_world_action_request_v0(
            surface_registry=r,
            policy_registry=p,
            proposal=proposal,
            request_id="drift-test",
            connector_action="UPDATE_RECORD",
            connector_args={"record_id": "cust-1"},
            current_target_state_hash=h("changed-state"),
        )


def test_pre_context_binds_exact_human_approval_and_request():
    _, _, _, request = request_for(*CASES[2])
    approval = approval_for(request)
    context = build_world_action_pre_context_v0(
        request,
        valid_at="2026-10-07T10:46:00+02:00",
        evidence_refs=("evidence:crm:001",),
        world_action_approval=approval,
    )

    assert context["decision_phase"] == WORLD_ACTION_PRE_PHASE
    assert context["world_action_request_hash"] == request.request_hash
    assert context["connector_call_hash"] == request.connector_call_hash
    assert context["world_action_approval_hash"] == approval["approval_hash"]
    assert context["allowed_to_act"] is False


def test_current_real_upstream_blocks_external_world_action_before_pre_evidence():
    _, _, _, request = request_for(*CASES[0])
    approval = approval_for(request)

    result = assess_world_action_pre_execution_v0(
        request=request,
        runtime_link_facts=runtime_link_facts(),
        pre_evidence=None,
        world_action_approval=approval,
    )

    assert result["status"] == PRE_EXECUTION_BLOCKED
    assert result["reason"] == CANONICAL_WORLD_BLOCKER
    assert result["execution_performed"] is False


def test_critical_world_action_class_is_blocked_even_if_runtime_claims_active():
    _, _, _, request = request_for(*CASES[5])
    approval = approval_for(request)
    pre = synthetic_pre_evidence(request, approval)

    result = assess_world_action_pre_execution_v0(
        request=request,
        runtime_link_facts=synthetic_activated_runtime(),
        pre_evidence=pre,
        world_action_approval=approval,
    )

    assert result["status"] == PRE_EXECUTION_BLOCKED
    assert result["reason"] == "WORLD_ACTION_POLICY_CLASS_BLOCKED"


def test_future_pre_evidence_contract_can_be_verified_without_executing():
    _, _, _, request = request_for(*CASES[1])
    approval = approval_for(request)
    pre = synthetic_pre_evidence(request, approval)

    assert verify_world_action_pre_evidence_v0(
        pre,
        request=request,
        world_action_approval=approval,
    ) == (True, None)

    ready = assess_world_action_pre_execution_v0(
        request=request,
        runtime_link_facts=synthetic_activated_runtime(),
        pre_evidence=pre,
        world_action_approval=approval,
    )

    assert ready["status"] == PRE_EXECUTION_READY
    assert ready["execution_performed"] is False
    assert ready["sovereign_ticket_id"] == "sim-live-ticket"


def test_wrong_exact_approval_invalidates_future_pre_evidence():
    _, _, _, request = request_for(*CASES[1])
    approval = approval_for(request)
    pre = synthetic_pre_evidence(request, approval)
    approval["approval_reference"] = "tampered-reference"

    ok, reason = verify_world_action_pre_evidence_v0(
        pre,
        request=request,
        world_action_approval=approval,
    )
    assert ok is False
    assert reason == "WORLD_ACTION_HUMAN_APPROVAL_HASH_MISMATCH"


def test_current_upstream_sovereign_ticket_and_gateway_remain_dry_run_only():
    _, _, _, request = request_for(*CASES[1])
    ticket_input = legacy_dry_run_ticket_input_v0(
        request,
        os3_ticket_id="sim-os3-ticket",
    )
    ticket = issue_sovereign_ticket(**ticket_input)

    assert ticket.dry_run_only is True
    assert ticket.scope == request.required_scope
    assert ticket.x108_gate == "ALLOW"

    decision = ObsidiaGateway().check(
        ticket,
        WorldCallClass(request.world_call_class),
        request.required_scope,
        agent_payload={"request_hash": request.request_hash},
    )
    assert decision.gate_result == "DRY_RUN_PASS"
    assert decision.dry_run_only is True
    assert decision.egress_allowed is False

    dry = execute_dry_run(request.request_id, decision)
    assert dry.simulated is True
    assert dry.executed is False


def test_current_upstream_gateway_blocks_wrong_scope():
    _, _, _, request = request_for(*CASES[2])
    ticket = issue_sovereign_ticket(
        **legacy_dry_run_ticket_input_v0(
            request,
            os3_ticket_id="sim-os3-ticket",
        )
    )
    decision = ObsidiaGateway().check(
        ticket,
        WorldCallClass(request.world_call_class),
        "wrong:scope",
        agent_payload={"request_hash": request.request_hash},
    )
    assert decision.gate_result == "BLOCK"
    assert decision.egress_allowed is False


def test_world_action_bus_bridge_is_append_only_dry_run_journal(tmp_path):
    _, _, _, request = request_for(*CASES[3])
    event_input = legacy_world_action_event_input_v0(
        request,
        sovereign_ticket_id="sim-ticket",
        blocked=True,
        block_reason=CANONICAL_WORLD_BLOCKER,
    )
    bus = tmp_path / "world_action_bus.jsonl"

    first = publish_event(**event_input, bus_path=str(bus))
    second = publish_event(**event_input, bus_path=str(bus))

    assert first.event_id != second.event_id
    assert first.dry_run_only is True
    assert first.blocked is True
    lines = bus.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert all(json.loads(line)["dry_run_only"] is True for line in lines)


def test_provider_receipt_requires_pre_execution_ready():
    _, _, _, request = request_for(*CASES[1])

    with pytest.raises(
        UniversalExecutionContractError,
        match="PRE_EXECUTION_READY_EVIDENCE_REQUIRED",
    ):
        build_provider_outcome_v0(
            request=request,
            pre_execution_ready=None,
            provider_result_identity={"event_id": "evt-provider-1"},
        )


def test_confirmed_provider_outcome_receipt_replays_and_blocks_duplicate():
    _, _, _, request = request_for(*CASES[1])
    approval = approval_for(request)
    pre = synthetic_pre_evidence(request, approval)
    ready = assess_world_action_pre_execution_v0(
        request=request,
        runtime_link_facts=synthetic_activated_runtime(),
        pre_evidence=pre,
        world_action_approval=approval,
    )

    receipt = build_provider_outcome_v0(
        request=request,
        pre_execution_ready=ready,
        provider_result_identity={"event_id": "provider-event-1"},
    )
    assert receipt["status"] == OUTCOME_CONFIRMED
    assert receipt["real_execution_proven"] is True

    replay = replay_world_action_receipt_v0(
        request=request,
        receipt=receipt,
    )
    assert replay["status"] == "PASS"
    assert replay["resend_required"] is False

    prior = assess_prior_attempts_v0(
        request=request,
        prior_attempts=(receipt,),
    )
    assert prior["status"] == "ALREADY_EXECUTED"
    assert prior["reason"] == "CONFIRMED_DUPLICATE_EXECUTION_BLOCKED"


def test_unknown_provider_outcome_never_auto_retries_and_blocks_next_attempt():
    _, _, _, request = request_for(*CASES[2])
    approval = approval_for(request)
    ready = assess_world_action_pre_execution_v0(
        request=request,
        runtime_link_facts=synthetic_activated_runtime(),
        pre_evidence=synthetic_pre_evidence(request, approval),
        world_action_approval=approval,
    )
    unknown = build_provider_outcome_v0(
        request=request,
        pre_execution_ready=ready,
        exception_class="TimeoutError",
    )

    assert unknown["status"] == OUTCOME_UNKNOWN
    assert unknown["automatic_retry_allowed"] is False
    assert unknown["requires_provider_reconciliation"] is True

    next_attempt = assess_world_action_pre_execution_v0(
        request=request,
        runtime_link_facts=synthetic_activated_runtime(),
        pre_evidence=synthetic_pre_evidence(request, approval),
        world_action_approval=approval,
        prior_attempts=(unknown,),
    )
    assert next_attempt["status"] == PRE_EXECUTION_BLOCKED
    assert next_attempt["reason"] == "UNKNOWN_PRIOR_OUTCOME_BLOCKS_RETRY"


def test_explicit_no_effect_retry_policy_differs_for_idempotent_and_irreversible():
    _, _, _, calendar = request_for(*CASES[1])
    calendar_approval = approval_for(calendar)
    calendar_ready = assess_world_action_pre_execution_v0(
        request=calendar,
        runtime_link_facts=synthetic_activated_runtime(),
        pre_evidence=synthetic_pre_evidence(calendar, calendar_approval),
        world_action_approval=calendar_approval,
    )
    no_effect_calendar = build_provider_outcome_v0(
        request=calendar,
        pre_execution_ready=calendar_ready,
        explicit_no_effect=True,
    )
    assert no_effect_calendar["automatic_retry_allowed"] is True

    _, _, _, mail = request_for(*CASES[0])
    mail_approval = approval_for(mail)
    mail_ready = assess_world_action_pre_execution_v0(
        request=mail,
        runtime_link_facts=synthetic_activated_runtime(),
        pre_evidence=synthetic_pre_evidence(mail, mail_approval),
        world_action_approval=mail_approval,
    )
    no_effect_mail = build_provider_outcome_v0(
        request=mail,
        pre_execution_ready=mail_ready,
        explicit_no_effect=True,
    )
    assert no_effect_mail["automatic_retry_allowed"] is False


def test_tampered_real_receipt_fails_replay():
    _, _, _, request = request_for(*CASES[1])
    approval = approval_for(request)
    ready = assess_world_action_pre_execution_v0(
        request=request,
        runtime_link_facts=synthetic_activated_runtime(),
        pre_evidence=synthetic_pre_evidence(request, approval),
        world_action_approval=approval,
    )
    receipt = build_provider_outcome_v0(
        request=request,
        pre_execution_ready=ready,
        provider_result_identity={"event_id": "provider-event-1"},
    )
    receipt["provider_result_identity"] = {"event_id": "tampered"}

    replay = replay_world_action_receipt_v0(
        request=request,
        receipt=receipt,
    )
    assert replay["status"] == "FAIL"
    assert replay["reason"] == "WORLD_ACTION_RECEIPT_HASH_MISMATCH"


def test_cssa_mail_uses_same_universal_world_action_rail_and_stays_blocked():
    cssa_proposal = build_action_proposal_v0(
        proposal_id="cssa-mail-proposal",
        surface="MAIL",
        operation="DRAFT_NOTIFICATION",
        target_ref="sim:mail-thread:001",
        payload={"class": "MATCHDAY_INFORMATION"},
        source_case_refs=("cssa:matchday:001",),
        evidence_refs=("cssa:fixture-proof:001",),
        expected_target_state_hash=h("cssa-mail-state"),
    )
    mail_plan = build_mail_send_plan_v0(
        proposal=cssa_proposal,
        plan_id="cssa-mail-plan",
        to=("supporter@example.invalid",),
        subject="Informations CSSA",
        body="Coup d'envoi confirme.",
        reply_message_id=None,
        sender_mailbox_ref="sim:cssa-mailbox",
        expected_target_state_hash=cssa_proposal.expected_target_state_hash,
        source_evidence_refs=("cssa:fixture-proof:001",),
    )
    _, _, universal_proposal, request = (
        build_cssa_mail_world_action_request_v0(
            proposal=cssa_proposal,
            plan=mail_plan,
            request_id="cssa-world-mail-001",
            current_target_state_hash=mail_plan.expected_target_state_hash,
        )
    )
    approval = approval_for(request)

    assert universal_proposal.domain_id == "administration"
    assert request.connector_id == "GMAIL"
    assert request.connector_action == "SEND_EMAIL"
    assert request.world_call_class == WCC_IRREVERSIBLE
    assert request.autonomy_level == 5

    result = assess_world_action_pre_execution_v0(
        request=request,
        runtime_link_facts=runtime_link_facts(),
        pre_evidence=None,
        world_action_approval=approval,
    )
    assert result["status"] == PRE_EXECUTION_BLOCKED
    assert result["reason"] == CANONICAL_WORLD_BLOCKER
