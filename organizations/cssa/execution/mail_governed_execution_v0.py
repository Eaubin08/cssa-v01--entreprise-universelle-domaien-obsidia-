"""F3H-B — CSSA governed MAIL execution surface V0.

The module binds an exact outbound message to:
- the F3H-A ActionProposal,
- a separate exact human approval,
- a fresh verified KX108 pre-execution result,
- the exact target/thread pre-state,
- an explicitly authorized CSSA operational mailbox.

It can build the exact Gmail connector call and verify/record the provider
result. It does not itself call Gmail. A live send is forbidden when the
connected account is not proven to be an authorized CSSA operational mailbox.
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

STATUS = "CSSA_MAIL_GOVERNED_EXECUTION_V0"

MAILBOX_ROLE = "CSSA_OPERATIONAL_MAILBOX"
CONNECTOR = "GMAIL"
CONNECTOR_ACTION = "SEND_EMAIL"

MAIL_PLAN_READY = "MAIL_PLAN_READY"
MAIL_PREPARED = "MAIL_PREPARED_FOR_CONNECTOR"
MAIL_SEND_RECORDED = "MAIL_SEND_RECORDED"
MAIL_REPLAY_PASS = "PASS"
REJECTED = "REJECTED_NO_SEND"
OUTCOME_UNKNOWN = "MAIL_CONNECTOR_OUTCOME_UNKNOWN_REQUIRES_RECONCILIATION"

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


def mail_pre_execution_runtime_state_v0(
    plan: MailSendPlanV0,
    *,
    valid_at: str,
    current_target_state_hash: str,
    confidence: float = 1.0,
    unknowns: tuple[str, ...] = (),
    contradictions: tuple[str, ...] = (),
    risk_flags: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Build exact state for the fresh KX108 world-action boundary decision."""
    binding = {
        "schema": "CSSA_MAIL_PRE_EXECUTION_BINDING_V0",
        "mail_plan_id": plan.plan_id,
        "mail_plan_hash": plan.plan_hash,
        "sender_mailbox_ref": plan.sender_mailbox_ref,
        "to": list(plan.to),
        "subject_sha256": sha256(plan.subject.encode("utf-8")).hexdigest(),
        "body_sha256": sha256(plan.body.encode("utf-8")).hexdigest(),
        "reply_message_id": plan.reply_message_id,
        "current_target_state_hash": current_target_state_hash,
        "decision_authority": DECISION_AUTHORITY,
    }
    binding_hash = _hash(binding)
    return {
        "case_ref": f"cssa:mail-pre-exec:{binding_hash}",
        "valid_at": valid_at,
        "source_ref": f"cssa-mail-plan:{plan.plan_hash}",
        "unknowns": tuple(unknowns),
        "contradictions": tuple(contradictions),
        "risk_flags": tuple(risk_flags),
        "evidence_refs": plan.source_evidence_refs,
        "provenance_refs": (
            f"mail-plan:{plan.plan_hash}",
            f"mail-pre-exec-binding:{binding_hash}",
        ),
        "confidence": float(confidence),
        "mail_plan_hash": plan.plan_hash,
        "mail_pre_execution_binding_hash": binding_hash,
        "current_target_state_hash": current_target_state_hash,
    }


