"""F3H-A — CSSA Decision Execution Contract V0.

This is the first operational bridge after F3G closure.

It DOES:
- build immutable action proposals for MAIL / CALENDAR / CRM / TASKS;
- bind exact proposal content with SHA-256;
- require a verified KX108 ALLOW result;
- require separate exact human approval;
- re-check the target/pre-state binding before dry-run;
- emit deterministic dry-run receipts.

It DOES NOT:
- send email;
- mutate a calendar;
- write a CRM;
- create/update tasks in an external service;
- synthesize human approval;
- replace KX108 authority.

Real connector execution remains disabled.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from typing import Any, Mapping

STATUS = "CSSA_DECISION_EXECUTION_CONTRACT_DRY_RUN_V0"
DECISION_AUTHORITY = "KX108_ONLY"

SURFACES = {"MAIL", "CALENDAR", "CRM", "TASKS"}

OPERATIONS = {
    "MAIL": {
        "DRAFT_REPLY",
        "DRAFT_NOTIFICATION",
        "DRAFT_FOLLOWUP",
    },
    "CALENDAR": {
        "PROPOSE_CREATE_EVENT",
        "PROPOSE_UPDATE_EVENT",
        "PROPOSE_CANCEL_EVENT",
    },
    "CRM": {
        "PROPOSE_CREATE_RECORD",
        "PROPOSE_UPDATE_RECORD",
        "PROPOSE_LINK_RECORD",
    },
    "TASKS": {
        "PROPOSE_CREATE_TASK",
        "PROPOSE_UPDATE_TASK",
        "PROPOSE_CLOSE_TASK",
    },
}

PREPARED = "PREPARED_AWAITING_KX108_AND_HUMAN_APPROVAL"
DRY_RUN_READY = "DRY_RUN_READY"
DRY_RUN_COMPLETED = "DRY_RUN_COMPLETED"
REJECTED = "REJECTED_NO_EXTERNAL_ACTION"


def _canonical_hash(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return sha256(raw).hexdigest()


@dataclass(frozen=True)
class ActionProposalV0:
    proposal_id: str
    surface: str
    operation: str
    target_ref: str
    payload: Mapping[str, Any]
    source_case_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    expected_target_state_hash: str
    proposal_hash: str
    requires_human_approval: bool = True
    allowed_to_decide: bool = False
    allowed_to_act: bool = False
    decision_authority: str = DECISION_AUTHORITY
    external_action: bool = False
    world_action_allowed: bool = False

    def assert_non_sovereign(self) -> None:
        if self.decision_authority != DECISION_AUTHORITY:
            raise ValueError("DECISION_AUTHORITY_NOT_KX108_ONLY")
        if self.allowed_to_decide:
            raise ValueError("PROPOSAL_CANNOT_DECIDE")
        if self.allowed_to_act:
            raise ValueError("PROPOSAL_CANNOT_ACT")
        if self.external_action:
            raise ValueError("PROPOSAL_CANNOT_ENABLE_EXTERNAL_ACTION")
        if self.world_action_allowed:
            raise ValueError("PROPOSAL_CANNOT_ENABLE_WORLD_ACTION")


def build_action_proposal_v0(
    *,
    proposal_id: str,
    surface: str,
    operation: str,
    target_ref: str,
    payload: Mapping[str, Any],
    source_case_refs: tuple[str, ...],
    evidence_refs: tuple[str, ...],
    expected_target_state_hash: str,
) -> ActionProposalV0:
    if surface not in SURFACES:
        raise ValueError(f"UNKNOWN_ACTION_SURFACE:{surface}")
    if operation not in OPERATIONS[surface]:
        raise ValueError(f"UNSUPPORTED_SURFACE_OPERATION:{surface}:{operation}")
    if not proposal_id:
        raise ValueError("PROPOSAL_ID_REQUIRED")
    if not target_ref:
        raise ValueError("TARGET_REF_REQUIRED")
    if not source_case_refs:
        raise ValueError("SOURCE_CASE_REF_REQUIRED")
    if not evidence_refs:
        raise ValueError("EVIDENCE_REF_REQUIRED")
    if not isinstance(expected_target_state_hash, str) or len(expected_target_state_hash) != 64:
        raise ValueError("EXPECTED_TARGET_STATE_HASH_REQUIRED")

    bound = {
        "schema": "CSSA_ACTION_PROPOSAL_V0",
        "proposal_id": proposal_id,
        "surface": surface,
        "operation": operation,
        "target_ref": target_ref,
        "payload": payload,
        "source_case_refs": list(source_case_refs),
        "evidence_refs": list(evidence_refs),
        "expected_target_state_hash": expected_target_state_hash,
        "requires_human_approval": True,
        "decision_authority": DECISION_AUTHORITY,
        "external_action": False,
    }
    proposal_hash = _canonical_hash(bound)

    out = ActionProposalV0(
        proposal_id=proposal_id,
        surface=surface,
        operation=operation,
        target_ref=target_ref,
        payload=dict(payload),
        source_case_refs=tuple(source_case_refs),
        evidence_refs=tuple(evidence_refs),
        expected_target_state_hash=expected_target_state_hash,
        proposal_hash=proposal_hash,
    )
    out.assert_non_sovereign()
    return out


def verify_action_proposal_v0(proposal: ActionProposalV0) -> tuple[bool, str | None]:
    proposal.assert_non_sovereign()
    if proposal.surface not in SURFACES:
        return False, "UNKNOWN_ACTION_SURFACE"
    if proposal.operation not in OPERATIONS[proposal.surface]:
        return False, "UNSUPPORTED_SURFACE_OPERATION"

    rebound = {
        "schema": "CSSA_ACTION_PROPOSAL_V0",
        "proposal_id": proposal.proposal_id,
        "surface": proposal.surface,
        "operation": proposal.operation,
        "target_ref": proposal.target_ref,
        "payload": proposal.payload,
        "source_case_refs": list(proposal.source_case_refs),
        "evidence_refs": list(proposal.evidence_refs),
        "expected_target_state_hash": proposal.expected_target_state_hash,
        "requires_human_approval": proposal.requires_human_approval,
        "decision_authority": proposal.decision_authority,
        "external_action": proposal.external_action,
    }
    if _canonical_hash(rebound) != proposal.proposal_hash:
        return False, "PROPOSAL_HASH_MISMATCH"
    return True, None


def build_human_approval_evidence_v0(
    *,
    approval_id: str,
    approved_by: str,
    proposal: ActionProposalV0,
    approval_reference: str,
) -> dict[str, Any]:
    """Build evidence of an explicit human approval.

    This function does not infer approval and does not make approval sovereign.
    """
    if not approval_id:
        raise ValueError("APPROVAL_ID_REQUIRED")
    if not approved_by or approved_by == "MACHINE":
        raise ValueError("EXPLICIT_HUMAN_APPROVER_REQUIRED")
    if not approval_reference:
        raise ValueError("HUMAN_APPROVAL_REFERENCE_REQUIRED")

    record = {
        "schema": "CSSA_HUMAN_ACTION_APPROVAL_V0",
        "approval_id": approval_id,
        "approved_by": approved_by,
        "approval_reference": approval_reference,
        "proposal_id": proposal.proposal_id,
        "proposal_hash": proposal.proposal_hash,
        "surface": proposal.surface,
        "operation": proposal.operation,
        "target_ref": proposal.target_ref,
        "decision_authority": DECISION_AUTHORITY,
        "is_execution_authority": False,
    }
    record["approval_hash"] = _canonical_hash(record)
    return record


def verify_human_approval_evidence_v0(
    approval: Mapping[str, Any] | None,
    proposal: ActionProposalV0,
) -> tuple[bool, str | None]:
    if approval is None:
        return False, "HUMAN_APPROVAL_MISSING"
    if approval.get("schema") != "CSSA_HUMAN_ACTION_APPROVAL_V0":
        return False, "HUMAN_APPROVAL_SCHEMA_INVALID"
    if approval.get("decision_authority") != DECISION_AUTHORITY:
        return False, "HUMAN_APPROVAL_DECISION_AUTHORITY_INVALID"
    if approval.get("is_execution_authority") is not False:
        return False, "HUMAN_APPROVAL_CANNOT_BE_SOVEREIGN"
    if approval.get("proposal_id") != proposal.proposal_id:
        return False, "HUMAN_APPROVAL_PROPOSAL_ID_MISMATCH"
    if approval.get("proposal_hash") != proposal.proposal_hash:
        return False, "HUMAN_APPROVAL_PROPOSAL_HASH_MISMATCH"
    if approval.get("surface") != proposal.surface:
        return False, "HUMAN_APPROVAL_SURFACE_MISMATCH"
    if approval.get("operation") != proposal.operation:
        return False, "HUMAN_APPROVAL_OPERATION_MISMATCH"
    if approval.get("target_ref") != proposal.target_ref:
        return False, "HUMAN_APPROVAL_TARGET_MISMATCH"

    expected = dict(approval)
    stored = expected.pop("approval_hash", None)
    if not stored or _canonical_hash(expected) != stored:
        return False, "HUMAN_APPROVAL_HASH_MISMATCH"
    return True, None


def prepare_dry_run_execution_v0(
    *,
    proposal: ActionProposalV0,
    kx108_gate: str,
    decision_record_verified: bool,
    decision_record_id: str,
    approval: Mapping[str, Any] | None,
    current_target_state_hash: str,
) -> dict[str, Any]:
    ok, reason = verify_action_proposal_v0(proposal)
    if not ok:
        return _reject(reason)

    if not decision_record_verified:
        return _reject("KX108_DECISION_RECORD_NOT_VERIFIED")
    if kx108_gate != "ALLOW":
        return _reject(f"KX108_PRECONDITION_NOT_ALLOW:{kx108_gate}")
    if not decision_record_id:
        return _reject("KX108_DECISION_RECORD_ID_REQUIRED")

    ok_a, reason_a = verify_human_approval_evidence_v0(approval, proposal)
    if not ok_a:
        return _reject(reason_a)

    if current_target_state_hash != proposal.expected_target_state_hash:
        return _reject(
            "TARGET_PRESTATE_HASH_MISMATCH",
            expected_target_state_hash=proposal.expected_target_state_hash,
            current_target_state_hash=current_target_state_hash,
        )

    binding = {
        "schema": "CSSA_DRY_RUN_EXECUTION_BINDING_V0",
        "proposal_id": proposal.proposal_id,
        "proposal_hash": proposal.proposal_hash,
        "approval_id": approval["approval_id"],
        "approval_hash": approval["approval_hash"],
        "kx108_decision_record_id": decision_record_id,
        "kx108_gate": kx108_gate,
        "surface": proposal.surface,
        "operation": proposal.operation,
        "target_ref": proposal.target_ref,
        "current_target_state_hash": current_target_state_hash,
        "decision_authority": DECISION_AUTHORITY,
        "external_action": False,
    }
    binding_hash = _canonical_hash(binding)

    return {
        "status": DRY_RUN_READY,
        "reason": None,
        "binding": binding,
        "binding_hash": binding_hash,
        "decision_authority": DECISION_AUTHORITY,
        "external_action": False,
        "world_action_allowed": False,
        "connector_invoked": False,
        "target_mutated": False,
    }


def execute_surface_dry_run_v0(
    *,
    proposal: ActionProposalV0,
    prepared: Mapping[str, Any],
) -> dict[str, Any]:
    """Produce a deterministic simulated adapter receipt.

    No connector call is performed. This is deliberately not real execution.
    """
    if prepared.get("status") != DRY_RUN_READY:
        return _reject("DRY_RUN_NOT_PREPARED")
    binding = prepared.get("binding")
    if not isinstance(binding, Mapping):
        return _reject("DRY_RUN_BINDING_MISSING")
    if _canonical_hash(binding) != prepared.get("binding_hash"):
        return _reject("DRY_RUN_BINDING_HASH_MISMATCH")
    if binding.get("proposal_hash") != proposal.proposal_hash:
        return _reject("DRY_RUN_PROPOSAL_BINDING_MISMATCH")

    simulated_effect = {
        "MAIL": "MESSAGE_WOULD_BE_DRAFTED_NOT_SENT",
        "CALENDAR": "CALENDAR_MUTATION_WOULD_BE_PROPOSED_NOT_APPLIED",
        "CRM": "CRM_MUTATION_WOULD_BE_PROPOSED_NOT_APPLIED",
        "TASKS": "TASK_MUTATION_WOULD_BE_PROPOSED_NOT_APPLIED",
    }[proposal.surface]

    receipt = {
        "schema": "CSSA_ACTION_DRY_RUN_RECEIPT_V0",
        "status": DRY_RUN_COMPLETED,
        "proposal_id": proposal.proposal_id,
        "proposal_hash": proposal.proposal_hash,
        "binding_hash": prepared["binding_hash"],
        "surface": proposal.surface,
        "operation": proposal.operation,
        "target_ref": proposal.target_ref,
        "simulated_effect": simulated_effect,
        "decision_authority": DECISION_AUTHORITY,
        "external_action": False,
        "world_action_allowed": False,
        "connector_invoked": False,
        "target_mutated": False,
    }
    receipt["receipt_sha256"] = _canonical_hash(receipt)
    return receipt


def _reject(reason: str | None, **extra: Any) -> dict[str, Any]:
    return {
        "status": REJECTED,
        "reason": reason,
        "decision_authority": DECISION_AUTHORITY,
        "external_action": False,
        "world_action_allowed": False,
        "connector_invoked": False,
        "target_mutated": False,
        **extra,
    }


def proposal_runtime_state_v0(
    proposal: ActionProposalV0,
    *,
    valid_at: str,
    confidence: float = 1.0,
    unknowns: tuple[str, ...] = (),
    contradictions: tuple[str, ...] = (),
    risk_flags: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Map a proposal to the existing portable Administration runtime input.

    The KX108 decision is about whether this proposal is structurally eligible
    to proceed to the separate human-approval/dry-run stage. It does not
    authorize world action.
    """
    ok, reason = verify_action_proposal_v0(proposal)
    if not ok:
        raise ValueError(f"INVALID_ACTION_PROPOSAL:{reason}")
    return {
        "case_ref": f"cssa:action-proposal:{proposal.proposal_id}",
        "valid_at": valid_at,
        "source_ref": f"cssa-action-proposal:{proposal.proposal_hash}",
        "unknowns": tuple(unknowns),
        "contradictions": tuple(contradictions),
        "risk_flags": tuple(risk_flags),
        "evidence_refs": proposal.evidence_refs,
        "provenance_refs": proposal.source_case_refs,
        "confidence": float(confidence),
        "surface": proposal.surface,
        "operation": proposal.operation,
        "proposal_hash": proposal.proposal_hash,
    }
