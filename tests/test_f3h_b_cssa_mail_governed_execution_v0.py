import hashlib
import json
import os
import sys
from pathlib import Path

from organizations.cssa.execution import build_action_proposal_v0
from organizations.cssa.execution.mail_governed_execution_v0 import (
    MAIL_LIVE_SEND_BLOCKED,
    MAIL_RECEIPT_CONTRACT_ONLY,
    OUTCOME_UNKNOWN,
    REAL_EXECUTION_BLOCKER,
    WORLD_ACTION_BLOCKER,
    build_gmail_send_call_candidate_v0,
    build_mail_human_approval_v0,
    build_mail_provider_receipt_contract_v0,
    build_mail_send_plan_v0,
    build_mailbox_authority_evidence_v0,
    prepare_mail_world_action_v0,
    replay_mail_receipt_contract_v0,
    verify_mail_send_plan_v0,
)

ROOT = Path(__file__).resolve().parents[1]
CALIBRATION = ROOT / "organizations" / "cssa" / "execution" / "mail_live_calibration_v0.json"
PROGRESS = ROOT / "organizations" / "cssa" / "execution" / "f3h_b_mail_execution_progress_v0.json"

UPSTREAM = Path(os.environ["OBSIDIA_UPSTREAM_ROOT"]).resolve()
if str(UPSTREAM) not in sys.path:
    sys.path.insert(0, str(UPSTREAM))

from scripts.kernel.kx108_runtime_link_facts_v1 import runtime_link_facts  # noqa: E402
from runtime_wiring.source_runtime.world_action_bus_dry_run_activation import (  # noqa: E402
    build_world_action_bus_dry_run_state,
)


