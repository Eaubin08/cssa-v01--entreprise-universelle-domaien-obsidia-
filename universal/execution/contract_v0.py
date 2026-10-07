"""Universal Decision-Execution Contract V0.

This module is domain-agnostic and connector-agnostic.

A business domain may:
- translate its own facts into an action proposal;
- select an explicitly registered execution surface/operation;
- attach evidence and an exact expected target pre-state.

It may NOT:
- decide;
- grant execution authority;
- bypass KX108;
- bypass required human approval;
- activate external world action;
- mutate memory/kernel/runtime authority.

The contract deliberately supports arbitrary future métier domains without
hardcoding football, finance, GPS, e-commerce, legal, logistics, etc.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

DECISION_AUTHORITY = "KX108_ONLY"

EFFECT_INTERNAL = "INTERNAL_BOUNDED"
EFFECT_COMMUNICATION = "EXTERNAL_COMMUNICATION"
EFFECT_DATA_MUTATION = "EXTERNAL_DATA_MUTATION"
EFFECT_FINANCIAL = "EXTERNAL_FINANCIAL"
EFFECT_PHYSICAL = "EXTERNAL_PHYSICAL"

EXTERNAL_EFFECT_CLASSES = {
    EFFECT_COMMUNICATION,
    EFFECT_DATA_MUTATION,
    EFFECT_FINANCIAL,
    EFFECT_PHYSICAL,
}


class UniversalExecutionContractError(ValueError):
    pass


def canonical_sha256_v0(value: Mapping[str, Any]) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return sha256(raw).hexdigest()


@dataclass(frozen=True)
class ExecutionSurfaceRegistrationV0:
    surface_id: str
    operation_ids: tuple[str, ...]
    effect_class: str
    connector_id: str | None = None
    requires_human_approval: bool = True
    decision_authority: str = DECISION_AUTHORITY
    allowed_to_decide: bool = False
    allowed_to_act: bool = False
    emits_act: bool = False
    kernel_mutation: bool = False
    memory_write: bool = False

    def __post_init__(self) -> None:
        if not self.surface_id or self.surface_id.strip() != self.surface_id:
            raise UniversalExecutionContractError(
                "surface_id must be non-empty and trimmed"
            )
        if not self.operation_ids:
            raise UniversalExecutionContractError(
                "at least one operation_id is required"
            )
        if any(not value or value.strip() != value for value in self.operation_ids):
            raise UniversalExecutionContractError(
                "operation_ids must be non-empty and trimmed"
            )
        if len(set(self.operation_ids)) != len(self.operation_ids):
            raise UniversalExecutionContractError(
                "duplicate operation_id"
            )
        if self.effect_class not in {
            EFFECT_INTERNAL,
            EFFECT_COMMUNICATION,
            EFFECT_DATA_MUTATION,
            EFFECT_FINANCIAL,
            EFFECT_PHYSICAL,
        }:
            raise UniversalExecutionContractError(
                f"unsupported effect_class:{self.effect_class}"
            )
        if self.effect_class in EXTERNAL_EFFECT_CLASSES and not self.connector_id:
            raise UniversalExecutionContractError(
                "external surface requires connector_id"
            )
        if self.decision_authority != DECISION_AUTHORITY:
            raise UniversalExecutionContractError(
                "decision authority must remain KX108_ONLY"
            )
        if any((
            self.allowed_to_decide,
            self.allowed_to_act,
            self.emits_act,
            self.kernel_mutation,
            self.memory_write,
        )):
            raise UniversalExecutionContractError(
                "surface registration cannot grant authority"
            )


class UniversalExecutionSurfaceRegistryV0:
    def __init__(self) -> None:
        self._items: dict[str, ExecutionSurfaceRegistrationV0] = {}

    def register(self, item: ExecutionSurfaceRegistrationV0) -> None:
        if item.surface_id in self._items:
            raise UniversalExecutionContractError(
                f"duplicate execution surface:{item.surface_id}"
            )
        self._items[item.surface_id] = item

    def get(self, surface_id: str) -> ExecutionSurfaceRegistrationV0:
        try:
            return self._items[surface_id]
        except KeyError as exc:
            raise UniversalExecutionContractError(
                f"UNREGISTERED_EXECUTION_SURFACE:{surface_id}"
            ) from exc

    def surfaces(self) -> tuple[str, ...]:
        return tuple(sorted(self._items))


@dataclass(frozen=True)
class UniversalActionProposalV0:
    proposal_id: str
    domain_id: str
    surface_id: str
    operation_id: str
    target_ref: str
    payload: Mapping[str, Any]
    source_case_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    expected_target_state_hash: str
    effect_class: str
    connector_id: str | None
    requires_human_approval: bool
    proposal_hash: str
    decision_authority: str = DECISION_AUTHORITY
    allowed_to_decide: bool = False
    allowed_to_act: bool = False
    emits_act: bool = False
    kernel_mutation: bool = False
    memory_write: bool = False

    def assert_non_sovereign(self) -> None:
        if self.decision_authority != DECISION_AUTHORITY:
            raise UniversalExecutionContractError(
                "proposal changed decision authority"
            )
        if any((
            self.allowed_to_decide,
            self.allowed_to_act,
            self.emits_act,
            self.kernel_mutation,
            self.memory_write,
        )):
            raise UniversalExecutionContractError(
                "proposal leaked execution authority"
            )


def _proposal_payload(
    *,
    proposal_id: str,
    domain_id: str,
    surface: ExecutionSurfaceRegistrationV0,
    operation_id: str,
    target_ref: str,
    payload: Mapping[str, Any],
    source_case_refs: tuple[str, ...],
    evidence_refs: tuple[str, ...],
    expected_target_state_hash: str,
) -> dict[str, Any]:
    return {
        "schema": "UNIVERSAL_ACTION_PROPOSAL_V0",
        "proposal_id": proposal_id,
        "domain_id": domain_id,
        "surface_id": surface.surface_id,
        "operation_id": operation_id,
        "target_ref": target_ref,
        "payload": dict(payload),
        "source_case_refs": list(source_case_refs),
        "evidence_refs": list(evidence_refs),
        "expected_target_state_hash": expected_target_state_hash,
        "effect_class": surface.effect_class,
        "connector_id": surface.connector_id,
        "requires_human_approval": surface.requires_human_approval,
        "decision_authority": DECISION_AUTHORITY,
    }


def build_universal_action_proposal_v0(
    *,
    registry: UniversalExecutionSurfaceRegistryV0,
    proposal_id: str,
    domain_id: str,
    surface_id: str,
    operation_id: str,
    target_ref: str,
    payload: Mapping[str, Any],
    source_case_refs: tuple[str, ...],
    evidence_refs: tuple[str, ...],
    expected_target_state_hash: str,
) -> UniversalActionProposalV0:
    surface = registry.get(surface_id)
    if operation_id not in surface.operation_ids:
        raise UniversalExecutionContractError(
            f"UNREGISTERED_SURFACE_OPERATION:{surface_id}:{operation_id}"
        )
    if not proposal_id:
        raise UniversalExecutionContractError("proposal_id is required")
    if not domain_id:
        raise UniversalExecutionContractError("domain_id is required")
    if not target_ref:
        raise UniversalExecutionContractError("target_ref is required")
    if not source_case_refs:
        raise UniversalExecutionContractError("source_case_refs are required")
    if not evidence_refs:
        raise UniversalExecutionContractError("evidence_refs are required")
    if len(expected_target_state_hash) != 64:
        raise UniversalExecutionContractError(
            "expected_target_state_hash must be sha256"
        )

    bound = _proposal_payload(
        proposal_id=proposal_id,
        domain_id=domain_id,
        surface=surface,
        operation_id=operation_id,
        target_ref=target_ref,
        payload=payload,
        source_case_refs=source_case_refs,
        evidence_refs=evidence_refs,
        expected_target_state_hash=expected_target_state_hash,
    )
    proposal = UniversalActionProposalV0(
        proposal_id=proposal_id,
        domain_id=domain_id,
        surface_id=surface_id,
        operation_id=operation_id,
        target_ref=target_ref,
        payload=dict(payload),
        source_case_refs=tuple(source_case_refs),
        evidence_refs=tuple(evidence_refs),
        expected_target_state_hash=expected_target_state_hash,
        effect_class=surface.effect_class,
        connector_id=surface.connector_id,
        requires_human_approval=surface.requires_human_approval,
        proposal_hash=canonical_sha256_v0(bound),
    )
    proposal.assert_non_sovereign()
    return proposal


def verify_universal_action_proposal_v0(
    *,
    registry: UniversalExecutionSurfaceRegistryV0,
    proposal: UniversalActionProposalV0,
) -> tuple[bool, str | None]:
    try:
        proposal.assert_non_sovereign()
        surface = registry.get(proposal.surface_id)
    except UniversalExecutionContractError as exc:
        return False, str(exc)

    if proposal.operation_id not in surface.operation_ids:
        return False, "UNREGISTERED_SURFACE_OPERATION"
    if proposal.effect_class != surface.effect_class:
        return False, "PROPOSAL_EFFECT_CLASS_MISMATCH"
    if proposal.connector_id != surface.connector_id:
        return False, "PROPOSAL_CONNECTOR_MISMATCH"
    if proposal.requires_human_approval != surface.requires_human_approval:
        return False, "PROPOSAL_APPROVAL_POLICY_MISMATCH"

    rebound = _proposal_payload(
        proposal_id=proposal.proposal_id,
        domain_id=proposal.domain_id,
        surface=surface,
        operation_id=proposal.operation_id,
        target_ref=proposal.target_ref,
        payload=proposal.payload,
        source_case_refs=proposal.source_case_refs,
        evidence_refs=proposal.evidence_refs,
        expected_target_state_hash=proposal.expected_target_state_hash,
    )
    if canonical_sha256_v0(rebound) != proposal.proposal_hash:
        return False, "PROPOSAL_HASH_MISMATCH"
    return True, None


def build_universal_human_approval_v0(
    *,
    approval_id: str,
    approved_by: str,
    approval_reference: str,
    proposal: UniversalActionProposalV0,
) -> dict[str, Any]:
    if not approval_id or not approved_by or not approval_reference:
        raise UniversalExecutionContractError(
            "explicit approval identity/reference required"
        )
    if approved_by == "MACHINE":
        raise UniversalExecutionContractError(
            "machine cannot synthesize human approval"
        )

    record = {
        "schema": "UNIVERSAL_HUMAN_ACTION_APPROVAL_V0",
        "approval_id": approval_id,
        "approved_by": approved_by,
        "approval_reference": approval_reference,
        "proposal_id": proposal.proposal_id,
        "proposal_hash": proposal.proposal_hash,
        "domain_id": proposal.domain_id,
        "surface_id": proposal.surface_id,
        "operation_id": proposal.operation_id,
        "target_ref": proposal.target_ref,
        "expected_target_state_hash": proposal.expected_target_state_hash,
        "decision_authority": DECISION_AUTHORITY,
        "is_execution_authority": False,
    }
    record["approval_hash"] = canonical_sha256_v0(record)
    return record


def verify_universal_human_approval_v0(
    *,
    approval: Mapping[str, Any] | None,
    proposal: UniversalActionProposalV0,
) -> tuple[bool, str | None]:
    if proposal.requires_human_approval and approval is None:
        return False, "HUMAN_APPROVAL_MISSING"
    if approval is None:
        return True, None
    if approval.get("schema") != "UNIVERSAL_HUMAN_ACTION_APPROVAL_V0":
        return False, "HUMAN_APPROVAL_SCHEMA_INVALID"
    if approval.get("decision_authority") != DECISION_AUTHORITY:
        return False, "HUMAN_APPROVAL_AUTHORITY_INVALID"
    if approval.get("is_execution_authority") is not False:
        return False, "HUMAN_APPROVAL_CANNOT_BE_SOVEREIGN"

    expected = {
        "proposal_id": proposal.proposal_id,
        "proposal_hash": proposal.proposal_hash,
        "domain_id": proposal.domain_id,
        "surface_id": proposal.surface_id,
        "operation_id": proposal.operation_id,
        "target_ref": proposal.target_ref,
        "expected_target_state_hash": proposal.expected_target_state_hash,
    }
    for key, value in expected.items():
        if approval.get(key) != value:
            return False, f"HUMAN_APPROVAL_{key.upper()}_MISMATCH"

    candidate = dict(approval)
    stored = candidate.pop("approval_hash", None)
    if not stored or canonical_sha256_v0(candidate) != stored:
        return False, "HUMAN_APPROVAL_HASH_MISMATCH"
    return True, None


def assess_universal_execution_readiness_v0(
    *,
    proposal: UniversalActionProposalV0,
    approval: Mapping[str, Any] | None,
    current_target_state_hash: str,
    kx108_gate: str,
    kx108_decision_record_verified: bool,
    upstream_world_action_activated: bool,
    upstream_missing_runtime_links: tuple[str, ...],
) -> dict[str, Any]:
    """Common final readiness gate.

    This does not execute anything. External actions remain blocked whenever
    the upstream world-action runtime is not activated.
    """
    if kx108_gate != "ALLOW":
        return _readiness_reject(f"KX108_NOT_ALLOW:{kx108_gate}")
    if not kx108_decision_record_verified:
        return _readiness_reject("KX108_DECISION_RECORD_NOT_VERIFIED")
    ok, reason = verify_universal_human_approval_v0(
        approval=approval,
        proposal=proposal,
    )
    if not ok:
        return _readiness_reject(reason or "HUMAN_APPROVAL_INVALID")
    if current_target_state_hash != proposal.expected_target_state_hash:
        return _readiness_reject("TARGET_PRESTATE_HASH_MISMATCH")

    if proposal.effect_class in EXTERNAL_EFFECT_CLASSES:
        if not upstream_world_action_activated:
            return _readiness_reject(
                "EXTERNAL_WORLD_ACTUATION_NOT_ACTIVATED",
                missing_runtime_links=tuple(upstream_missing_runtime_links),
            )

    return {
        "status": "READY_FOR_REGISTERED_EXECUTION_SURFACE",
        "reason": None,
        "proposal_hash": proposal.proposal_hash,
        "domain_id": proposal.domain_id,
        "surface_id": proposal.surface_id,
        "operation_id": proposal.operation_id,
        "effect_class": proposal.effect_class,
        "connector_id": proposal.connector_id,
        "decision_authority": DECISION_AUTHORITY,
        "execution_performed": False,
    }


def _readiness_reject(reason: str, **extra: Any) -> dict[str, Any]:
    return {
        "status": "EXECUTION_NOT_READY",
        "reason": reason,
        "decision_authority": DECISION_AUTHORITY,
        "execution_performed": False,
        **extra,
    }


def build_universal_provider_receipt_contract_v0(
    *,
    proposal: UniversalActionProposalV0,
    execution_call_hash: str,
    provider_result_identity: Mapping[str, Any],
    real_execution_proven: bool,
) -> dict[str, Any]:
    """Generic receipt shape.

    Production callers must set real_execution_proven only from actual connector
    evidence. Unit tests should keep it False.
    """
    receipt = {
        "schema": "UNIVERSAL_PROVIDER_RECEIPT_V0",
        "proposal_id": proposal.proposal_id,
        "proposal_hash": proposal.proposal_hash,
        "domain_id": proposal.domain_id,
        "surface_id": proposal.surface_id,
        "operation_id": proposal.operation_id,
        "execution_call_hash": execution_call_hash,
        "provider_result_identity": dict(provider_result_identity),
        "real_execution_proven": bool(real_execution_proven),
        "decision_authority": DECISION_AUTHORITY,
    }
    receipt["receipt_sha256"] = canonical_sha256_v0(receipt)
    return receipt


def replay_universal_provider_receipt_v0(
    *,
    proposal: UniversalActionProposalV0,
    receipt: Mapping[str, Any],
) -> dict[str, Any]:
    if receipt.get("schema") != "UNIVERSAL_PROVIDER_RECEIPT_V0":
        return {"status": "FAIL", "reason": "RECEIPT_SCHEMA_INVALID"}
    if receipt.get("proposal_id") != proposal.proposal_id:
        return {"status": "FAIL", "reason": "RECEIPT_PROPOSAL_ID_MISMATCH"}
    if receipt.get("proposal_hash") != proposal.proposal_hash:
        return {"status": "FAIL", "reason": "RECEIPT_PROPOSAL_HASH_MISMATCH"}
    candidate = dict(receipt)
    stored = candidate.pop("receipt_sha256", None)
    if not stored or canonical_sha256_v0(candidate) != stored:
        return {"status": "FAIL", "reason": "RECEIPT_HASH_MISMATCH"}
    return {
        "status": "PASS",
        "real_execution_proven": bool(receipt.get("real_execution_proven")),
        "decision_authority": DECISION_AUTHORITY,
    }
