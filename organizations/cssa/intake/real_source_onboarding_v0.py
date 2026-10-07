"""F3H-G — real operational source onboarding pilot V0.

This module turns one observed external source into an explicitly authorized
F3H-F READONLY operational source.

Two-key boundary:
1. ObservedSourceCandidateV0 binds what the connector actually exposed.
2. HumanOperationalSourceAuthorizationV0 binds a human claim that this exact
   candidate is an internal CSSA operational source.

Only an exact pair can activate F3H-F registration.

No connector mutation is performed here.
"""
from __future__ import annotations

import datetime
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from organizations.cssa.intake.operational_source_registry_v0 import (
    DECISION_AUTHORITY,
    OperationalSourceRegistrationV0,
    OperationalSourceRegistryV0,
    SOURCE_KINDS,
    SOURCE_MAILBOX,
    build_operational_source_registration_v0,
    mailbox_registration_to_f3h_e_authority_v0,
)

STATUS = "CSSA_REAL_SOURCE_ONBOARDING_PILOT_V0"


def _hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            default=str,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _require_time(value: str) -> str:
    parsed = datetime.datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("SOURCE_ONBOARDING_TIME_MUST_BE_TIMEZONE_AWARE")
    return value


@dataclass(frozen=True)
class ObservedSourceCandidateV0:
    schema: str
    candidate_id: str
    source_kind: str
    provider: str
    source_identity_sha256: str
    observed_capabilities: tuple[str, ...]
    connector_reference: str
    observed_at: str
    raw_source_identity_persisted: bool
    raw_credentials_persisted: bool
    internal_cssa_source_claimed: bool
    allowed_to_decide: bool
    allowed_to_act: bool
    decision_authority: str
    candidate_hash: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["observed_capabilities"] = list(self.observed_capabilities)
        return data


@dataclass(frozen=True)
class HumanOperationalSourceAuthorizationV0:
    schema: str
    authorization_id: str
    candidate_id: str
    candidate_hash: str
    source_identity_sha256: str
    approved_capabilities: tuple[str, ...]
    authority_reference: str
    approved_by: str
    authorized_at: str
    internal_cssa_source: bool
    readonly_only: bool
    is_execution_authority: bool
    decision_authority: str
    authorization_hash: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["approved_capabilities"] = list(self.approved_capabilities)
        return data


@dataclass(frozen=True)
class OperationalSourceActivationReceiptV0:
    schema: str
    receipt_id: str
    candidate_hash: str
    authorization_hash: str
    registration_hash: str
    source_id: str
    source_kind: str
    provider: str
    active: bool
    readonly: bool
    external_mutation_allowed: bool
    f3h_e_mailbox_authority_ready: bool
    activated_at: str
    decision_authority: str
    receipt_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _candidate_payload(value: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "schema", "candidate_id", "source_kind", "provider",
        "source_identity_sha256", "observed_capabilities",
        "connector_reference", "observed_at",
        "raw_source_identity_persisted", "raw_credentials_persisted",
        "internal_cssa_source_claimed", "allowed_to_decide",
        "allowed_to_act", "decision_authority",
    )
    return {key: value[key] for key in keys}


def build_observed_source_candidate_v0(
    *,
    candidate_id: str,
    source_kind: str,
    provider: str,
    source_identity_sha256: str,
    observed_capabilities: tuple[str, ...],
    connector_reference: str,
    observed_at: str,
) -> ObservedSourceCandidateV0:
    if source_kind not in SOURCE_KINDS:
        raise ValueError("SOURCE_ONBOARDING_KIND_INVALID")
    if not candidate_id or not provider or not connector_reference:
        raise ValueError("SOURCE_ONBOARDING_CANDIDATE_FIELDS_REQUIRED")
    if len(source_identity_sha256) != 64:
        raise ValueError("SOURCE_ONBOARDING_IDENTITY_HASH_INVALID")
    if not observed_capabilities:
        raise ValueError("SOURCE_ONBOARDING_CAPABILITIES_REQUIRED")
    _require_time(observed_at)
    capabilities = tuple(sorted(set(observed_capabilities)))
    payload = {
        "schema": "CSSA_OBSERVED_SOURCE_CANDIDATE_V0",
        "candidate_id": candidate_id,
        "source_kind": source_kind,
        "provider": provider,
        "source_identity_sha256": source_identity_sha256,
        "observed_capabilities": list(capabilities),
        "connector_reference": connector_reference,
        "observed_at": observed_at,
        "raw_source_identity_persisted": False,
        "raw_credentials_persisted": False,
        "internal_cssa_source_claimed": False,
        "allowed_to_decide": False,
        "allowed_to_act": False,
        "decision_authority": DECISION_AUTHORITY,
    }
    return ObservedSourceCandidateV0(
        schema=payload["schema"],
        candidate_id=candidate_id,
        source_kind=source_kind,
        provider=provider,
        source_identity_sha256=source_identity_sha256,
        observed_capabilities=capabilities,
        connector_reference=connector_reference,
        observed_at=observed_at,
        raw_source_identity_persisted=False,
        raw_credentials_persisted=False,
        internal_cssa_source_claimed=False,
        allowed_to_decide=False,
        allowed_to_act=False,
        decision_authority=DECISION_AUTHORITY,
        candidate_hash=_hash(payload),
    )


