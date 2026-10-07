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
from universal.runtime.full_cycle_v0 import (  # noqa: E402
    inject_portable_resolver_v0,
    run_portable_governed_runtime_cycle,
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


def action(action_id="admin-cycle-1", domain="administration"):
    return ActionCandidate(
        action_id=action_id,
        domain=domain,
        actor_id="f24-test",
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


def admin_state(**overrides):
    data = {
        "case_ref": "admin:case:1",
        "valid_at": "2026-10-06T20:00:00Z",
        "source_ref": "source:fixture:1",
        "unknowns": (),
        "contradictions": (),
        "risk_flags": (),
        "evidence_refs": ("admin:e1",),
        "provenance_refs": ("source:public",),
        "confidence": 0.90,
        "email_subject": "business-only-field",
    }
    data.update(overrides)
    return data


class CountingProvider:
    def __init__(self):
        self.invocations = 0
        self.runtime_id = "runtime-f24-administration"

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


def run_admin(tmp_path, state, action_id):
    r = rig(tmp_path)
    result = run_portable_governed_runtime_cycle(
        make_resolver(),
        AGENT_ID,
        action(action_id),
        state,
        execution_surface=r["flow"],
        mission_id=f"mission-{action_id}",
        provider_id="administration_provider",
        capability="analysis",
        execution_payload={"domain": "administration", "case": state["case_ref"]},
        agent_context_store_dir=r["ctx_dir"],
        decision_store_dir=r["dec_dir"],
    )
    return result, r


def test_full_portable_allow_runs_real_canonical_lifecycle(tmp_path):
    result, r = run_admin(tmp_path, admin_state(), "admin-allow")

    assert result.domain == "administration"
    assert result.decision_rendered is True
    assert result.x108_gate == "ALLOW"

    assert result.context_id.startswith("cp-agent-")
    assert result.context_validation["valid"] is True
    assert result.context_boundary["passed"] is True

    assert result.agent_pre_execution_context_verified is True
    assert result.decision_record_persisted is True
    assert result.decision_record_verified is True
    assert result.decision_phase == "AGENT_PRE_EXECUTION"

    assert result.os3_ticket_id
    assert result.input_hash
    assert result.output_hash
    assert result.trace_hash
    assert result.merkle_root
    assert result.replay_status == "PASS"

    assert result.execution_authorized is True
    assert result.execution_authorization_reason == upstream_runtime.EXECUTION_AUTHORIZED
    assert result.provider_invoked is True
    assert r["provider"].invocations == 1

    assert result.envelope_status == "SEALED"
    assert result.receipt["status"] == "COMPLETED"
    assert result.receipt["result_ref"] == r["provider"].runtime_id

    assert result.feedback["memory_write_allowed"] is False
    assert result.next_context_id.startswith("cp-feedback-")

    assert result.memory_write is False
    assert result.kernel_mutation is False
    assert result.emits_act is False
    assert result.world_action_allowed is False
    assert result.world_action_dry_run_only is True
    assert result.decision_authority == "KX108_ONLY"
    result.assert_non_sovereign()


def test_full_portable_hold_is_recorded_and_never_executes(tmp_path):
    result, r = run_admin(
        tmp_path,
        admin_state(unknowns=("u1", "u2")),
        "admin-hold",
    )

    assert result.x108_gate == "HOLD"
    assert result.decision_rendered is True
    assert result.decision_record_persisted is True
    assert result.decision_record_verified is True
    assert result.execution_authorized is False
    assert result.execution_authorization_reason == upstream_runtime.REFUSED_GATE_NOT_ALLOW
    assert result.provider_invoked is False
    assert r["provider"].invocations == 0
    assert result.receipt is None
    result.assert_non_sovereign()


def test_full_portable_block_is_recorded_and_never_executes(tmp_path):
    result, r = run_admin(
        tmp_path,
        admin_state(contradictions=("c1", "c2")),
        "admin-block",
    )

    assert result.x108_gate == "BLOCK"
    assert result.decision_rendered is True
    assert result.decision_record_persisted is True
    assert result.decision_record_verified is True
    assert result.execution_authorized is False
    assert r["provider"].invocations == 0
    assert result.receipt is None
    result.assert_non_sovereign()


def test_unregistered_domain_still_refused_without_decision_or_execution(tmp_path):
    r = rig(tmp_path)
    result = run_portable_governed_runtime_cycle(
        make_resolver(),
        AGENT_ID,
        action("unknown-domain", domain="not_registered"),
        admin_state(),
        execution_surface=r["flow"],
        mission_id="mission-unknown",
        provider_id="administration_provider",
        capability="analysis",
        execution_payload={"domain": "not_registered"},
        agent_context_store_dir=r["ctx_dir"],
        decision_store_dir=r["dec_dir"],
    )

    assert result.execution_authorization_reason.startswith(
        upstream_runtime.REFUSED_UNSUPPORTED_DOMAIN
    )
    assert result.decision_rendered is False
    assert result.decision_id == ""
    assert result.decision_record_persisted is False
    assert result.execution_authorized is False
    assert result.provider_invoked is False
    assert r["provider"].invocations == 0


def test_injection_restores_real_upstream_resolver_after_success(tmp_path):
    original_supported = upstream_runtime.is_supported_domain
    original_resolve = upstream_runtime.resolve_domain_pipeline

    run_admin(tmp_path, admin_state(), "restore-success")

    assert upstream_runtime.is_supported_domain is original_supported
    assert upstream_runtime.resolve_domain_pipeline is original_resolve
    assert upstream_runtime.is_supported_domain("administration") is False


def test_injection_restores_real_upstream_resolver_after_exception():
    resolver = make_resolver()
    original_supported = upstream_runtime.is_supported_domain
    original_resolve = upstream_runtime.resolve_domain_pipeline

    with pytest.raises(RuntimeError):
        with inject_portable_resolver_v0(resolver):
            assert upstream_runtime.is_supported_domain("administration") is True
            raise RuntimeError("fixture")

    assert upstream_runtime.is_supported_domain is original_supported
    assert upstream_runtime.resolve_domain_pipeline is original_resolve
    assert upstream_runtime.is_supported_domain("administration") is False


def test_upstream_supported_domain_table_is_never_mutated(tmp_path):
    before = tuple(upstream_runtime.SUPPORTED_DOMAINS)
    run_admin(tmp_path, admin_state(), "table-immutability")
    after = tuple(upstream_runtime.SUPPORTED_DOMAINS)

    assert before == after
    assert "administration" not in after
