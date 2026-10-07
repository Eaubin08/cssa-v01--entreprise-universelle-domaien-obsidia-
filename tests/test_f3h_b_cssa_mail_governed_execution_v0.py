import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

from organizations.cssa.execution import build_action_proposal_v0
from organizations.cssa.execution.mail_governed_execution_v0 import (
    MAIL_PREPARED,
    MAIL_REPLAY_PASS,
    MAIL_SEND_RECORDED,
    OUTCOME_UNKNOWN,
    REJECTED,
    build_mail_human_approval_v0,
    build_mail_kx108_pre_evidence_v0,
    build_mail_send_plan_v0,
    build_mailbox_authority_evidence_v0,
    mail_pre_execution_runtime_state_v0,
    prepare_mail_connector_call_v0,
    record_mail_connector_exception_v0,
    record_mail_connector_success_v0,
    replay_mail_receipt_v0,
    verify_mail_send_plan_v0,
)
from organizations.cssa.public_admin_v0 import cssa_public_case_adapter
from universal.registry.portable_v0 import (
    PortableDomainRegistrationV0,
    PortableDomainRegistryV0,
)
from universal.runtime.resolver_v0 import (
    CanonicalCompatibleResolverV0,
    PortableRuntimeBindingV0,
)


ROOT = Path(__file__).resolve().parents[1]
CALIBRATION = (
    ROOT / "organizations" / "cssa" / "execution"
    / "mail_live_calibration_v0.json"
)
PROGRESS = (
    ROOT / "organizations" / "cssa" / "execution"
    / "f3h_b_mail_execution_progress_v0.json"
)

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
VALID_AT = "2026-10-07T10:00:00+02:00"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def h(seed):
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def proposal():
    return build_action_proposal_v0(
        proposal_id="MAIL_PROP_001",
        surface="MAIL",
        operation="DRAFT_NOTIFICATION",
        target_ref="sim:mail-thread:001",
        payload={
            "message_class": "MATCHDAY_INFORMATION",
            "audience": "supporter",
            "language": "fr",
        },
        source_case_refs=("sim:matchday-case:001",),
        evidence_refs=("sim:fixture-proof:001",),
        expected_target_state_hash=h("mail-thread-state-001"),
    )


def plan(*, body="Coup d'envoi confirmé à 18h30.", mailbox_ref="sim:cssa-mailbox"):
    p = proposal()
    return build_mail_send_plan_v0(
        proposal=p,
        plan_id="MAIL_PLAN_001",
        to=("supporter@example.invalid",),
        subject="Informations match CSSA",
        body=body,
        reply_message_id=None,
        sender_mailbox_ref=mailbox_ref,
        expected_target_state_hash=p.expected_target_state_hash,
        source_evidence_refs=("sim:fixture-proof:001",),
    )


def approval(mail_plan):
    return build_mail_human_approval_v0(
        approval_id="MAIL_APPROVAL_001",
        approved_by="HUMAN:CSSA_REVIEWER",
        approval_reference="sim:human-review:mail:001",
        plan=mail_plan,
    )


def cssa_mailbox(mail_plan):
    return build_mailbox_authority_evidence_v0(
        mailbox_ref=mail_plan.sender_mailbox_ref,
        mailbox_role="CSSA_OPERATIONAL_MAILBOX",
        connector_account_ref="sim:gmail-account:cssa",
        cssa_operational_authority_ref="sim:cssa-mail-authority:001",
        account_verified_for_cssa=True,
    )


def personal_mailbox(mail_plan):
    return build_mailbox_authority_evidence_v0(
        mailbox_ref=mail_plan.sender_mailbox_ref,
        mailbox_role="PERSONAL_USER_MAILBOX",
        connector_account_ref="sim:gmail-account:personal",
        cssa_operational_authority_ref=None,
        account_verified_for_cssa=False,
    )


