"""F2 — bounded universal-domain conformance harness.

This module does not implement the Obsidia kernel or any business domain.
It checks whether an input surface can be reduced to the F1 universal contract
without leaking authority or domain-specific semantics into Universal.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Iterable

from universal.contracts.domain_v0 import (
    DECISION_AUTHORITY,
    DomainStateRefV0,
    GovernancePayloadV0,
    domain_state_to_governance_payload,
)


class ConformanceError(ValueError):
    """Raised when a candidate source violates the universal boundary."""


@dataclass(frozen=True)
class ConformanceReportV0:
    profile_id: str
    domain_id: str
    status: str
    checks: tuple[str, ...]
    preserved_fields: tuple[str, ...]
    ignored_domain_fields: tuple[str, ...]
    decision_authority: str = DECISION_AUTHORITY
    emits_act: bool = False
    kernel_mutation: bool = False


_REQUIRED_SOVEREIGNTY_FALSE = (
    "emits_act",
    "emits_verdict",
    "kernel_mutation",
    "x108_mutation",
)

_OPTIONAL_WRITE_FALSE = (
    "memory_write",
    "graphiti_write",
    "neo4j_write",
)


def _tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        return tuple(str(v) for v in value)
    if isinstance(value, list):
        return tuple(str(v) for v in value)
    raise ConformanceError("list/tuple field expected")


def _assert_source_non_sovereign(source: Mapping[str, Any]) -> None:
    authority = source.get("decision_authority", DECISION_AUTHORITY)
    if authority != DECISION_AUTHORITY:
        raise ConformanceError("source attempts to change decision authority")

    if source.get("allowed_to_decide") is True:
        raise ConformanceError("source cannot decide")
    if source.get("allowed_to_act") is True:
        raise ConformanceError("source cannot act")

    for key in _REQUIRED_SOVEREIGNTY_FALSE:
        if source.get(key) is True:
            raise ConformanceError(f"{key} must remain false")

    for key in _OPTIONAL_WRITE_FALSE:
        if source.get(key) is True:
            raise ConformanceError(f"{key} must remain false")


def main_domain_snapshot_to_state(
    source: Mapping[str, Any],
    *,
    state_ref: str,
    valid_at: str,
    upstream_state_ref: str | None = None,
    provenance_refs: Iterable[str] = (),
) -> DomainStateRefV0:
    """Adapt the stable, common part of a current-main domain snapshot.

    Business/advisory fields are deliberately ignored. In particular,
    market_verdict is never transported as a decision.
    """

    _assert_source_non_sovereign(source)

    domain_id = str(source.get("domain") or "").strip()
    if not domain_id:
        raise ConformanceError("source domain is required")
    if not state_ref:
        raise ConformanceError("state_ref is required")
    if not valid_at:
        raise ConformanceError("valid_at is required")

    return DomainStateRefV0(
        domain_id=domain_id,
        state_ref=state_ref,
        valid_at=valid_at,
        upstream_state_ref=upstream_state_ref,
        unknowns=_tuple(source.get("unknowns")),
        contradictions=_tuple(source.get("contradictions")),
        risk_flags=_tuple(source.get("risk_flags")),
        evidence_refs=_tuple(source.get("evidence_refs")),
        provenance_refs=tuple(str(v) for v in provenance_refs),
    )


def build_conformance_report(
    *,
    profile_id: str,
    source: Mapping[str, Any],
    state: DomainStateRefV0,
    payload: GovernancePayloadV0,
) -> ConformanceReportV0:
    """Produce a deterministic audit report for a candidate translation."""

    _assert_source_non_sovereign(source)

    if payload.domain_id != state.domain_id:
        raise ConformanceError("domain identity drift")
    if payload.domain_state_ref != state.state_ref:
        raise ConformanceError("state reference drift")
    if payload.unknowns != state.unknowns:
        raise ConformanceError("unknowns were not conserved")
    if payload.contradictions != state.contradictions:
        raise ConformanceError("contradictions were not conserved")
    if payload.risk_flags != state.risk_flags:
        raise ConformanceError("risk flags were not conserved")
    if payload.evidence_refs != state.evidence_refs:
        raise ConformanceError("evidence references were not conserved")
    if payload.provenance_refs != state.provenance_refs:
        raise ConformanceError("provenance references were not conserved")
    if payload.decision is not None:
        raise ConformanceError("payload contains a decision")
    if payload.binder_permission:
        raise ConformanceError("payload grants Binder permission")
    if payload.allowed_to_act:
        raise ConformanceError("payload authorizes action")
    if payload.decision_authority != DECISION_AUTHORITY:
        raise ConformanceError("payload changed decision authority")

    consumed = {
        "domain",
        "unknowns",
        "contradictions",
        "risk_flags",
        "evidence_refs",
        "decision_authority",
        "allowed_to_decide",
        "allowed_to_act",
        *_REQUIRED_SOVEREIGNTY_FALSE,
        *_OPTIONAL_WRITE_FALSE,
    }
    ignored = tuple(sorted(str(k) for k in source.keys() if k not in consumed))

    return ConformanceReportV0(
        profile_id=profile_id,
        domain_id=state.domain_id,
        status="PASS",
        checks=(
            "DOMAIN_IDENTITY_PRESERVED",
            "STATE_REFERENCE_PRESERVED",
            "UNKNOWNS_PRESERVED",
            "CONTRADICTIONS_PRESERVED",
            "RISKS_PRESERVED",
            "EVIDENCE_PRESERVED",
            "PROVENANCE_PRESERVED",
            "NO_DECISION_CREATED",
            "NO_BINDER_PERMISSION_CREATED",
            "NO_ACTION_AUTHORITY_CREATED",
            "KX108_ONLY_PRESERVED",
        ),
        preserved_fields=(
            "domain_id",
            "state_ref",
            "upstream_state_ref",
            "unknowns",
            "contradictions",
            "risk_flags",
            "evidence_refs",
            "provenance_refs",
        ),
        ignored_domain_fields=ignored,
    )


def conform_main_domain_snapshot(
    source: Mapping[str, Any],
    *,
    profile_id: str,
    state_ref: str,
    valid_at: str,
    upstream_state_ref: str | None = None,
    provenance_refs: Iterable[str] = (),
    proposed_action_ref: str | None = None,
) -> tuple[DomainStateRefV0, GovernancePayloadV0, ConformanceReportV0]:
    state = main_domain_snapshot_to_state(
        source,
        state_ref=state_ref,
        valid_at=valid_at,
        upstream_state_ref=upstream_state_ref,
        provenance_refs=provenance_refs,
    )
    payload = domain_state_to_governance_payload(
        state,
        proposed_action_ref=proposed_action_ref,
    )
    report = build_conformance_report(
        profile_id=profile_id,
        source=source,
        state=state,
        payload=payload,
    )
    return state, payload, report
