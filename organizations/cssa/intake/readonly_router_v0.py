"""F3H-E — CSSA real READONLY intake router V0.

Purpose:
- classify incoming mail/document observations without mutating the source;
- distinguish information, marketing, transactions and true operational work;
- prevent personal/fan mailbox traffic from becoming internal CSSA truth;
- create a native CRM/TASK intake candidate only for an explicitly trusted
  CSSA operational source and only after actionable intent is structurally
  proven.

This module never sends mail, modifies Gmail, or writes native CRM/TASK state.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Optional

from organizations.cssa.native_ops.cssa_native_ops_bridge_v0 import (
    CSSANativeIntakePlanV0,
    build_cssa_native_intake_plan_v0,
)

STATUS = "CSSA_REAL_READONLY_INTAKE_ROUTER_V0"
DECISION_AUTHORITY = "KX108_ONLY"

SOURCE_PERSONAL_INBOX = "PERSONAL_INBOX"
SOURCE_CSSA_OPERATIONAL_MAILBOX = "CSSA_OPERATIONAL_MAILBOX"
SOURCE_PUBLIC_READONLY = "PUBLIC_READONLY"

SOURCE_SCOPES = {
    SOURCE_PERSONAL_INBOX,
    SOURCE_CSSA_OPERATIONAL_MAILBOX,
    SOURCE_PUBLIC_READONLY,
}

CLASS_MATCHDAY_INFORMATION = "CLUB_MATCHDAY_INFORMATION"
CLASS_MARKETING_COMMUNICATION = "CLUB_MARKETING_COMMUNICATION"
CLASS_TICKETING_TRANSACTION = "TICKETING_TRANSACTION_CONFIRMATION"
CLASS_ACCOUNTING_DOCUMENT = "ACCOUNTING_DOCUMENT"
CLASS_OPERATIONAL_ACTION_REQUEST = "OPERATIONAL_ACTION_REQUEST"
CLASS_DEADLINE_OBLIGATION = "DEADLINE_OBLIGATION"
CLASS_INCIDENT_ALERT = "INCIDENT_ALERT"
CLASS_UNKNOWN_CSSA = "UNKNOWN_CSSA_REVIEW_REQUIRED"
CLASS_NON_CSSA = "NON_CSSA"

ROUTE_SHADOW_INTERACTION = "READONLY_SHADOW_INTERACTION_ONLY"
ROUTE_PERSONAL_TRANSACTION = "PERSONAL_TRANSACTION_INTERACTION_ONLY"
ROUTE_NATIVE_CASE_TASK = "NATIVE_CASE_TASK_FOLLOWUP_CANDIDATE"
ROUTE_NATIVE_CASE_TASK_CALENDAR = "NATIVE_CASE_TASK_CALENDAR_CANDIDATE"
ROUTE_REVIEW_HOLD = "READONLY_REVIEW_HOLD"
ROUTE_IGNORE = "IGNORE_NON_CSSA"

ACTIONABLE_CLASSES = {
    CLASS_OPERATIONAL_ACTION_REQUEST,
    CLASS_DEADLINE_OBLIGATION,
    CLASS_INCIDENT_ALERT,
}

_CSSA_TERMS = (
    "cssa",
    "cs sedan",
    "cs sedan ardennes",
    "sedan ardennes",
    "dugauguez",
)
_MATCHDAY_TERMS = (
    "coup d'envoi",
    "ouverture des portes",
    "ouverture du stade",
    "stade louis-dugauguez",
    "stade louis dugauguez",
    "tribune honneur",
    "billetterie",
    "buvette",
)
_MARKETING_TERMS = (
    "maillot",
    "boutique officielle",
    "découvrir le maillot",
    "nouveau maillot",
    "abonnez-vous",
    "acheter mes billets",
    "réservez dès maintenant",
)
_TRANSACTION_TERMS = (
    "merci pour votre commande",
    "votre commande est confirmée",
    "votre commande pour",
    "commande n°",
    "téléchargez vos billets",
    "je télécharge mes billets",
)
_ACCOUNTING_TERMS = (
    "votre facture",
    "pièce comptable",
    "service facturation",
    "télécharger ma facture",
)
_INCIDENT_TERMS = (
    "incident",
    "urgence",
    "blocage",
    "impossible",
    "refus",
    "anomalie",
    "erreur critique",
)
_DEADLINE_TERMS = (
    "au plus tard",
    "échéance",
    "avant le ",
    "date limite",
    "deadline",
)
_ACTION_REQUEST_TERMS = (
    "action requise",
    "merci de nous répondre",
    "merci de répondre",
    "merci de nous transmettre",
    "merci de transmettre",
    "merci de nous retourner",
    "veuillez nous transmettre",
    "veuillez compléter",
    "merci de compléter",
    "merci de fournir",
    "réponse attendue",
    "à retourner",
)


def _hash_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower()).strip()


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _require_timestamp(value: str) -> str:
    parsed = datetime.datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("READONLY_MESSAGE_TIME_MUST_BE_TIMEZONE_AWARE")
    return value


@dataclass(frozen=True)
class ReadonlyMessageObservationV0:
    schema: str
    observation_id: str
    source_scope: str
    sender_family: str
    received_at: str
    provider_message_id_sha256: str
    subject_sha256: str
    body_sha256: str
    has_attachment: bool
    cssa_relevant: bool
    matchday_signal: bool
    marketing_signal: bool
    transaction_signal: bool
    accounting_signal: bool
    incident_signal: bool
    deadline_signal: bool
    explicit_action_request: bool
    raw_provider_message_id_persisted: bool
    raw_subject_persisted: bool
    raw_body_persisted: bool
    raw_recipient_persisted: bool
    observation_hash: str
    decision_authority: str = DECISION_AUTHORITY
    allowed_to_decide: bool = False
    allowed_to_act: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReadonlyRouteDecisionV0:
    schema: str
    observation_id: str
    observation_hash: str
    classification: str
    route: str
    reason: str
    canonical_native_candidate: bool
    calendar_candidate: bool
    real_internal_cssa_evidence: bool
    requires_human_review: bool
    route_hash: str
    decision_authority: str = DECISION_AUTHORITY
    allowed_to_decide: bool = False
    allowed_to_act: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _observation_payload(value: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "schema",
        "observation_id",
        "source_scope",
        "sender_family",
        "received_at",
        "provider_message_id_sha256",
        "subject_sha256",
        "body_sha256",
        "has_attachment",
        "cssa_relevant",
        "matchday_signal",
        "marketing_signal",
        "transaction_signal",
        "accounting_signal",
        "incident_signal",
        "deadline_signal",
        "explicit_action_request",
        "raw_provider_message_id_persisted",
        "raw_subject_persisted",
        "raw_body_persisted",
        "raw_recipient_persisted",
        "decision_authority",
    )
    return {key: value[key] for key in keys}


def build_readonly_message_observation_v0(
    *,
    provider_message_id: str,
    subject: str,
    body: str,
    sender_family: str,
    received_at: str,
    source_scope: str,
    has_attachment: bool,
) -> ReadonlyMessageObservationV0:
    if source_scope not in SOURCE_SCOPES:
        raise ValueError("READONLY_SOURCE_SCOPE_INVALID")
    if not provider_message_id:
        raise ValueError("READONLY_PROVIDER_MESSAGE_ID_REQUIRED")
    if not sender_family:
        raise ValueError("READONLY_SENDER_FAMILY_REQUIRED")
    _require_timestamp(received_at)

    combined = _normalize(f"{subject}\n{body}")
    cssa_relevant = _contains_any(combined, _CSSA_TERMS)
    accounting = _contains_any(combined, _ACCOUNTING_TERMS)
    transaction = _contains_any(combined, _TRANSACTION_TERMS)
    incident = _contains_any(combined, _INCIDENT_TERMS)
    deadline = _contains_any(combined, _DEADLINE_TERMS)
    action_request = _contains_any(combined, _ACTION_REQUEST_TERMS)
    matchday = _contains_any(combined, _MATCHDAY_TERMS)
    marketing = _contains_any(combined, _MARKETING_TERMS)

    seed = {
        "schema": "CSSA_READONLY_MESSAGE_OBSERVATION_V0",
        "source_scope": source_scope,
        "sender_family": sender_family,
        "received_at": received_at,
        "provider_message_id_sha256": _hash_text(provider_message_id),
        "subject_sha256": _hash_text(subject),
        "body_sha256": _hash_text(body),
        "has_attachment": bool(has_attachment),
        "cssa_relevant": cssa_relevant,
        "matchday_signal": matchday,
        "marketing_signal": marketing,
        "transaction_signal": transaction,
        "accounting_signal": accounting,
        "incident_signal": incident,
        "deadline_signal": deadline,
        "explicit_action_request": action_request,
        "raw_provider_message_id_persisted": False,
        "raw_subject_persisted": False,
        "raw_body_persisted": False,
        "raw_recipient_persisted": False,
        "decision_authority": DECISION_AUTHORITY,
    }
    observation_id = f"readonly:{_hash_text(provider_message_id)[:24]}"
    payload = {"observation_id": observation_id, **seed}
    return ReadonlyMessageObservationV0(
        **payload,
        observation_hash=_hash_text(
            json.dumps(
                payload,
                sort_keys=True,
                ensure_ascii=False,
                separators=(",", ":"),
            )
        ),
    )


def verify_readonly_message_observation_v0(
    observation: ReadonlyMessageObservationV0,
) -> tuple[bool, Optional[str]]:
    if observation.decision_authority != DECISION_AUTHORITY:
        return False, "READONLY_OBSERVATION_AUTHORITY_INVALID"
    if observation.allowed_to_decide or observation.allowed_to_act:
        return False, "READONLY_OBSERVATION_CANNOT_GRANT_AUTHORITY"
    if observation.source_scope not in SOURCE_SCOPES:
        return False, "READONLY_OBSERVATION_SOURCE_SCOPE_INVALID"
    if any(
        (
            observation.raw_provider_message_id_persisted,
            observation.raw_subject_persisted,
            observation.raw_body_persisted,
            observation.raw_recipient_persisted,
        )
    ):
        return False, "READONLY_OBSERVATION_PRIVACY_BOUNDARY_VIOLATED"
    payload = _observation_payload(observation.to_dict())
    expected = _hash_text(
        json.dumps(
            payload,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )
    if expected != observation.observation_hash:
        return False, "READONLY_OBSERVATION_HASH_MISMATCH"
    return True, None


def _route_payload(value: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "schema",
        "observation_id",
        "observation_hash",
        "classification",
        "route",
        "reason",
        "canonical_native_candidate",
        "calendar_candidate",
        "real_internal_cssa_evidence",
        "requires_human_review",
        "decision_authority",
    )
    return {key: value[key] for key in keys}


def route_readonly_observation_v0(
    observation: ReadonlyMessageObservationV0,
) -> ReadonlyRouteDecisionV0:
    ok, reason = verify_readonly_message_observation_v0(observation)
    if not ok:
        raise ValueError(reason)

    classification: str
    if not observation.cssa_relevant:
        classification = CLASS_NON_CSSA
    elif observation.accounting_signal:
        classification = CLASS_ACCOUNTING_DOCUMENT
    elif observation.transaction_signal:
        classification = CLASS_TICKETING_TRANSACTION
    elif observation.incident_signal:
        classification = CLASS_INCIDENT_ALERT
    elif observation.explicit_action_request and observation.deadline_signal:
        classification = CLASS_DEADLINE_OBLIGATION
    elif observation.explicit_action_request:
        classification = CLASS_OPERATIONAL_ACTION_REQUEST
    elif observation.matchday_signal:
        classification = CLASS_MATCHDAY_INFORMATION
    elif observation.marketing_signal:
        classification = CLASS_MARKETING_COMMUNICATION
    else:
        classification = CLASS_UNKNOWN_CSSA

    trusted_operational = (
        observation.source_scope == SOURCE_CSSA_OPERATIONAL_MAILBOX
    )

    if classification == CLASS_NON_CSSA:
        route = ROUTE_IGNORE
        reason_text = "MESSAGE_NOT_CSSA_RELEVANT"
        canonical = False
        calendar = False
        review = False
    elif classification in {
        CLASS_TICKETING_TRANSACTION,
        CLASS_ACCOUNTING_DOCUMENT,
    } and observation.source_scope == SOURCE_PERSONAL_INBOX:
        route = ROUTE_PERSONAL_TRANSACTION
        reason_text = "PERSONAL_CUSTOMER_TRANSACTION_NOT_INTERNAL_CSSA_WORK"
        canonical = False
        calendar = False
        review = False
    elif classification in {
        CLASS_MATCHDAY_INFORMATION,
        CLASS_MARKETING_COMMUNICATION,
        CLASS_TICKETING_TRANSACTION,
        CLASS_ACCOUNTING_DOCUMENT,
    }:
        route = ROUTE_SHADOW_INTERACTION
        reason_text = "INFORMATIONAL_OR_TRANSACTIONAL_NO_ACTION_PROVEN"
        canonical = False
        calendar = False
        review = False
    elif classification == CLASS_DEADLINE_OBLIGATION:
        if trusted_operational:
            route = ROUTE_NATIVE_CASE_TASK_CALENDAR
            reason_text = "TRUSTED_OPERATIONAL_ACTION_WITH_DEADLINE"
            canonical = True
            calendar = True
            review = True
        else:
            route = ROUTE_REVIEW_HOLD
            reason_text = "ACTIONABLE_CONTENT_FROM_UNTRUSTED_READONLY_SOURCE"
            canonical = False
            calendar = False
            review = True
    elif classification in {
        CLASS_OPERATIONAL_ACTION_REQUEST,
        CLASS_INCIDENT_ALERT,
    }:
        if trusted_operational:
            route = ROUTE_NATIVE_CASE_TASK
            reason_text = "TRUSTED_OPERATIONAL_ACTION_OR_INCIDENT"
            canonical = True
            calendar = False
            review = True
        else:
            route = ROUTE_REVIEW_HOLD
            reason_text = "ACTIONABLE_CONTENT_FROM_UNTRUSTED_READONLY_SOURCE"
            canonical = False
            calendar = False
            review = True
    else:
        route = ROUTE_REVIEW_HOLD
        reason_text = "CSSA_RELEVANT_BUT_SEMANTICS_NOT_PROVEN"
        canonical = False
        calendar = False
        review = True

    real_internal = trusted_operational
    payload = {
        "schema": "CSSA_READONLY_ROUTE_DECISION_V0",
        "observation_id": observation.observation_id,
        "observation_hash": observation.observation_hash,
        "classification": classification,
        "route": route,
        "reason": reason_text,
        "canonical_native_candidate": canonical,
        "calendar_candidate": calendar,
        "real_internal_cssa_evidence": real_internal,
        "requires_human_review": review,
        "decision_authority": DECISION_AUTHORITY,
    }
    return ReadonlyRouteDecisionV0(
        **payload,
        route_hash=_hash_text(
            json.dumps(
                payload,
                sort_keys=True,
                ensure_ascii=False,
                separators=(",", ":"),
            )
        ),
    )


def build_native_intake_candidate_from_route_v0(
    *,
    observation: ReadonlyMessageObservationV0,
    route: ReadonlyRouteDecisionV0,
    cssa_case_id: str,
    case_type: str,
    title: str,
    summary: str,
    owner_ref: str | None,
    priority: str,
    due_at: Optional[str],
    source_refs: tuple[str, ...],
    evidence_refs: tuple[str, ...],
    tags: tuple[str, ...] = (),
) -> CSSANativeIntakePlanV0:
    if route.observation_hash != observation.observation_hash:
        raise ValueError("READONLY_ROUTE_OBSERVATION_BINDING_MISMATCH")
    if not route.canonical_native_candidate:
        raise ValueError("READONLY_ROUTE_NOT_NATIVE_CANDIDATE")
    if observation.source_scope != SOURCE_CSSA_OPERATIONAL_MAILBOX:
        raise ValueError("READONLY_SOURCE_NOT_OPERATIONAL_CSSA")
    if route.classification not in ACTIONABLE_CLASSES:
        raise ValueError("READONLY_CLASS_NOT_ACTIONABLE")
    if not due_at:
        raise ValueError("READONLY_NATIVE_CANDIDATE_DUE_AT_REQUIRED")
    _require_timestamp(due_at)

    combined_evidence = tuple(
        dict.fromkeys(
            (
                *evidence_refs,
                f"readonly-observation:{observation.observation_hash}",
                f"readonly-route:{route.route_hash}",
            )
        )
    )
    combined_sources = tuple(
        dict.fromkeys(
            (
                *source_refs,
                f"readonly-source:{observation.source_scope}",
            )
        )
    )
    return build_cssa_native_intake_plan_v0(
        cssa_case_id=cssa_case_id,
        case_type=case_type,
        title=title,
        summary=summary,
        owner_ref=owner_ref,
        priority=priority,
        occurred_at=observation.received_at,
        due_at=due_at,
        source_refs=combined_sources,
        evidence_refs=combined_evidence,
        tags=tuple(dict.fromkeys((*tags, route.classification))),
    )
