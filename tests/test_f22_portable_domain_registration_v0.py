import os
import sys
from pathlib import Path

import pytest

from universal.bridge.generic_guard_bridge_v0 import (
    decide_registered_domain_with_real_guard,
    payload_to_real_upstream_generic_aggregate,
    registered_raw_input_to_payload,
)
from universal.contracts.domain_v0 import DomainStateRefV0
from universal.integration.main_runtime_v0 import current_main_supported_domains
from universal.registry.portable_v0 import (
    DomainRegistrationError,
    PortableDomainRegistrationV0,
    PortableDomainRegistryV0,
)


UPSTREAM = Path(os.environ["OBSIDIA_UPSTREAM_ROOT"]).resolve()
if str(UPSTREAM) not in sys.path:
    sys.path.insert(0, str(UPSTREAM))


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


def warehouse_adapter(raw):
    return DomainStateRefV0(
        domain_id="warehouse",
        state_ref=str(raw["state_ref"]),
        valid_at=str(raw["valid_at"]),
        unknowns=tuple(raw.get("unknowns", ())),
        contradictions=tuple(raw.get("contradictions", ())),
        risk_flags=tuple(raw.get("risk_flags", ())),
        evidence_refs=tuple(raw.get("evidence_refs", ())),
        provenance_refs=tuple(raw.get("provenance_refs", ())),
    )


def registry():
    r = PortableDomainRegistryV0()
    r.register(
        PortableDomainRegistrationV0(
            domain_id="administration",
            adapter_id="administration.v0",
            schema_ref="schemas/administration-v0",
            capabilities=("read", "classify", "propose"),
        ),
        admin_adapter,
    )
    r.register(
        PortableDomainRegistrationV0(
            domain_id="warehouse",
            adapter_id="warehouse.v0",
            schema_ref="schemas/warehouse-v0",
            capabilities=("observe", "propose"),
        ),
        warehouse_adapter,
    )
    return r


def admin_raw(**overrides):
    raw = {
        "case_ref": "admin:case:1",
        "valid_at": "2026-10-06T20:00:00Z",
        "source_ref": "source:mail:1",
        "unknowns": (),
        "contradictions": (),
        "risk_flags": (),
        "evidence_refs": ("rule:1",),
        "provenance_refs": ("source:public",),
        # Business-only fields that must not be promoted by Universal:
        "email_subject": "fixture change",
        "assigned_person": "human-1",
        "deadline_days": 10,
    }
    raw.update(overrides)
    return raw


def test_portable_registry_registers_multiple_unrelated_domains():
    r = registry()
    assert r.domains() == ("administration", "warehouse")


def test_registration_is_non_sovereign():
    reg = registry().registration("administration")
    assert reg.decision_authority == "KX108_ONLY"
    assert reg.allowed_to_decide is False
    assert reg.binder_permission is False
    assert reg.allowed_to_act is False
    assert reg.emits_act is False
    assert reg.emits_verdict is False
    assert reg.kernel_mutation is False
    assert reg.x108_mutation is False
    assert reg.memory_write is False


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
def test_registration_authority_leak_fails_closed(mutation):
    kwargs = {
        "domain_id": "bad",
        "adapter_id": "bad.v0",
    }
    kwargs.update(mutation)
    with pytest.raises(DomainRegistrationError):
        PortableDomainRegistrationV0(**kwargs)


def test_duplicate_domain_registration_is_rejected():
    r = PortableDomainRegistryV0()
    reg = PortableDomainRegistrationV0(
        domain_id="administration",
        adapter_id="administration.v0",
    )
    r.register(reg, admin_adapter)
    with pytest.raises(DomainRegistrationError, match="duplicate domain"):
        r.register(
            PortableDomainRegistrationV0(
                domain_id="administration",
                adapter_id="administration.v1",
            ),
            admin_adapter,
        )


def test_unregistered_domain_is_rejected_before_guard():
    r = registry()
    with pytest.raises(
        DomainRegistrationError,
        match="UNREGISTERED_PORTABLE_DOMAIN:not_registered",
    ):
        decide_registered_domain_with_real_guard(
            r,
            "not_registered",
            {
                "state_ref": "x",
                "valid_at": "2026-10-06T20:00:00Z",
            },
            confidence=0.9,
        )


