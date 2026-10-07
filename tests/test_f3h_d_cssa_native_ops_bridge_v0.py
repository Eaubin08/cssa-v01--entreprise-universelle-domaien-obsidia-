import json
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = (
    ROOT
    / "organizations"
    / "cssa"
    / "native_ops"
    / "cssa_native_ops_intake_fixtures_v0.json"
)

from organizations.cssa.native_ops.cssa_native_ops_bridge_v0 import (
    build_cssa_native_intake_plan_v0,
    execute_cssa_native_intake_v0,
    verify_cssa_native_intake_plan_v0,
)


def load_cases():
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert data["status"] == "SIMULATED_NOT_OBSERVED"
    return data["cases"]


def build_plan(case):
    return build_cssa_native_intake_plan_v0(
        cssa_case_id=case["cssa_case_id"],
        case_type=case["case_type"],
        title=case["title"],
        summary=case["summary"],
        owner_ref=case["owner_ref"],
        priority=case["priority"],
        occurred_at=case["occurred_at"],
        due_at=case["due_at"],
        source_refs=tuple(case["source_refs"]),
        evidence_refs=tuple(case["evidence_refs"]),
        tags=tuple(case["tags"]),
    )


@pytest.mark.parametrize("case", load_cases(), ids=lambda x: x["case_type"])
def test_cssa_case_commits_to_native_crm_task_followup(tmp_path, case):
    plan = build_plan(case)
    assert verify_cssa_native_intake_plan_v0(plan) == (True, None)

    result = execute_cssa_native_intake_v0(
        plan=plan,
        native_store_root=tmp_path / "native",
        governance_root=tmp_path / "governance",
        approved_by="HUMAN:CSSA_TEST_OPERATOR",
        approval_reference=f"fixture-approval:{case['cssa_case_id']}",
    )

    assert result["status"] == "CSSA_NATIVE_INTAKE_COMMITTED"
    assert result["canonical_mutation_count"] == 4
    assert len(result["receipt_ids"]) == 4
    assert result["timeline_event_count"] == 3
    assert result["decision_authority"] == "KX108_ONLY"
    assert result["external_action"] is False
    assert result["external_saas_required"] is False

    upstream = Path(os.environ["OBSIDIA_UPSTREAM_ROOT"])
    import sys
    for candidate in (upstream, upstream / "scripts"):
        if str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))

    from periphery.native_ops.common_v0 import NativeEntityStoreV0
    from periphery.native_ops.tasks_native_v0 import (
        DOMAIN_ID as TASK_DOMAIN,
        ENTITY_KIND as TASK_KIND,
    )
    from periphery.native_ops.crm_native_v0 import (
        DOMAIN_ID as CRM_DOMAIN,
        KIND_FOLLOWUP,
        KIND_INTERACTION,
        KIND_RECORD,
    )

    store = NativeEntityStoreV0(tmp_path / "native")
    case_state = store.load_state(
        CRM_DOMAIN, KIND_RECORD, plan.case_record_id
    )
    task_state = store.load_state(
        TASK_DOMAIN, TASK_KIND, plan.task_id
    )
    interaction_state = store.load_state(
        CRM_DOMAIN, KIND_INTERACTION, plan.interaction_id
    )
    followup_state = store.load_state(
        CRM_DOMAIN, KIND_FOLLOWUP, plan.followup_id
    )

    assert case_state["fields"]["cssa_case_id"] == case["cssa_case_id"]
    assert case_state["fields"]["case_type"] == case["case_type"]
    assert case_state["lifecycle_status"] == "OPEN"
    assert task_state["title"] == case["title"]
    assert task_state["priority"] == case["priority"]
    assert task_state["assignee_ref"] == case["owner_ref"]
    assert interaction_state["record_id"] == plan.case_record_id
    assert followup_state["record_id"] == plan.case_record_id
    assert followup_state["task_ref"] == plan.task_id

    replayed_case, replay_case_hash = store.replay(
        CRM_DOMAIN, KIND_RECORD, plan.case_record_id
    )
    replayed_task, replay_task_hash = store.replay(
        TASK_DOMAIN, TASK_KIND, plan.task_id
    )
    assert replayed_case == case_state
    assert replayed_task == task_state
    assert replay_case_hash == result["case_state_hash"]
    assert replay_task_hash == result["task_state_hash"]