def make_resolver():
    registry = PortableDomainRegistryV0()
    registry.register(
        PortableDomainRegistrationV0(
            domain_id="administration",
            adapter_id="cssa.mail.pre-execution.v0",
            schema_ref=(
                "organizations/cssa/execution/"
                "mail_governed_execution_v0.py"
            ),
            capabilities=("read", "classify", "propose", "pre_execute"),
        ),
        cssa_public_case_adapter,
    )
    resolver = CanonicalCompatibleResolverV0(
        source_root=UPSTREAM,
        registry=registry,
    )
    resolver.bind_portable_runtime(
        PortableRuntimeBindingV0(
            domain_id="administration",
            confidence_provider_id="cssa.mail.pre-execution.confidence.v0",
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
            "runtime_id": "cssa-mail-pre-execution-proof",
            "provider": "cssa_mail_pre_execution",
            "external_action": False,
        }


def run_kx108_pre(
    tmp_path,
    mail_plan,
    *,
    current_state_hash=None,
    unknowns=(),
    contradictions=(),
):
    current_state_hash = (
        current_state_hash or mail_plan.expected_target_state_hash
    )
    raw = mail_pre_execution_runtime_state_v0(
        mail_plan,
        valid_at=VALID_AT,
        current_target_state_hash=current_state_hash,
        confidence=1.0,
        unknowns=tuple(unknowns),
        contradictions=tuple(contradictions),
    )

    flow = CanonicalRuntimeReceiptFlow()
    provider = CountingProvider()
    flow.register_provider("cssa_mail_pre_execution", provider)

    action = ActionCandidate(
        action_id=f"mail-pre-{mail_plan.plan_id}",
        domain="administration",
        actor_id="f3h-b",
        intent="pre_execute_exact_mail_plan",
        action_type="analysis",
        irreversible=False,
        timestamp_plan="",
        payload={
            "freshness_score": 1.0,
            "source_count": len(mail_plan.source_evidence_refs),
            "clean_json_ready": True,
            "critical": False,
            "mail_plan_hash": mail_plan.plan_hash,
            "mail_pre_execution_binding_hash":
                raw["mail_pre_execution_binding_hash"],
        },
    )

    result = upstream_runtime.run_governed_runtime_cycle(
        AGENT_ID,
        action,
        raw,
        execution_surface=flow,
        mission_id=f"mission-mail-pre-{mail_plan.plan_id}",
        provider_id="cssa_mail_pre_execution",
        capability="analysis",
        execution_payload={
            "mode": "MAIL_WORLD_ACTION_PRE_EXECUTION",
            "mail_plan_hash": mail_plan.plan_hash,
            "mail_pre_execution_binding_hash":
                raw["mail_pre_execution_binding_hash"],
            "external_action": False,
        },
        agent_context_store_dir=tmp_path / "contexts",
        decision_store_dir=tmp_path / "decisions",
        domain_extension_resolver=make_resolver(),
    )
    return result, provider, raw["mail_pre_execution_binding_hash"]


def prepared_call(tmp_path, mail_plan=None, mailbox=None):
    mail_plan = mail_plan or plan()
    result, _, binding_hash = run_kx108_pre(tmp_path, mail_plan)
    pre = build_mail_kx108_pre_evidence_v0(
        plan=mail_plan,
        runtime_result=result,
        expected_binding_hash=binding_hash,
    )
    return prepare_mail_connector_call_v0(
        proposal=proposal(),
        plan=mail_plan,
        human_approval=approval(mail_plan),
        mailbox_authority=mailbox or cssa_mailbox(mail_plan),
        kx108_pre_evidence=pre,
        current_target_state_hash=mail_plan.expected_target_state_hash,
        expected_binding_hash=binding_hash,
    )


def test_live_calibration_is_privacy_safe_and_does_not_claim_sender_access():
    data = load(CALIBRATION)

    assert data["status"] == (
        "PRIVATE_READONLY_PATTERN_CALIBRATION_NO_MESSAGE_CONTENT_PERSISTED"
    )
    assert {row["class"] for row in data["observed_message_classes"]} == {
        "CLUB_MATCHDAY_INFORMATION",
        "TICKETING_TRANSACTION_CONFIRMATION",
        "EVENT_MARKETING_CAMPAIGN",
    }
    assert data["execution_boundary"][
        "cssa_operational_sender_mailbox_verified"
    ] is False
    assert data["execution_boundary"]["real_send_permitted_now"] is False
    assert data["privacy_boundary"]["gmail_message_ids_persisted"] is False
    assert data["privacy_boundary"]["recipient_personal_data_persisted"] is False
    assert data["privacy_boundary"]["raw_message_bodies_persisted"] is False


def test_exact_mail_send_plan_is_bound_to_proposal_and_content():
    p = proposal()
    mail_plan = plan()

    ok, reason = verify_mail_send_plan_v0(mail_plan, p)
    assert ok is True
    assert reason is None
    assert mail_plan.proposal_hash == p.proposal_hash
    assert len(mail_plan.plan_hash) == 64

    changed = plan(body="Horaire différent.")
    assert changed.plan_hash != mail_plan.plan_hash


def test_mail_specific_human_approval_binds_exact_body_subject_recipient():
    original = plan()
    changed = plan(body="Autre corps.")
    old_approval = approval(original)

    result, _, binding_hash = run_kx108_pre(
        Path("/tmp") / "unused-f3hb-approval",
        changed,
    )
    pre = build_mail_kx108_pre_evidence_v0(
        plan=changed,
        runtime_result=result,
        expected_binding_hash=binding_hash,
    )

    prepared = prepare_mail_connector_call_v0(
        proposal=proposal(),
        plan=changed,
        human_approval=old_approval,
        mailbox_authority=cssa_mailbox(changed),
        kx108_pre_evidence=pre,
        current_target_state_hash=changed.expected_target_state_hash,
        expected_binding_hash=binding_hash,
    )

    assert prepared["status"] == REJECTED
    assert prepared["reason"] == "MAIL_HUMAN_APPROVAL_MAIL_PLAN_HASH_MISMATCH"


def test_fresh_world_action_kx108_is_real_verified_agent_pre_execution(tmp_path):
    mail_plan = plan()
    result, provider, binding_hash = run_kx108_pre(tmp_path, mail_plan)

    assert result.x108_gate == "ALLOW"
    assert result.decision_phase == "AGENT_PRE_EXECUTION"
    assert result.decision_record_persisted is True
    assert result.decision_record_verified is True
    assert result.execution_plan_binding_verified is True
    assert result.replay_status == "PASS"
    assert result.decision_authority == "KX108_ONLY"
    assert result.world_action_allowed is False
    assert provider.invocations == 1

    evidence = build_mail_kx108_pre_evidence_v0(
        plan=mail_plan,
        runtime_result=result,
        expected_binding_hash=binding_hash,
    )
    assert evidence["x108_gate"] == "ALLOW"
    assert evidence["decision_phase"] == "AGENT_PRE_EXECUTION"
    assert len(evidence["evidence_hash"]) == 64


def test_kx108_hold_never_reaches_mail_connector_preparation(tmp_path):
    mail_plan = plan()
    result, provider, binding_hash = run_kx108_pre(
        tmp_path,
        mail_plan,
        unknowns=("MAIL_RECIPIENT_SCOPE_UNKNOWN", "MAIL_FACT_UNKNOWN"),
    )

    assert result.x108_gate == "HOLD"
    assert result.provider_invoked is False
    assert provider.invocations == 0

    with pytest.raises(ValueError, match="MAIL_KX108_PRE_GATE_NOT_ALLOW"):
        build_mail_kx108_pre_evidence_v0(
            plan=mail_plan,
            runtime_result=result,
            expected_binding_hash=binding_hash,
        )


def test_personal_connected_mailbox_cannot_be_used_as_cssa_sender(tmp_path):
    mail_plan = plan()
    result, _, binding_hash = run_kx108_pre(tmp_path, mail_plan)
    pre = build_mail_kx108_pre_evidence_v0(
        plan=mail_plan,
        runtime_result=result,
        expected_binding_hash=binding_hash,
    )

    prepared = prepare_mail_connector_call_v0(
        proposal=proposal(),
        plan=mail_plan,
        human_approval=approval(mail_plan),
        mailbox_authority=personal_mailbox(mail_plan),
        kx108_pre_evidence=pre,
        current_target_state_hash=mail_plan.expected_target_state_hash,
        expected_binding_hash=binding_hash,
    )

    assert prepared["status"] == REJECTED
    assert prepared["reason"] == "CONNECTED_MAILBOX_NOT_CSSA_OPERATIONAL_MAILBOX"
    assert prepared["message_sent"] is False


def test_missing_real_cssa_mailbox_authority_rejects(tmp_path):
    mail_plan = plan()
    result, _, binding_hash = run_kx108_pre(tmp_path, mail_plan)
    pre = build_mail_kx108_pre_evidence_v0(
        plan=mail_plan,
        runtime_result=result,
        expected_binding_hash=binding_hash,
    )

    prepared = prepare_mail_connector_call_v0(
        proposal=proposal(),
        plan=mail_plan,
        human_approval=approval(mail_plan),
        mailbox_authority=None,
        kx108_pre_evidence=pre,
        current_target_state_hash=mail_plan.expected_target_state_hash,
        expected_binding_hash=binding_hash,
    )

    assert prepared["status"] == REJECTED
    assert prepared["reason"] == "CSSA_OPERATIONAL_MAILBOX_EVIDENCE_MISSING"


def test_target_state_drift_after_human_and_kx108_rejects(tmp_path):
    mail_plan = plan()
    result, _, binding_hash = run_kx108_pre(tmp_path, mail_plan)
    pre = build_mail_kx108_pre_evidence_v0(
        plan=mail_plan,
        runtime_result=result,
        expected_binding_hash=binding_hash,
    )

    prepared = prepare_mail_connector_call_v0(
        proposal=proposal(),
        plan=mail_plan,
        human_approval=approval(mail_plan),
        mailbox_authority=cssa_mailbox(mail_plan),
        kx108_pre_evidence=pre,
        current_target_state_hash=h("thread-changed-after-approval"),
        expected_binding_hash=binding_hash,
    )

    assert prepared["status"] == REJECTED
    assert prepared["reason"] == "MAIL_TARGET_PRESTATE_HASH_MISMATCH"


def test_exact_gmail_send_call_contract_is_built_only_after_all_gates(tmp_path):
    mail_plan = plan()
    prepared = prepared_call(tmp_path, mail_plan)

    assert prepared["status"] == MAIL_PREPARED
    assert prepared["connector_invoked"] is False
    assert prepared["message_sent"] is False
    assert prepared["world_action_allowed"] is True

    call = prepared["call"]
    assert call["connector"] == "GMAIL"
    assert call["action"] == "SEND_EMAIL"
    assert call["args"] == {
        "to": "supporter@example.invalid",
        "subject": "Informations match CSSA",
        "body": "Coup d'envoi confirmé à 18h30.",
        "content_type": "text/plain",
        "reply_message_id": None,
    }
    assert len(prepared["call_hash"]) == 64


def test_provider_success_becomes_immutable_mail_receipt_and_replay_passes(tmp_path):
    mail_plan = plan()
    prepared = prepared_call(tmp_path, mail_plan)

    receipt = record_mail_connector_success_v0(
        prepared=prepared,
        provider_result={
            "id": "sim-provider-message-001",
            "threadId": "sim-provider-thread-001",
            "labelIds": ["SENT"],
        },
    )

    assert receipt["status"] == MAIL_SEND_RECORDED
    assert receipt["provider_message_id"] == "sim-provider-message-001"
    assert receipt["provider_thread_id"] == "sim-provider-thread-001"
    assert len(receipt["receipt_sha256"]) == 64

    replay = replay_mail_receipt_v0(receipt=receipt, plan=mail_plan)
    assert replay["status"] == MAIL_REPLAY_PASS
    assert replay["resend_required"] is False


def test_incomplete_provider_result_is_unknown_outcome_and_forbids_autoretry(tmp_path):
    prepared = prepared_call(tmp_path)

    outcome = record_mail_connector_success_v0(
        prepared=prepared,
        provider_result={"id": "maybe-sent-but-thread-id-missing"},
    )

    assert outcome["status"] == OUTCOME_UNKNOWN
    assert outcome["automatic_retry_allowed"] is False
    assert outcome["requires_sent_mail_reconciliation"] is True


def test_connector_exception_is_unknown_outcome_and_forbids_autoretry(tmp_path):
    prepared = prepared_call(tmp_path)

    outcome = record_mail_connector_exception_v0(
        prepared=prepared,
        exception_class="TimeoutError",
    )

    assert outcome["status"] == OUTCOME_UNKNOWN
    assert outcome["automatic_retry_allowed"] is False
    assert outcome["requires_sent_mail_reconciliation"] is True


def test_tampered_receipt_fails_replay(tmp_path):
    mail_plan = plan()
    prepared = prepared_call(tmp_path, mail_plan)
    receipt = record_mail_connector_success_v0(
        prepared=prepared,
        provider_result={
            "id": "sim-provider-message-001",
            "threadId": "sim-provider-thread-001",
        },
    )
    receipt["provider_thread_id"] = "tampered"

    replay = replay_mail_receipt_v0(receipt=receipt, plan=mail_plan)
    assert replay["status"] == "FAIL"
    assert replay["reason"] == "MAIL_RECEIPT_HASH_MISMATCH"


def test_progress_records_connector_ready_but_real_send_still_blocked():
    progress = load(PROGRESS)

    assert progress["status"] == (
        "MAIL_CONNECTOR_READY_SEND_BLOCKED_BY_REAL_MAILBOX_AUTHORITY"
    )
    assert progress["current_maximum"] == "CONNECTOR_READY_NO_REAL_CSSA_SEND"
    assert {
        "REAL_CSSA_OPERATIONAL_MAILBOX_CONNECTION",
        "REAL_CSSA_MAILBOX_AUTHORITY_EVIDENCE",
        "ONE_HUMAN_APPROVED_REAL_SEND_PILOT",
        "SENT_MAIL_RECONCILIATION_AFTER_UNKNOWN_OUTCOME",
    } <= set(progress["still_open_for_mail"])
    assert progress["boundaries"] == {
        "real_send_performed": False,
        "personal_mailbox_as_cssa_sender": False,
        "decision_authority": "KX108_ONLY",
    }
