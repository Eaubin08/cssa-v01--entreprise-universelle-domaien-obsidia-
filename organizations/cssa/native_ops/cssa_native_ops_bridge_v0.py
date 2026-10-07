"""CSSA -> Obsidia native TASKS/CRM bridge V0.

CSSA owns métier interpretation. Obsidia native_ops owns canonical TASKS/CRM
state. This bridge translates one CSSA administrative case into a canonical
native intake bundle:

CSSA case
  -> CRM CASE record
  -> CRM intake interaction
  -> TASKS task
  -> CRM follow-up linked to that task

Every native mutation is separately bound to the canonical
WORLD_ACTION_PRE_EXECUTION rail and must receive a verified KX108 ALLOW before
any canonical native state is written.

The batch is fail-closed: all PRE decisions and a shadow semantic apply must
pass before the first real native mutation is committed.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha256
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any, Mapping, Optional

STATUS = "CSSA_NATIVE_OPS_BRIDGE_V0"
DECISION_AUTHORITY = "KX108_ONLY"


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            default=str,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _ensure_upstream_importable() -> None:
    root = os.environ.get("OBSIDIA_UPSTREAM_ROOT")
    if root and root not in sys.path:
        sys.path.insert(0, root)


def _native_modules():
    _ensure_upstream_importable()
    common = importlib.import_module("periphery.native_ops.common_v0")
    tasks = importlib.import_module("periphery.native_ops.tasks_native_v0")
    crm = importlib.import_module("periphery.native_ops.crm_native_v0")
    bridge = importlib.import_module(
        "periphery.native_ops.world_action_bridge_v0"
    )
    pre = importlib.import_module(
        "scripts.obsidia_world_action_pre_execution_v0"
    )
    return common, tasks, crm, bridge, pre


@dataclass(frozen=True)
class CSSANativeIntakePlanV0:
    plan_id: str
    cssa_case_id: str
    case_record_id: str
    task_id: str
    interaction_id: str
    followup_id: str
    case_type: str
    title: str
    summary: str
    owner_ref: str | None
    priority: str
    occurred_at: str
    due_at: str
    source_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    tags: tuple[str, ...]
    plan_hash: str
    decision_authority: str = DECISION_AUTHORITY
    allowed_to_decide: bool = False
    allowed_to_act: bool = False

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["source_refs"] = list(self.source_refs)
        data["evidence_refs"] = list(self.evidence_refs)
        data["tags"] = list(self.tags)
        return data


def build_cssa_native_intake_plan_v0(
    *,
    cssa_case_id: str,
    case_type: str,
    title: str,
    summary: str,
    owner_ref: str | None,
    priority: str,
    occurred_at: str,
    due_at: str,
    source_refs: tuple[str, ...],
    evidence_refs: tuple[str, ...],
    tags: tuple[str, ...] = (),
) -> CSSANativeIntakePlanV0:
    if not cssa_case_id or not case_type or not title.strip():
        raise ValueError("CSSA_NATIVE_CASE_ID_TYPE_TITLE_REQUIRED")
    if not summary.strip():
        raise ValueError("CSSA_NATIVE_CASE_SUMMARY_REQUIRED")
    if priority not in {"LOW", "NORMAL", "HIGH", "CRITICAL"}:
        raise ValueError("CSSA_NATIVE_CASE_PRIORITY_INVALID")
    if not source_refs:
        raise ValueError("CSSA_NATIVE_CASE_SOURCE_REFS_REQUIRED")
    if not evidence_refs:
        raise ValueError("CSSA_NATIVE_CASE_EVIDENCE_REFS_REQUIRED")

    # Upstream builders validate timezone-aware timestamps too. We keep the
    # translation deterministic and domain-neutral here.
    digest = _canonical_hash(
        {"cssa_case_id": cssa_case_id, "case_type": case_type}
    )[:20]
    bound = {
        "schema": "CSSA_NATIVE_INTAKE_PLAN_V0",
        "cssa_case_id": cssa_case_id,
        "case_record_id": f"cssa-case:{digest}",
        "task_id": f"cssa-task:{digest}",
        "interaction_id": f"cssa-intake:{digest}",
        "followup_id": f"cssa-followup:{digest}",
        "case_type": case_type,
        "title": title,
        "summary": summary,
        "owner_ref": owner_ref,
        "priority": priority,
        "occurred_at": occurred_at,
        "due_at": due_at,
        "source_refs": list(source_refs),
        "evidence_refs": list(evidence_refs),
        "tags": sorted(set(("CSSA", case_type, *tags))),
        "decision_authority": DECISION_AUTHORITY,
    }
    plan_hash = _canonical_hash(bound)
    return CSSANativeIntakePlanV0(
        plan_id=f"cssa-native-intake:{digest}",
        cssa_case_id=cssa_case_id,
        case_record_id=bound["case_record_id"],
        task_id=bound["task_id"],
        interaction_id=bound["interaction_id"],
        followup_id=bound["followup_id"],
        case_type=case_type,
        title=title,
        summary=summary,
        owner_ref=owner_ref,
        priority=priority,
        occurred_at=occurred_at,
        due_at=due_at,
        source_refs=tuple(source_refs),
        evidence_refs=tuple(evidence_refs),
        tags=tuple(bound["tags"]),
        plan_hash=plan_hash,
    )


def verify_cssa_native_intake_plan_v0(
    plan: CSSANativeIntakePlanV0,
) -> tuple[bool, str | None]:
    if plan.decision_authority != DECISION_AUTHORITY:
        return False, "CSSA_NATIVE_PLAN_AUTHORITY_INVALID"
    if plan.allowed_to_decide or plan.allowed_to_act:
        return False, "CSSA_NATIVE_PLAN_CANNOT_GRANT_AUTHORITY"
    rebound = {
        "schema": "CSSA_NATIVE_INTAKE_PLAN_V0",
        "cssa_case_id": plan.cssa_case_id,
        "case_record_id": plan.case_record_id,
        "task_id": plan.task_id,
        "interaction_id": plan.interaction_id,
        "followup_id": plan.followup_id,
        "case_type": plan.case_type,
        "title": plan.title,
        "summary": plan.summary,
        "owner_ref": plan.owner_ref,
        "priority": plan.priority,
        "occurred_at": plan.occurred_at,
        "due_at": plan.due_at,
        "source_refs": list(plan.source_refs),
        "evidence_refs": list(plan.evidence_refs),
        "tags": list(plan.tags),
        "decision_authority": DECISION_AUTHORITY,
    }
    if _canonical_hash(rebound) != plan.plan_hash:
        return False, "CSSA_NATIVE_PLAN_HASH_MISMATCH"
    return True, None


def _build_mutations(plan: CSSANativeIntakePlanV0):
    common, tasks, crm, _, _ = _native_modules()
    absent = common.ABSENT_STATE_HASH

    record = crm.build_crm_mutation_v0(
        mutation_id=f"{plan.plan_id}:crm-record",
        entity_kind=crm.KIND_RECORD,
        entity_id=plan.case_record_id,
        operation="CREATE_RECORD",
        payload={
            "occurred_at": plan.occurred_at,
            "record_type": "CASE",
            "display_label": plan.title,
            "lifecycle_status": "OPEN",
            "owner_ref": plan.owner_ref,
            "fields": {
                "cssa_case_id": plan.cssa_case_id,
                "case_type": plan.case_type,
                "summary": plan.summary,
                "source_status": "INTAKE",
            },
            "tags": list(plan.tags),
        },
        expected_prestate_hash=absent,
        source_refs=plan.source_refs,
        requested_by="CSSA_NATIVE_BRIDGE_V0",
    )
    task = tasks.build_task_mutation_v0(
        mutation_id=f"{plan.plan_id}:task",
        task_id=plan.task_id,
        operation="CREATE_TASK",
        payload={
            "occurred_at": plan.occurred_at,
            "title": plan.title,
            "description": plan.summary,
            "priority": plan.priority,
            "assignee_ref": plan.owner_ref,
            "due_at": plan.due_at,
            "dependency_ids": [],
            "tags": list(plan.tags),
        },
        expected_prestate_hash=absent,
        source_refs=plan.source_refs,
        requested_by="CSSA_NATIVE_BRIDGE_V0",
    )
    interaction = crm.build_crm_mutation_v0(
        mutation_id=f"{plan.plan_id}:interaction",
        entity_kind=crm.KIND_INTERACTION,
        entity_id=plan.interaction_id,
        operation="APPEND_INTERACTION",
        payload={
            "occurred_at": plan.occurred_at,
            "record_id": plan.case_record_id,
            "interaction_type": "SYSTEM_EVENT",
            "summary": plan.summary,
            "evidence_refs": list(plan.evidence_refs),
        },
        expected_prestate_hash=absent,
        source_refs=plan.source_refs,
        requested_by="CSSA_NATIVE_BRIDGE_V0",
    )
    followup = crm.build_crm_mutation_v0(
        mutation_id=f"{plan.plan_id}:followup",
        entity_kind=crm.KIND_FOLLOWUP,
        entity_id=plan.followup_id,
        operation="CREATE_FOLLOWUP",
        payload={
            "occurred_at": plan.occurred_at,
            "record_id": plan.case_record_id,
            "task_ref": plan.task_id,
            "due_at": plan.due_at,
        },
        expected_prestate_hash=absent,
        source_refs=plan.source_refs,
        requested_by="CSSA_NATIVE_BRIDGE_V0",
    )
    return (record, task, interaction, followup)


def _apply_one(
    *,
    store,
    mutation,
    request,
    decision_record_id: str,
    decision_store_dir: Path,
    context_store_dir: Path,
):
    _, tasks, crm, _, _ = _native_modules()
    if mutation.domain_id == tasks.DOMAIN_ID:
        return tasks.apply_task_mutation_v0(
            store=store,
            mutation=mutation,
            request=request,
            decision_record_id=decision_record_id,
            decision_store_dir=decision_store_dir,
            context_store_dir=context_store_dir,
        )
    if mutation.domain_id == crm.DOMAIN_ID:
        return crm.apply_crm_mutation_v0(
            store=store,
            mutation=mutation,
            request=request,
            decision_record_id=decision_record_id,
            decision_store_dir=decision_store_dir,
            context_store_dir=context_store_dir,
        )
    raise ValueError(f"CSSA_NATIVE_UNSUPPORTED_DOMAIN:{mutation.domain_id}")


def execute_cssa_native_intake_v0(
    *,
    plan: CSSANativeIntakePlanV0,
    native_store_root: Path,
    governance_root: Path,
    approved_by: str,
    approval_reference: str,
    gate_overrides: Optional[Mapping[str, Mapping[str, tuple[str, ...]]]] = None,
) -> dict[str, Any]:
    """Gate all four mutations, shadow-apply, then commit canonical native state.

    gate_overrides is test/audit-only structure keyed by mutation operation,
    with optional unknowns / contradictions / risk_flags tuples.
    """
    ok, reason = verify_cssa_native_intake_plan_v0(plan)
    if not ok:
        raise ValueError(reason)
    if not approved_by or approved_by == "MACHINE":
        raise ValueError("CSSA_NATIVE_EXPLICIT_HUMAN_APPROVER_REQUIRED")
    if not approval_reference:
        raise ValueError("CSSA_NATIVE_APPROVAL_REFERENCE_REQUIRED")

    common, tasks, crm, native_bridge, pre_mod = _native_modules()
    store = common.NativeEntityStoreV0(native_store_root)
    mutations = _build_mutations(plan)

    # Intake V0 is create-only. Existing canonical objects fail before PRE.
    for mutation in mutations:
        current = store.state_hash(
            mutation.domain_id, mutation.entity_kind, mutation.entity_id
        )
        if current != common.ABSENT_STATE_HASH:
            return {
                "status": "CSSA_NATIVE_INTAKE_REJECTED",
                "reason": "CANONICAL_NATIVE_TARGET_ALREADY_EXISTS",
                "mutation_id": mutation.mutation_id,
                "canonical_mutation_count": 0,
                "decision_authority": DECISION_AUTHORITY,
            }

    gated: list[tuple[Any, dict[str, Any], Any, Path, Path]] = []
    for mutation in mutations:
        request = native_bridge.build_native_world_action_request_v0(mutation)
        approval = native_bridge.build_native_human_approval_v0(
            request,
            approval_id=f"approval:{mutation.mutation_id}",
            approved_by=approved_by,
            approval_reference=(
                f"{approval_reference}:{mutation.mutation_id}"
            ),
        )
        step_root = governance_root / _canonical_hash(
            {"mutation_id": mutation.mutation_id}
        )[:20]
        decision_dir = step_root / "decisions"
        context_dir = step_root / "contexts"
        override = dict((gate_overrides or {}).get(mutation.operation, {}))
        pre = pre_mod.run_world_action_pre_execution_v0(
            request=request,
            human_approval=approval,
            evidence_refs=list(plan.evidence_refs),
            unknowns=list(override.get("unknowns", ())),
            contradictions=list(override.get("contradictions", ())),
            risk_flags=list(override.get("risk_flags", ())),
            context_store_dir=context_dir,
            decision_store_dir=decision_dir,
        )
        if pre.x108_gate != "ALLOW":
            return {
                "status": "CSSA_NATIVE_INTAKE_GATED_NO_MUTATION",
                "reason": f"KX108_{pre.x108_gate}",
                "blocked_mutation_id": mutation.mutation_id,
                "blocked_operation": mutation.operation,
                "canonical_mutation_count": 0,
                "decision_authority": DECISION_AUTHORITY,
            }
        gated.append((mutation, request, pre, decision_dir, context_dir))

    # Semantic transaction preflight against an isolated native store.
    with tempfile.TemporaryDirectory(prefix="cssa-native-shadow-") as tmp:
        shadow = common.NativeEntityStoreV0(Path(tmp))
        for mutation, request, pre, decision_dir, context_dir in gated:
            _apply_one(
                store=shadow,
                mutation=mutation,
                request=request,
                decision_record_id=pre.decision_record_id,
                decision_store_dir=decision_dir,
                context_store_dir=context_dir,
            )

    receipts = []
    for mutation, request, pre, decision_dir, context_dir in gated:
        # Recheck all create targets are still absent before each canonical
        # apply. Any concurrent write fails closed.
        if store.state_hash(
            mutation.domain_id, mutation.entity_kind, mutation.entity_id
        ) != common.ABSENT_STATE_HASH:
            raise ValueError("CSSA_NATIVE_PRESTATE_CHANGED_BEFORE_COMMIT")
        receipt = _apply_one(
            store=store,
            mutation=mutation,
            request=request,
            decision_record_id=pre.decision_record_id,
            decision_store_dir=decision_dir,
            context_store_dir=context_dir,
        )
        receipts.append(receipt.to_dict())

    case_state = store.load_state(
        crm.DOMAIN_ID, crm.KIND_RECORD, plan.case_record_id
    )
    task_state = store.load_state(
        tasks.DOMAIN_ID, tasks.ENTITY_KIND, plan.task_id
    )
    followup_state = store.load_state(
        crm.DOMAIN_ID, crm.KIND_FOLLOWUP, plan.followup_id
    )
    timeline = crm.crm_timeline_v0(store, plan.case_record_id)

    return {
        "status": "CSSA_NATIVE_INTAKE_COMMITTED",
        "plan_id": plan.plan_id,
        "plan_hash": plan.plan_hash,
        "canonical_mutation_count": len(receipts),
        "receipt_ids": [item["receipt_id"] for item in receipts],
        "case_record_id": plan.case_record_id,
        "task_id": plan.task_id,
        "followup_id": plan.followup_id,
        "case_state_hash": common.canonical_hash(case_state),
        "task_state_hash": common.canonical_hash(task_state),
        "followup_state_hash": common.canonical_hash(followup_state),
        "timeline_event_count": len(timeline),
        "decision_authority": DECISION_AUTHORITY,
        "external_action": False,
        "external_saas_required": False,
    }