def test_one_hold_blocks_entire_intake_before_native_commit(tmp_path):
    plan = build_plan(load_cases()[0])
    result = execute_cssa_native_intake_v0(
        plan=plan,
        native_store_root=tmp_path / "native",
        governance_root=tmp_path / "governance",
        approved_by="HUMAN:CSSA_TEST_OPERATOR",
        approval_reference="fixture-approval:hold",
        gate_overrides={
            "CREATE_TASK": {
                "unknowns": (
                    "REAL_ASSIGNEE_AUTHORITY_UNKNOWN",
                    "REAL_DELEGATION_SCOPE_UNKNOWN",
                )
            }
        },
    )
    assert result["status"] == "CSSA_NATIVE_INTAKE_GATED_NO_MUTATION"
    assert result["reason"] == "KX108_HOLD"
    assert result["canonical_mutation_count"] == 0
    assert not (tmp_path / "native").exists()


def test_one_block_blocks_entire_intake_before_native_commit(tmp_path):
    plan = build_plan(load_cases()[1])
    result = execute_cssa_native_intake_v0(
        plan=plan,
        native_store_root=tmp_path / "native",
        governance_root=tmp_path / "governance",
        approved_by="HUMAN:CSSA_TEST_OPERATOR",
        approval_reference="fixture-approval:block",
        gate_overrides={
            "APPEND_INTERACTION": {
                "contradictions": (
                    "SOURCE_CONFLICT",
                    "AUTHORITY_CONFLICT",
                )
            }
        },
    )
    assert result["status"] == "CSSA_NATIVE_INTAKE_GATED_NO_MUTATION"
    assert result["reason"] == "KX108_BLOCK"
    assert result["canonical_mutation_count"] == 0
    assert not (tmp_path / "native").exists()


def test_duplicate_cssa_case_is_rejected_without_second_mutation_batch(tmp_path):
    plan = build_plan(load_cases()[2])
    first = execute_cssa_native_intake_v0(
        plan=plan,
        native_store_root=tmp_path / "native",
        governance_root=tmp_path / "governance-a",
        approved_by="HUMAN:CSSA_TEST_OPERATOR",
        approval_reference="fixture-approval:first",
    )
    assert first["canonical_mutation_count"] == 4

    second = execute_cssa_native_intake_v0(
        plan=plan,
        native_store_root=tmp_path / "native",
        governance_root=tmp_path / "governance-b",
        approved_by="HUMAN:CSSA_TEST_OPERATOR",
        approval_reference="fixture-approval:second",
    )
    assert second["status"] == "CSSA_NATIVE_INTAKE_REJECTED"
    assert second["reason"] == "CANONICAL_NATIVE_TARGET_ALREADY_EXISTS"
    assert second["canonical_mutation_count"] == 0


def test_plan_tamper_is_detected():
    plan = build_plan(load_cases()[0])
    object.__setattr__(plan, "title", "tampered")
    ok, reason = verify_cssa_native_intake_plan_v0(plan)
    assert ok is False
    assert reason == "CSSA_NATIVE_PLAN_HASH_MISMATCH"


def test_machine_cannot_approve_native_intake(tmp_path):
    plan = build_plan(load_cases()[0])
    with pytest.raises(
        ValueError,
        match="CSSA_NATIVE_EXPLICIT_HUMAN_APPROVER_REQUIRED",
    ):
        execute_cssa_native_intake_v0(
            plan=plan,
            native_store_root=tmp_path / "native",
            governance_root=tmp_path / "governance",
            approved_by="MACHINE",
            approval_reference="invalid",
        )


def test_native_bridge_never_requires_external_saas():
    for case in load_cases():
        plan = build_plan(case)
        assert plan.decision_authority == "KX108_ONLY"
        assert plan.allowed_to_decide is False
        assert plan.allowed_to_act is False
