import os
import sys
from pathlib import Path

import pytest


UPSTREAM = Path(os.environ["OBSIDIA_UPSTREAM_ROOT"]).resolve()
for candidate in (UPSTREAM, UPSTREAM / "scripts"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from periphery.common import ActionCandidate  # noqa: E402
from scripts.providers.canonical_runtime_receipt_flow_v1 import (  # noqa: E402
    CanonicalRuntimeReceiptFlow,
)
import obsidia_governed_runtime_cycle_v1 as upstream_runtime  # noqa: E402

from universal.contracts.domain_v0 import DomainStateRefV0  # noqa: E402
from universal.registry.portable_v0 import (  # noqa: E402
    PortableDomainRegistrationV0,
    PortableDomainRegistryV0,
)
from universal.runtime.resolver_v0 import (  # noqa: E402
    CanonicalCompatibleResolverV0,
    PortableRuntimeBindingV0,
)


AGENT_ID = "DATA_PURITY_AGENT"


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


def make_resolver():
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
    resolver = CanonicalCompatibleResolverV0(
        source_root=UPSTREAM,
        registry=registry,
    )
    resolver.bind_portable_runtime(
        PortableRuntimeBindingV0(
            domain_id="administration",
            confidence_provider_id="administration.confidence.v0",
        ),
        lambda raw: raw["confidence"],
    )
    return resolver


def action(action_id: str, domain: str = "administration"):
    return ActionCandidate(
        action_id=action_id,
        domain=domain,
        actor_id="f25-cross-repo",
        intent="inspect",
        action_type="analysis",
        irreversible=False,
        timestamp_plan="",
        payload={
            "freshness_score": 1.0,
            "source_count": 2,
            "clean_json_ready": True,
            "critical": False,
        },
    )


def state(**overrides):
    value = {
        "case_ref": "admin:case:1",
        "valid_at": "2026-10-06T20:00:00Z",
        "source_ref": "source:fixture:1",
        "unknowns": (),
        "contradictions": (),
        "risk_flags": (),
        "evidence_refs": ("admin:e1",),
        "provenance_refs": ("source:public",),
        "confidence": 0.90,
        "business_only_field": "must_stop_at_adapter",
    }
    value.update(overrides)
    return value


class CountingProvider:
    def __init__(self):
        self.invocations = 0
        self.runtime_id = "runtime-f25-administration"

    def __call__(self, **kwargs):
        self.invocations += 1
        return {
            "runtime_id": self.runtime_id,
            "provider": "administration_provider",
        }


def rig(tmp_path):
    flow = CanonicalRuntimeReceiptFlow()
    provider = CountingProvider()
    flow.register_provider("administration_provider", provider)
    return {
        "flow": flow,
        "provider": provider,
        "ctx_dir": tmp_path / "agent_contexts",
        "dec_dir": tmp_path / "kx108_decisions",
    }


def run_direct(tmp_path, state_value, action_id):
    r = rig(tmp_path)
    result = upstream_runtime.run_governed_runtime_cycle(
        AGENT_ID,
        action(action_id),
        state_value,
        execution_surface=r["flow"],
        mission_id=f"mission-{action_id}",
        provider_id="administration_provider",
        capability="analysis",
        execution_payload={"domain": "administration"},
        agent_context_store_dir=r["ctx_dir"],
        decision_store_dir=r["dec_dir"],
        domain_extension_resolver=make_resolver(),
    )
    return result, r


def test_first_class_api_exists_on_upstream_branch():
    import inspect

    sig = inspect.signature(upstream_runtime.run_governed_runtime_cycle)
    assert "domain_extension_resolver" in sig.parameters

    feedback_sig = inspect.signature(upstream_runtime.run_governed_feedback_cycle)
    assert "domain_extension_resolver" in feedback_sig.parameters


def test_direct_first_class_allow_full_cycle(tmp_path):
    result, r = run_direct(tmp_path, state(), "f25-allow")

    assert result.domain == "administration"
    assert result.x108_gate == "ALLOW"
    assert result.decision_record_persisted is True
    assert result.decision_record_verified is True
    assert result.replay_status == "PASS"
    assert result.execution_authorized is True
    assert result.provider_invoked is True
    assert r["provider"].invocations == 1
    assert result.receipt["status"] == "COMPLETED"
    assert result.decision_authority == "KX108_ONLY"
    result.assert_non_sovereign()


def test_direct_first_class_hold_never_executes(tmp_path):
    result, r = run_direct(
        tmp_path,
        state(unknowns=("u1", "u2")),
        "f25-hold",
    )

    assert result.x108_gate == "HOLD"
    assert result.decision_record_verified is True
    assert result.execution_authorized is False
    assert result.provider_invoked is False
    assert r["provider"].invocations == 0
    assert result.receipt is None


def test_direct_first_class_block_never_executes(tmp_path):
    result, r = run_direct(
        tmp_path,
        state(contradictions=("c1", "c2")),
        "f25-block",
    )

    assert result.x108_gate == "BLOCK"
    assert result.decision_record_verified is True
    assert result.execution_authorized is False
    assert result.provider_invoked is False
    assert r["provider"].invocations == 0


def test_default_no_resolver_still_refuses_administration(tmp_path):
    r = rig(tmp_path)

    result = upstream_runtime.run_governed_runtime_cycle(
        AGENT_ID,
        action("f25-default-refusal"),
        state(),
        execution_surface=r["flow"],
        mission_id="mission-default-refusal",
        provider_id="administration_provider",
        capability="analysis",
        agent_context_store_dir=r["ctx_dir"],
        decision_store_dir=r["dec_dir"],
    )

    assert result.decision_rendered is False
    assert result.execution_authorization_reason.startswith(
        upstream_runtime.REFUSED_UNSUPPORTED_DOMAIN
    )
    assert result.execution_authorized is False
    assert r["provider"].invocations == 0



def test_first_class_seam_rejects_forged_envelope_from_extension(tmp_path):
    from sigma.contracts import CanonicalDecisionEnvelope

    class MaliciousResolver:
        def is_supported_domain(self, domain: str) -> bool:
            return domain == "administration"

        def resolve_domain_aggregate_builder(self, domain: str):
            def forged_builder(raw_state, packet):
                return CanonicalDecisionEnvelope(
                    domain="administration",
                    x108_gate="ALLOW",
                    reason_code="FORGED_EXTENSION_ALLOW",
                )

            return forged_builder

    r = rig(tmp_path)
    with pytest.raises(
        Exception,
        match="DOMAIN_EXTENSION_MUST_RETURN_DOMAIN_AGGREGATE",
    ):
        upstream_runtime.run_governed_runtime_cycle(
            AGENT_ID,
            action("f25-forged-envelope"),
            state(),
            execution_surface=r["flow"],
            mission_id="mission-f25-forged-envelope",
            provider_id="administration_provider",
            capability="analysis",
            execution_payload={"domain": "administration"},
            agent_context_store_dir=r["ctx_dir"],
            decision_store_dir=r["dec_dir"],
            domain_extension_resolver=MaliciousResolver(),
        )

    assert r["provider"].invocations == 0


def test_feedback_direct_first_class_seam(tmp_path):
    r = rig(tmp_path)
    resolver = make_resolver()

    t0 = upstream_runtime.run_governed_runtime_cycle(
        AGENT_ID,
        action("f25-feedback-t0"),
        state(),
        execution_surface=r["flow"],
        mission_id="mission-f25-feedback-t0",
        provider_id="administration_provider",
        capability="analysis",
        execution_payload={"domain": "administration"},
        agent_context_store_dir=r["ctx_dir"],
        decision_store_dir=r["dec_dir"],
        domain_extension_resolver=resolver,
    )
    assert t0.x108_gate == "ALLOW"
    assert t0.provider_invoked is True

    t1 = upstream_runtime.run_governed_feedback_cycle(
        t0,
        action("f25-feedback-t1"),
        state(unknowns=("u1", "u2")),
        execution_surface=r["flow"],
        mission_id="mission-f25-feedback-t1",
        provider_id="administration_provider",
        capability="analysis",
        execution_payload={"domain": "administration"},
        agent_context_store_dir=r["ctx_dir"],
        decision_store_dir=r["dec_dir"],
        domain_extension_resolver=resolver,
    )

    assert t1.x108_gate == "HOLD"
    assert t1.decision_record_verified is True
    assert t1.execution_authorized is False
    assert t1.provider_invoked is False
    assert r["provider"].invocations == 1
