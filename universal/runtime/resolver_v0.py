"""F2.3 — canonical-runtime-compatible resolver overlay.

The current upstream runtime has two explicit boundaries:

    is_supported_domain(domain)
    resolve_domain_pipeline(domain) -> Callable[[state, packet], envelope]

This module preserves that shape.

Resolution order is strict:
1. current upstream canonical domain pipeline, if one exists;
2. explicitly registered portable runtime binding;
3. fail closed.

A portable binding cannot shadow a canonical upstream domain.
No upstream source file is modified here.
"""
from __future__ import annotations

from dataclasses import dataclass
import importlib
import math
from pathlib import Path
import sys
from typing import Any, Callable, Mapping

from universal.bridge.generic_guard_bridge_v0 import (
    payload_to_real_upstream_generic_aggregate,
    registered_raw_input_to_payload,
)
from universal.contracts.domain_v0 import GovernancePayloadV0
from universal.registry.portable_v0 import (
    DomainRegistrationError,
    PortableDomainRegistryV0,
)


class PortableRuntimeResolutionError(RuntimeError):
    pass


ConfidenceProvider = Callable[[Mapping[str, Any]], float]


@dataclass(frozen=True)
class PortableRuntimeBindingV0:
    domain_id: str
    confidence_provider_id: str
    decision_authority: str = "KX108_ONLY"
    allowed_to_decide: bool = False
    binder_permission: bool = False
    allowed_to_act: bool = False
    emits_act: bool = False
    emits_verdict: bool = False
    kernel_mutation: bool = False
    x108_mutation: bool = False
    memory_write: bool = False

    def __post_init__(self) -> None:
        if not self.domain_id:
            raise PortableRuntimeResolutionError("domain_id is required")
        if not self.confidence_provider_id:
            raise PortableRuntimeResolutionError("confidence_provider_id is required")
        if self.decision_authority != "KX108_ONLY":
            raise PortableRuntimeResolutionError(
                "decision authority must remain KX108_ONLY"
            )
        if any(
            (
                self.allowed_to_decide,
                self.binder_permission,
                self.allowed_to_act,
                self.emits_act,
                self.emits_verdict,
                self.kernel_mutation,
                self.x108_mutation,
                self.memory_write,
            )
        ):
            raise PortableRuntimeResolutionError(
                "portable runtime binding cannot grant authority"
            )


def _ensure_upstream_import_paths(source_root: str | Path) -> Path:
    root = Path(source_root).resolve()
    for candidate in (root, root / "scripts"):
        value = str(candidate)
        if value not in sys.path:
            sys.path.insert(0, value)
    return root


def _load_real_upstream_runtime(source_root: str | Path):
    _ensure_upstream_import_paths(source_root)
    try:
        return importlib.import_module("obsidia_governed_runtime_cycle_v1")
    except Exception as exc:  # pragma: no cover - cross-repo CI path
        raise PortableRuntimeResolutionError(
            f"cannot import upstream governed runtime: {exc}"
        ) from exc


def _load_real_guard():
    try:
        from sigma.guard import GuardX108
    except Exception as exc:  # pragma: no cover - cross-repo CI path
        raise PortableRuntimeResolutionError(
            f"cannot import upstream GuardX108: {exc}"
        ) from exc
    return GuardX108


def _bounded_confidence(value: Any) -> float:
    try:
        result = float(value)
    except Exception as exc:
        raise PortableRuntimeResolutionError(
            "confidence provider must return a number"
        ) from exc
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise PortableRuntimeResolutionError(
            "confidence provider must return a finite value in [0,1]"
        )
    return result


def _merge_packet_into_payload(
    payload: GovernancePayloadV0,
    packet: Any,
) -> GovernancePayloadV0:
    """Conservative equivalent of the current periphery signal merge.

    It preserves current packet semantics:
    - packet cannot emit ACT;
    - HOLD recommendation contributes an unknown;
    - BLOCK_CANDIDATE contributes a contradiction;
    - packet evidence is conserved.

    It never turns recommended_gate into a decision.
    """

    packet.assert_non_sovereign()

    unknowns = list(payload.unknowns)
    contradictions = list(payload.contradictions)
    risk_flags = list(payload.risk_flags)
    evidence_refs = list(payload.evidence_refs)

    unknowns.extend(list(getattr(packet, "unknowns", ()) or ()))
    contradictions.extend(list(getattr(packet, "contradictions", ()) or ()))
    risk_flags.extend(list(getattr(packet, "risk_flags", ()) or ()))
    evidence_refs.extend(list(getattr(packet, "evidence_refs", ()) or ()))

    recommended_gate = str(getattr(packet, "recommended_gate", "NONE"))
    if recommended_gate == "HOLD":
        unknowns.append("PERIPHERY_RECOMMENDS_HOLD")
    elif recommended_gate == "BLOCK_CANDIDATE":
        contradictions.append("PERIPHERY_BLOCK_CANDIDATE")
    elif recommended_gate != "NONE":
        raise PortableRuntimeResolutionError(
            f"unsupported peripheral gate hint: {recommended_gate}"
        )

    evidence_refs.append(
        f"periphery:{getattr(packet, 'action_id', '')}:{recommended_gate}"
    )

    return GovernancePayloadV0(
        domain_id=payload.domain_id,
        domain_state_ref=payload.domain_state_ref,
        upstream_state_ref=payload.upstream_state_ref,
        unknowns=tuple(sorted(set(unknowns))),
        contradictions=tuple(sorted(set(contradictions))),
        risk_flags=tuple(sorted(set(risk_flags))),
        evidence_refs=tuple(sorted(set(evidence_refs))),
        provenance_refs=payload.provenance_refs,
        proposed_action_ref=payload.proposed_action_ref,
    )


