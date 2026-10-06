import os
import sys
from pathlib import Path

import pytest

from universal.contracts.domain_v0 import DomainStateRefV0
from universal.registry.portable_v0 import (
    PortableDomainRegistrationV0,
    PortableDomainRegistryV0,
)
from universal.runtime.resolver_v0 import (
    CanonicalCompatibleResolverV0,
    PortableRuntimeBindingV0,
    PortableRuntimeResolutionError,
)


UPSTREAM = Path(os.environ["OBSIDIA_UPSTREAM_ROOT"]).resolve()
for candidate in (UPSTREAM, UPSTREAM / "scripts"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from periphery.common import PeripheralSignalPacket  # noqa: E402
import obsidia_governed_runtime_cycle_v1 as upstream_runtime  # noqa: E402


def admin_adapter(raw):
    return DomainStateRefV0(
        domain_id="administration",
        state_ref=str(raw["case_ref"]),
        valid_at=str(raw["valid_at"]),
        upstream_state_ref=raw.get("source_ref"),
        unknowns=tuple(raw.get("unknowns", ())),
        contradictions=tuple(raw.get("contradictions", ())),
        risk_flags=tuple(raw.get("risk_flags", ())),
        evidence_refs=tuple(raw.get("evidence_refs", ())),
        provenance_refs=tuple(raw.get("provenance_refs", ())),
    )


def bank_adapter(raw):
    return DomainStateRefV0(
        domain_id="bank",
        state_ref="portable:bank:shadow",
        valid_at="2026-10-06T20:00:00Z",
    )


def make_registry():
    registry = PortableDomainRegistryV0()
    registry.register(
        PortableDomainRegistrationV0(
            domain_id="administration",
            adapter_id="administration.v0",
            schema_ref="schemas/administration-v0",
            capabilities=("read", "classify", "propose"),
        ),
        admin_adapter,
    )
    return registry


def make_resolver():
    resolver = CanonicalCompatibleResolverV0(
        source_root=UPSTREAM,
        registry=make_registry(),
    )
    resolver.bind_portable_runtime(
        PortableRuntimeBindingV0(
            domain_id="administration",
            confidence_provider_id="administration.confidence.v0",
        ),
        lambda raw: raw["confidence"],
    )
    return resolver


def raw_admin(**overrides):
    value = {
        "case_ref": "admin:case:1",
        "valid_at": "2026-10-06T20:00:00Z",
        "source_ref": "source:mail:1",
        "unknowns": (),
        "contradictions": (),
        "risk_flags": (),
        "evidence_refs": ("rule:1",),
        "provenance_refs": ("source:public",),
        "confidence": 0.90,
        "email_subject": "fixture change",
    }
    value.update(overrides)
    return value


def packet(**overrides):
    value = {
        "action_id": "action-admin-1",
        "domain": "administration",
        "extra_metrics": {"fixture": True},
        "unknowns": [],
        "risk_flags": [],
        "contradictions": [],
        "evidence_refs": ["packet:e1"],
        "recommended_gate": "NONE",
        "can_emit_act": False,
    }
    value.update(overrides)
    return PeripheralSignalPacket(**value)


def test_builtin_current_main_resolution_has_strict_precedence():
    resolver = make_resolver()

    for domain in ("bank", "trading", "ecom", "gps", "gps_defense_aviation"):
        resolved = resolver.resolve_domain_pipeline(domain)
        canonical = upstream_runtime.resolve_domain_pipeline(domain)
        assert resolved is canonical


def test_supported_domains_are_union_without_mutating_upstream_table():
    before = tuple(upstream_runtime.SUPPORTED_DOMAINS)
    resolver = make_resolver()

    assert resolver.is_supported_domain("administration") is True
    assert "administration" in resolver.supported_domains()

    assert tuple(upstream_runtime.SUPPORTED_DOMAINS) == before
    assert "administration" not in upstream_runtime.SUPPORTED_DOMAINS
    assert upstream_runtime.is_supported_domain("administration") is False


def test_portable_domain_cannot_shadow_current_main_domain():
    registry = make_registry()
    registry.register(
        PortableDomainRegistrationV0(
            domain_id="bank",
            adapter_id="bank.shadow.v0",
        ),
        bank_adapter,
    )
    resolver = CanonicalCompatibleResolverV0(
        source_root=UPSTREAM,
        registry=registry,
    )

    with pytest.raises(
        PortableRuntimeResolutionError,
        match="CANONICAL_DOMAIN_SHADOW_FORBIDDEN:bank",
    ):
        resolver.bind_portable_runtime(
            PortableRuntimeBindingV0(
                domain_id="bank",
                confidence_provider_id="bank.shadow.confidence",
            ),
            lambda raw: 0.9,
        )


def test_unknown_domain_still_fails_closed_before_guard():
    resolver = make_resolver()

    assert resolver.is_supported_domain("not_registered") is False
    with pytest.raises(
        PortableRuntimeResolutionError,
        match="NO_CANONICAL_OR_PORTABLE_DOMAIN_PIPELINE:not_registered",
    ):
        resolver.resolve_domain_pipeline("not_registered")


def test_portable_pipeline_has_same_state_packet_signature_and_reaches_real_guard():
    resolver = make_resolver()
    pipeline = resolver.resolve_domain_pipeline("administration")

    envelope = pipeline(raw_admin(), packet())

    from sigma.contracts import CanonicalDecisionEnvelope

    assert isinstance(envelope, CanonicalDecisionEnvelope)
    assert envelope.domain == "administration"
    assert envelope.market_verdict == "HOLD"
    assert envelope.x108_gate == "ALLOW"
    assert envelope.reason_code == "GUARD_ALLOW"
    assert envelope.metrics["f23_resolver"] == "CANONICAL_COMPATIBLE_RESOLVER_V0"
    assert envelope.metrics["canonical_upstream_pipeline_shadowed"] is False


def test_packet_domain_mismatch_fails_closed():
    pipeline = make_resolver().resolve_domain_pipeline("administration")

    with pytest.raises(
        PortableRuntimeResolutionError,
        match="PACKET_DOMAIN_BINDING_MISMATCH",
    ):
        pipeline(raw_admin(), packet(domain="warehouse"))


def test_periphery_cannot_emit_act():
    pipeline = make_resolver().resolve_domain_pipeline("administration")

    with pytest.raises(AssertionError, match="PERIPHERY_CANNOT_EMIT_ACT"):
        pipeline(raw_admin(), packet(can_emit_act=True))


def test_periphery_unknowns_are_conserved_into_real_guard():
    pipeline = make_resolver().resolve_domain_pipeline("administration")

    envelope = pipeline(
        raw_admin(unknowns=("domain-u1",)),
        packet(unknowns=["packet-u2"]),
    )
    assert envelope.x108_gate == "HOLD"
    assert "domain-u1" in envelope.unknowns
    assert "packet-u2" in envelope.unknowns


def test_periphery_hold_hint_never_becomes_decision_but_contributes_unknown():
    pipeline = make_resolver().resolve_domain_pipeline("administration")

    envelope = pipeline(
        raw_admin(unknowns=("domain-u1",)),
        packet(recommended_gate="HOLD"),
    )
    assert envelope.market_verdict == "HOLD"
    assert envelope.x108_gate == "HOLD"
    assert "PERIPHERY_RECOMMENDS_HOLD" in envelope.unknowns


def test_periphery_block_candidate_never_becomes_decision_but_contributes_contradiction():
    pipeline = make_resolver().resolve_domain_pipeline("administration")

    envelope = pipeline(
        raw_admin(contradictions=("domain-c1",)),
        packet(recommended_gate="BLOCK_CANDIDATE"),
    )
    assert envelope.market_verdict == "HOLD"
    assert envelope.x108_gate == "BLOCK"
    assert "PERIPHERY_BLOCK_CANDIDATE" in envelope.contradictions


@pytest.mark.parametrize("bad_confidence", [-0.1, 1.1, float("inf"), "not-a-number"])
def test_invalid_domain_confidence_fails_closed(bad_confidence):
    pipeline = make_resolver().resolve_domain_pipeline("administration")

    with pytest.raises(PortableRuntimeResolutionError):
        pipeline(raw_admin(confidence=bad_confidence), packet())


def test_low_domain_confidence_reaches_real_guard_as_hold():
    pipeline = make_resolver().resolve_domain_pipeline("administration")

    envelope = pipeline(raw_admin(confidence=0.30), packet())
    assert envelope.x108_gate == "HOLD"
    assert envelope.reason_code == "UNKNOWNS_OR_CONFIDENCE_LOW"


@pytest.mark.parametrize(
    "mutation",
    [
        {"decision_authority": "DOMAIN"},
        {"allowed_to_decide": True},
        {"binder_permission": True},
        {"allowed_to_act": True},
        {"emits_act": True},
        {"emits_verdict": True},
        {"kernel_mutation": True},
        {"x108_mutation": True},
        {"memory_write": True},
    ],
)
def test_runtime_binding_authority_leak_is_rejected(mutation):
    kwargs = {
        "domain_id": "administration",
        "confidence_provider_id": "confidence.v0",
    }
    kwargs.update(mutation)
    with pytest.raises(PortableRuntimeResolutionError):
        PortableRuntimeBindingV0(**kwargs)