def build_mail_kx108_pre_evidence_v0(
    *,
    plan: MailSendPlanV0,
    runtime_result: Any,
    expected_binding_hash: str,
) -> dict[str, Any]:
    if getattr(runtime_result, "x108_gate", None) != "ALLOW":
        raise ValueError("MAIL_KX108_PRE_GATE_NOT_ALLOW")
    if getattr(runtime_result, "decision_record_verified", None) is not True:
        raise ValueError("MAIL_KX108_PRE_DECISION_NOT_VERIFIED")
    if getattr(runtime_result, "execution_plan_binding_verified", None) is not True:
        raise ValueError("MAIL_KX108_PRE_EXECUTION_PLAN_NOT_BOUND")
    if not getattr(runtime_result, "decision_record_id", ""):
        raise ValueError("MAIL_KX108_PRE_DECISION_RECORD_ID_MISSING")
    if getattr(runtime_result, "decision_phase", None) != "AGENT_PRE_EXECUTION":
        raise ValueError("MAIL_KX108_PRE_DECISION_PHASE_INVALID")
    if getattr(runtime_result, "decision_authority", None) != DECISION_AUTHORITY:
        raise ValueError("MAIL_KX108_PRE_AUTHORITY_INVALID")
    if getattr(runtime_result, "world_action_allowed", True) is not False:
        raise ValueError("MAIL_RUNTIME_WORLD_ACTION_BOUNDARY_VIOLATED")

    record = {
        "schema": "CSSA_MAIL_KX108_PRE_EVIDENCE_V0",
        "mail_plan_id": plan.plan_id,
        "mail_plan_hash": plan.plan_hash,
        "mail_pre_execution_binding_hash": expected_binding_hash,
        "decision_record_id": runtime_result.decision_record_id,
        "decision_record_hash": runtime_result.decision_record_hash,
        "decision_phase": runtime_result.decision_phase,
        "x108_gate": runtime_result.x108_gate,
        "execution_plan_digest": runtime_result.execution_plan_digest,
        "decision_authority": runtime_result.decision_authority,
    }
    record["evidence_hash"] = _hash(record)
    return record


def verify_mail_kx108_pre_evidence_v0(
    evidence: Mapping[str, Any] | None,
    plan: MailSendPlanV0,
    expected_binding_hash: str,
) -> tuple[bool, str | None]:
    if evidence is None:
        return False, "MAIL_KX108_PRE_EVIDENCE_MISSING"
    if evidence.get("schema") != "CSSA_MAIL_KX108_PRE_EVIDENCE_V0":
        return False, "MAIL_KX108_PRE_EVIDENCE_SCHEMA_INVALID"
    if evidence.get("mail_plan_id") != plan.plan_id:
        return False, "MAIL_KX108_PRE_PLAN_ID_MISMATCH"
    if evidence.get("mail_plan_hash") != plan.plan_hash:
        return False, "MAIL_KX108_PRE_PLAN_HASH_MISMATCH"
    if evidence.get("mail_pre_execution_binding_hash") != expected_binding_hash:
        return False, "MAIL_KX108_PRE_BINDING_HASH_MISMATCH"
    if evidence.get("x108_gate") != "ALLOW":
        return False, "MAIL_KX108_PRE_GATE_NOT_ALLOW"
    if evidence.get("decision_phase") != "AGENT_PRE_EXECUTION":
        return False, "MAIL_KX108_PRE_DECISION_PHASE_INVALID"
    if evidence.get("decision_authority") != DECISION_AUTHORITY:
        return False, "MAIL_KX108_PRE_AUTHORITY_INVALID"
    if not evidence.get("decision_record_id") or not evidence.get("decision_record_hash"):
        return False, "MAIL_KX108_PRE_DECISION_IDENTITY_MISSING"

    candidate = dict(evidence)
    stored = candidate.pop("evidence_hash", None)
    if not stored or _hash(candidate) != stored:
        return False, "MAIL_KX108_PRE_EVIDENCE_HASH_MISMATCH"
    return True, None


def prepare_mail_connector_call_v0(
    *,
    proposal: ActionProposalV0,
    plan: MailSendPlanV0,
    human_approval: Mapping[str, Any] | None,
    mailbox_authority: Mapping[str, Any] | None,
    kx108_pre_evidence: Mapping[str, Any] | None,
    current_target_state_hash: str,
    expected_binding_hash: str,
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

    ok, reason = verify_mail_kx108_pre_evidence_v0(
        kx108_pre_evidence,
        plan,
        expected_binding_hash,
    )
    if not ok:
        return _reject(reason or "MAIL_KX108_PRE_INVALID")

    if current_target_state_hash != plan.expected_target_state_hash:
        return _reject(
            "MAIL_TARGET_PRESTATE_HASH_MISMATCH",
            expected_target_state_hash=plan.expected_target_state_hash,
            current_target_state_hash=current_target_state_hash,
        )

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
        "approval_id": human_approval["approval_id"],
        "approval_hash": human_approval["approval_hash"],
        "kx108_pre_decision_record_id": kx108_pre_evidence["decision_record_id"],
        "kx108_pre_evidence_hash": kx108_pre_evidence["evidence_hash"],
        "mailbox_authority_evidence_hash": mailbox_authority["evidence_hash"],
        "target_prestate_hash": current_target_state_hash,
        "decision_authority": DECISION_AUTHORITY,
    }
    call_hash = _hash(call)
    return {
        "status": MAIL_PREPARED,
        "call": call,
        "call_hash": call_hash,
        "connector_invoked": False,
        "message_sent": False,
        "world_action_allowed": True,
        "decision_authority": DECISION_AUTHORITY,
    }