class CanonicalCompatibleResolverV0:
    """Overlay resolver preserving upstream canonical precedence and fail-closed."""

    def __init__(
        self,
        *,
        source_root: str | Path,
        registry: PortableDomainRegistryV0,
    ) -> None:
        self.source_root = _ensure_upstream_import_paths(source_root)
        self.registry = registry
        self._runtime = _load_real_upstream_runtime(self.source_root)
        self._bindings: dict[str, PortableRuntimeBindingV0] = {}
        self._confidence: dict[str, ConfidenceProvider] = {}

    def bind_portable_runtime(
        self,
        binding: PortableRuntimeBindingV0,
        confidence_provider: ConfidenceProvider,
    ) -> None:
        # Domain semantics must already be explicitly registered.
        self.registry.registration(binding.domain_id)

        # Never shadow a real canonical current-main pipeline.
        if self._runtime.is_supported_domain(binding.domain_id):
            raise PortableRuntimeResolutionError(
                f"CANONICAL_DOMAIN_SHADOW_FORBIDDEN:{binding.domain_id}"
            )
        if binding.domain_id in self._bindings:
            raise PortableRuntimeResolutionError(
                f"DUPLICATE_PORTABLE_RUNTIME_BINDING:{binding.domain_id}"
            )
        if not callable(confidence_provider):
            raise PortableRuntimeResolutionError(
                "confidence_provider must be callable"
            )

        self._bindings[binding.domain_id] = binding
        self._confidence[binding.domain_id] = confidence_provider

    def is_supported_domain(self, domain_id: str) -> bool:
        return self._runtime.is_supported_domain(domain_id) or (
            domain_id in self._bindings
        )

    def supported_domains(self) -> tuple[str, ...]:
        upstream = set(getattr(self._runtime, "SUPPORTED_DOMAINS", ()))
        return tuple(sorted(upstream | set(self._bindings)))

    def resolve_domain_pipeline(
        self,
        domain_id: str,
    ) -> Callable[[Any, Any], Any]:
        # Existing canonical upstream route always wins.
        if self._runtime.is_supported_domain(domain_id):
            return self._runtime.resolve_domain_pipeline(domain_id)

        binding = self._bindings.get(domain_id)
        if binding is None:
            raise PortableRuntimeResolutionError(
                f"NO_CANONICAL_OR_PORTABLE_DOMAIN_PIPELINE:{domain_id}"
            )

        confidence_provider = self._confidence[domain_id]

        def portable_pipeline(raw_state: Any, packet: Any):
            if getattr(packet, "domain", None) != domain_id:
                raise PortableRuntimeResolutionError(
                    f"PACKET_DOMAIN_BINDING_MISMATCH:{domain_id}:"
                    f"{getattr(packet, 'domain', None)}"
                )
            if not isinstance(raw_state, Mapping):
                raise PortableRuntimeResolutionError(
                    "portable raw state must be a mapping"
                )

            payload = registered_raw_input_to_payload(
                self.registry,
                domain_id,
                raw_state,
                proposed_action_ref=f"action:{getattr(packet, 'action_id', '')}",
            )
            payload = _merge_packet_into_payload(payload, packet)

            confidence = _bounded_confidence(confidence_provider(raw_state))
            aggregate = payload_to_real_upstream_generic_aggregate(
                self.registry,
                payload,
                confidence=confidence,
            )

            aggregate.extra_metrics.update(
                dict(getattr(packet, "extra_metrics", {}) or {})
            )
            aggregate.extra_metrics.update(
                {
                    "f23_resolver": "CANONICAL_COMPATIBLE_RESOLVER_V0",
                    "portable_runtime_binding": binding.domain_id,
                    "portable_runtime_binding_can_decide": False,
                    "portable_runtime_binding_can_act": False,
                    "canonical_upstream_pipeline_shadowed": False,
                }
            )

            GuardX108 = _load_real_guard()
            return GuardX108().decide(aggregate)

        portable_pipeline.__name__ = f"run_{domain_id}_portable_v0"
        return portable_pipeline
