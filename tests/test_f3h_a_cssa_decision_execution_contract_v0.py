import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

from organizations.cssa.execution import (
    DRY_RUN_COMPLETED,
    DRY_RUN_READY,
    REJECTED,
    build_action_proposal_v0,
    build_human_approval_evidence_v0,
    execute_surface_dry_run_v0,
    prepare_dry_run_execution_v0,
    proposal_runtime_state_v0,
    verify_action_proposal_v0,
)
from organizations.cssa.public_admin_v0 import cssa_public_case_adapter
from universal.registry.portable_v0 import (
    PortableDomainRegistrationV0,
    PortableDomainRegistryV0,
)
from universal.runtime.resolver_v0 import (
    CanonicalCompatibleResolverV0,
    PortableRuntimeBindingV0,
)


ROOT = Path(__file__).resolve().parents[1]
SPECS = (
    ROOT / "organizations" / "cssa" / "execution"
    / "action_proposal_specs_v0.json"
)
PROGRESS = (
    ROOT / "organizations" / "cssa" / "execution"
    / "f3h_a_decision_execution_progress_v0.json"
)

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
VALID_AT = "2026-10-07T09:00:00+02:00"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def state_hash(seed):
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def proposals():
    out = {}
    for spec in load(SPECS)["proposals"]:
        out[spec["proposal_id"]] = build_action_proposal_v0(
            proposal_id=spec["proposal_id"],
            surface=spec["surface"],
            operation=spec["operation"],
            target_ref=spec["target_ref"],
            payload=spec["payload"],
            source_case_refs=tuple(spec["source_case_refs"]),
            evidence_refs=tuple(spec["evidence_refs"]),
            expected_target_state_hash=state_hash(
                spec["expected_target_state_seed"]
            ),
        )
    return out


def make_resolver():
    registry = PortableDomainRegistryV0()
    registry.register(
        PortableDomainRegistrationV0(
            domain_id="administration",
            adapter_id="cssa.decision.execution.v0",
            schema_ref=(
                "organizations/cssa/execution/decision_execution_v0.py"
            ),
            capabilities=("read", "classify", "draft", "propose"),
        ),
        cssa_public_case_adapter,
    )
    resolver = CanonicalCompatibleResolverV0(
        source_root=UPSTREAM,
        registry=registry,
    )
    resolver.bind_portable_runtime(
        PortableRuntimeBindingV0(
            domain_id="administration",
            confidence_provider_id="cssa.execution.confidence.v0",
        ),
        lambda raw: raw["confidence"],
    )
    return resolver


class DryRunProvider:
    def __init__(self):
        self.invocations = 0

    def __call__(self, **kwargs):
        self.invocations += 1
        return {
            "runtime_id": "cssa-action-proposal-dry-run",
            "provider": "cssa_action_proposal_dry_run",
            "external_action": False,
            "connector_invoked": False,
        }


def run_kx108(tmp_path, proposal, *, unknowns=(), contradictions=()):
    flow = CanonicalRuntimeReceiptFlow()
    provider = DryRunProvider()
    flow.register_provider("cssa_action_proposal_dry_run", provider)

    raw = proposal_runtime_state_v0(
        proposal,
        valid_at=VALID_AT,
        confidence=1.0,
        unknowns=tuple(unknowns),
        contradictions=tuple(contradictions),
    )
    action = ActionCandidate(
        action_id=f"kx108-{proposal.proposal_id}",
        domain="administration",
        actor_id="f3h-a",
        intent="evaluate_cssa_action_proposal",
        action_type="analysis",
        irreversible=False,
        timestamp_plan="",
        payload={
            "freshness_score": 1.0,
            "source_count": len(proposal.evidence_refs),
            "clean_json_ready": True,
            "critical": False,
            "surface": proposal.surface,
            "proposal_hash": proposal.proposal_hash,
        },
    )
    result = upstream_runtime.run_governed_runtime_cycle(
        AGENT_ID,
        action,
        raw,
        execution_surface=flow,
        mission_id=f"mission-{proposal.proposal_id}",
        provider_id="cssa_action_proposal_dry_run",
        capability="analysis",
        execution_payload={
            "mode": "CSSA_ACTION_PROPOSAL_DRY_RUN",
            "surface": proposal.surface,
            "operation": proposal.operation,
            "proposal_hash": proposal.proposal_hash,
            "external_action": False,
        },
        agent_context_store_dir=tmp_path / proposal.proposal_id / "contexts",
        decision_store_dir=tmp_path / proposal.proposal_id / "decisions",
        domain_extension_resolver=make_resolver(),
    )
    return result, provider


