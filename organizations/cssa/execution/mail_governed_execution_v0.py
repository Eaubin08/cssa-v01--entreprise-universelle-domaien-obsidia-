"""F3H-B — CSSA governed MAIL execution preflight V0.

Current upstream truth (obsidia-x108-proofs):
- the governed agent PRE_EXECUTION rail is INTERNAL_BOUNDED only;
- EXTERNAL_WORLD_ACTUATION_NOT_ACTIVATED remains a canonical missing link;
- the WorldActionBus is dry-run only and performs no email/API egress.

Therefore this module MUST NOT reinterpret AGENT_PRE_EXECUTION as authority to
send email. It prepares and hashes the exact mail action, verifies exact human
approval and CSSA mailbox authority, exposes the exact Gmail call candidate,
and then fails closed on the upstream world-action blocker.

No Gmail connector is invoked by this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

from .decision_execution_v0 import (
    ActionProposalV0,
    DECISION_AUTHORITY,
    verify_action_proposal_v0,
)

STATUS = "CSSA_MAIL_GOVERNED_EXECUTION_PREFLIGHT_V0"

MAILBOX_ROLE = "CSSA_OPERATIONAL_MAILBOX"
CONNECTOR = "GMAIL"
CONNECTOR_ACTION = "SEND_EMAIL"

WORLD_ACTION_BLOCKER = "EXTERNAL_WORLD_ACTUATION_NOT_ACTIVATED"
REAL_EXECUTION_BLOCKER = "REAL_X108_GATED_EXECUTION_PATH_NOT_ACTIVATED"

MAIL_LIVE_SEND_BLOCKED = "MAIL_LIVE_SEND_BLOCKED"
MAIL_LIVE_SEND_PREPARED = "MAIL_LIVE_SEND_PREPARED"
MAIL_RECEIPT_CONTRACT_ONLY = "MAIL_RECEIPT_CONTRACT_ONLY"
OUTCOME_UNKNOWN = "MAIL_CONNECTOR_OUTCOME_UNKNOWN_REQUIRES_RECONCILIATION"
REJECTED = "REJECTED_NO_SEND"

SUPPORTED_PROPOSAL_OPERATIONS = {
    "DRAFT_REPLY",
    "DRAFT_NOTIFICATION",
    "DRAFT_FOLLOWUP",
}


def _hash(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return sha256(raw).hexdigest()


def _reject(reason: str, **extra: Any) -> dict[str, Any]:
    return {
        "status": REJECTED,
        "reason": reason,
        "connector_invoked": False,
        "message_sent": False,
        "world_action_allowed": False,
        "decision_authority": DECISION_AUTHORITY,
        **extra,
    }


@dataclass(frozen=True)
class MailSendPlanV0:
    plan_id: str
    proposal_id: str
    proposal_hash: str
    to: tuple[str, ...]
    subject: str
    body: str
    reply_message_id: str | None
    sender_mailbox_ref: str
    expected_target_state_hash: str
    source_evidence_refs: tuple[str, ...]
    plan_hash: str
    decision_authority: str = DECISION_AUTHORITY

    def assert_valid(self) -> None:
        if self.decision_authority != DECISION_AUTHORITY:
            raise ValueError("MAIL_PLAN_DECISION_AUTHORITY_NOT_KX108_ONLY")
        if not self.plan_id:
            raise ValueError("MAIL_PLAN_ID_REQUIRED")
        if not self.to:
            raise ValueError("MAIL_RECIPIENT_REQUIRED")
        if any("@" not in value for value in self.to):
            raise ValueError("MAIL_RECIPIENT_MALFORMED")
        if not self.subject:
            raise ValueError("MAIL_SUBJECT_REQUIRED")
        if not self.body:
            raise ValueError("MAIL_BODY_REQUIRED")
        if not self.sender_mailbox_ref:
            raise ValueError("SENDER_MAILBOX_REF_REQUIRED")
        if len(self.expected_target_state_hash) != 64:
            raise ValueError("EXPECTED_TARGET_STATE_HASH_REQUIRED")


def build_mail_send_plan_v0(
    *,
    proposal: ActionProposalV0,
    plan_id: str,
    to: tuple[str, ...],
    subject: str,
    body: str,
    reply_message_id: str | None,
    sender_mailbox_ref: str,
    expected_target_state_hash: str,
    source_evidence_refs: tuple[str, ...],
) -> MailSendPlanV0:
    ok, reason = verify_action_proposal_v0(proposal)
    if not ok:
        raise ValueError(f"INVALID_ACTION_PROPOSAL:{reason}")
    if proposal.surface != "MAIL":
        raise ValueError("MAIL_PLAN_REQUIRES_MAIL_PROPOSAL")
    if proposal.operation not in SUPPORTED_PROPOSAL_OPERATIONS:
        raise ValueError(
            f"MAIL_PLAN_UNSUPPORTED_PROPOSAL_OPERATION:{proposal.operation}"
        )
    if not source_evidence_refs:
        raise ValueError("MAIL_PLAN_EVIDENCE_REQUIRED")

    bound = {
        "schema": "CSSA_MAIL_SEND_PLAN_V0",
        "plan_id": plan_id,
        "proposal_id": proposal.proposal_id,
        "proposal_hash": proposal.proposal_hash,
        "to": list(to),
        "subject": subject,
        "body": body,
        "reply_message_id": reply_message_id,
        "sender_mailbox_ref": sender_mailbox_ref,
        "expected_target_state_hash": expected_target_state_hash,
        "source_evidence_refs": list(source_evidence_refs),
        "decision_authority": DECISION_AUTHORITY,
    }
    out = MailSendPlanV0(
        plan_id=plan_id,
        proposal_id=proposal.proposal_id,
        proposal_hash=proposal.proposal_hash,
        to=tuple(to),
        subject=subject,
        body=body,
        reply_message_id=reply_message_id,
        sender_mailbox_ref=sender_mailbox_ref,
        expected_target_state_hash=expected_target_state_hash,
        source_evidence_refs=tuple(source_evidence_refs),
        plan_hash=_hash(bound),
    )
    out.assert_valid()
    return out


def verify_mail_send_plan_v0(
    plan: MailSendPlanV0,
    proposal: ActionProposalV0,
) -> tuple[bool, str | None]:
    try:
        plan.assert_valid()
    except ValueError as exc:
        return False, str(exc)
    ok, reason = verify_action_proposal_v0(proposal)
    if not ok:
        return False, f"INVALID_ACTION_PROPOSAL:{reason}"
    if proposal.surface != "MAIL":
        return False, "MAIL_PLAN_REQUIRES_MAIL_PROPOSAL"
    if plan.proposal_id != proposal.proposal_id:
        return False, "MAIL_PLAN_PROPOSAL_ID_MISMATCH"
    if plan.proposal_hash != proposal.proposal_hash:
        return False, "MAIL_PLAN_PROPOSAL_HASH_MISMATCH"

    rebound = {
        "schema": "CSSA_MAIL_SEND_PLAN_V0",
        "plan_id": plan.plan_id,
        "proposal_id": plan.proposal_id,
        "proposal_hash": plan.proposal_hash,
        "to": list(plan.to),
        "subject": plan.subject,
        "body": plan.body,
        "reply_message_id": plan.reply_message_id,
        "sender_mailbox_ref": plan.sender_mailbox_ref,
        "expected_target_state_hash": plan.expected_target_state_hash,
        "source_evidence_refs": list(plan.source_evidence_refs),
        "decision_authority": plan.decision_authority,
    }
    if _hash(rebound) != plan.plan_hash:
        return False, "MAIL_PLAN_HASH_MISMATCH"
    return True, None


def build_mail_human_approval_v0(
    *,
    approval_id: str,
    approved_by: str,
    approval_reference: str,
    plan: MailSendPlanV0,
) -> dict[str, Any]:
    if not approval_id:
        raise ValueError("MAIL_APPROVAL_ID_REQUIRED")
    if not approved_by or approved_by == "MACHINE":
        raise ValueError("EXPLICIT_HUMAN_APPROVER_REQUIRED")
    if not approval_reference:
        raise ValueError("MAIL_APPROVAL_REFERENCE_REQUIRED")

    record = {
        "schema": "CSSA_MAIL_HUMAN_APPROVAL_V0",
        "approval_id": approval_id,
        "approved_by": approved_by,
        "approval_reference": approval_reference,
        "mail_plan_id": plan.plan_id,
        "mail_plan_hash": plan.plan_hash,
        "proposal_id": plan.proposal_id,
        "proposal_hash": plan.proposal_hash,
        "sender_mailbox_ref": plan.sender_mailbox_ref,
        "to": list(plan.to),
        "subject_sha256": sha256(plan.subject.encode("utf-8")).hexdigest(),
        "body_sha256": sha256(plan.body.encode("utf-8")).hexdigest(),
        "reply_message_id": plan.reply_message_id,
        "decision_authority": DECISION_AUTHORITY,
        "is_execution_authority": False,
    }
    record["approval_hash"] = _hash(record)
    return record


def verify_mail_human_approval_v0(
    approval: Mapping[str, Any] | None,
    plan: MailSendPlanV0,
) -> tuple[bool, str | None]:
    if approval is None:
        return False, "MAIL_HUMAN_APPROVAL_MISSING"
    if approval.get("schema") != "CSSA_MAIL_HUMAN_APPROVAL_V0":
        return False, "MAIL_HUMAN_APPROVAL_SCHEMA_INVALID"
    if approval.get("decision_authority") != DECISION_AUTHORITY:
        return False, "MAIL_HUMAN_APPROVAL_AUTHORITY_INVALID"
    if approval.get("is_execution_authority") is not False:
        return False, "MAIL_HUMAN_APPROVAL_CANNOT_BE_SOVEREIGN"
    expected_pairs = {
        "mail_plan_id": plan.plan_id,
        "mail_plan_hash": plan.plan_hash,
        "proposal_id": plan.proposal_id,
        "proposal_hash": plan.proposal_hash,
        "sender_mailbox_ref": plan.sender_mailbox_ref,
        "to": list(plan.to),
        "subject_sha256": sha256(plan.subject.encode("utf-8")).hexdigest(),
        "body_sha256": sha256(plan.body.encode("utf-8")).hexdigest(),
        "reply_message_id": plan.reply_message_id,
    }
    for key, value in expected_pairs.items():
        if approval.get(key) != value:
            return False, f"MAIL_HUMAN_APPROVAL_{key.upper()}_MISMATCH"
    candidate = dict(approval)
    stored = candidate.pop("approval_hash", None)
    if not stored or _hash(candidate) != stored:
        return False, "MAIL_HUMAN_APPROVAL_HASH_MISMATCH"
    return True, None


def build_mailbox_authority_evidence_v0(
    *,
    mailbox_ref: str,
    mailbox_role: str,
    connector_account_ref: str,
    cssa_operational_authority_ref: str | None,
    account_verified_for_cssa: bool,
) -> dict[str, Any]:
    record = {
        "schema": "CSSA_MAILBOX_AUTHORITY_EVIDENCE_V0",
        "mailbox_ref": mailbox_ref,
        "mailbox_role": mailbox_role,
        "connector": CONNECTOR,
        "connector_account_ref": connector_account_ref,
        "cssa_operational_authority_ref": cssa_operational_authority_ref,
        "account_verified_for_cssa": bool(account_verified_for_cssa),
        "decision_authority": DECISION_AUTHORITY,
        "is_execution_authority": False,
    }
    record["evidence_hash"] = _hash(record)
    return record


def verify_mailbox_authority_evidence_v0(
    evidence: Mapping[str, Any] | None,
    plan: MailSendPlanV0,
) -> tuple[bool, str | None]:
    if evidence is None:
        return False, "CSSA_OPERATIONAL_MAILBOX_EVIDENCE_MISSING"
    if evidence.get("schema") != "CSSA_MAILBOX_AUTHORITY_EVIDENCE_V0":
        return False, "MAILBOX_AUTHORITY_SCHEMA_INVALID"
    if evidence.get("mailbox_ref") != plan.sender_mailbox_ref:
        return False, "MAILBOX_REF_MISMATCH"
    if evidence.get("mailbox_role") != MAILBOX_ROLE:
        return False, "CONNECTED_MAILBOX_NOT_CSSA_OPERATIONAL_MAILBOX"
    if evidence.get("connector") != CONNECTOR:
        return False, "MAILBOX_CONNECTOR_NOT_GMAIL"
    if evidence.get("account_verified_for_cssa") is not True:
        return False, "CONNECTED_ACCOUNT_NOT_VERIFIED_FOR_CSSA"
    if not evidence.get("cssa_operational_authority_ref"):
        return False, "CSSA_MAILBOX_OPERATIONAL_AUTHORITY_UNKNOWN"
    candidate = dict(evidence)
    stored = candidate.pop("evidence_hash", None)
    if not stored or _hash(candidate) != stored:
        return False, "MAILBOX_AUTHORITY_EVIDENCE_HASH_MISMATCH"
    return True, None


def build_gmail_send_call_candidate_v0(plan: MailSendPlanV0) -> dict[str, Any]:
    """Pure connector-call candidate. Building it is never authority to call."""
    call = {
        "connector": CONNECTOR,
        "action": CONNECTOR_ACTION,
        "args": {
            "to": ",".join(plan.to),
            "subject": plan.subject,
            "body": plan.body,
            "content_type": "text/plain",
            "reply_message_id": plan.reply_message_id,
        },
        "mail_plan_id": plan.plan_id,
        "mail_plan_hash": plan.plan_hash,
        "decision_authority": DECISION_AUTHORITY,
    }
    return {
        "call": call,
        "call_hash": _hash(call),
        "connector_invoked": False,
        "message_sent": False,
        "world_action_allowed": False,
    }


def verify_world_action_pre_evidence_v0(
    evidence: Mapping[str, Any] | None,
    *,
    plan: MailSendPlanV0,
    call_hash: str,
) -> tuple[bool, str | None]:
    """Future external PRE contract.

    No current upstream producer exists for this evidence. AGENT_PRE_EXECUTION
    is explicitly rejected because it is INTERNAL_BOUNDED only.
    """
    if evidence is None:
        return False, "WORLD_ACTION_PRE_EVIDENCE_MISSING"
    if evidence.get("schema") != "CSSA_WORLD_ACTION_PRE_EVIDENCE_V0":
        return False, "WORLD_ACTION_PRE_EVIDENCE_SCHEMA_INVALID"
    if evidence.get("decision_phase") != "WORLD_ACTION_PRE_EXECUTION":
        return False, "WORLD_ACTION_PRE_DECISION_PHASE_INVALID"
    if evidence.get("x108_gate") != "ALLOW":
        return False, "WORLD_ACTION_PRE_GATE_NOT_ALLOW"
    if evidence.get("decision_authority") != DECISION_AUTHORITY:
        return False, "WORLD_ACTION_PRE_AUTHORITY_INVALID"
    if evidence.get("mail_plan_hash") != plan.plan_hash:
        return False, "WORLD_ACTION_PRE_MAIL_PLAN_HASH_MISMATCH"
    if evidence.get("connector_call_hash") != call_hash:
        return False, "WORLD_ACTION_PRE_CONNECTOR_CALL_HASH_MISMATCH"
    if not evidence.get("decision_record_id") or not evidence.get("decision_record_hash"):
        return False, "WORLD_ACTION_PRE_DECISION_IDENTITY_MISSING"
    candidate = dict(evidence)
    stored = candidate.pop("evidence_hash", None)
    if not stored or _hash(candidate) != stored:
        return False, "WORLD_ACTION_PRE_EVIDENCE_HASH_MISMATCH"
    return True, None


def prepare_mail_world_action_v0(
    *,
    proposal: ActionProposalV0,
    plan: MailSendPlanV0,
    human_approval: Mapping[str, Any] | None,
    mailbox_authority: Mapping[str, Any] | None,
    current_target_state_hash: str,
    runtime_link_facts: Mapping[str, Any],
    world_action_dry_run_state: Mapping[str, Any],
    world_action_pre_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    ok, reason = verify_mail_send_plan_v0(plan, proposal)
    if not ok:
        return _reject(reason or "MAIL_PLAN_INVALID")
    ok, reason = verify_mail_human_approval_v0(human_approval, plan)
    if not ok:
        return _reject(reason or "MAIL_HUMAN_APPROVAL_INVALID")
    ok, reason = verify_mailbox_authority_evidence_v0(mailbox_authority, plan)
    if not ok:
        return _reject(reason or "MAILBOX_AUTHORITY_INVALID")
    if current_target_state_hash != plan.expected_target_state_hash:
        return _reject(
            "MAIL_TARGET_PRESTATE_HASH_MISMATCH",
            expected_target_state_hash=plan.expected_target_state_hash,
            current_target_state_hash=current_target_state_hash,
        )

    candidate = build_gmail_send_call_candidate_v0(plan)

    if runtime_link_facts.get("decision_authority") != DECISION_AUTHORITY:
        return _reject("UPSTREAM_RUNTIME_AUTHORITY_INVALID")
    missing_links = set(runtime_link_facts.get("missing_runtime_links") or ())
    world_active = runtime_link_facts.get("world_action_runtime_activated") is True

    dry_run_only = world_action_dry_run_state.get("dry_run_enabled") is True
    real_action_enabled = (
        world_action_dry_run_state.get("real_action_enabled") is True
    )
    detected_email = (
        world_action_dry_run_state.get("detected_action_type") == "EMAIL_SEND"
    )
    action_blocked = (
        world_action_dry_run_state.get("action_request_blocked") is True
    )

    blockers: list[str] = []
    if WORLD_ACTION_BLOCKER in missing_links or not world_active:
        blockers.append(WORLD_ACTION_BLOCKER)
    if REAL_EXECUTION_BLOCKER in missing_links:
        blockers.append(REAL_EXECUTION_BLOCKER)
    if dry_run_only and not real_action_enabled:
        blockers.append("WORLD_ACTION_BUS_DRY_RUN_ONLY")
    if detected_email and action_blocked:
        blockers.append("EMAIL_SEND_BLOCKED_AT_WORLD_ACTION_BOUNDARY")

    if blockers:
        return {
            "status": MAIL_LIVE_SEND_BLOCKED,
            "reason": blockers[0],
            "blockers": tuple(dict.fromkeys(blockers)),
            "gmail_call_candidate": candidate,
            "connector_invoked": False,
            "message_sent": False,
            "world_action_allowed": False,
            "decision_authority": DECISION_AUTHORITY,
        }

    ok, reason = verify_world_action_pre_evidence_v0(
        world_action_pre_evidence,
        plan=plan,
        call_hash=candidate["call_hash"],
    )
    if not ok:
        return _reject(reason or "WORLD_ACTION_PRE_INVALID")

    return {
        "status": MAIL_LIVE_SEND_PREPARED,
        "reason": None,
        "gmail_call_candidate": candidate,
        "world_action_pre_evidence_hash":
            world_action_pre_evidence["evidence_hash"],
        "connector_invoked": False,
        "message_sent": False,
        "world_action_allowed": True,
        "decision_authority": DECISION_AUTHORITY,
    }


def build_mail_provider_receipt_contract_v0(
    *,
    plan: MailSendPlanV0,
    call_hash: str,
    provider_result: Mapping[str, Any],
) -> dict[str, Any]:
    """Provider result parser/receipt contract.

    This function does NOT prove the connector was actually called. Until the
    external world-action rail is activated, receipts produced in tests remain
    contract-only artifacts.
    """
    provider_message_id = provider_result.get("id")
    provider_thread_id = provider_result.get("threadId")
    if not provider_message_id or not provider_thread_id:
        return {
            "status": OUTCOME_UNKNOWN,
            "reason": "MAIL_PROVIDER_RESULT_IDENTITY_INCOMPLETE",
            "automatic_retry_allowed": False,
            "requires_sent_mail_reconciliation": True,
            "real_send_proven": False,
            "decision_authority": DECISION_AUTHORITY,
        }

    receipt = {
        "schema": "CSSA_MAIL_SEND_RECEIPT_CONTRACT_V0",
        "status": MAIL_RECEIPT_CONTRACT_ONLY,
        "mail_plan_id": plan.plan_id,
        "mail_plan_hash": plan.plan_hash,
        "call_hash": call_hash,
        "provider": CONNECTOR,
        "provider_message_id": str(provider_message_id),
        "provider_thread_id": str(provider_thread_id),
        "real_send_proven": False,
        "decision_authority": DECISION_AUTHORITY,
    }
    receipt["receipt_sha256"] = _hash(receipt)
    return receipt


def replay_mail_receipt_contract_v0(
    *,
    receipt: Mapping[str, Any],
    plan: MailSendPlanV0,
) -> dict[str, Any]:
    if receipt.get("schema") != "CSSA_MAIL_SEND_RECEIPT_CONTRACT_V0":
        return {"status": "FAIL", "reason": "MAIL_RECEIPT_SCHEMA_INVALID"}
    if receipt.get("real_send_proven") is not False:
        return {"status": "FAIL", "reason": "MAIL_RECEIPT_TRUTH_CLASS_INVALID"}
    if receipt.get("mail_plan_id") != plan.plan_id:
        return {"status": "FAIL", "reason": "MAIL_RECEIPT_PLAN_ID_MISMATCH"}
    if receipt.get("mail_plan_hash") != plan.plan_hash:
        return {"status": "FAIL", "reason": "MAIL_RECEIPT_PLAN_HASH_MISMATCH"}
    candidate = dict(receipt)
    stored = candidate.pop("receipt_sha256", None)
    if not stored or _hash(candidate) != stored:
        return {"status": "FAIL", "reason": "MAIL_RECEIPT_HASH_MISMATCH"}
    return {
        "status": "PASS_CONTRACT_ONLY",
        "provider_message_id": receipt["provider_message_id"],
        "provider_thread_id": receipt["provider_thread_id"],
        "resend_authorized": False,
        "real_send_proven": False,
        "decision_authority": DECISION_AUTHORITY,
    }
