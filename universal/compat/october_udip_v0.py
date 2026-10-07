"""Compatibility adapter for the October 2026 UDIP bridge candidate."""
from __future__ import annotations

from typing import Any, Mapping

from universal.contracts.domain_v0 import DomainStateRefV0


def october_udip_state_to_f1(source: Mapping[str, Any]) -> DomainStateRefV0:
    domain_id = str(source.get("domain_id") or "").strip()
    world_state_ref = str(source.get("world_state_ref") or "").strip()
    valid_at = str(source.get("valid_at") or "").strip()

    if not domain_id or not world_state_ref or not valid_at:
        raise ValueError("domain_id, world_state_ref and valid_at are required")

    if source.get("decision_authority", "KX108_ONLY") != "KX108_ONLY":
        raise ValueError("decision authority must remain KX108_ONLY")
    if source.get("allowed_to_decide") is True:
        raise ValueError("October UDIP state cannot decide")
    if source.get("allowed_to_act") is True:
        raise ValueError("October UDIP state cannot act")

    state_ref = f"{domain_id}:{world_state_ref}:{valid_at}"

    return DomainStateRefV0(
        domain_id=domain_id,
        state_ref=state_ref,
        valid_at=valid_at,
        upstream_state_ref=world_state_ref,
        unknowns=tuple(str(v) for v in source.get("unknowns", ()) or ()),
        contradictions=tuple(str(v) for v in source.get("contradictions", ()) or ()),
        risk_flags=tuple(str(v) for v in source.get("risk_flags", ()) or ()),
        evidence_refs=tuple(str(v) for v in source.get("evidence_refs", ()) or ()),
        provenance_refs=tuple(str(v) for v in source.get("provenance_refs", ()) or ()),
    )