def approval_for(proposal):
    return build_human_approval_evidence_v0(
        approval_id=f"approval-{proposal.proposal_id}",
        approved_by="HUMAN:CSSA_REVIEWER",
        proposal=proposal,
        approval_reference=f"sim:human-review:{proposal.proposal_id}",
    )


def test_specs_cover_all_four_surfaces():
    spec = load(SPECS)

    assert spec["status"] == "SIMULATED_NOT_OBSERVED"
    assert {row["surface"] for row in spec["proposals"]} == {
        "MAIL",
        "CALENDAR",
        "CRM",
        "TASKS",
    }


def test_all_proposals_are_non_sovereign_and_hash_verified():
    for proposal in proposals().values():
        proposal.assert_non_sovereign()
        ok, reason = verify_action_proposal_v0(proposal)
        assert ok is True
        assert reason is None
        assert proposal.allowed_to_decide is False
        assert proposal.allowed_to_act is False
        assert proposal.external_action is False
        assert proposal.world_action_allowed is False
        assert len(proposal.proposal_hash) == 64


@pytest.mark.parametrize(
    "proposal_id",
    ["ACT_MAIL_001", "ACT_CALENDAR_001", "ACT_CRM_001", "ACT_TASK_001"],
)
def test_each_surface_crosses_real_kx108_runtime_in_dry_run(
    tmp_path,
    proposal_id,
):
    proposal = proposals()[proposal_id]
    result, provider = run_kx108(tmp_path, proposal)

    assert result.x108_gate == "ALLOW"
    assert result.decision_record_persisted is True
    assert result.decision_record_verified is True
    assert result.replay_status == "PASS"
    assert result.execution_authorized is True
    assert result.provider_invoked is True
    assert provider.invocations == 1

    # Existing runtime boundary remains strictly internal/dry-run.
    assert result.world_action_allowed is False
    assert result.world_action_dry_run_only is True
    assert result.emits_act is False
    assert result.memory_write is False
    assert result.kernel_mutation is False
    assert result.decision_authority == "KX108_ONLY"


@pytest.mark.parametrize(
    "proposal_id",
    ["ACT_MAIL_001", "ACT_CALENDAR_001", "ACT_CRM_001", "ACT_TASK_001"],
)
def test_human_approved_exact_proposal_can_complete_only_surface_dry_run(
    tmp_path,
    proposal_id,
):
    proposal = proposals()[proposal_id]
    result, _ = run_kx108(tmp_path, proposal)
    approval = approval_for(proposal)

    prepared = prepare_dry_run_execution_v0(
        proposal=proposal,
        kx108_gate=result.x108_gate,
        decision_record_verified=result.decision_record_verified,
        decision_record_id=result.decision_record_id,
        approval=approval,
        current_target_state_hash=proposal.expected_target_state_hash,
    )
    assert prepared["status"] == DRY_RUN_READY
    assert prepared["external_action"] is False
    assert prepared["connector_invoked"] is False
    assert prepared["target_mutated"] is False

    receipt = execute_surface_dry_run_v0(
        proposal=proposal,
        prepared=prepared,
    )
    assert receipt["status"] == DRY_RUN_COMPLETED
    assert receipt["connector_invoked"] is False
    assert receipt["target_mutated"] is False
    assert receipt["world_action_allowed"] is False
    assert len(receipt["receipt_sha256"]) == 64


def test_human_approval_alone_never_replaces_kx108():
    proposal = proposals()["ACT_MAIL_001"]
    approval = approval_for(proposal)

    prepared = prepare_dry_run_execution_v0(
        proposal=proposal,
        kx108_gate="HOLD",
        decision_record_verified=True,
        decision_record_id="sim-kx-record",
        approval=approval,
        current_target_state_hash=proposal.expected_target_state_hash,
    )

    assert prepared["status"] == REJECTED
    assert prepared["reason"] == "KX108_PRECONDITION_NOT_ALLOW:HOLD"
    assert prepared["connector_invoked"] is False


def test_kx108_allow_without_human_approval_still_rejects(tmp_path):
    proposal = proposals()["ACT_MAIL_001"]
    result, _ = run_kx108(tmp_path, proposal)

    prepared = prepare_dry_run_execution_v0(
        proposal=proposal,
        kx108_gate=result.x108_gate,
        decision_record_verified=result.decision_record_verified,
        decision_record_id=result.decision_record_id,
        approval=None,
        current_target_state_hash=proposal.expected_target_state_hash,
    )

    assert prepared["status"] == REJECTED
    assert prepared["reason"] == "HUMAN_APPROVAL_MISSING"