def h(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def proposal():
    return build_action_proposal_v0(
        proposal_id="MAIL_PROP_001",
        surface="MAIL",
        operation="DRAFT_NOTIFICATION",
        target_ref="sim:mail-thread:001",
        payload={"message_class": "MATCHDAY_INFORMATION"},
        source_case_refs=("sim:matchday:001",),
        evidence_refs=("sim:fixture-proof:001",),
        expected_target_state_hash=h("mail-thread-state-001"),
    )


def plan(body="Coup d'envoi confirme a 18h30."):
    p = proposal()
    return build_mail_send_plan_v0(
        proposal=p,
        plan_id="MAIL_PLAN_001",
        to=("supporter@example.invalid",),
        subject="Informations match CSSA",
        body=body,
        reply_message_id=None,
        sender_mailbox_ref="sim:cssa-mailbox",
        expected_target_state_hash=p.expected_target_state_hash,
        source_evidence_refs=("sim:fixture-proof:001",),
    )


def approval(mail_plan):
    return build_mail_human_approval_v0(
        approval_id="MAIL_APPROVAL_001",
        approved_by="HUMAN:CSSA_REVIEWER",
        approval_reference="sim:review:001",
        plan=mail_plan,
    )


def mailbox(mail_plan, role="CSSA_OPERATIONAL_MAILBOX", verified=True):
    return build_mailbox_authority_evidence_v0(
        mailbox_ref=mail_plan.sender_mailbox_ref,
        mailbox_role=role,
        connector_account_ref="sim:gmail-account",
        cssa_operational_authority_ref=(
            "sim:cssa-mail-authority" if verified else None
        ),
        account_verified_for_cssa=verified,
    )


def world_state():
    return build_world_action_bus_dry_run_state("email action request")


def test_mail_plan_is_exact_and_hash_bound():
    p = proposal()
    first = plan()
    second = plan("Autre contenu.")
    assert verify_mail_send_plan_v0(first, p) == (True, None)
    assert first.plan_hash != second.plan_hash


def test_live_calibration_persists_no_private_message_content():
    data = load(CALIBRATION)
    assert data["execution_boundary"]["real_send_permitted_now"] is False
    assert data["privacy_boundary"]["gmail_message_ids_persisted"] is False
    assert data["privacy_boundary"]["recipient_personal_data_persisted"] is False
    assert data["privacy_boundary"]["raw_message_bodies_persisted"] is False


def test_upstream_canonically_blocks_external_world_actuation():
    facts = runtime_link_facts()
    assert facts["world_action_runtime_activated"] is False
    assert WORLD_ACTION_BLOCKER in facts["missing_runtime_links"]
    assert REAL_EXECUTION_BLOCKER in facts["missing_runtime_links"]
    assert facts["execution_authority"] is False
    assert facts["decision_authority"] == "KX108_ONLY"


def test_world_action_bus_is_dry_run_only_for_email_class():
    state = world_state()
    assert state["detected_action_type"] == "EMAIL_SEND"
    assert state["action_request_blocked"] is True
    assert state["dry_run_enabled"] is True
    assert state["real_action_enabled"] is False
    assert state["world_action"] is False


def test_personal_mailbox_cannot_become_cssa_sender():
    mail_plan = plan()
    out = prepare_mail_world_action_v0(
        proposal=proposal(),
        plan=mail_plan,
        human_approval=approval(mail_plan),
        mailbox_authority=mailbox(
            mail_plan,
            role="PERSONAL_USER_MAILBOX",
            verified=False,
        ),
        current_target_state_hash=mail_plan.expected_target_state_hash,
        runtime_link_facts=runtime_link_facts(),
        world_action_dry_run_state=world_state(),
    )
    assert out["status"] == "REJECTED_NO_SEND"
    assert out["reason"] == "CONNECTED_MAILBOX_NOT_CSSA_OPERATIONAL_MAILBOX"


def test_exact_cssa_mail_preflight_still_blocks_on_upstream_world_boundary():
    mail_plan = plan()
    out = prepare_mail_world_action_v0(
        proposal=proposal(),
        plan=mail_plan,
        human_approval=approval(mail_plan),
        mailbox_authority=mailbox(mail_plan),
        current_target_state_hash=mail_plan.expected_target_state_hash,
        runtime_link_facts=runtime_link_facts(),
        world_action_dry_run_state=world_state(),
    )
    assert out["status"] == MAIL_LIVE_SEND_BLOCKED
    assert out["reason"] == WORLD_ACTION_BLOCKER
    assert REAL_EXECUTION_BLOCKER in out["blockers"]
    assert "WORLD_ACTION_BUS_DRY_RUN_ONLY" in out["blockers"]
    assert out["connector_invoked"] is False
    assert out["message_sent"] is False
    assert out["world_action_allowed"] is False


def test_target_drift_blocks_before_any_world_action():
    mail_plan = plan()
    out = prepare_mail_world_action_v0(
        proposal=proposal(),
        plan=mail_plan,
        human_approval=approval(mail_plan),
        mailbox_authority=mailbox(mail_plan),
        current_target_state_hash=h("changed"),
        runtime_link_facts=runtime_link_facts(),
        world_action_dry_run_state=world_state(),
    )
    assert out["status"] == "REJECTED_NO_SEND"
    assert out["reason"] == "MAIL_TARGET_PRESTATE_HASH_MISMATCH"


def test_gmail_call_candidate_is_exact_but_non_executable():
    mail_plan = plan()
    candidate = build_gmail_send_call_candidate_v0(mail_plan)
    assert candidate["call"]["connector"] == "GMAIL"
    assert candidate["call"]["action"] == "SEND_EMAIL"
    assert candidate["call"]["args"]["to"] == "supporter@example.invalid"
    assert candidate["call"]["args"]["subject"] == "Informations match CSSA"
    assert candidate["connector_invoked"] is False
    assert candidate["world_action_allowed"] is False


def test_provider_receipt_contract_never_claims_real_send():
    mail_plan = plan()
    candidate = build_gmail_send_call_candidate_v0(mail_plan)
    receipt = build_mail_provider_receipt_contract_v0(
        plan=mail_plan,
        call_hash=candidate["call_hash"],
        provider_result={"id": "sim-msg", "threadId": "sim-thread"},
    )
    assert receipt["status"] == MAIL_RECEIPT_CONTRACT_ONLY
    assert receipt["real_send_proven"] is False
    replay = replay_mail_receipt_contract_v0(receipt=receipt, plan=mail_plan)
    assert replay["status"] == "PASS_CONTRACT_ONLY"
    assert replay["resend_authorized"] is False


def test_unknown_provider_result_forbids_auto_retry():
    mail_plan = plan()
    candidate = build_gmail_send_call_candidate_v0(mail_plan)
    out = build_mail_provider_receipt_contract_v0(
        plan=mail_plan,
        call_hash=candidate["call_hash"],
        provider_result={"id": "sim-msg"},
    )
    assert out["status"] == OUTCOME_UNKNOWN
    assert out["automatic_retry_allowed"] is False
    assert out["requires_sent_mail_reconciliation"] is True


def test_progress_keeps_real_mail_execution_open():
    progress = load(PROGRESS)
    assert progress["current_maximum"] == "EXACT_MAIL_PREFLIGHT_DRY_RUN_BLOCKED"
    assert "GENERIC_WORLD_ACTION_PRE_EXECUTION_RAIL" in progress["still_open_for_mail"]
    assert progress["boundaries"]["real_send_performed"] is False
    assert progress["boundaries"]["gmail_connector_invoked"] is False
    assert progress["boundaries"]["agent_pre_execution_used_as_world_authority"] is False