def verify_observed_source_candidate_v0(
    candidate: ObservedSourceCandidateV0 | Mapping[str, Any] | None,
) -> tuple[bool, Optional[str]]:
    if candidate is None:
        return False, "SOURCE_ONBOARDING_CANDIDATE_MISSING"
    data = (
        candidate.to_dict()
        if isinstance(candidate, ObservedSourceCandidateV0)
        else dict(candidate)
    )
    if data.get("schema") != "CSSA_OBSERVED_SOURCE_CANDIDATE_V0":
        return False, "SOURCE_ONBOARDING_CANDIDATE_SCHEMA_INVALID"
    if data.get("source_kind") not in SOURCE_KINDS:
        return False, "SOURCE_ONBOARDING_KIND_INVALID"
    if len(str(data.get("source_identity_sha256", ""))) != 64:
        return False, "SOURCE_ONBOARDING_IDENTITY_HASH_INVALID"
    if data.get("raw_source_identity_persisted") is not False:
        return False, "SOURCE_ONBOARDING_RAW_IDENTITY_FORBIDDEN"
    if data.get("raw_credentials_persisted") is not False:
        return False, "SOURCE_ONBOARDING_RAW_CREDENTIALS_FORBIDDEN"
    if data.get("internal_cssa_source_claimed") is not False:
        return False, "SOURCE_ONBOARDING_CANDIDATE_CANNOT_SELF_CLAIM"
    if data.get("allowed_to_decide") is not False:
        return False, "SOURCE_ONBOARDING_CANDIDATE_DECISION_FORBIDDEN"
    if data.get("allowed_to_act") is not False:
        return False, "SOURCE_ONBOARDING_CANDIDATE_ACTION_FORBIDDEN"
    if data.get("decision_authority") != DECISION_AUTHORITY:
        return False, "SOURCE_ONBOARDING_CANDIDATE_AUTHORITY_INVALID"
    try:
        _require_time(str(data.get("observed_at")))
    except Exception:
        return False, "SOURCE_ONBOARDING_OBSERVED_AT_INVALID"
    if _hash(_candidate_payload(data)) != data.get("candidate_hash"):
        return False, "SOURCE_ONBOARDING_CANDIDATE_HASH_MISMATCH"
    return True, None


def _authorization_payload(value: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "schema", "authorization_id", "candidate_id", "candidate_hash",
        "source_identity_sha256", "approved_capabilities",
        "authority_reference", "approved_by", "authorized_at",
        "internal_cssa_source", "readonly_only",
        "is_execution_authority", "decision_authority",
    )
    return {key: value[key] for key in keys}


