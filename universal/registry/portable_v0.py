"""F2.2 — portable, non-sovereign domain registration contract.

This registry is descriptive and routing-only.

A registration:
- names a domain;
- names an adapter;
- states the contract version;
- may expose descriptive capabilities;
- never grants decision, Binder, execution, memory, or kernel authority.

DOMAIN REGISTRATION != DOMAIN AUTHORITY
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Any

from universal.contracts.domain_v0 import DomainStateRefV0


class DomainRegistrationError(ValueError):
    pass


@dataclass(frozen=True)
class PortableDomainRegistrationV0:
    domain_id: str
    adapter_id: str
    contract_version: str = "PORTABLE_DOMAIN_REGISTRATION_V0"
    schema_ref: str | None = None
    capabilities: tuple[str, ...] = ()
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
        if not self.domain_id or self.domain_id.strip() != self.domain_id:
            raise DomainRegistrationError("domain_id must be non-empty and trimmed")
        if not self.adapter_id or self.adapter_id.strip() != self.adapter_id:
            raise DomainRegistrationError("adapter_id must be non-empty and trimmed")
        if self.decision_authority != "KX108_ONLY":
            raise DomainRegistrationError("decision authority must remain KX108_ONLY")
        forbidden = (
            self.allowed_to_decide,
            self.binder_permission,
            self.allowed_to_act,
            self.emits_act,
            self.emits_verdict,
            self.kernel_mutation,
            self.x108_mutation,
            self.memory_write,
        )
        if any(forbidden):
            raise DomainRegistrationError("portable registration cannot grant authority")


AdapterFn = Callable[[Mapping[str, Any]], DomainStateRefV0]


class PortableDomainRegistryV0:
    """In-memory registry used to prove the contract.

    It does not auto-discover modules, execute arbitrary entry points, or mutate
    the Obsidia runtime. Adapter functions are explicitly supplied by the host.
    """

    def __init__(self) -> None:
        self._registrations: dict[str, PortableDomainRegistrationV0] = {}
        self._adapters: dict[str, AdapterFn] = {}

    def register(
        self,
        registration: PortableDomainRegistrationV0,
        adapter: AdapterFn,
    ) -> None:
        if registration.domain_id in self._registrations:
            raise DomainRegistrationError(
                f"duplicate domain registration: {registration.domain_id}"
            )
        if registration.adapter_id in self._adapters:
            raise DomainRegistrationError(
                f"duplicate adapter registration: {registration.adapter_id}"
            )
        if not callable(adapter):
            raise DomainRegistrationError("adapter must be callable")

        self._registrations[registration.domain_id] = registration
        self._adapters[registration.adapter_id] = adapter

    def domains(self) -> tuple[str, ...]:
        return tuple(sorted(self._registrations))

    def registration(self, domain_id: str) -> PortableDomainRegistrationV0:
        try:
            return self._registrations[domain_id]
        except KeyError as exc:
            raise DomainRegistrationError(
                f"UNREGISTERED_PORTABLE_DOMAIN:{domain_id}"
            ) from exc

    def adapt(
        self,
        domain_id: str,
        raw_input: Mapping[str, Any],
    ) -> DomainStateRefV0:
        reg = self.registration(domain_id)
        adapter = self._adapters[reg.adapter_id]
        state = adapter(raw_input)

        if not isinstance(state, DomainStateRefV0):
            raise DomainRegistrationError(
                f"adapter {reg.adapter_id} did not return DomainStateRefV0"
            )
        if state.domain_id != domain_id:
            raise DomainRegistrationError(
                f"DOMAIN_BINDING_MISMATCH:{domain_id}!={state.domain_id}"
            )
        if state.decision_authority != "KX108_ONLY":
            raise DomainRegistrationError("adapter changed decision authority")
        if state.allowed_to_decide or state.allowed_to_act:
            raise DomainRegistrationError("adapter state leaked authority")
        return state