def record_mail_connector_success_v0(
    *,
    prepared: Mapping[str, Any],
    provider_result: Mapping[str, Any],
) -> dict[str, Any]:
    if prepared.get("status") != MAIL_PREPARED:
        return _reject("MAIL_CONNECTOR_CALL_NOT_PREPARED")
    call = prepared.get("call")
    if not isinstance(call, Mapping):
        return _reject("MAIL_CONNECTOR_CALL_MISSING")
    if _hash(call) != prepared.get("call_hash"):
        return _reject("MAIL_CONNECTOR_CALL_HASH_MISMATCH")

    provider_message_id = provider_result.get("id")
    provider_thread_id = provider_result.get("threadId")
    if not provider_message_id or not provider_thread_id:
        return {
            "status": OUTCOME_UNKNOWN,
            "reason": "MAIL_PROVIDER_RESULT_IDENTITY_INCOMPLETE",
            "call_hash": prepared.get("call_hash"),
            "automatic_retry_allowed": False,
            "requires_sent_mail_reconciliation": True,
            "decision_authority": DECISION_AUTHORITY,
        }

    receipt = {
        "schema": "CSSA_MAIL_SEND_RECEIPT_V0",
        "status": MAIL_SEND_RECORDED,
        "mail_plan_id": call["mail_plan_id"],
        "mail_plan_hash": call["mail_plan_hash"],
        "call_hash": prepared["call_hash"],
        "provider": CONNECTOR,
        "provider_message_id": str(provider_message_id),
        "provider_thread_id": str(provider_thread_id),
        "approval_id": call["approval_id"],
        "kx108_pre_decision_record_id": call["kx108_pre_decision_record_id"],
        "target_prestate_hash": call["target_prestate_hash"],
        "decision_authority": DECISION_AUTHORITY,
    }
    receipt["receipt_sha256"] = _hash(receipt)
    return receipt


def record_mail_connector_exception_v0(
    *,
    prepared: Mapping[str, Any],
    exception_class: str,
) -> dict[str, Any]:
    return {
        "status": OUTCOME_UNKNOWN,
        "reason": f"MAIL_CONNECTOR_EXCEPTION:{exception_class}",
        "call_hash": prepared.get("call_hash"),
        "automatic_retry_allowed": False,
        "requires_sent_mail_reconciliation": True,
        "decision_authority": DECISION_AUTHORITY,
    }


def replay_mail_receipt_v0(
    *,
    receipt: Mapping[str, Any],
    plan: MailSendPlanV0,
) -> dict[str, Any]:
    if receipt.get("schema") != "CSSA_MAIL_SEND_RECEIPT_V0":
        return {"status": "FAIL", "reason": "MAIL_RECEIPT_SCHEMA_INVALID"}
    if receipt.get("mail_plan_id") != plan.plan_id:
        return {"status": "FAIL", "reason": "MAIL_RECEIPT_PLAN_ID_MISMATCH"}
    if receipt.get("mail_plan_hash") != plan.plan_hash:
        return {"status": "FAIL", "reason": "MAIL_RECEIPT_PLAN_HASH_MISMATCH"}
    candidate = dict(receipt)
    stored = candidate.pop("receipt_sha256", None)
    if not stored or _hash(candidate) != stored:
        return {"status": "FAIL", "reason": "MAIL_RECEIPT_HASH_MISMATCH"}
    return {
        "status": MAIL_REPLAY_PASS,
        "provider_message_id": receipt["provider_message_id"],
        "provider_thread_id": receipt["provider_thread_id"],
        "resend_required": False,
        "decision_authority": DECISION_AUTHORITY,
    }
