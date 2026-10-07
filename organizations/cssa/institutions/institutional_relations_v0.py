"""F3G-H — CSSA institutional relations workflow V0.

Readonly case-state model for relationships with football authorities and public
institutions. It does not send correspondence, bind the club, assume an
institution's authority, or treat acknowledgement as approval.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Mapping

STATUS = "CSSA_INSTITUTIONAL_RELATIONS_READONLY_V0"

INSTITUTIONS = {
    "FFF",
    "LGEF",
    "DISTRICT",
    "VILLE_DE_SEDAN",
    "ARDENNE_METROPOLE",
    "OTHER_COLLECTIVITY",
}

LIFECYCLE_STATES = {
    "DRAFT",
    "READY_TO_SEND",
    "SENT",
    "ACKNOWLEDGED",
    "UNDER_REVIEW",
    "APPROVED",
    "REFUSED",
    "CLOSED",
    "CONTESTED",
}

FINAL_STATES = {"APPROVED", "REFUSED", "CLOSED"}


@dataclass(frozen=True)
class InstitutionalAssessmentV0:
    case_id: str
    assessed_at: str
    institution: str
    lifecycle_state: str
    subject_family: str
    unknowns: tuple[str, ...]
    contradictions: tuple[str, ...]
    risk_flags: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    responsible_role: str | None
    status: str = STATUS
    decision_authority: str = "KX108_ONLY"
    external_action: bool = False

    @property
    def event_id(self) -> str:
        return self.case_id

    @property
    def event_date(self) -> str:
        return self.assessed_at

    @property
    def family(self) -> str:
        return "GOVERNANCE_LEGAL"

    @property
    def case_type(self) -> str:
        return "institutional_relation_case"

    @property
    def team_id(self) -> None:
        return None

    @property
    def expected_gate(self) -> str:
        if len(self.contradictions) >= 2:
            return "BLOCK"
        if len(self.unknowns) > 1:
            return "HOLD"
        return "ALLOW"


def assess_institutional_case_v0(
    raw: Mapping[str, Any],
    *,
    as_of: date,
) -> InstitutionalAssessmentV0:
    institution = str(raw["institution"])
    state = str(raw["lifecycle_state"])

    if institution not in INSTITUTIONS:
        raise ValueError(f"UNKNOWN_INSTITUTION:{institution}")
    if state not in LIFECYCLE_STATES:
        raise ValueError(f"UNKNOWN_INSTITUTIONAL_STATE:{state}")

    unknowns = [str(v) for v in raw.get("forced_unknowns", ())]
    contradictions = [str(v) for v in raw.get("forced_contradictions", ())]
    risks = [str(v) for v in raw.get("risk_flags", ())]
    evidence = tuple(str(v) for v in raw.get("evidence_refs", ()))

    responsible_role = raw.get("responsible_role")
    if not responsible_role:
        unknowns.extend((
            "INSTITUTIONAL_CASE_OWNER_UNKNOWN",
            "INSTITUTIONAL_ESCALATION_ROUTE_UNKNOWN",
        ))

    authority_scope_known = raw.get("authority_scope_known")
    if authority_scope_known is None:
        unknowns.extend((
            "INSTITUTION_AUTHORITY_SCOPE_UNKNOWN",
            "INSTITUTIONAL_BINDING_SCOPE_UNKNOWN",
        ))
    elif authority_scope_known is False:
        contradictions.extend((
            "INSTITUTION_NOT_AUTHORIZED_FOR_REQUEST",
            "INSTITUTIONAL_CASE_MISROUTED",
        ))

    required_channel = raw.get("required_channel")
    sent_channel = raw.get("sent_channel")
    if required_channel and state not in {"DRAFT", "READY_TO_SEND"}:
        if not sent_channel:
            unknowns.extend((
                "INSTITUTIONAL_SENT_CHANNEL_UNKNOWN",
                "CHANNEL_COMPLIANCE_UNKNOWN",
            ))
        elif sent_channel != required_channel:
            contradictions.extend((
                "INSTITUTIONAL_CHANNEL_MISMATCH",
                "INSTITUTIONAL_SUBMISSION_NOT_ON_REQUIRED_CHANNEL",
            ))

    approval_required = bool(raw.get("approval_required_before_action", False))
    downstream_action_requested = bool(raw.get("downstream_action_requested", False))
    approval_evidence_ref = raw.get("approval_evidence_ref")

    if approval_required and state == "APPROVED" and not approval_evidence_ref:
        unknowns.extend((
            "INSTITUTIONAL_APPROVAL_EVIDENCE_MISSING",
            "INSTITUTIONAL_APPROVAL_NOT_AUDITABLE",
        ))

    if approval_required and downstream_action_requested:
        if state in {"ACKNOWLEDGED", "SENT", "UNDER_REVIEW", "READY_TO_SEND", "DRAFT"}:
            unknowns.extend((
                "INSTITUTIONAL_APPROVAL_NOT_RECEIVED",
                "NON_FINAL_INSTITUTIONAL_STATE_CANNOT_AUTHORIZE_ACTION",
            ))
        elif state == "REFUSED":
            contradictions.extend((
                "INSTITUTIONAL_REQUEST_REFUSED",
                "DOWNSTREAM_ACTION_CONFLICTS_WITH_REFUSAL",
            ))

    instruction_refs = tuple(str(v) for v in raw.get("instruction_refs", ()))
    instruction_values = tuple(str(v) for v in raw.get("instruction_values", ()))
    if len(instruction_refs) > 1 and len(set(instruction_values)) > 1:
        contradictions.extend((
            "CONFLICTING_INSTITUTIONAL_INSTRUCTIONS",
            "CANONICAL_INSTITUTIONAL_INSTRUCTION_UNRESOLVED",
        ))

    due = raw.get("due_date")
    if due:
        due_date = date.fromisoformat(str(due))
        days_left = (due_date - as_of).days
        if 0 <= days_left <= 7 and state not in FINAL_STATES:
            risks.append("INSTITUTIONAL_DEADLINE_WITHIN_7_DAYS")
        if bool(raw.get("hard_deadline", False)) and days_left < 0 and state not in FINAL_STATES:
            contradictions.extend((
                "HARD_INSTITUTIONAL_DEADLINE_MISSED",
                "INSTITUTIONAL_CASE_UNRESOLVED_AFTER_DEADLINE",
            ))

    if state == "CONTESTED":
        contradictions.extend((
            "INSTITUTIONAL_OUTCOME_CONTESTED",
            "INSTITUTIONAL_RESOLUTION_NOT_FINAL",
        ))

    if state in {"APPROVED", "REFUSED", "CLOSED"} and not evidence:
        unknowns.extend((
            "FINAL_INSTITUTIONAL_STATE_EVIDENCE_MISSING",
            "FINAL_INSTITUTIONAL_STATE_NOT_AUDITABLE",
        ))

    return InstitutionalAssessmentV0(
        case_id=str(raw["id"]),
        assessed_at=as_of.isoformat(),
        institution=institution,
        lifecycle_state=state,
        subject_family=str(raw["subject_family"]),
        unknowns=tuple(dict.fromkeys(unknowns)),
        contradictions=tuple(dict.fromkeys(contradictions)),
        risk_flags=tuple(dict.fromkeys(risks)),
        evidence_refs=evidence,
        responsible_role=str(responsible_role) if responsible_role else None,
    )


def assess_institutional_catalog_v0(
    catalog: Mapping[str, Any],
    *,
    as_of: date,
) -> tuple[InstitutionalAssessmentV0, ...]:
    return tuple(
        assess_institutional_case_v0(row, as_of=as_of)
        for row in catalog["cases"]
    )


def institutional_summary_v0(
    assessments: tuple[InstitutionalAssessmentV0, ...],
) -> dict[str, Any]:
    gates: dict[str, int] = {}
    institutions: dict[str, int] = {}
    for row in assessments:
        gates[row.expected_gate] = gates.get(row.expected_gate, 0) + 1
        institutions[row.institution] = institutions.get(row.institution, 0) + 1
    return {
        "status": STATUS,
        "case_count": len(assessments),
        "gate_counts": dict(sorted(gates.items())),
        "institution_counts": dict(sorted(institutions.items())),
        "decision_authority": "KX108_ONLY",
        "external_action": False,
        "memory_write": False,
        "emits_act": False,
        "kernel_mutation": False,
    }
