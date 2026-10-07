import json
import os
import sys
from pathlib import Path

import pytest

from organizations.cssa.field import field_runtime_adapter
from organizations.cssa.simulated import (
    SIMULATION_STATUS,
    scenario_from_mapping,
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
MATRIX = ROOT / "organizations" / "cssa" / "simulated" / "scenario_matrix_v0.json"

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


def load_raw_matrix():
    return json.loads(MATRIX.read_text(encoding="utf-8"))


def load_scenarios():
    return [scenario_from_mapping(x) for x in load_raw_matrix()["scenarios"]]


def make_resolver():
    registry = PortableDomainRegistryV0()
    registry.register(
        PortableDomainRegistrationV0(
            domain_id="administration",
            adapter_id="cssa.simulated.field.v0",
            schema_ref="organizations/cssa/simulated/scenarios_v0.py",
            capabilities=("read", "classify", "detect", "propose"),
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
            confidence_provider_id="cssa.simulated.confidence.v0",
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
            "runtime_id": "cssa-simulated-readonly",
            "provider": "cssa_simulated_readonly",
        }


def test_matrix_has_15_scenarios_and_is_explicitly_synthetic():
    raw = load_raw_matrix()
    assert raw["status"] == SIMULATION_STATUS
    assert len(raw["scenarios"]) == 15

    ids = [s["scenario_id"] for s in raw["scenarios"]]
    assert len(ids) == len(set(ids))


def test_no_raw_user_mail_identifiers_are_committed():
    text = MATRIX.read_text(encoding="utf-8").lower()
    forbidden = (
        "aetienne08260",
        "@gmail.com",
        "1a0f121baf783a14",
        "1a0d2c5aae0900cc",
        "1a0cec842faf4c0b",
    )
    assert all(value not in text for value in forbidden)


@pytest.mark.parametrize("scenario", load_scenarios(), ids=lambda s: s.scenario_id)
def test_every_scenario_preserves_simulation_truth_boundary(scenario):
    assert scenario.simulation_status == SIMULATION_STATUS
    assert scenario.field_case.validated_by_cssa is False

    bundle = scenario.to_bundle()
    assert bundle.validate() == ()
    for source in bundle.sources:
        assert source.evidence_class == "INFERRED_PATTERN"
        assert "F3C_SIMULATION_ONLY" in source.provenance_refs


@pytest.mark.parametrize("scenario", load_scenarios(), ids=lambda s: s.scenario_id)
def test_privacy_gate_matches_scenario_expectation(scenario):
    bundle = scenario.to_bundle()
    ready = scenario.field_case.case_ref in bundle.runtime_ready_case_refs()

    if scenario.expected_gate == "PRE_RUNTIME_BLOCK":
        assert ready is False
        assert any(s.requires_manual_privacy_review for s in bundle.sources)
    else:
        assert ready is True


@pytest.mark.parametrize(
    "scenario",
    [s for s in load_scenarios() if s.expected_gate != "PRE_RUNTIME_BLOCK"],
    ids=lambda s: s.scenario_id,
)
def test_simulated_cssa_cases_cross_real_runtime_with_expected_gate(
    tmp_path,
    scenario,
):
    raw = scenario.to_simulated_runtime_mapping(confidence=0.92)
    assert raw["simulation_status"] == SIMULATION_STATUS
    assert raw["simulation_truth_assumed"] is True

    flow = CanonicalRuntimeReceiptFlow()
    provider = CountingProvider()
    flow.register_provider("cssa_simulated_readonly", provider)

    action = ActionCandidate(
        action_id=f"f3c-{scenario.scenario_id.lower()}",
        domain="administration",
        actor_id="f3c-simulation",
        intent="evaluate_simulated_cssa_case",
        action_type="analysis",
        irreversible=False,
        timestamp_plan="",
        payload={
            "freshness_score": 1.0,
            "source_count": max(2, len(scenario.field_case.source_ids)),
            "clean_json_ready": True,
            "critical": False,
        },
    )

    result = upstream_runtime.run_governed_runtime_cycle(
        AGENT_ID,
        action,
        raw,
        execution_surface=flow,
        mission_id=f"mission-{scenario.scenario_id.lower()}",
        provider_id="cssa_simulated_readonly",
        capability="analysis",
        execution_payload={
            "mode": "READONLY_SIMULATION",
            "scenario_id": scenario.scenario_id,
        },
        agent_context_store_dir=tmp_path / scenario.scenario_id / "contexts",
        decision_store_dir=tmp_path / scenario.scenario_id / "decisions",
        domain_extension_resolver=make_resolver(),
    )

    assert result.domain == "administration"
    assert result.x108_gate == scenario.expected_gate
    assert result.provider_invoked is scenario.expected_provider_invoked
    assert provider.invocations == (1 if scenario.expected_provider_invoked else 0)

    assert result.decision_record_verified is True
    assert result.decision_authority == "KX108_ONLY"
    assert result.memory_write is False
    assert result.kernel_mutation is False
    assert result.emits_act is False
    assert result.world_action_allowed is False

    if scenario.expected_provider_invoked:
        assert result.execution_authorized is True
        assert result.receipt["status"] == "COMPLETED"
    else:
        assert result.execution_authorized is False
        assert result.receipt is None


def test_transactional_confirmation_does_not_become_administration_authority():
    scenario = next(
        s for s in load_scenarios()
        if s.scenario_id == "S07_TICKET_PURCHASE_CONFIRMATION"
    )
    raw = scenario.to_simulated_runtime_mapping(confidence=0.92)
    state = field_runtime_adapter(raw)

    assert state.domain_id == "administration"
    assert state.allowed_to_decide is False
    assert state.allowed_to_act is False
    assert state.decision_authority == "KX108_ONLY"


def test_visible_channel_difference_does_not_infer_internal_migration():
    scenario = next(
        s for s in load_scenarios()
        if s.scenario_id == "S13_CHANNEL_MIGRATION_NOT_INFERRED"
    )
    raw = scenario.to_simulated_runtime_mapping(confidence=0.92)

    assert "INTERNAL_TOOLING_UNKNOWN" in raw["unknowns"]
    assert "CHANNEL_MIGRATION_NOT_PROVEN" in raw["unknowns"]
    assert scenario.expected_gate == "HOLD"
