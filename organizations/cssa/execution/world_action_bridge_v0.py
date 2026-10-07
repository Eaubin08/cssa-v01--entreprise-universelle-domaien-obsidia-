"""CSSA MAIL -> Universal World Action bridge V0.

Sedan remains a métier implementation. The execution rail is universal.
"""
from __future__ import annotations

from organizations.cssa.execution.decision_execution_v0 import ActionProposalV0
from organizations.cssa.execution.mail_governed_execution_v0 import (
    MailSendPlanV0,
    verify_mail_send_plan_v0,
)
from organizations.cssa.execution.universal_bridge_v0 import (
    cssa_action_proposal_to_universal_v0,
)
from universal.execution import (
    ARC_IRREVERSIBLE,
    RETRY_NEVER_ON_UNKNOWN,
    WCC_IRREVERSIBLE,
    WorldActionOperationPolicyV0,
    WorldActionPolicyRegistryV0,
    build_world_action_request_v0,
)


def build_cssa_mail_world_action_request_v0(
    *,
    proposal: ActionProposalV0,
    plan: MailSendPlanV0,
    request_id: str,
    current_target_state_hash: str,
):
    ok, reason = verify_mail_send_plan_v0(plan, proposal)
    if not ok:
        raise ValueError(f"INVALID_CSSA_MAIL_PLAN:{reason}")

    surface_registry, universal_proposal = (
        cssa_action_proposal_to_universal_v0(proposal)
    )
    policies = WorldActionPolicyRegistryV0(
        surface_registry=surface_registry,
    )
    policies.register(
        WorldActionOperationPolicyV0(
            surface_id="MAIL",
            operation_id=universal_proposal.operation_id,
            connector_id="GMAIL",
            connector_action="SEND_EMAIL",
            required_scope="gmail:send",
            world_call_class=WCC_IRREVERSIBLE,
            action_risk_class=ARC_IRREVERSIBLE,
            autonomy_level=5,
            retry_policy=RETRY_NEVER_ON_UNKNOWN,
            irreversible=True,
            requires_human_approval=True,
        )
    )
    request = build_world_action_request_v0(
        surface_registry=surface_registry,
        policy_registry=policies,
        proposal=universal_proposal,
        request_id=request_id,
        connector_action="SEND_EMAIL",
        connector_args={
            "to": ",".join(plan.to),
            "subject": plan.subject,
            "body": plan.body,
            "content_type": "text/plain",
            "reply_message_id": plan.reply_message_id,
        },
        current_target_state_hash=current_target_state_hash,
    )
    return surface_registry, policies, universal_proposal, request
