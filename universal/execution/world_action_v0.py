"""F3H-C — Universal World Action PRE-Execution Rail V0.

Domain-agnostic contract between a verified UniversalActionProposal and a
future real external connector call.

Current upstream Obsidia remains dry-run only. This module therefore:
- binds exact connector calls and operation policy;
- binds explicit human approval to the exact world-action request;
- derives deterministic idempotency keys;
- defines the future sovereign WORLD_ACTION_PRE_EXECUTION evidence contract;
- detects duplicate/unknown prior attempts;
- defines provider outcome / receipt / replay semantics;
- bridges to the existing SovereignTicket/Gateway/WorldActionBus dry-run
  components without treating them as live egress authority;
- fails closed until the upstream world-action runtime is truly activated.

It never calls an external connector itself.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .contract_v0 import (
    DECISION_AUTHORITY,
    EXTERNAL_EFFECT_CLASSES,
    UniversalActionProposalV0,
    UniversalExecutionContractError,
    UniversalExecutionSurfaceRegistryV0,
    canonical_sha256_v0,
    verify_universal_action_proposal_v0,
)

WORLD_ACTION_PRE_PHASE = "WORLD_ACTION_PRE_EXECUTION"

WCC_READ_ONLY = "READ_ONLY_WORLD_CALL"
WCC_REVERSIBLE = "REVERSIBLE_WORLD_CALL"
WCC_IRREVERSIBLE = "IRREVERSIBLE_WORLD_CALL"
WCC_CRITICAL = "CRITICAL_WORLD_CALL"
WCC_FORBIDDEN = "FORBIDDEN_WORLD_CALL"

ARC_EXTERNAL_API = "ACTION_EXTERNAL_API"
ARC_FINANCIAL = "ACTION_FINANCIAL"
ARC_COMPLIANCE = "ACTION_COMPLIANCE_BOUND"
ARC_SENSITIVE = "ACTION_SENSITIVE"
ARC_IRREVERSIBLE = "ACTION_IRREVERSIBLE"
ARC_FORBIDDEN = "ACTION_FORBIDDEN"

AUTONOMY_LEVELS = {3, 4, 5}

RETRY_NEVER_ON_UNKNOWN = "NEVER_AUTORETRY_ON_UNKNOWN"
RETRY_IDEMPOTENT_AFTER_RECONCILIATION = (
    "IDEMPOTENT_RETRY_ONLY_AFTER_RECONCILIATION"
)

PRE_EXECUTION_BLOCKED = "WORLD_ACTION_PRE_EXECUTION_BLOCKED"
PRE_EXECUTION_READY = "WORLD_ACTION_PRE_EXECUTION_READY"
OUTCOME_CONFIRMED = "WORLD_ACTION_OUTCOME_CONFIRMED"
OUTCOME_NO_EFFECT = "WORLD_ACTION_FAILED_NO_EFFECT"
OUTCOME_UNKNOWN = "WORLD_ACTION_OUTCOME_UNKNOWN_REQUIRES_RECONCILIATION"

CANONICAL_WORLD_BLOCKER = "EXTERNAL_WORLD_ACTUATION_NOT_ACTIVATED"
CANONICAL_REAL_EXECUTION_BLOCKER = (
    "REAL_X108_GATED_EXECUTION_PATH_NOT_ACTIVATED"
)

_SECRET_KEY_FRAGMENTS = (
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "private_key",
    "access_key",
)


@dataclass(frozen=True)
class WorldActionOperationPolicyV0:
    surface_id: str
    operation_id: str
    connector_id: str
    connector_action: str
    required_scope: str
    world_call_class: str
    action_risk_class: str
    autonomy_level: int
    retry_policy: str
    irreversible: bool
    requires_human_approval: bool = True
    decision_authority: str = DECISION_AUTHORITY
    allowed_to_decide: bool = False
    allowed_to_act: bool = False
    emits_act: bool = False
    memory_write: bool = False
    kernel_mutation: bool = False

    def __post_init__(self) -> None:
        required = (
            self.surface_id,
            self.operation_id,
            self.connector_id,
            self.connector_action,
            self.required_scope,
        )
        if any(not value or value.strip() != value for value in required):
            raise UniversalExecutionContractError(
                "world-action policy identifiers must be non-empty and trimmed"
            )
        if self.world_call_class not in {
            WCC_READ_ONLY,
            WCC_REVERSIBLE,
            WCC_IRREVERSIBLE,
            WCC_CRITICAL,
            WCC_FORBIDDEN,
        }:
            raise UniversalExecutionContractError(
                f"unsupported world_call_class:{self.world_call_class}"
            )
        if self.action_risk_class not in {
            ARC_EXTERNAL_API,
            ARC_FINANCIAL,
            ARC_COMPLIANCE,
            ARC_SENSITIVE,
            ARC_IRREVERSIBLE,
            ARC_FORBIDDEN,
        }:
            raise UniversalExecutionContractError(
                f"unsupported action_risk_class:{self.action_risk_class}"
            )
        if self.autonomy_level not in AUTONOMY_LEVELS:
            raise UniversalExecutionContractError(
                f"unsupported autonomy_level:{self.autonomy_level}"
            )
        if self.retry_policy not in {
            RETRY_NEVER_ON_UNKNOWN,
            RETRY_IDEMPOTENT_AFTER_RECONCILIATION,
        }:
            raise UniversalExecutionContractError(
                f"unsupported retry_policy:{self.retry_policy}"
            )
        if self.decision_authority != DECISION_AUTHORITY:
            raise UniversalExecutionContractError(
                "world-action policy must remain KX108_ONLY"
            )
        if any((
            self.allowed_to_decide,
            self.allowed_to_act,
            self.emits_act,
            self.memory_write,
            self.kernel_mutation,
        )):
            raise UniversalExecutionContractError(
                "world-action policy cannot grant authority"
            )
        if self.irreversible and self.world_call_class != WCC_IRREVERSIBLE:
            raise UniversalExecutionContractError(
                "irreversible policy must use IRREVERSIBLE_WORLD_CALL"
            )


class WorldActionPolicyRegistryV0:
    def __init__(
        self,
        *,
        surface_registry: UniversalExecutionSurfaceRegistryV0,
    ) -> None:
        self.surface_registry = surface_registry
        self._policies: dict[
            tuple[str, str],
            WorldActionOperationPolicyV0,
        ] = {}

    def register(self, policy: WorldActionOperationPolicyV0) -> None:
        surface = self.surface_registry.get(policy.surface_id)
        if policy.operation_id not in surface.operation_ids:
            raise UniversalExecutionContractError(
                f"WORLD_ACTION_OPERATION_NOT_ON_SURFACE:"
                f"{policy.surface_id}:{policy.operation_id}"
            )
        if surface.effect_class not in EXTERNAL_EFFECT_CLASSES:
            raise UniversalExecutionContractError(
                "world-action policy requires external effect surface"
            )
        if surface.connector_id != policy.connector_id:
            raise UniversalExecutionContractError(
                "world-action policy connector mismatch"
            )
        if surface.requires_human_approval != policy.requires_human_approval:
            raise UniversalExecutionContractError(
                "world-action policy human-approval mismatch"
            )
        key = (policy.surface_id, policy.operation_id)
        if key in self._policies:
            raise UniversalExecutionContractError(
                f"duplicate world-action policy:{key[0]}:{key[1]}"
            )
        self._policies[key] = policy

    def get(
        self,
        surface_id: str,
        operation_id: str,
    ) -> WorldActionOperationPolicyV0:
        try:
            return self._policies[(surface_id, operation_id)]
        except KeyError as exc:
            raise UniversalExecutionContractError(
                f"UNREGISTERED_WORLD_ACTION_POLICY:"
                f"{surface_id}:{operation_id}"
            ) from exc


@dataclass(frozen=True)
class WorldActionRequestV0:
    request_id: str
    proposal_id: str
    proposal_hash: str
    domain_id: str
    surface_id: str
    operation_id: str
    effect_class: str
    connector_id: str
    connector_action: str
    connector_args: Mapping[str, Any]
    connector_call_hash: str
    target_ref: str
    target_prestate_hash: str
    required_scope: str
    world_call_class: str
    action_risk_class: str
    autonomy_level: int
    irreversible: bool
    retry_policy: str
    idempotency_key: str
    request_hash: str
    decision_authority: str = DECISION_AUTHORITY
    allowed_to_decide: bool = False
    allowed_to_act: bool = False
    emits_act: bool = False

    def assert_non_sovereign(self) -> None:
        if self.decision_authority != DECISION_AUTHORITY:
            raise UniversalExecutionContractError(
                "world-action request changed decision authority"
            )
        if any((
            self.allowed_to_decide,
            self.allowed_to_act,
            self.emits_act,
        )):
            raise UniversalExecutionContractError(
                "world-action request leaked authority"
            )


def _assert_no_secret_fields(value: Any, path: str = "connector_args") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            lowered = str(key).lower()
            if any(fragment in lowered for fragment in _SECRET_KEY_FRAGMENTS):
                raise UniversalExecutionContractError(
                    f"SECRET_FIELD_FORBIDDEN_IN_ACTION_PAYLOAD:{path}.{key}"
                )
            _assert_no_secret_fields(child, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _assert_no_secret_fields(child, f"{path}[{index}]")


def build_world_action_request_v0(
    *,
    surface_registry: UniversalExecutionSurfaceRegistryV0,
    policy_registry: WorldActionPolicyRegistryV0,
    proposal: UniversalActionProposalV0,
    request_id: str,
    connector_action: str,
    connector_args: Mapping[str, Any],
    current_target_state_hash: str,
) -> WorldActionRequestV0:
    ok, reason = verify_universal_action_proposal_v0(
        registry=surface_registry,
        proposal=proposal,
    )
    if not ok:
        raise UniversalExecutionContractError(
            f"INVALID_UNIVERSAL_ACTION_PROPOSAL:{reason}"
        )
    if proposal.effect_class not in EXTERNAL_EFFECT_CLASSES:
        raise UniversalExecutionContractError(
            "world-action request requires external effect proposal"
        )
    if current_target_state_hash != proposal.expected_target_state_hash:
        raise UniversalExecutionContractError(
            "TARGET_PRESTATE_HASH_MISMATCH"
        )
    policy = policy_registry.get(
        proposal.surface_id,
        proposal.operation_id,
    )
    if connector_action != policy.connector_action:
        raise UniversalExecutionContractError(
            "CONNECTOR_ACTION_POLICY_MISMATCH"
        )
    _assert_no_secret_fields(connector_args)

    connector_call = {
        "connector_id": policy.connector_id,
        "connector_action": connector_action,
        "connector_args": dict(connector_args),
    }
    connector_call_hash = canonical_sha256_v0(connector_call)
    idempotency_key = canonical_sha256_v0({
        "schema": "UNIVERSAL_WORLD_ACTION_IDEMPOTENCY_V0",
        "proposal_hash": proposal.proposal_hash,
        "connector_call_hash": connector_call_hash,
        "target_prestate_hash": current_target_state_hash,
        "required_scope": policy.required_scope,
    })
    bound = {
        "schema": "UNIVERSAL_WORLD_ACTION_REQUEST_V0",
        "request_id": request_id,
        "proposal_id": proposal.proposal_id,
        "proposal_hash": proposal.proposal_hash,
        "domain_id": proposal.domain_id,
        "surface_id": proposal.surface_id,
        "operation_id": proposal.operation_id,
        "effect_class": proposal.effect_class,
        "connector_id": policy.connector_id,
        "connector_action": connector_action,
        "connector_args": dict(connector_args),
        "connector_call_hash": connector_call_hash,
        "target_ref": proposal.target_ref,
        "target_prestate_hash": current_target_state_hash,
        "required_scope": policy.required_scope,
        "world_call_class": policy.world_call_class,
        "action_risk_class": policy.action_risk_class,
        "autonomy_level": policy.autonomy_level,
        "irreversible": policy.irreversible,
        "retry_policy": policy.retry_policy,
        "idempotency_key": idempotency_key,
        "decision_authority": DECISION_AUTHORITY,
    }
    request = WorldActionRequestV0(
        request_id=request_id,
        proposal_id=proposal.proposal_id,
        proposal_hash=proposal.proposal_hash,
        domain_id=proposal.domain_id,
        surface_id=proposal.surface_id,
        operation_id=proposal.operation_id,
        effect_class=proposal.effect_class,
        connector_id=policy.connector_id,
        connector_action=connector_action,
        connector_args=dict(connector_args),
        connector_call_hash=connector_call_hash,
        target_ref=proposal.target_ref,
        target_prestate_hash=current_target_state_hash,
        required_scope=policy.required_scope,
        world_call_class=policy.world_call_class,
        action_risk_class=policy.action_risk_class,
        autonomy_level=policy.autonomy_level,
        irreversible=policy.irreversible,
        retry_policy=policy.retry_policy,
        idempotency_key=idempotency_key,
        request_hash=canonical_sha256_v0(bound),
    )
    request.assert_non_sovereign()
    return request


def build_world_action_human_approval_v0(
    *,
    approval_id: str,
    approved_by: str,
    approval_reference: str,
    request: WorldActionRequestV0,
) -> dict[str, Any]:
    request.assert_non_sovereign()
    if not approval_id or not approved_by or not approval_reference:
        raise UniversalExecutionContractError(
            "explicit world-action human approval required"
        )
    if approved_by == "MACHINE":
        raise UniversalExecutionContractError(
            "machine cannot synthesize world-action human approval"
        )
    record = {
        "schema": "UNIVERSAL_WORLD_ACTION_HUMAN_APPROVAL_V0",
        "approval_id": approval_id,
        "approved_by": approved_by,
        "approval_reference": approval_reference,
        "request_id": request.request_id,
        "request_hash": request.request_hash,
        "proposal_hash": request.proposal_hash,
        "domain_id": request.domain_id,
        "surface_id": request.surface_id,
        "operation_id": request.operation_id,
        "connector_id": request.connector_id,
        "connector_action": request.connector_action,
        "connector_call_hash": request.connector_call_hash,
        "target_ref": request.target_ref,
        "target_prestate_hash": request.target_prestate_hash,
        "required_scope": request.required_scope,
        "idempotency_key": request.idempotency_key,
        "decision_authority": DECISION_AUTHORITY,
        "is_execution_authority": False,
    }
    record["approval_hash"] = canonical_sha256_v0(record)
    return record


def verify_world_action_human_approval_v0(
    *,
    approval: Mapping[str, Any] | None,
    request: WorldActionRequestV0,
) -> tuple[bool, str | None]:
    if approval is None:
        return False, "WORLD_ACTION_HUMAN_APPROVAL_MISSING"
    if approval.get("schema") != "UNIVERSAL_WORLD_ACTION_HUMAN_APPROVAL_V0":
        return False, "WORLD_ACTION_HUMAN_APPROVAL_SCHEMA_INVALID"
    if approval.get("decision_authority") != DECISION_AUTHORITY:
        return False, "WORLD_ACTION_HUMAN_APPROVAL_AUTHORITY_INVALID"
    if approval.get("is_execution_authority") is not False:
        return False, "WORLD_ACTION_HUMAN_APPROVAL_CANNOT_BE_SOVEREIGN"
    expected = {
        "request_id": request.request_id,
        "request_hash": request.request_hash,
        "proposal_hash": request.proposal_hash,
        "domain_id": request.domain_id,
        "surface_id": request.surface_id,
        "operation_id": request.operation_id,
        "connector_id": request.connector_id,
        "connector_action": request.connector_action,
        "connector_call_hash": request.connector_call_hash,
        "target_ref": request.target_ref,
        "target_prestate_hash": request.target_prestate_hash,
        "required_scope": request.required_scope,
        "idempotency_key": request.idempotency_key,
    }
    for key, value in expected.items():
        if approval.get(key) != value:
            return False, f"WORLD_ACTION_HUMAN_APPROVAL_{key.upper()}_MISMATCH"
    candidate = dict(approval)
    stored = candidate.pop("approval_hash", None)
    if not stored or canonical_sha256_v0(candidate) != stored:
        return False, "WORLD_ACTION_HUMAN_APPROVAL_HASH_MISMATCH"
    return True, None


def build_world_action_pre_context_v0(
    request: WorldActionRequestV0,
    *,
    valid_at: str,
    evidence_refs: Sequence[str],
    world_action_approval: Mapping[str, Any],
    unknowns: Sequence[str] = (),
    contradictions: Sequence[str] = (),
    risk_flags: Sequence[str] = (),
) -> dict[str, Any]:
    request.assert_non_sovereign()
    ok, reason = verify_world_action_human_approval_v0(
        approval=world_action_approval,
        request=request,
    )
    if not ok:
        raise UniversalExecutionContractError(
            f"INVALID_WORLD_ACTION_HUMAN_APPROVAL:{reason}"
        )
    if not evidence_refs:
        raise UniversalExecutionContractError(
            "WORLD_ACTION_PRE_EVIDENCE_REFS_REQUIRED"
        )
    return {
        "schema": "UNIVERSAL_WORLD_ACTION_PRE_CONTEXT_V0",
        "decision_phase": WORLD_ACTION_PRE_PHASE,
        "case_ref": f"world-action:{request.request_hash}",
        "valid_at": valid_at,
        "domain_id": request.domain_id,
        "proposal_hash": request.proposal_hash,
        "world_action_request_hash": request.request_hash,
        "connector_call_hash": request.connector_call_hash,
        "target_prestate_hash": request.target_prestate_hash,
        "world_action_approval_hash": world_action_approval["approval_hash"],
        "required_scope": request.required_scope,
        "world_call_class": request.world_call_class,
        "action_risk_class": request.action_risk_class,
        "autonomy_level": request.autonomy_level,
        "irreversible": request.irreversible,
        "idempotency_key": request.idempotency_key,
        "unknowns": tuple(unknowns),
        "contradictions": tuple(contradictions),
        "risk_flags": tuple(risk_flags),
        "evidence_refs": tuple(evidence_refs),
        "decision_authority": DECISION_AUTHORITY,
        "allowed_to_act": False,
    }


def verify_world_action_pre_evidence_v0(
    evidence: Mapping[str, Any] | None,
    *,
    request: WorldActionRequestV0,
    world_action_approval: Mapping[str, Any],
) -> tuple[bool, str | None]:
    if evidence is None:
        return False, "WORLD_ACTION_PRE_EVIDENCE_MISSING"
    if evidence.get("schema") != "UNIVERSAL_WORLD_ACTION_PRE_EVIDENCE_V0":
        return False, "WORLD_ACTION_PRE_EVIDENCE_SCHEMA_INVALID"
    if evidence.get("decision_phase") != WORLD_ACTION_PRE_PHASE:
        return False, "WORLD_ACTION_PRE_PHASE_INVALID"
    if evidence.get("decision_authority") != DECISION_AUTHORITY:
        return False, "WORLD_ACTION_PRE_AUTHORITY_INVALID"
    if evidence.get("x108_gate") != "ALLOW":
        return False, "WORLD_ACTION_PRE_GATE_NOT_ALLOW"

    ok, reason = verify_world_action_human_approval_v0(
        approval=world_action_approval,
        request=request,
    )
    if not ok:
        return False, reason

    expected = {
        "proposal_hash": request.proposal_hash,
        "world_action_request_hash": request.request_hash,
        "connector_call_hash": request.connector_call_hash,
        "target_prestate_hash": request.target_prestate_hash,
        "world_action_approval_hash": world_action_approval["approval_hash"],
        "required_scope": request.required_scope,
        "world_call_class": request.world_call_class,
        "action_risk_class": request.action_risk_class,
        "autonomy_level": request.autonomy_level,
        "idempotency_key": request.idempotency_key,
    }
    for key, value in expected.items():
        if evidence.get(key) != value:
            return False, f"WORLD_ACTION_PRE_{key.upper()}_MISMATCH"
    if not evidence.get("decision_record_id"):
        return False, "WORLD_ACTION_PRE_DECISION_RECORD_ID_MISSING"
    if not evidence.get("decision_record_hash"):
        return False, "WORLD_ACTION_PRE_DECISION_RECORD_HASH_MISSING"
    if not evidence.get("sovereign_ticket_id"):
        return False, "WORLD_ACTION_PRE_SOVEREIGN_TICKET_ID_MISSING"
    if evidence.get("dry_run_only") is not False:
        return False, "WORLD_ACTION_PRE_MUST_NOT_BE_DRY_RUN"
    if evidence.get("egress_allowed") is not True:
        return False, "WORLD_ACTION_PRE_EGRESS_NOT_ALLOWED"

    candidate = dict(evidence)
    stored = candidate.pop("evidence_hash", None)
    if not stored or canonical_sha256_v0(candidate) != stored:
        return False, "WORLD_ACTION_PRE_EVIDENCE_HASH_MISMATCH"
    return True, None


def assess_world_action_pre_execution_v0(
    *,
    request: WorldActionRequestV0,
    runtime_link_facts: Mapping[str, Any],
    pre_evidence: Mapping[str, Any] | None,
    world_action_approval: Mapping[str, Any],
    prior_attempts: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    request.assert_non_sovereign()

    duplicate = assess_prior_attempts_v0(
        request=request,
        prior_attempts=prior_attempts,
    )
    if duplicate["status"] != "NO_PRIOR_EFFECT":
        return {
            "status": PRE_EXECUTION_BLOCKED,
            "reason": duplicate["reason"],
            "duplicate_state": duplicate,
            "execution_performed": False,
            "decision_authority": DECISION_AUTHORITY,
        }

    if (
        request.world_call_class in {WCC_CRITICAL, WCC_FORBIDDEN}
        or request.action_risk_class == ARC_FORBIDDEN
    ):
        return _blocked("WORLD_ACTION_POLICY_CLASS_BLOCKED")

    missing = tuple(runtime_link_facts.get("missing_runtime_links") or ())
    if runtime_link_facts.get("decision_authority") != DECISION_AUTHORITY:
        return _blocked("UPSTREAM_RUNTIME_AUTHORITY_INVALID")
    if runtime_link_facts.get("world_action_runtime_activated") is not True:
        return _blocked(
            CANONICAL_WORLD_BLOCKER,
            missing_runtime_links=missing,
        )
    if CANONICAL_REAL_EXECUTION_BLOCKER in missing:
        return _blocked(
            CANONICAL_REAL_EXECUTION_BLOCKER,
            missing_runtime_links=missing,
        )

    ok, reason = verify_world_action_pre_evidence_v0(
        pre_evidence,
        request=request,
        world_action_approval=world_action_approval,
    )
    if not ok:
        return _blocked(reason or "WORLD_ACTION_PRE_INVALID")

    return {
        "status": PRE_EXECUTION_READY,
        "reason": None,
        "request_hash": request.request_hash,
        "connector_call_hash": request.connector_call_hash,
        "sovereign_ticket_id": pre_evidence["sovereign_ticket_id"],
        "decision_record_id": pre_evidence["decision_record_id"],
        "idempotency_key": request.idempotency_key,
        "execution_performed": False,
        "decision_authority": DECISION_AUTHORITY,
    }


def assess_prior_attempts_v0(
    *,
    request: WorldActionRequestV0,
    prior_attempts: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    matching = [
        attempt
        for attempt in prior_attempts
        if attempt.get("idempotency_key") == request.idempotency_key
    ]
    if not matching:
        return {"status": "NO_PRIOR_EFFECT", "reason": None}

    for attempt in matching:
        if attempt.get("status") == OUTCOME_CONFIRMED:
            return {
                "status": "ALREADY_EXECUTED",
                "reason": "CONFIRMED_DUPLICATE_EXECUTION_BLOCKED",
                "receipt_sha256": attempt.get("receipt_sha256"),
            }
        if attempt.get("status") == OUTCOME_UNKNOWN:
            return {
                "status": "RECONCILIATION_REQUIRED",
                "reason": "UNKNOWN_PRIOR_OUTCOME_BLOCKS_RETRY",
            }

    return {"status": "NO_PRIOR_EFFECT", "reason": None}


def _assert_pre_execution_ready_v0(
    *,
    request: WorldActionRequestV0,
    pre_execution_ready: Mapping[str, Any] | None,
) -> None:
    if pre_execution_ready is None:
        raise UniversalExecutionContractError(
            "PRE_EXECUTION_READY_EVIDENCE_REQUIRED"
        )
    if pre_execution_ready.get("status") != PRE_EXECUTION_READY:
        raise UniversalExecutionContractError(
            "PRE_EXECUTION_READY_STATUS_REQUIRED"
        )
    expected = {
        "request_hash": request.request_hash,
        "connector_call_hash": request.connector_call_hash,
        "idempotency_key": request.idempotency_key,
        "decision_authority": DECISION_AUTHORITY,
    }
    for key, value in expected.items():
        if pre_execution_ready.get(key) != value:
            raise UniversalExecutionContractError(
                f"PRE_EXECUTION_READY_{key.upper()}_MISMATCH"
            )
    if not pre_execution_ready.get("sovereign_ticket_id"):
        raise UniversalExecutionContractError(
            "PRE_EXECUTION_READY_SOVEREIGN_TICKET_MISSING"
        )
    if not pre_execution_ready.get("decision_record_id"):
        raise UniversalExecutionContractError(
            "PRE_EXECUTION_READY_DECISION_RECORD_MISSING"
        )


def build_provider_outcome_v0(
    *,
    request: WorldActionRequestV0,
    pre_execution_ready: Mapping[str, Any] | None,
    provider_result_identity: Mapping[str, Any] | None = None,
    explicit_no_effect: bool = False,
    exception_class: str | None = None,
) -> dict[str, Any]:
    _assert_pre_execution_ready_v0(
        request=request,
        pre_execution_ready=pre_execution_ready,
    )
    if explicit_no_effect and provider_result_identity:
        raise UniversalExecutionContractError(
            "provider result cannot be both success identity and no-effect"
        )
    if provider_result_identity:
        outcome = {
            "schema": "UNIVERSAL_WORLD_ACTION_RECEIPT_V0",
            "status": OUTCOME_CONFIRMED,
            "request_id": request.request_id,
            "request_hash": request.request_hash,
            "proposal_hash": request.proposal_hash,
            "connector_call_hash": request.connector_call_hash,
            "idempotency_key": request.idempotency_key,
            "provider_result_identity": dict(provider_result_identity),
            "real_execution_proven": True,
            "decision_authority": DECISION_AUTHORITY,
        }
        outcome["receipt_sha256"] = canonical_sha256_v0(outcome)
        return outcome

    if explicit_no_effect:
        return {
            "schema": "UNIVERSAL_WORLD_ACTION_NO_EFFECT_V0",
            "status": OUTCOME_NO_EFFECT,
            "request_hash": request.request_hash,
            "idempotency_key": request.idempotency_key,
            "automatic_retry_allowed": (
                request.retry_policy
                == RETRY_IDEMPOTENT_AFTER_RECONCILIATION
            ),
            "decision_authority": DECISION_AUTHORITY,
        }

    return {
        "schema": "UNIVERSAL_WORLD_ACTION_UNKNOWN_OUTCOME_V0",
        "status": OUTCOME_UNKNOWN,
        "request_hash": request.request_hash,
        "idempotency_key": request.idempotency_key,
        "exception_class": exception_class,
        "automatic_retry_allowed": False,
        "requires_provider_reconciliation": True,
        "decision_authority": DECISION_AUTHORITY,
    }


def replay_world_action_receipt_v0(
    *,
    request: WorldActionRequestV0,
    receipt: Mapping[str, Any],
) -> dict[str, Any]:
    if receipt.get("schema") != "UNIVERSAL_WORLD_ACTION_RECEIPT_V0":
        return {"status": "FAIL", "reason": "WORLD_ACTION_RECEIPT_SCHEMA_INVALID"}
    if receipt.get("status") != OUTCOME_CONFIRMED:
        return {"status": "FAIL", "reason": "WORLD_ACTION_RECEIPT_STATUS_INVALID"}
    if receipt.get("request_hash") != request.request_hash:
        return {"status": "FAIL", "reason": "WORLD_ACTION_RECEIPT_REQUEST_MISMATCH"}
    if receipt.get("proposal_hash") != request.proposal_hash:
        return {"status": "FAIL", "reason": "WORLD_ACTION_RECEIPT_PROPOSAL_MISMATCH"}
    if receipt.get("connector_call_hash") != request.connector_call_hash:
        return {"status": "FAIL", "reason": "WORLD_ACTION_RECEIPT_CALL_MISMATCH"}
    if receipt.get("idempotency_key") != request.idempotency_key:
        return {"status": "FAIL", "reason": "WORLD_ACTION_RECEIPT_IDEMPOTENCY_MISMATCH"}

    candidate = dict(receipt)
    stored = candidate.pop("receipt_sha256", None)
    if not stored or canonical_sha256_v0(candidate) != stored:
        return {"status": "FAIL", "reason": "WORLD_ACTION_RECEIPT_HASH_MISMATCH"}

    return {
        "status": "PASS",
        "real_execution_proven": True,
        "resend_required": False,
        "idempotency_key": request.idempotency_key,
        "decision_authority": DECISION_AUTHORITY,
    }


def legacy_dry_run_ticket_input_v0(
    request: WorldActionRequestV0,
    *,
    os3_ticket_id: str,
) -> dict[str, Any]:
    return {
        "action_id": request.request_id,
        "os3_ticket_id": os3_ticket_id,
        "x108_gate": "ALLOW",
        "scope": request.required_scope,
        "autonomy_level": request.autonomy_level,
        "world_call_class": request.world_call_class,
    }


def legacy_world_action_event_input_v0(
    request: WorldActionRequestV0,
    *,
    sovereign_ticket_id: str,
    blocked: bool,
    block_reason: str,
) -> dict[str, Any]:
    return {
        "action_id": request.request_id,
        "sovereign_ticket_id": sovereign_ticket_id,
        "world_call_class": request.world_call_class,
        "action_risk_class": request.action_risk_class,
        "autonomy_level": request.autonomy_level,
        "intent": (
            f"{request.connector_id}:{request.connector_action}:"
            f"{request.request_hash}"
        ),
        "domain": request.domain_id,
        "blocked": blocked,
        "block_reason": block_reason,
    }


def _blocked(reason: str, **extra: Any) -> dict[str, Any]:
    return {
        "status": PRE_EXECUTION_BLOCKED,
        "reason": reason,
        "execution_performed": False,
        "decision_authority": DECISION_AUTHORITY,
        **extra,
    }
