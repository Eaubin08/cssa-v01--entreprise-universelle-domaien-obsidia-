"""Universal métier-domain -> execution proposal adapter contract V0.

A domain adapter translates domain facts into UniversalActionProposalV0.
It is routing/translation only and cannot grant decision or execution authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .contract_v0 import (
    DECISION_AUTHORITY,
    UniversalActionProposalV0,
    UniversalExecutionContractError,
    UniversalExecutionSurfaceRegistryV0,
    verify_universal_action_proposal_v0,
)


@dataclass(frozen=True)
class ExecutionDomainAdapterRegistrationV0:
    domain_id: str
    adapter_id: str
    allowed_surface_ids: tuple[str, ...]
    contract_version: str = "UNIVERSAL_EXECUTION_DOMAIN_ADAPTER_V0"
    decision_authority: str = DECISION_AUTHORITY
    allowed_to_decide: bool = False
    allowed_to_act: bool = False
    emits_act: bool = False
    kernel_mutation: bool = False
    memory_write: bool = False

    def __post_init__(self) -> None:
        if not self.domain_id or self.domain_id.strip() != self.domain_id:
            raise UniversalExecutionContractError(
                "domain_id must be non-empty and trimmed"
            )
        if not self.adapter_id or self.adapter_id.strip() != self.adapter_id:
            raise UniversalExecutionContractError(
                "adapter_id must be non-empty and trimmed"
            )
        if not self.allowed_surface_ids:
            raise UniversalExecutionContractError(
                "allowed_surface_ids cannot be empty"
            )
        if len(set(self.allowed_surface_ids)) != len(self.allowed_surface_ids):
            raise UniversalExecutionContractError(
                "duplicate allowed_surface_id"
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
                "domain adapter registration cannot grant authority"
            )


ExecutionDomainAdapterFn = Callable[
    [Mapping[str, Any], UniversalExecutionSurfaceRegistryV0],
    UniversalActionProposalV0,
]


class UniversalExecutionDomainAdapterRegistryV0:
    def __init__(
        self,
        *,
        surface_registry: UniversalExecutionSurfaceRegistryV0,
    ) -> None:
        self.surface_registry = surface_registry
        self._registrations: dict[
            str,
            ExecutionDomainAdapterRegistrationV0,
        ] = {}
        self._adapters: dict[str, ExecutionDomainAdapterFn] = {}

    def register(
        self,
        registration: ExecutionDomainAdapterRegistrationV0,
        adapter: ExecutionDomainAdapterFn,
    ) -> None:
        if registration.domain_id in self._registrations:
            raise UniversalExecutionContractError(
                f"duplicate execution domain:{registration.domain_id}"
            )
        if registration.adapter_id in self._adapters:
            raise UniversalExecutionContractError(
                f"duplicate execution adapter:{registration.adapter_id}"
            )
        if not callable(adapter):
            raise UniversalExecutionContractError(
                "execution domain adapter must be callable"
            )

        for surface_id in registration.allowed_surface_ids:
            self.surface_registry.get(surface_id)

        self._registrations[registration.domain_id] = registration
        self._adapters[registration.adapter_id] = adapter

    def domains(self) -> tuple[str, ...]:
        return tuple(sorted(self._registrations))

    def registration(
        self,
        domain_id: str,
    ) -> ExecutionDomainAdapterRegistrationV0:
        try:
            return self._registrations[domain_id]
        except KeyError as exc:
            raise UniversalExecutionContractError(
                f"UNREGISTERED_EXECUTION_DOMAIN:{domain_id}"
            ) from exc

    def propose(
        self,
        domain_id: str,
        raw_case: Mapping[str, Any],
    ) -> UniversalActionProposalV0:
        registration = self.registration(domain_id)
        adapter = self._adapters[registration.adapter_id]
        proposal = adapter(raw_case, self.surface_registry)

        if not isinstance(proposal, UniversalActionProposalV0):
            raise UniversalExecutionContractError(
                "execution domain adapter did not return UniversalActionProposalV0"
            )
        proposal.assert_non_sovereign()
        if proposal.domain_id != domain_id:
            raise UniversalExecutionContractError(
                f"EXECUTION_DOMAIN_BINDING_MISMATCH:"
                f"{domain_id}!={proposal.domain_id}"
            )
        if proposal.surface_id not in registration.allowed_surface_ids:
            raise UniversalExecutionContractError(
                f"EXECUTION_SURFACE_NOT_ALLOWED_FOR_DOMAIN:"
                f"{domain_id}:{proposal.surface_id}"
            )

        ok, reason = verify_universal_action_proposal_v0(
            registry=self.surface_registry,
            proposal=proposal,
        )
        if not ok:
            raise UniversalExecutionContractError(
                f"INVALID_UNIVERSAL_ACTION_PROPOSAL:{reason}"
            )
        return proposal
