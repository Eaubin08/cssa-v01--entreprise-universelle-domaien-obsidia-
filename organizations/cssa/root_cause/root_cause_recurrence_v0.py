"""F3G-I — CSSA incident root-cause and recurrence-prevention lifecycle V0.

This layer structures incident investigation and closure proof. It does not
apply corrective actions, mutate external systems, or grant operational
authority. KX108 remains the only decision authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
import json
from typing import Any, Mapping

STATUS = "CSSA_ROOT_CAUSE_RECURRENCE_READONLY_V0"

LIFECYCLE_STATES = {
    "OPEN",
    "CONTAINED",
    "ROOT_CAUSE_ANALYSIS",
    "ROOT_CAUSE_CONFIRMED",
    "CORRECTIVE_ACTION_DEFINED",
    "CORRECTIVE_ACTION_APPLIED",
    "VERIFICATION_PENDING",
    "VERIFIED_EFFECTIVE",
    "RECURRENCE_MONITORING",
    "CLOSED",
}

VERIFICATION_STATES = {
    "NOT_RUN",
    "PENDING",
    "EFFECTIVE",
    "INEFFECTIVE",
}

FINAL_STATE = "CLOSED"


@dataclass(frozen=True)
class RootCauseAssessmentV0:
    case_id: str
    assessed_at: str
    lifecycle_state: str
    incident_family: str
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
        return "PROOF_AUDIT"

    @property
    def case_type(self) -> str:
        return "incident_root_cause_case"

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


def _dedupe(values: list[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def assess_root_cause_case_v0(
    raw: Mapping[str, Any],
    *,
    as_of: date,
) -> RootCauseAssessmentV0:
    state = str(raw["lifecycle_state"])
    if state not in LIFECYCLE_STATES:
        raise ValueError(f"UNKNOWN_RCA_LIFECYCLE_STATE:{state}")

    verification_state = str(raw.get("verification_state", "NOT_RUN"))
    if verification_state not in VERIFICATION_STATES:
        raise ValueError(f"UNKNOWN_RCA_VERIFICATION_STATE:{verification_state}")

    unknowns = [str(v) for v in raw.get("forced_unknowns", ())]
    contradictions = [str(v) for v in raw.get("forced_contradictions", ())]
    risks = [str(v) for v in raw.get("risk_flags", ())]
    evidence = [str(v) for v in raw.get("evidence_refs", ())]

    responsible_role = raw.get("responsible_role")
    if not responsible_role:
        unknowns.extend((
            "RCA_OWNER_UNKNOWN",
            "RCA_ESCALATION_ROUTE_UNKNOWN",
        ))

    root_cause_confirmed = bool(raw.get("root_cause_confirmed", False))
    root_cause_ref = raw.get("root_cause_ref")
    root_cause_evidence = tuple(
        str(v) for v in raw.get("root_cause_evidence_refs", ())
    )

    closure_requested = bool(raw.get("closure_requested", False))

    if closure_requested and not root_cause_confirmed:
        unknowns.extend((
            "ROOT_CAUSE_NOT_CONFIRMED",
            "CLOSURE_REQUESTED_BEFORE_ROOT_CAUSE_PROOF",
        ))

    if root_cause_confirmed:
        if not root_cause_ref:
            unknowns.extend((
                "CONFIRMED_ROOT_CAUSE_REF_MISSING",
                "ROOT_CAUSE_IDENTITY_NOT_AUDITABLE",
            ))
        if not root_cause_evidence:
            unknowns.extend((
                "ROOT_CAUSE_EVIDENCE_MISSING",
                "ROOT_CAUSE_CONFIRMATION_NOT_AUDITABLE",
            ))

    correction_applied = bool(raw.get("corrective_action_applied", False))
    correction_ref = raw.get("corrective_action_ref")
    correction_evidence = tuple(
        str(v) for v in raw.get("corrective_action_evidence_refs", ())
    )

    if correction_applied:
        if not correction_ref:
            unknowns.extend((
                "CORRECTIVE_ACTION_REF_MISSING",
                "CORRECTIVE_ACTION_IDENTITY_UNKNOWN",
            ))
        if not correction_evidence:
            unknowns.extend((
                "CORRECTIVE_ACTION_EVIDENCE_MISSING",
                "CORRECTIVE_ACTION_APPLICATION_NOT_AUDITABLE",
            ))

    if state in {
        "CORRECTIVE_ACTION_APPLIED",
        "VERIFICATION_PENDING",
        "VERIFIED_EFFECTIVE",
        "RECURRENCE_MONITORING",
        "CLOSED",
    } and not correction_applied:
        unknowns.extend((
            "CORRECTIVE_ACTION_NOT_PROVEN_APPLIED",
            "POST_CORRECTION_STATE_WITHOUT_APPLICATION_PROOF",
        ))

    verification_evidence = tuple(
        str(v) for v in raw.get("verification_evidence_refs", ())
    )

    if verification_state == "EFFECTIVE" and not verification_evidence:
        unknowns.extend((
            "EFFECTIVENESS_VERIFICATION_EVIDENCE_MISSING",
            "EFFECTIVENESS_CLAIM_NOT_AUDITABLE",
        ))

    if verification_state == "INEFFECTIVE" and closure_requested:
        contradictions.extend((
            "CORRECTIVE_ACTION_VERIFIED_INEFFECTIVE",
            "CLOSURE_REQUEST_CONFLICTS_WITH_FAILED_VERIFICATION",
        ))

    recurrence_observed = bool(raw.get("recurrence_observed", False))
    if recurrence_observed and verification_state == "EFFECTIVE":
        contradictions.extend((
            "RECURRENCE_OBSERVED_AFTER_EFFECTIVE_VERIFICATION",
            "EFFECTIVENESS_CLAIM_INVALIDATED_BY_RECURRENCE",
        ))

    prior_signature_ref = raw.get("same_failure_signature_as")
    linked_to_prior = raw.get("linked_to_prior_incident")
    if prior_signature_ref and linked_to_prior is not True:
        unknowns.extend((
            "RECURRENT_SIGNATURE_NOT_LINKED_TO_PRIOR_INCIDENT",
            "RECURRENCE_HISTORY_INCOMPLETE",
        ))

    prevention_controls = tuple(
        str(v) for v in raw.get("prevention_control_refs", ())
    )
    monitoring_evidence = tuple(
        str(v) for v in raw.get("monitoring_evidence_refs", ())
    )
    closure_authority_ref = raw.get("closure_authority_ref")

    if state == "CLOSED":
        if verification_state != "EFFECTIVE":
            unknowns.extend((
                "CLOSED_WITHOUT_EFFECTIVE_VERIFICATION",
                "CLOSURE_EFFECTIVENESS_UNKNOWN",
            ))
        if not prevention_controls:
            unknowns.extend((
                "RECURRENCE_PREVENTION_CONTROL_MISSING",
                "DURABLE_CLOSURE_NOT_PROVEN",
            ))
        if not monitoring_evidence:
            unknowns.extend((
                "RECURRENCE_MONITORING_EVIDENCE_MISSING",
                "NON_RECURRENCE_NOT_AUDITABLE",
            ))
        if not closure_authority_ref:
            unknowns.extend((
                "RCA_CLOSURE_AUTHORITY_UNKNOWN",
                "RCA_CLOSURE_SCOPE_UNKNOWN",
            ))
        if recurrence_observed:
            contradictions.extend((
                "CLOSED_INCIDENT_HAS_OBSERVED_RECURRENCE",
                "DURABLE_CLOSURE_INVALIDATED",
            ))

    due = raw.get("root_cause_due_date")
    if due:
        due_date = date.fromisoformat(str(due))
        days_left = (due_date - as_of).days
        if 0 <= days_left <= 7 and state not in {"ROOT_CAUSE_CONFIRMED", "CLOSED"}:
            risks.append("ROOT_CAUSE_DEADLINE_WITHIN_7_DAYS")
        if bool(raw.get("hard_root_cause_deadline", False)) and days_left < 0:
            if state not in {"ROOT_CAUSE_CONFIRMED", "CLOSED"}:
                contradictions.extend((
                    "HARD_ROOT_CAUSE_DEADLINE_MISSED",
                    "ROOT_CAUSE_STILL_UNRESOLVED_AFTER_DEADLINE",
                ))

    all_evidence = list(evidence)
    all_evidence.extend(root_cause_evidence)
    all_evidence.extend(correction_evidence)
    all_evidence.extend(verification_evidence)
    all_evidence.extend(monitoring_evidence)

    return RootCauseAssessmentV0(
        case_id=str(raw["id"]),
        assessed_at=as_of.isoformat(),
        lifecycle_state=state,
        incident_family=str(raw["incident_family"]),
        unknowns=_dedupe(unknowns),
        contradictions=_dedupe(contradictions),
        risk_flags=_dedupe(risks),
        evidence_refs=_dedupe(all_evidence),
        responsible_role=str(responsible_role) if responsible_role else None,
    )


def build_recurrence_prevention_receipt_v0(
    raw: Mapping[str, Any],
    assessment: RootCauseAssessmentV0,
) -> dict[str, Any]:
    """Build a deterministic closure receipt only for fully auditable closure."""

    if assessment.lifecycle_state != FINAL_STATE:
        raise ValueError("RCA_RECEIPT_REQUIRES_CLOSED_STATE")
    if assessment.expected_gate != "ALLOW":
        raise ValueError(
            f"RCA_RECEIPT_REQUIRES_ALLOW_GATE:{assessment.expected_gate}"
        )
    if not bool(raw.get("root_cause_confirmed", False)):
        raise ValueError("RCA_RECEIPT_REQUIRES_CONFIRMED_ROOT_CAUSE")
    if not bool(raw.get("corrective_action_applied", False)):
        raise ValueError("RCA_RECEIPT_REQUIRES_APPLIED_CORRECTIVE_ACTION")
    if str(raw.get("verification_state", "")) != "EFFECTIVE":
        raise ValueError("RCA_RECEIPT_REQUIRES_EFFECTIVE_VERIFICATION")
    if bool(raw.get("recurrence_observed", False)):
        raise ValueError("RCA_RECEIPT_FORBIDS_OBSERVED_RECURRENCE")

    payload = {
        "version": "CSSA_RECURRENCE_PREVENTION_RECEIPT_V0",
        "incident_id": assessment.case_id,
        "root_cause_ref": str(raw["root_cause_ref"]),
        "root_cause_evidence_refs": sorted(
            str(v) for v in raw["root_cause_evidence_refs"]
        ),
        "corrective_action_ref": str(raw["corrective_action_ref"]),
        "corrective_action_evidence_refs": sorted(
            str(v) for v in raw["corrective_action_evidence_refs"]
        ),
        "verification_evidence_refs": sorted(
            str(v) for v in raw["verification_evidence_refs"]
        ),
        "prevention_control_refs": sorted(
            str(v) for v in raw["prevention_control_refs"]
        ),
        "monitoring_evidence_refs": sorted(
            str(v) for v in raw["monitoring_evidence_refs"]
        ),
        "closure_authority_ref": str(raw["closure_authority_ref"]),
        "decision_authority": "KX108_ONLY",
        "external_action": False,
        "memory_write": False,
        "emits_act": False,
        "kernel_mutation": False,
    }
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    payload["receipt_sha256"] = hashlib.sha256(canonical).hexdigest()
    return payload


def assess_root_cause_catalog_v0(
    catalog: Mapping[str, Any],
    *,
    as_of: date,
) -> tuple[RootCauseAssessmentV0, ...]:
    return tuple(
        assess_root_cause_case_v0(row, as_of=as_of)
        for row in catalog["cases"]
    )


def root_cause_summary_v0(
    assessments: tuple[RootCauseAssessmentV0, ...],
) -> dict[str, Any]:
    gates: dict[str, int] = {}
    for row in assessments:
        gates[row.expected_gate] = gates.get(row.expected_gate, 0) + 1
    return {
        "status": STATUS,
        "case_count": len(assessments),
        "gate_counts": dict(sorted(gates.items())),
        "decision_authority": "KX108_ONLY",
        "external_action": False,
        "memory_write": False,
        "emits_act": False,
        "kernel_mutation": False,
    }
