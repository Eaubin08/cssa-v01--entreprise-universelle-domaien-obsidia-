"""F3G-G — CSSA contract and generic compliance lifecycle V0.

Business-state analysis only. This layer does not sign contracts, send filings,
change external systems or gain decision authority. It turns contract/compliance
cases into explicit evidence/unknown/contradiction structures for KX108_ONLY
governance.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Mapping

STATUS = "CSSA_CONTRACT_COMPLIANCE_READONLY_V0"

CONTRACT_STATES = {
    "DRAFT",
    "REVIEW",
    "APPROVED",
    "SIGNED",
    "ACTIVE",
    "EXPIRING",
    "EXPIRED",
    "TERMINATED",
}

ALLOWED_CONTRACT_TRANSITIONS = {
    "DRAFT": {"REVIEW"},
    "REVIEW": {"DRAFT", "APPROVED"},
    "APPROVED": {"REVIEW", "SIGNED"},
    "SIGNED": {"ACTIVE", "TERMINATED"},
    "ACTIVE": {"EXPIRING", "EXPIRED", "TERMINATED"},
    "EXPIRING": {"ACTIVE", "EXPIRED", "TERMINATED"},
    "EXPIRED": set(),
    "TERMINATED": set(),
}

COMPLIANCE_STATES = {
    "NOT_ASSESSED",
    "APPLICABILITY_REVIEW",
    "OPEN",
    "EVIDENCE_PENDING",
    "SATISFIED",
    "OVERDUE",
    "CONTESTED",
    "CLOSED",
}


@dataclass(frozen=True)
class ContractAssessmentV0:
    case_id: str
    assessed_at: str
    lifecycle_state: str
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
        return "contract_lifecycle_case"

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


@dataclass(frozen=True)
class ComplianceAssessmentV0:
    case_id: str
    assessed_at: str
    lifecycle_state: str
    unknowns: tuple[str, ...]
    contradictions: tuple[str, ...]
    risk_flags: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    responsible_role: str | None
    authority_ref: str | None
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
        return "compliance_lifecycle_case"

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


def validate_contract_transition_v0(current: str, target: str) -> None:
    if current not in CONTRACT_STATES:
        raise ValueError(f"UNKNOWN_CONTRACT_STATE:{current}")
    if target not in CONTRACT_STATES:
        raise ValueError(f"UNKNOWN_CONTRACT_STATE:{target}")
    if target not in ALLOWED_CONTRACT_TRANSITIONS[current]:
        raise ValueError(f"INVALID_CONTRACT_TRANSITION:{current}->{target}")


def _iso(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def assess_contract_v0(
    raw: Mapping[str, Any],
    *,
    as_of: date,
) -> ContractAssessmentV0:
    state = str(raw["lifecycle_state"])
    if state not in CONTRACT_STATES:
        raise ValueError(f"UNKNOWN_CONTRACT_STATE:{state}")

    unknowns = [str(v) for v in raw.get("forced_unknowns", ())]
    contradictions = [str(v) for v in raw.get("forced_contradictions", ())]
    risks = [str(v) for v in raw.get("risk_flags", ())]
    evidence = tuple(str(v) for v in raw.get("evidence_refs", ()))
    responsible_role = raw.get("responsible_role")

    if not responsible_role:
        unknowns.extend(("CONTRACT_OWNER_UNKNOWN", "CONTRACT_ESCALATION_ROUTE_UNKNOWN"))

    authority_ref = raw.get("signature_authority_ref")
    signature_ref = raw.get("signature_evidence_ref")

    if state in {"APPROVED", "SIGNED", "ACTIVE", "EXPIRING"} and not authority_ref:
        unknowns.extend((
            "SIGNATURE_AUTHORITY_UNKNOWN",
            "AUTHORITY_SCOPE_UNKNOWN",
        ))

    if state in {"SIGNED", "ACTIVE", "EXPIRING"} and not signature_ref:
        unknowns.extend((
            "SIGNATURE_EVIDENCE_MISSING",
            "SIGNATURE_VALIDITY_UNKNOWN",
        ))

    start = _iso(raw.get("effective_date"))
    end = _iso(raw.get("end_date"))

    if start and end and end < start:
        contradictions.extend((
            "CONTRACT_END_BEFORE_EFFECTIVE_DATE",
            "CONTRACT_DATE_RANGE_INVALID",
        ))

    operational_use_requested = bool(raw.get("operational_use_requested", False))
    if end and as_of > end and state in {"ACTIVE", "EXPIRING"}:
        contradictions.extend((
            "CONTRACT_EXPIRED_BY_DATE",
            "ACTIVE_STATE_CONFLICTS_WITH_END_DATE",
        ))

    if state == "EXPIRED" and operational_use_requested:
        contradictions.extend((
            "EXPIRED_CONTRACT_OPERATION_REQUESTED",
            "NO_VALID_ACTIVE_CONTRACT_FOR_OPERATION",
        ))

    if state == "TERMINATED" and operational_use_requested:
        contradictions.extend((
            "TERMINATED_CONTRACT_OPERATION_REQUESTED",
            "TERMINATED_CONTRACT_HAS_NO_EXECUTION_AUTHORITY",
        ))

    versions = tuple(str(v) for v in raw.get("active_version_refs", ()))
    if len(set(versions)) > 1:
        contradictions.extend((
            "MULTIPLE_ACTIVE_CONTRACT_VERSIONS",
            "CANONICAL_CONTRACT_VERSION_UNRESOLVED",
        ))

    renewal_notice_days = raw.get("renewal_notice_days")
    if end and renewal_notice_days is not None and state == "ACTIVE":
        days_left = (end - as_of).days
        if 0 <= days_left <= int(renewal_notice_days):
            risks.append("CONTRACT_RENEWAL_WINDOW_OPEN")

    return ContractAssessmentV0(
        case_id=str(raw["id"]),
        assessed_at=as_of.isoformat(),
        lifecycle_state=state,
        unknowns=tuple(dict.fromkeys(unknowns)),
        contradictions=tuple(dict.fromkeys(contradictions)),
        risk_flags=tuple(dict.fromkeys(risks)),
        evidence_refs=evidence,
        responsible_role=str(responsible_role) if responsible_role else None,
    )


def assess_compliance_v0(
    raw: Mapping[str, Any],
    *,
    as_of: date,
) -> ComplianceAssessmentV0:
    state = str(raw["lifecycle_state"])
    if state not in COMPLIANCE_STATES:
        raise ValueError(f"UNKNOWN_COMPLIANCE_STATE:{state}")

    unknowns = [str(v) for v in raw.get("forced_unknowns", ())]
    contradictions = [str(v) for v in raw.get("forced_contradictions", ())]
    risks = [str(v) for v in raw.get("risk_flags", ())]
    evidence = tuple(str(v) for v in raw.get("evidence_refs", ()))

    authority_ref = raw.get("authority_ref")
    responsible_role = raw.get("responsible_role")
    applicable = raw.get("applicable")
    evidence_verified = raw.get("evidence_verified")
    due = _iso(raw.get("due_date"))

    if applicable is None:
        unknowns.extend((
            "COMPLIANCE_APPLICABILITY_UNKNOWN",
            "APPLICABILITY_BASIS_UNKNOWN",
        ))

    if not authority_ref:
        unknowns.extend((
            "COMPLIANCE_AUTHORITY_UNKNOWN",
            "COMPLIANCE_SOURCE_OF_OBLIGATION_UNKNOWN",
        ))

    if not responsible_role and state not in {"NOT_ASSESSED", "CLOSED"}:
        unknowns.extend((
            "COMPLIANCE_OWNER_UNKNOWN",
            "COMPLIANCE_ESCALATION_ROUTE_UNKNOWN",
        ))

    if applicable is True and due and as_of > due and state not in {"SATISFIED", "CLOSED"}:
        contradictions.extend((
            "MANDATORY_COMPLIANCE_DEADLINE_MISSED",
            "OPEN_REQUIREMENT_AFTER_DEADLINE",
        ))

    if state in {"SATISFIED", "CLOSED"}:
        if not evidence:
            unknowns.extend((
                "COMPLIANCE_CLOSURE_EVIDENCE_MISSING",
                "COMPLIANCE_CLOSURE_NOT_AUDITABLE",
            ))
        elif evidence_verified is not True:
            unknowns.extend((
                "COMPLIANCE_EVIDENCE_NOT_VERIFIED",
                "COMPLIANCE_CLOSURE_VALIDITY_UNKNOWN",
            ))

    if state == "CONTESTED":
        contradictions.extend((
            "COMPLIANCE_REQUIREMENT_CONTESTED",
            "COMPLIANCE_RESOLUTION_NOT_FINAL",
        ))

    if state in {"OPEN", "EVIDENCE_PENDING"} and due:
        days_left = (due - as_of).days
        if 0 <= days_left <= 7:
            risks.append("COMPLIANCE_DEADLINE_WITHIN_7_DAYS")

    return ComplianceAssessmentV0(
        case_id=str(raw["id"]),
        assessed_at=as_of.isoformat(),
        lifecycle_state=state,
        unknowns=tuple(dict.fromkeys(unknowns)),
        contradictions=tuple(dict.fromkeys(contradictions)),
        risk_flags=tuple(dict.fromkeys(risks)),
        evidence_refs=evidence,
        responsible_role=str(responsible_role) if responsible_role else None,
        authority_ref=str(authority_ref) if authority_ref else None,
    )


def assess_contract_catalog_v0(
    catalog: Mapping[str, Any],
    *,
    as_of: date,
) -> tuple[ContractAssessmentV0, ...]:
    return tuple(assess_contract_v0(row, as_of=as_of) for row in catalog["contracts"])


def assess_compliance_catalog_v0(
    catalog: Mapping[str, Any],
    *,
    as_of: date,
) -> tuple[ComplianceAssessmentV0, ...]:
    return tuple(assess_compliance_v0(row, as_of=as_of) for row in catalog["compliance_cases"])


def lifecycle_summary_v0(
    contracts: tuple[ContractAssessmentV0, ...],
    compliance: tuple[ComplianceAssessmentV0, ...],
) -> dict[str, Any]:
    gates: dict[str, int] = {}
    for row in (*contracts, *compliance):
        gates[row.expected_gate] = gates.get(row.expected_gate, 0) + 1
    return {
        "status": STATUS,
        "contract_count": len(contracts),
        "compliance_count": len(compliance),
        "gate_counts": dict(sorted(gates.items())),
        "decision_authority": "KX108_ONLY",
        "external_action": False,
        "memory_write": False,
        "emits_act": False,
        "kernel_mutation": False,
    }