def build_human_operational_source_authorization_v0(
    *,
    candidate: ObservedSourceCandidateV0,
    authorization_id: str,
    approved_capabilities: tuple[str, ...],
    authority_reference: str,
    approved_by: str,
    authorized_at: str,
) -> HumanOperationalSourceAuthorizationV0:
    ok, reason = verify_observed_source_candidate_v0(candidate)
    if not ok:
        raise ValueError(reason)
    if not authorization_id or not authority_reference:
        raise ValueError("SOURCE_ONBOARDING_AUTHORIZATION_FIELDS_REQUIRED")
    if not approved_by or approved_by == "MACHINE":
        raise ValueError("SOURCE_ONBOARDING_HUMAN_AUTHORIZATION_REQUIRED")
    _require_time(authorized_at)
    approved = tuple(sorted(set(approved_capabilities)))
    if not approved:
        raise ValueError("SOURCE_ONBOARDING_APPROVED_CAPABILITIES_REQUIRED")
    if not set(approved).issubset(set(candidate.observed_capabilities)):
        raise ValueError("SOURCE_ONBOARDING_CAPABILITY_ESCALATION_FORBIDDEN")

    payload = {
        "schema": "CSSA_HUMAN_OPERATIONAL_SOURCE_AUTHORIZATION_V0",
        "authorization_id": authorization_id,
        "candidate_id": candidate.candidate_id,
        "candidate_hash": candidate.candidate_hash,
        "source_identity_sha256": candidate.source_identity_sha256,
        "approved_capabilities": list(approved),
        "authority_reference": authority_reference,
        "approved_by": approved_by,
        "authorized_at": authorized_at,
        "internal_cssa_source": True,
        "readonly_only": True,
        "is_execution_authority": False,
        "decision_authority": DECISION_AUTHORITY,
    }
    return HumanOperationalSourceAuthorizationV0(
        schema=payload["schema"],
        authorization_id=authorization_id,
        candidate_id=candidate.candidate_id,
        candidate_hash=candidate.candidate_hash,
        source_identity_sha256=candidate.source_identity_sha256,
        approved_capabilities=approved,
        authority_reference=authority_reference,
        approved_by=approved_by,
        authorized_at=authorized_at,
        internal_cssa_source=True,
        readonly_only=True,
        is_execution_authority=False,
        decision_authority=DECISION_AUTHORITY,
        authorization_hash=_hash(payload),
    )


def verify_human_operational_source_authorization_v0(
    authorization: HumanOperationalSourceAuthorizationV0 | Mapping[str, Any] | None,
    *,
    candidate: ObservedSourceCandidateV0,
) -> tuple[bool, Optional[str]]:
    if authorization is None:
        return False, "SOURCE_ONBOARDING_AUTHORIZATION_MISSING"
    data = (
        authorization.to_dict()
        if isinstance(authorization, HumanOperationalSourceAuthorizationV0)
        else dict(authorization)
    )
    if data.get("schema") != "CSSA_HUMAN_OPERATIONAL_SOURCE_AUTHORIZATION_V0":
        return False, "SOURCE_ONBOARDING_AUTHORIZATION_SCHEMA_INVALID"
    if data.get("candidate_id") != candidate.candidate_id:
        return False, "SOURCE_ONBOARDING_AUTHORIZATION_CANDIDATE_ID_MISMATCH"
    if data.get("candidate_hash") != candidate.candidate_hash:
        return False, "SOURCE_ONBOARDING_AUTHORIZATION_CANDIDATE_HASH_MISMATCH"
    if data.get("source_identity_sha256") != candidate.source_identity_sha256:
        return False, "SOURCE_ONBOARDING_AUTHORIZATION_IDENTITY_MISMATCH"
    if not set(data.get("approved_capabilities") or ()).issubset(
        set(candidate.observed_capabilities)
    ):
        return False, "SOURCE_ONBOARDING_AUTHORIZATION_CAPABILITY_ESCALATION"
    if data.get("internal_cssa_source") is not True:
        return False, "SOURCE_ONBOARDING_INTERNAL_SCOPE_REQUIRED"
    if data.get("readonly_only") is not True:
        return False, "SOURCE_ONBOARDING_READONLY_REQUIRED"
    if data.get("is_execution_authority") is not False:
        return False, "SOURCE_ONBOARDING_EXECUTION_AUTHORITY_FORBIDDEN"
    if data.get("decision_authority") != DECISION_AUTHORITY:
        return False, "SOURCE_ONBOARDING_AUTHORITY_INVALID"
    if not data.get("approved_by") or data.get("approved_by") == "MACHINE":
        return False, "SOURCE_ONBOARDING_HUMAN_AUTHORIZATION_REQUIRED"
    try:
        _require_time(str(data.get("authorized_at")))
    except Exception:
        return False, "SOURCE_ONBOARDING_AUTHORIZED_AT_INVALID"
    if _hash(_authorization_payload(data)) != data.get("authorization_hash"):
        return False, "SOURCE_ONBOARDING_AUTHORIZATION_HASH_MISMATCH"
    return True, None


def _receipt_payload(value: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "schema", "receipt_id", "candidate_hash", "authorization_hash",
        "registration_hash", "source_id", "source_kind", "provider",
        "active", "readonly", "external_mutation_allowed",
        "f3h_e_mailbox_authority_ready", "activated_at",
        "decision_authority",
    )
    return {key: value[key] for key in keys}