def test_adapter_domain_binding_mismatch_is_rejected():
    r = PortableDomainRegistryV0()

    def bad_adapter(raw):
        return DomainStateRefV0(
            domain_id="wrong_domain",
            state_ref="x",
            valid_at="2026-10-06T20:00:00Z",
        )

    r.register(
        PortableDomainRegistrationV0(
            domain_id="administration",
            adapter_id="bad.v0",
        ),
        bad_adapter,
    )

    with pytest.raises(DomainRegistrationError, match="DOMAIN_BINDING_MISMATCH"):
        r.adapt("administration", {})


def test_current_main_remains_unmodified_and_does_not_register_administration():
    assert "administration" not in set(current_main_supported_domains(UPSTREAM))


def test_registered_administration_reaches_real_guard_without_main_registration():
    envelope = decide_registered_domain_with_real_guard(
        registry(),
        "administration",
        admin_raw(),
        confidence=0.90,
        proposed_action_ref="proposal:admin:1",
    )

    from sigma.contracts import CanonicalDecisionEnvelope

    assert isinstance(envelope, CanonicalDecisionEnvelope)
    assert envelope.domain == "administration"
    assert envelope.market_verdict == "HOLD"
    assert envelope.x108_gate == "ALLOW"
    assert envelope.reason_code == "GUARD_ALLOW"


def test_arbitrary_second_domain_reaches_same_real_guard_without_kernel_change():
    envelope = decide_registered_domain_with_real_guard(
        registry(),
        "warehouse",
        {
            "state_ref": "warehouse:state:1",
            "valid_at": "2026-10-06T20:00:00Z",
            "evidence_refs": ("sensor:1",),
        },
        confidence=0.90,
    )
    assert envelope.domain == "warehouse"
    assert envelope.x108_gate == "ALLOW"


def test_registered_domain_unknowns_reach_real_guard_hold():
    envelope = decide_registered_domain_with_real_guard(
        registry(),
        "administration",
        admin_raw(unknowns=("u1", "u2")),
        confidence=0.90,
    )
    assert envelope.domain == "administration"
    assert envelope.x108_gate == "HOLD"
    assert envelope.reason_code == "UNKNOWNS_OR_CONFIDENCE_LOW"


def test_registered_domain_contradictions_reach_real_guard_block():
    envelope = decide_registered_domain_with_real_guard(
        registry(),
        "administration",
        admin_raw(contradictions=("c1", "c2")),
        confidence=0.90,
    )
    assert envelope.domain == "administration"
    assert envelope.x108_gate == "BLOCK"
    assert envelope.reason_code == "CONTRADICTION_THRESHOLD_REACHED"


def test_business_fields_stop_at_domain_adapter_boundary():
    r = registry()
    payload = registered_raw_input_to_payload(
        r,
        "administration",
        admin_raw(),
        proposed_action_ref="proposal:admin:1",
    )
    assert not hasattr(payload, "email_subject")
    assert not hasattr(payload, "assigned_person")
    assert not hasattr(payload, "deadline_days")
    assert payload.domain_id == "administration"


def test_generic_aggregate_is_real_upstream_type_and_non_sovereign():
    r = registry()
    payload = registered_raw_input_to_payload(
        r,
        "administration",
        admin_raw(),
    )
    aggregate = payload_to_real_upstream_generic_aggregate(
        r,
        payload,
        confidence=0.90,
    )

    from sigma.contracts import DomainAggregate

    assert isinstance(aggregate, DomainAggregate)
    assert aggregate.domain.value == "administration"
    assert aggregate.market_verdict == "HOLD"
    assert aggregate.extra_metrics["portable_registry_can_decide"] is False
    assert aggregate.extra_metrics["portable_registry_can_act"] is False
    assert aggregate.extra_metrics["canonical_runtime_registration_proven"] is False
    assert "provenance:source:public" in aggregate.evidence_refs
