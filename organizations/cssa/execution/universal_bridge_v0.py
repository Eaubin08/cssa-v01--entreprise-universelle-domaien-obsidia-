"""CSSA -> Universal Decision-Execution bridge V0.

This bridge preserves the already-proven CSSA F3H-A proposal semantics while
mapping them onto the new domain-agnostic universal execution contract.
"""
from __future__ import annotations

from organizations.cssa.execution.decision_execution_v0 import ActionProposalV0
from universal.execution import (
    EFFECT_COMMUNICATION,
    EFFECT_DATA_MUTATION,
    ExecutionSurfaceRegistrationV0,
    UniversalExecutionSurfaceRegistryV0,
    build_universal_action_proposal_v0,
)


def build_cssa_execution_surface_registry_v0() -> UniversalExecutionSurfaceRegistryV0:
    registry = UniversalExecutionSurfaceRegistryV0()
    registry.register(
        ExecutionSurfaceRegistrationV0(
            surface_id="MAIL",
            operation_ids=(
                "DRAFT_REPLY",
                "DRAFT_NOTIFICATION",
                "DRAFT_FOLLOWUP",
            ),
            effect_class=EFFECT_COMMUNICATION,
            connector_id="GMAIL",
            requires_human_approval=True,
        )
    )
    registry.register(
        ExecutionSurfaceRegistrationV0(
            surface_id="CALENDAR",
            operation_ids=(
                "PROPOSE_CREATE_EVENT",
                "PROPOSE_UPDATE_EVENT",
                "PROPOSE_CANCEL_EVENT",
            ),
            effect_class=EFFECT_DATA_MUTATION,
            connector_id="CALENDAR_CONNECTOR",
            requires_human_approval=True,
        )
    )
    registry.register(
        ExecutionSurfaceRegistrationV0(
            surface_id="CRM",
            operation_ids=(
                "PROPOSE_CREATE_RECORD",
                "PROPOSE_UPDATE_RECORD",
                "PROPOSE_LINK_RECORD",
            ),
            effect_class=EFFECT_DATA_MUTATION,
            connector_id="CRM_CONNECTOR",
            requires_human_approval=True,
        )
    )
    registry.register(
        ExecutionSurfaceRegistrationV0(
            surface_id="TASKS",
            operation_ids=(
                "PROPOSE_CREATE_TASK",
                "PROPOSE_UPDATE_TASK",
                "PROPOSE_CLOSE_TASK",
            ),
            effect_class=EFFECT_DATA_MUTATION,
            connector_id="TASK_CONNECTOR",
            requires_human_approval=True,
        )
    )
    return registry


def cssa_action_proposal_to_universal_v0(
    proposal: ActionProposalV0,
):
    proposal.assert_non_sovereign()
    registry = build_cssa_execution_surface_registry_v0()
    universal = build_universal_action_proposal_v0(
        registry=registry,
        proposal_id=proposal.proposal_id,
        domain_id="administration",
        surface_id=proposal.surface,
        operation_id=proposal.operation,
        target_ref=proposal.target_ref,
        payload=proposal.payload,
        source_case_refs=proposal.source_case_refs,
        evidence_refs=proposal.evidence_refs,
        expected_target_state_hash=proposal.expected_target_state_hash,
    )
    return registry, universal
