"""F2.2 generic registered-domain bridge to the REAL upstream GuardX108.

This is a proof candidate OUTSIDE the canonical upstream governed-runtime
coordinator. It does not change upstream files and does not create execution
authority.

The only purpose is to answer a narrow question:

Can an explicitly registered new domain, carrying only the F1 universal
contract, reach the existing GuardX108 without adding its business semantics
to KX108?

Yes, if the bridge supplies a non-sovereign domain identity token and the
current Guard contract continues to consume only aggregate.domain.value.

This is NOT yet a canonical runtime registration mechanism.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from universal.contracts.domain_v0 import (
    GovernancePayloadV0,
    domain_state_to_governance_payload,
)
from universal.registry.portable_v0 import PortableDomainRegistryV0


@dataclass(frozen=True)
class PortableDomainValueV0:
    """Minimal domain identity carrier expected by current GuardX108."""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("portable domain value is required")


def _load_real_upstream_types():
    try:
        from sigma.contracts import DomainAggregate
        from sigma.guard import GuardX108
    except Exception as exc:  # pragma: no cover - cross-repo CI path
        raise RuntimeError(f"cannot import real upstream Guard surfaces: {exc}") from exc
    return DomainAggregate, GuardX108


def registered_raw_input_to_payload(
    registry: PortableDomainRegistryV0,
    domain_id: str,
    raw_input: Mapping[str, Any],
    *,
    proposed_action_ref: str | None = None,
) -> GovernancePayloadV0:
    state = registry.adapt(domain_id, raw_input)
    return domain_state_to_governance_payload(
        state,
        proposed_action_ref=proposed_action_ref,
    )


def payload_to_real_upstream_generic_aggregate(
    registry: PortableDomainRegistryV0,
    payload: GovernancePayloadV0,
    *,
    confidence: float,
):
    """Build the REAL upstream DomainAggregate with registered identity only."""

    registry.registration(payload.domain_id)

    if payload.decision is not None:
        raise ValueError("payload contains a decision")
    if payload.binder_permission:
        raise ValueError("payload grants Binder permission")
    if payload.allowed_to_act:
        raise ValueError("payload authorizes action")
    if payload.decision_authority != "KX108_ONLY":
        raise ValueError("payload changed decision authority")

    DomainAggregate, _ = _load_real_upstream_types()

    provenance_evidence = [
        f"provenance:{ref}" for ref in payload.provenance_refs
    ]

    return DomainAggregate(
        domain=PortableDomainValueV0(payload.domain_id),
        market_verdict="HOLD",
        confidence=float(confidence),
        contradictions=list(payload.contradictions),
        unknowns=list(payload.unknowns),
        risk_flags=list(payload.risk_flags),
        evidence_refs=list(
            dict.fromkeys([*payload.evidence_refs, *provenance_evidence])
        ),
        agent_votes=[],
        extra_metrics={
            "f22_source": "PORTABLE_DOMAIN_REGISTRATION_V0",
            "registered_domain": payload.domain_id,
            "domain_state_ref": payload.domain_state_ref,
            "upstream_state_ref": payload.upstream_state_ref,
            "proposed_action_ref": payload.proposed_action_ref,
            "input_decision_authority": payload.decision_authority,
            "portable_registry_can_decide": False,
            "portable_registry_can_act": False,
            "canonical_runtime_registration_proven": False,
        },
    )


def decide_registered_domain_with_real_guard(
    registry: PortableDomainRegistryV0,
    domain_id: str,
    raw_input: Mapping[str, Any],
    *,
    confidence: float,
    proposed_action_ref: str | None = None,
):
    """Use the real upstream Guard; never grants runtime/execution authority."""

    payload = registered_raw_input_to_payload(
        registry,
        domain_id,
        raw_input,
        proposed_action_ref=proposed_action_ref,
    )
    aggregate = payload_to_real_upstream_generic_aggregate(
        registry,
        payload,
        confidence=confidence,
    )
    _, GuardX108 = _load_real_upstream_types()
    return GuardX108().decide(aggregate)