def test_target_state_drift_after_approval_rejects(tmp_path):
    proposal = proposals()["ACT_CALENDAR_001"]
    result, _ = run_kx108(tmp_path, proposal)
    approval = approval_for(proposal)

    prepared = prepare_dry_run_execution_v0(
        proposal=proposal,
        kx108_gate=result.x108_gate,
        decision_record_verified=result.decision_record_verified,
        decision_record_id=result.decision_record_id,
        approval=approval,
        current_target_state_hash=state_hash("calendar-event-changed"),
    )

    assert prepared["status"] == REJECTED
    assert prepared["reason"] == "TARGET_PRESTATE_HASH_MISMATCH"
    assert prepared["target_mutated"] is False


def test_tampered_human_approval_is_rejected(tmp_path):
    proposal = proposals()["ACT_CRM_001"]
    result, _ = run_kx108(tmp_path, proposal)
    approval = approval_for(proposal)
    approval["target_ref"] = "sim:crm-contact:other"

    prepared = prepare_dry_run_execution_v0(
        proposal=proposal,
        kx108_gate=result.x108_gate,
        decision_record_verified=result.decision_record_verified,
        decision_record_id=result.decision_record_id,
        approval=approval,
        current_target_state_hash=proposal.expected_target_state_hash,
    )

    assert prepared["status"] == REJECTED
    assert prepared["reason"] == "HUMAN_APPROVAL_TARGET_MISMATCH"


def test_kx108_hold_and_block_never_invoke_dry_run_provider(tmp_path):
    proposal = proposals()["ACT_TASK_001"]

    hold, hold_provider = run_kx108(
        tmp_path / "hold",
        proposal,
        unknowns=("TARGET_OWNER_UNKNOWN", "TASK_SCOPE_UNKNOWN"),
    )
    assert hold.x108_gate == "HOLD"
    assert hold.execution_authorized is False
    assert hold.provider_invoked is False
    assert hold_provider.invocations == 0

    block, block_provider = run_kx108(
        tmp_path / "block",
        proposal,
        contradictions=(
            "TASK_TARGET_STATE_CONFLICT",
            "TASK_AUTHORITY_CONFLICT",
        ),
    )
    assert block.x108_gate == "BLOCK"
    assert block.execution_authorized is False
    assert block.provider_invoked is False
    assert block_provider.invocations == 0


def test_real_world_send_operation_is_not_available_in_f3h_a():
    with pytest.raises(
        ValueError,
        match="UNSUPPORTED_SURFACE_OPERATION:MAIL:SEND_EMAIL",
    ):
        build_action_proposal_v0(
            proposal_id="ACT_FORBIDDEN_SEND",
            surface="MAIL",
            operation="SEND_EMAIL",
            target_ref="sim:mail:forbidden",
            payload={"body": "must not send"},
            source_case_refs=("sim:case:x",),
            evidence_refs=("sim:evidence:x",),
            expected_target_state_hash=state_hash("mail-state-x"),
        )


def test_dry_run_receipt_is_deterministic():
    proposal = proposals()["ACT_TASK_001"]
    approval = approval_for(proposal)
    prepared = prepare_dry_run_execution_v0(
        proposal=proposal,
        kx108_gate="ALLOW",
        decision_record_verified=True,
        decision_record_id="sim:kx:verified:001",
        approval=approval,
        current_target_state_hash=proposal.expected_target_state_hash,
    )

    first = execute_surface_dry_run_v0(
        proposal=proposal,
        prepared=prepared,
    )
    second = execute_surface_dry_run_v0(
        proposal=proposal,
        prepared=prepared,
    )

    assert first == second


def test_progress_overlay_keeps_decision_execution_open_for_real_connectors():
    progress = load(PROGRESS)

    assert progress["status"] == (
        "PARTIAL_STRUCTURAL_CLOSURE_NO_EXTERNAL_ACTION"
    )
    assert progress["base_gap"] == "DECISION_EXECUTION"
    assert progress["current_maximum"] == "HUMAN_APPROVED_DRY_RUN"
    assert {
        "MAIL_REAL_CONNECTOR_EXECUTION",
        "CALENDAR_REAL_CONNECTOR_EXECUTION",
        "CRM_REAL_CONNECTOR_EXECUTION",
        "TASKS_REAL_CONNECTOR_EXECUTION",
        "PRE_EXECUTION_KX108_RECHECK_AT_WORLD_ACTION_BOUNDARY",
        "REAL_ACTION_RECEIPT",
        "REAL_ACTION_REPLAY",
    } <= set(progress["still_open"])
    assert progress["boundaries"] == {
        "real_external_action": False,
        "connector_invoked": False,
        "world_action_allowed": False,
        "decision_authority": "KX108_ONLY",
    }
