"""F1 — minimal universal domain contracts for Obsidia V0.1.

Recovered from existing Obsidia domain/UDIP invariants and the October 2026
UDIP bridge candidate. This module is deliberately business-agnostic.

DOMAIN != AUTHORITY
PROPOSAL != DECISION
DECISION != ACTION
SOURCE != TRUST
KX108_ONLY
"""
from __future__ import annotations

from dataclasses import dataclass

DECISION_AUTHORITY = "KX108_ONLY"


@dataclass(frozen=True)
class DomainStateRefV0:
    """Reference to a domain state without importing domain semantics into Core.

    state_ref identifies the domain-owned state/object. upstream_state_ref is
    optional and can point to a world/organization/source-state object when one
    exists. The universal contract does not require a world model.
    """

    domain_id: str
    state_ref: str
    valid_at: str
    upstream_state_ref: str | None = None
    unknowns: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    risk_flags: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = ()
    decision_authority: str = DECISION_AUTHORITY
    allowed_to_decide: bool = False
    allowed_to_act: bool = False

    def __post_init__(self) -> None:
        if not self.domain_id:
            raise ValueError("domain_id is required")
        if not self.state_ref:
            raise ValueError("state_ref is required")
        if not self.valid_at:
            raise ValueError("valid_at is required")
        if self.decision_authority != DECISION_AUTHORITY:
            raise ValueError("decision authority must remain KX108_ONLY")
        if self.allowed_to_decide:
            raise ValueError("DomainStateRefV0 cannot decide")
        if self.allowed_to_act:
            raise ValueError("DomainStateRefV0 cannot act")


@dataclass(frozen=True)
class GovernancePayloadV0:
    """Transport from a domain boundary toward governed decision logic.

    It conserves uncertainty/evidence and can carry a proposal reference. It
    cannot contain a decision, grant Binder permission, or authorize action.
    """

    domain_id: str
    domain_state_ref: str
    upstream_state_ref: str | None = None
    unknowns: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    risk_flags: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = ()
    proposed_action_ref: str | None = None
    decision: str | None = None
    binder_permission: bool = False
    allowed_to_act: bool = False
    decision_authority: str = DECISION_AUTHORITY

    def __post_init__(self) -> None:
        if not self.domain_id:
            raise ValueError("domain_id is required")
        if not self.domain_state_ref:
            raise ValueError("domain_state_ref is required")
        if self.decision is not None:
            raise ValueError("GovernancePayloadV0 cannot contain a decision")
        if self.binder_permission:
            raise ValueError("GovernancePayloadV0 cannot grant Binder permission")
        if self.allowed_to_act:
            raise ValueError("GovernancePayloadV0 cannot authorize action")
        if self.decision_authority != DECISION_AUTHORITY:
            raise ValueError("decision authority must remain KX108_ONLY")


def domain_state_to_governance_payload(
    state: DomainStateRefV0,
    *,
    proposed_action_ref: str | None = None,
) -> GovernancePayloadV0:
    """Conservative domain -> governance translation.

    No semantic interpretation occurs here. All uncertainty, contradiction,
    risk, evidence and provenance references are preserved verbatim.
    """

    return GovernancePayloadV0(
        domain_id=state.domain_id,
        domain_state_ref=state.state_ref,
        upstream_state_ref=state.upstream_state_ref,
        unknowns=state.unknowns,
        contradictions=state.contradictions,
        risk_flags=state.risk_flags,
        evidence_refs=state.evidence_refs,
        provenance_refs=state.provenance_refs,
        proposed_action_ref=proposed_action_ref,
    )
