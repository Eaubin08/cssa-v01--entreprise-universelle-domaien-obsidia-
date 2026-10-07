"""F2.1 — direct compatibility probe against obsidia-x108-proofs main.

No kernel code is copied here.

At test/runtime, a frozen upstream checkout can be placed on sys.path. This
module then:
1. reads the upstream governed-runtime domain table;
2. refuses domains that current main has not registered;
3. converts an F1 GovernancePayloadV0 into the REAL upstream DomainAggregate;
4. calls the REAL upstream GuardX108;
5. returns the REAL upstream CanonicalDecisionEnvelope.

The bridge itself never decides and never grants execution permission.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable

from universal.contracts.domain_v0 import GovernancePayloadV0


class UpstreamRuntimeCompatibilityError(RuntimeError):
    pass


class UnsupportedCurrentMainDomain(UpstreamRuntimeCompatibilityError):
    pass


def _read_domain_pipeline_keys(source_root: str | Path) -> tuple[str, ...]:
    root = Path(source_root)
    path = root / "scripts" / "obsidia_governed_runtime_cycle_v1.py"
    if not path.is_file():
        raise UpstreamRuntimeCompatibilityError(
            f"upstream runtime file missing: {path}"
        )

    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))

    for node in tree.body:
        target_name = None
        value = None

        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target_name = node.target.id
            value = node.value
        elif isinstance(node, ast.Assign):
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                target_name = node.targets[0].id
                value = node.value

        if target_name != "_DOMAIN_PIPELINES" or not isinstance(value, ast.Dict):
            continue

        keys: list[str] = []
        for key in value.keys:
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                keys.append(key.value)
            else:
                raise UpstreamRuntimeCompatibilityError(
                    "_DOMAIN_PIPELINES contains a non-literal domain key"
                )
        return tuple(keys)

    raise UpstreamRuntimeCompatibilityError(
        "_DOMAIN_PIPELINES not found in upstream governed runtime"
    )


def current_main_supported_domains(source_root: str | Path) -> tuple[str, ...]:
    """Return the actual governed-runtime domain keys from frozen upstream source."""
    return tuple(sorted(_read_domain_pipeline_keys(source_root)))


def _load_real_upstream_types():
    """Import only after the upstream checkout has been placed on sys.path."""
    try:
        from sigma.contracts import Domain, DomainAggregate
        from sigma.guard import GuardX108
    except Exception as exc:  # pragma: no cover - exercised in cross-repo CI
        raise UpstreamRuntimeCompatibilityError(
            f"cannot import real upstream sigma surfaces: {exc}"
        ) from exc

    return Domain, DomainAggregate, GuardX108


def governance_payload_to_real_upstream_aggregate(
    payload: GovernancePayloadV0,
    *,
    source_root: str | Path,
    confidence: float,
):
    """Translate F1 payload to the real current-main aggregate type.

    The pre-Guard business verdict is forced to HOLD. A domain payload never
    supplies a sovereign gate.
    """

    supported = set(current_main_supported_domains(source_root))
    if payload.domain_id not in supported:
        raise UnsupportedCurrentMainDomain(
            f"NO_CANONICAL_DOMAIN_PIPELINE:{payload.domain_id}"
        )

    if payload.decision is not None:
        raise UpstreamRuntimeCompatibilityError("payload contains a decision")
    if payload.binder_permission:
        raise UpstreamRuntimeCompatibilityError("payload grants Binder permission")
    if payload.allowed_to_act:
        raise UpstreamRuntimeCompatibilityError("payload authorizes action")
    if payload.decision_authority != "KX108_ONLY":
        raise UpstreamRuntimeCompatibilityError(
            "payload changed decision authority"
        )

    Domain, DomainAggregate, _ = _load_real_upstream_types()

    by_value = {member.value: member for member in Domain}

    # Current main has an explicit "gps" runtime alias but its canonical
    # Domain enum is gps_defense_aviation. Preserve that current-main alias
    # without inventing a new sovereign domain.
    enum_domain_id = (
        "gps_defense_aviation"
        if payload.domain_id == "gps"
        else payload.domain_id
    )
    domain = by_value.get(enum_domain_id)
    if domain is None:
        raise UnsupportedCurrentMainDomain(
            f"NO_UPSTREAM_DOMAIN_ENUM:{payload.domain_id}"
        )

    provenance_evidence = [
        f"provenance:{ref}" for ref in payload.provenance_refs
    ]

    return DomainAggregate(
        domain=domain,
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
            "f21_source": "UNIVERSAL_GOVERNANCE_PAYLOAD_V0",
            "domain_state_ref": payload.domain_state_ref,
            "upstream_state_ref": payload.upstream_state_ref,
            "proposed_action_ref": payload.proposed_action_ref,
            "input_decision_authority": payload.decision_authority,
            "universal_payload_can_decide": False,
            "universal_payload_can_act": False,
        },
    )


def decide_with_real_current_main_guard(
    payload: GovernancePayloadV0,
    *,
    source_root: str | Path,
    confidence: float,
):
    """Call the real upstream GuardX108 after bounded compatibility checks."""

    aggregate = governance_payload_to_real_upstream_aggregate(
        payload,
        source_root=source_root,
        confidence=confidence,
    )
    _, _, GuardX108 = _load_real_upstream_types()
    return GuardX108().decide(aggregate)
