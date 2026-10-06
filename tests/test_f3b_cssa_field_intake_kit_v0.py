import json
import os
import sys
from pathlib import Path

import pytest

from organizations.cssa.field import (
    CSSAFieldBundleV0,
    CSSAFieldCaseV0,
    CSSAFieldSourceV0,
    bundle_from_mapping,
    field_runtime_adapter,
)
from universal.registry.portable_v0 import (
    PortableDomainRegistrationV0,
    PortableDomainRegistryV0,
)
from universal.runtime.resolver_v0 import (
    CanonicalCompatibleResolverV0,
    PortableRuntimeBindingV0,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "organizations" / "cssa" / "field" / "fixtures"

UPSTREAM = Path(os.environ["OBSIDIA_UPSTREAM_ROOT"]).resolve()
for candidate in (UPSTREAM, UPSTREAM / "scripts"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from periphery.common import ActionCandidate  # noqa: E402
from scripts.providers.canonical_runtime_receipt_flow_v1 import (  # noqa: E402
    CanonicalRuntimeReceiptFlow,
)
import obsidia_governed_runtime_cycle_v1 as upstream_runtime  # noqa: E402


AGENT_ID = "DATA_PURITY_AGENT"


def load_fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_fixture_change_sample_loads_and_validates():
    bundle = bundle_from_mapping(load_fixture("fixture_change_anonymized_v0.json"))
    assert isinstance(bundle, CSSAFieldBundleV0)
    assert bundle.validate() == ()
    assert bundle.runtime_ready_case_refs() == ("sample-fixture-change-001",)


def test_fmi_exception_marks_human_memory_dependency_and_unvalidated_unknown():
    bundle = bundle_from_mapping(load_fixture("fmi_exception_anonymized_v0.json"))
    case = bundle.cases[0]
    state = case.to_domain_state_ref()

    assert "HUMAN_MEMORY_ONLY_DEPENDENCY" in state.risk_flags
    assert "EXCEPTION_PATH_OBSERVED" in state.risk_flags
    assert "FIELD_CASE_NOT_YET_CSSA_VALIDATED" in state.unknowns
    assert "who_validates_paper_send" in state.unknowns


def test_high_sensitivity_source_stops_before_runtime_ingest():
    bundle = bundle_from_mapping(load_fixture("high_sensitivity_blocked_v0.json"))
    source = bundle.sources[0]

    assert source.requires_manual_privacy_review is True
    assert source.runtime_ingest_allowed is False
    assert bundle.runtime_ready_case_refs() == ()


def test_field_sources_are_readonly_only():
    with pytest.raises(ValueError, match="READONLY"):
        CSSAFieldSourceV0(
            source_id="x",
            evidence_class="EMAIL_THREAD",
            observed_at="2026-10-06T20:00:00Z",
            source_type="EMAIL",
            source_ref="x",
            access_scope="WRITE",
        )


def test_unknown_evidence_class_rejected():
    with pytest.raises(ValueError, match="evidence_class"):
        CSSAFieldSourceV0(
            source_id="x",
            evidence_class="MAGIC",
            observed_at="2026-10-06T20:00:00Z",
            source_type="EMAIL",
            source_ref="x",
        )


def test_missing_source_reference_fails_bundle_validation():
    raw = load_fixture("fixture_change_anonymized_v0.json")
    raw["cases"][0]["source_ids"] = ["missing-source"]
    with pytest.raises(ValueError, match="MISSING_SOURCE_REF"):
        bundle_from_mapping(raw)


def test_repeated_local_practice_is_evidence_not_rule():
    case = CSSAFieldCaseV0(
        case_ref="practice:1",
        case_type_observed="recurring_reminder",
        valid_at="2026-10-06T20:00:00Z",
        source_ids=("staff-statement-1",),
        local_practice_refs=("practice:always-phone-first",),
        validated_by_cssa=False,
    )
    state = case.to_domain_state_ref()

    assert "practice:always-phone-first" in state.evidence_refs
    assert "FIELD_CASE_NOT_YET_CSSA_VALIDATED" in state.unknowns
    assert state.decision_authority == "KX108_ONLY"


def test_business_semantics_stop_at_field_runtime_adapter():
    bundle = bundle_from_mapping(load_fixture("fixture_change_anonymized_v0.json"))
    raw = bundle.cases[0].to_runtime_mapping(confidence=0.80)
    state = field_runtime_adapter(raw)

    assert state.domain_id == "administration"
    assert state.decision_authority == "KX108_ONLY"
    assert not hasattr(state, "responsible_role_observed")
    assert not hasattr(state, "tools_observed")
    assert not hasattr(state, "channel_observed")


def make_resolver():
    registry = PortableDomainRegistryV0()
    registry.register(
        PortableDomainRegistrationV0(
            domain_id="administration",
            adapter_id="cssa.field.v0",
            schema_ref="organizations/cssa/field/contracts_v0.py",
            capabilities=("read", "classify", "link", "detect", "propose"),
        ),
        field_runtime_adapter,
    )
    resolver = CanonicalCompatibleResolverV0(
        source_root=UPSTREAM,
        registry=registry,
    )
    resolver.bind_portable_runtime(
        PortableRuntimeBindingV0(
            domain_id="administration",
            confidence_provider_id="cssa.field.confidence.v0",
        ),
        lambda raw: raw["confidence"],
    )
    return resolver


class CountingProvider:
    def __init__(self):
        self.invocations = 0

    def __call__(self, **kwargs):
        self.invocations += 1
        return {
            "runtime_id": "cssa-field-readonly-provider",
            "provider": "cssa_field_readonly",
        }


def test_unvalidated_field_case_goes_hold_not_execution(tmp_path):
    bundle = bundle_from_mapping(load_fixture("fixture_change_anonymized_v0.json"))
    raw = bundle.cases[0].to_runtime_mapping(confidence=0.90)

    flow = CanonicalRuntimeReceiptFlow()
    provider = CountingProvider()
    flow.register_provider("cssa_field_readonly", provider)

    action = ActionCandidate(
        action_id="cssa-field-unvalidated",
        domain="administration",
        actor_id="f3b",
        intent="inspect_field_case",
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

    result = upstream_runtime.run_governed_runtime_cycle(
        AGENT_ID,
        action,
        raw,
        execution_surface=flow,
        mission_id="mission-cssa-field-unvalidated",
        provider_id="cssa_field_readonly",
        capability="analysis",
        execution_payload={"mode": "READONLY_FIELD_REVIEW"},
        agent_context_store_dir=tmp_path / "contexts",
        decision_store_dir=tmp_path / "decisions",
        domain_extension_resolver=make_resolver(),
    )

    # Unvalidated field evidence is intentionally not silently trusted.
    assert result.x108_gate == "HOLD"
    assert result.reason_code == "UNKNOWNS_OR_CONFIDENCE_LOW"
    assert result.execution_authorized is False
    assert result.provider_invoked is False
    assert provider.invocations == 0


def test_cssa_validated_clean_field_case_can_reach_bounded_readonly_provider(tmp_path):
    raw_bundle = load_fixture("fixture_change_anonymized_v0.json")
    raw_bundle["cases"][0]["validated_by_cssa"] = True
    raw_bundle["cases"][0]["missing_information"] = []
    raw_bundle["cases"][0]["exceptions"] = []
    bundle = bundle_from_mapping(raw_bundle)
    raw = bundle.cases[0].to_runtime_mapping(confidence=0.92)

    flow = CanonicalRuntimeReceiptFlow()
    provider = CountingProvider()
    flow.register_provider("cssa_field_readonly", provider)

    action = ActionCandidate(
        action_id="cssa-field-validated",
        domain="administration",
        actor_id="f3b",
        intent="classify_validated_field_case",
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

    result = upstream_runtime.run_governed_runtime_cycle(
        AGENT_ID,
        action,
        raw,
        execution_surface=flow,
        mission_id="mission-cssa-field-validated",
        provider_id="cssa_field_readonly",
        capability="analysis",
        execution_payload={"mode": "READONLY_FIELD_CLASSIFICATION"},
        agent_context_store_dir=tmp_path / "contexts",
        decision_store_dir=tmp_path / "decisions",
        domain_extension_resolver=make_resolver(),
    )

    assert result.x108_gate == "ALLOW"
    assert result.provider_invoked is True
    assert provider.invocations == 1
    assert result.receipt["status"] == "COMPLETED"
    assert result.memory_write is False
    assert result.kernel_mutation is False
    assert result.emits_act is False
    assert result.world_action_allowed is False