def activate_operational_source_v0(
    *,
    candidate: ObservedSourceCandidateV0,
    authorization: HumanOperationalSourceAuthorizationV0,
    registry: OperationalSourceRegistryV0,
    source_id: str,
    activated_at: str,
) -> tuple[
    OperationalSourceRegistrationV0,
    OperationalSourceActivationReceiptV0,
]:
    ok, reason = verify_observed_source_candidate_v0(candidate)
    if not ok:
        raise ValueError(reason)
    ok, reason = verify_human_operational_source_authorization_v0(
        authorization,
        candidate=candidate,
    )
    if not ok:
        raise ValueError(reason)
    _require_time(activated_at)

    registration = build_operational_source_registration_v0(
        source_id=source_id,
        source_kind=candidate.source_kind,
        provider=candidate.provider,
        source_identity_sha256=candidate.source_identity_sha256,
        capabilities=authorization.approved_capabilities,
        authority_reference=(
            f"onboarding-authorization:{authorization.authorization_hash}"
        ),
        approved_by=authorization.approved_by,
        registered_at=activated_at,
    )
    registry.register(registration)

    mailbox_ready = False
    if registration.source_kind == SOURCE_MAILBOX:
        mailbox_registration_to_f3h_e_authority_v0(
            registration=registration,
            registry=registry,
        )
        mailbox_ready = True

    payload = {
        "schema": "CSSA_OPERATIONAL_SOURCE_ACTIVATION_RECEIPT_V0",
        "receipt_id": f"source-activation:{_hash({
            'candidate': candidate.candidate_hash,
            'authorization': authorization.authorization_hash,
            'registration': registration.registration_hash,
        })[:24]}",
        "candidate_hash": candidate.candidate_hash,
        "authorization_hash": authorization.authorization_hash,
        "registration_hash": registration.registration_hash,
        "source_id": registration.source_id,
        "source_kind": registration.source_kind,
        "provider": registration.provider,
        "active": registry.is_active(registration.source_id),
        "readonly": registration.readonly,
        "external_mutation_allowed": registration.external_mutation_allowed,
        "f3h_e_mailbox_authority_ready": mailbox_ready,
        "activated_at": activated_at,
        "decision_authority": DECISION_AUTHORITY,
    }
    return registration, OperationalSourceActivationReceiptV0(
        **payload,
        receipt_hash=_hash(payload),
    )


def verify_operational_source_activation_receipt_v0(
    receipt: OperationalSourceActivationReceiptV0 | Mapping[str, Any],
    *,
    candidate: ObservedSourceCandidateV0,
    authorization: HumanOperationalSourceAuthorizationV0,
    registration: OperationalSourceRegistrationV0,
) -> tuple[bool, Optional[str]]:
    data = (
        receipt.to_dict()
        if isinstance(receipt, OperationalSourceActivationReceiptV0)
        else dict(receipt)
    )
    if data.get("schema") != "CSSA_OPERATIONAL_SOURCE_ACTIVATION_RECEIPT_V0":
        return False, "SOURCE_ONBOARDING_RECEIPT_SCHEMA_INVALID"
    if data.get("candidate_hash") != candidate.candidate_hash:
        return False, "SOURCE_ONBOARDING_RECEIPT_CANDIDATE_MISMATCH"
    if data.get("authorization_hash") != authorization.authorization_hash:
        return False, "SOURCE_ONBOARDING_RECEIPT_AUTHORIZATION_MISMATCH"
    if data.get("registration_hash") != registration.registration_hash:
        return False, "SOURCE_ONBOARDING_RECEIPT_REGISTRATION_MISMATCH"
    if data.get("source_id") != registration.source_id:
        return False, "SOURCE_ONBOARDING_RECEIPT_SOURCE_ID_MISMATCH"
    if data.get("readonly") is not True:
        return False, "SOURCE_ONBOARDING_RECEIPT_READONLY_INVALID"
    if data.get("external_mutation_allowed") is not False:
        return False, "SOURCE_ONBOARDING_RECEIPT_MUTATION_INVALID"
    if data.get("decision_authority") != DECISION_AUTHORITY:
        return False, "SOURCE_ONBOARDING_RECEIPT_AUTHORITY_INVALID"
    if _hash(_receipt_payload(data)) != data.get("receipt_hash"):
        return False, "SOURCE_ONBOARDING_RECEIPT_HASH_MISMATCH"
    return True, None
