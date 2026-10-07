"""F3G-J — CSSA matchday buvette/restauration operating workflow V0.

Readonly operational assessment for stock, suppliers, shifts, readiness and
cash reconciliation. This layer does not place orders, assign people, open a
till, move money or mutate external systems.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
import json
from typing import Any, Mapping

STATUS = "CSSA_MATCHDAY_BUVETTE_RESTAURATION_READONLY_V0"

CASE_TYPES = {
    "STOCK",
    "SUPPLIER",
    "SHIFT",
    "READINESS",
    "CASH_RECONCILIATION",
}

REPORTING_FAMILIES = {
    "MATCHDAY",
    "FINANCE_ACCOUNTING",
    "PEOPLE_HR_VOLUNTEERS",
}

FINAL_CASE_STATES = {
    "CLOSED",
    "RECONCILED",
}


@dataclass(frozen=True)
class BuvetteAssessmentV0:
    case_id: str
    assessed_at: str
    case_type_name: str
    reporting_family: str
    lifecycle_state: str
    match_ref: str | None
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
        return self.reporting_family

    @property
    def case_type(self) -> str:
        return "matchday_buvette_restauration_case"

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


def _num(raw: Mapping[str, Any], key: str) -> float | None:
    value = raw.get(key)
    if value is None:
        return None
    return float(value)


def assess_buvette_case_v0(
    raw: Mapping[str, Any],
    *,
    as_of: date,
) -> BuvetteAssessmentV0:
    case_type = str(raw["case_type"])
    reporting_family = str(raw["reporting_family"])
    if case_type not in CASE_TYPES:
        raise ValueError(f"UNKNOWN_BUVETTE_CASE_TYPE:{case_type}")
    if reporting_family not in REPORTING_FAMILIES:
        raise ValueError(
            f"UNKNOWN_BUVETTE_REPORTING_FAMILY:{reporting_family}"
        )

    unknowns = [str(v) for v in raw.get("forced_unknowns", ())]
    contradictions = [str(v) for v in raw.get("forced_contradictions", ())]
    risks = [str(v) for v in raw.get("risk_flags", ())]
    evidence = [str(v) for v in raw.get("evidence_refs", ())]

    match_ref = raw.get("match_ref")
    if not match_ref:
        unknowns.extend((
            "MATCHDAY_REFERENCE_UNKNOWN",
            "BUVETTE_CASE_NOT_LINKED_TO_MATCH",
        ))

    responsible_role = raw.get("responsible_role")
    if not responsible_role:
        unknowns.extend((
            "BUVETTE_CASE_OWNER_UNKNOWN",
            "BUVETTE_ESCALATION_ROUTE_UNKNOWN",
        ))

    lifecycle_state = str(raw.get("lifecycle_state", "OPEN"))
    opening_requested = bool(raw.get("opening_requested", False))

    venue_buvette_status = raw.get("venue_buvette_status")
    if opening_requested and venue_buvette_status == "CLOSED":
        contradictions.extend((
            "BUVETTE_OPENING_CONFLICTS_WITH_VENUE_CONFIGURATION",
            "MATCHDAY_SERVICE_PLAN_INCONSISTENT",
        ))
    elif opening_requested and venue_buvette_status is None:
        unknowns.extend((
            "VENUE_BUVETTE_STATUS_UNKNOWN",
            "MATCHDAY_SERVICE_CONFIGURATION_UNKNOWN",
        ))

    if case_type == "STOCK":
        required = _num(raw, "required_stock_units")
        available = _num(raw, "available_stock_units")
        if required is None:
            unknowns.extend((
                "REQUIRED_STOCK_UNKNOWN",
                "STOCK_REQUIREMENT_BASIS_UNKNOWN",
            ))
        if available is None:
            unknowns.extend((
                "AVAILABLE_STOCK_UNKNOWN",
                "STOCK_COUNT_NOT_AUDITABLE",
            ))
        if required is not None and available is not None:
            if available < required and opening_requested:
                contradictions.extend((
                    "STOCK_BELOW_MATCHDAY_REQUIREMENT",
                    "OPENING_REQUESTED_WITH_INSUFFICIENT_STOCK",
                ))
            elif required > 0:
                ratio = available / required
                if ratio < 1.15:
                    risks.append("STOCK_BUFFER_BELOW_15_PERCENT")

        if bool(raw.get("perishable_stock", False)):
            expiry_checked = raw.get("expiry_checked")
            if expiry_checked is not True:
                unknowns.extend((
                    "PERISHABLE_EXPIRY_CHECK_MISSING",
                    "PERISHABLE_STOCK_SUITABILITY_UNKNOWN",
                ))

    if case_type == "SUPPLIER":
        order_required = bool(raw.get("supplier_order_required", False))
        order_ref = raw.get("supplier_order_ref")
        delivery_status = raw.get("delivery_status")

        if order_required and not order_ref:
            unknowns.extend((
                "SUPPLIER_ORDER_REF_MISSING",
                "SUPPLIER_COMMITMENT_NOT_AUDITABLE",
            ))

        if order_required and delivery_status in {"CANCELLED", "REFUSED"}:
            contradictions.extend((
                "REQUIRED_SUPPLIER_DELIVERY_UNAVAILABLE",
                "MATCHDAY_RESTAURATION_SUPPLY_BROKEN",
            ))
        elif order_required and delivery_status in {None, "UNKNOWN"}:
            unknowns.extend((
                "SUPPLIER_DELIVERY_STATUS_UNKNOWN",
                "MATCHDAY_SUPPLY_READINESS_UNKNOWN",
            ))

        if bool(raw.get("supplier_compliance_required", False)):
            compliance_refs = tuple(
                str(v) for v in raw.get("supplier_compliance_evidence_refs", ())
            )
            if not compliance_refs:
                unknowns.extend((
                    "SUPPLIER_COMPLIANCE_EVIDENCE_MISSING",
                    "SUPPLIER_READINESS_NOT_AUDITABLE",
                ))
            else:
                evidence.extend(compliance_refs)

    if case_type == "SHIFT":
        required_slots = raw.get("required_shift_slots")
        assigned_slots = raw.get("assigned_shift_slots")
        if required_slots is None or assigned_slots is None:
            unknowns.extend((
                "SHIFT_CAPACITY_UNKNOWN",
                "SHIFT_COVERAGE_NOT_AUDITABLE",
            ))
        else:
            required_i = int(required_slots)
            assigned_i = int(assigned_slots)
            if assigned_i < required_i and opening_requested:
                contradictions.extend((
                    "SHIFT_UNDERSTAFFED_FOR_OPENING",
                    "MATCHDAY_BUVETTE_COVERAGE_INSUFFICIENT",
                ))

        if raw.get("assignment_authority_known") is not True:
            unknowns.extend((
                "SHIFT_ASSIGNMENT_AUTHORITY_UNKNOWN",
                "VOLUNTEER_ASSIGNMENT_SCOPE_UNKNOWN",
            ))

        overlap_refs = tuple(
            str(v) for v in raw.get("overlapping_assignment_refs", ())
        )
        if overlap_refs:
            contradictions.extend((
                "VOLUNTEER_DOUBLE_ASSIGNED",
                "SHIFT_ASSIGNMENT_COLLISION_UNRESOLVED",
            ))
            evidence.extend(overlap_refs)

    if case_type == "READINESS":
        required_checks = {
            str(v) for v in raw.get("required_check_ids", ())
        }
        passed_checks = {
            str(v) for v in raw.get("passed_check_ids", ())
        }
        unknown_checks = sorted(required_checks - passed_checks)
        if unknown_checks:
            unknowns.extend((
                "MATCHDAY_READINESS_CHECKS_INCOMPLETE",
                "BUVETTE_OPENING_READINESS_NOT_PROVEN",
            ))
        if lifecycle_state == "READY" and unknown_checks:
            contradictions.extend((
                "READY_STATE_WITH_INCOMPLETE_CHECKS",
                "READINESS_STATE_CONFLICTS_WITH_EVIDENCE",
            ))

    if case_type == "CASH_RECONCILIATION":
        expected_cash = _num(raw, "expected_cash_eur")
        counted_cash = _num(raw, "counted_cash_eur")
        tolerance = _num(raw, "variance_tolerance_eur")

        if expected_cash is None:
            unknowns.extend((
                "EXPECTED_CASH_UNKNOWN",
                "CASH_EXPECTATION_BASIS_UNKNOWN",
            ))
        if counted_cash is None:
            unknowns.extend((
                "COUNTED_CASH_UNKNOWN",
                "CASH_COUNT_NOT_AUDITABLE",
            ))
        if tolerance is None:
            unknowns.extend((
                "CASH_VARIANCE_TOLERANCE_UNKNOWN",
                "RECONCILIATION_POLICY_UNKNOWN",
            ))

        if (
            expected_cash is not None
            and counted_cash is not None
            and tolerance is not None
        ):
            variance = abs(expected_cash - counted_cash)
            if variance > tolerance:
                contradictions.extend((
                    "CASH_VARIANCE_OVER_TOLERANCE",
                    "MATCHDAY_CASH_RECONCILIATION_UNRESOLVED",
                ))
            elif variance > 0:
                risks.append("CASH_VARIANCE_WITHIN_TOLERANCE")

        if lifecycle_state in FINAL_CASE_STATES:
            reconciliation_refs = tuple(
                str(v) for v in raw.get("reconciliation_evidence_refs", ())
            )
            if not reconciliation_refs:
                unknowns.extend((
                    "RECONCILIATION_EVIDENCE_MISSING",
                    "MATCHDAY_CASH_CLOSURE_NOT_AUDITABLE",
                ))
            else:
                evidence.extend(reconciliation_refs)

    due = raw.get("due_date")
    if due:
        due_date = date.fromisoformat(str(due))
        days_left = (due_date - as_of).days
        if 0 <= days_left <= 2 and lifecycle_state not in FINAL_CASE_STATES:
            risks.append("MATCHDAY_OPERATION_DEADLINE_WITHIN_48H")
        if bool(raw.get("hard_deadline", False)) and days_left < 0:
            if lifecycle_state not in FINAL_CASE_STATES:
                contradictions.extend((
                    "HARD_MATCHDAY_OPERATION_DEADLINE_MISSED",
                    "MATCHDAY_CASE_UNRESOLVED_AFTER_DEADLINE",
                ))

    return BuvetteAssessmentV0(
        case_id=str(raw["id"]),
        assessed_at=as_of.isoformat(),
        case_type_name=case_type,
        reporting_family=reporting_family,
        lifecycle_state=lifecycle_state,
        match_ref=str(match_ref) if match_ref else None,
        unknowns=_dedupe(unknowns),
        contradictions=_dedupe(contradictions),
        risk_flags=_dedupe(risks),
        evidence_refs=_dedupe(evidence),
        responsible_role=str(responsible_role) if responsible_role else None,
    )


def build_matchday_reconciliation_receipt_v0(
    raw: Mapping[str, Any],
    assessment: BuvetteAssessmentV0,
) -> dict[str, Any]:
    if assessment.case_type_name != "CASH_RECONCILIATION":
        raise ValueError("MATCHDAY_RECEIPT_REQUIRES_CASH_RECONCILIATION_CASE")
    if assessment.lifecycle_state not in FINAL_CASE_STATES:
        raise ValueError("MATCHDAY_RECEIPT_REQUIRES_FINAL_STATE")
    if assessment.expected_gate != "ALLOW":
        raise ValueError(
            f"MATCHDAY_RECEIPT_REQUIRES_ALLOW_GATE:{assessment.expected_gate}"
        )

    reconciliation_refs = sorted(
        str(v) for v in raw.get("reconciliation_evidence_refs", ())
    )
    if not reconciliation_refs:
        raise ValueError("MATCHDAY_RECEIPT_REQUIRES_RECONCILIATION_EVIDENCE")

    payload = {
        "version": "CSSA_MATCHDAY_CASH_RECONCILIATION_RECEIPT_V0",
        "case_id": assessment.case_id,
        "match_ref": assessment.match_ref,
        "expected_cash_eur": float(raw["expected_cash_eur"]),
        "counted_cash_eur": float(raw["counted_cash_eur"]),
        "variance_tolerance_eur": float(raw["variance_tolerance_eur"]),
        "reconciliation_evidence_refs": reconciliation_refs,
        "responsible_role": assessment.responsible_role,
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


def assess_buvette_catalog_v0(
    catalog: Mapping[str, Any],
    *,
    as_of: date,
) -> tuple[BuvetteAssessmentV0, ...]:
    return tuple(
        assess_buvette_case_v0(row, as_of=as_of)
        for row in catalog["cases"]
    )


def buvette_summary_v0(
    assessments: tuple[BuvetteAssessmentV0, ...],
) -> dict[str, Any]:
    gates: dict[str, int] = {}
    case_types: dict[str, int] = {}
    for row in assessments:
        gates[row.expected_gate] = gates.get(row.expected_gate, 0) + 1
        case_types[row.case_type_name] = case_types.get(row.case_type_name, 0) + 1
    return {
        "status": STATUS,
        "case_count": len(assessments),
        "gate_counts": dict(sorted(gates.items())),
        "case_type_counts": dict(sorted(case_types.items())),
        "decision_authority": "KX108_ONLY",
        "external_action": False,
        "memory_write": False,
        "emits_act": False,
        "kernel_mutation": False,
    }
