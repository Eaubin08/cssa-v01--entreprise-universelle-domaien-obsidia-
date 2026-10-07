import json
from datetime import date
from pathlib import Path

import pytest

from organizations.cssa.reporting import build_report_pack_v0
from organizations.cssa.root_cause import (
    assess_root_cause_case_v0,
    assess_root_cause_catalog_v0,
    build_recurrence_prevention_receipt_v0,
    root_cause_summary_v0,
)


ROOT = Path(__file__).resolve().parents[1]
CASES = (
    ROOT / "organizations" / "cssa" / "root_cause"
    / "root_cause_cases_v0.json"
)
OVERLAY = (
    ROOT / "organizations" / "cssa" / "root_cause"
    / "f3g_i_coverage_closure_overlay_v0.json"
)
ROUTING = ROOT / "organizations" / "cssa" / "reporting" / "routing_v0.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def assessed():
    return assess_root_cause_catalog_v0(
        load(CASES),
        as_of=date(2026, 10, 7),
    )


def case_raw(case_id):
    return next(
        row for row in load(CASES)["cases"]
        if row["id"] == case_id
    )


def test_catalog_is_simulated_not_observed():
    catalog = load(CASES)

    assert catalog["status"] == "SIMULATED_NOT_OBSERVED"
    assert len(catalog["cases"]) == 11


def test_gate_distribution_is_fail_closed_without_overblocking_triage():
    summary = root_cause_summary_v0(assessed())

    assert summary["case_count"] == 11
    assert summary["gate_counts"] == {
        "ALLOW": 2,
        "BLOCK": 3,
        "HOLD": 6,
    }
    assert summary["decision_authority"] == "KX108_ONLY"
    assert summary["external_action"] is False
    assert summary["memory_write"] is False
    assert summary["emits_act"] is False
    assert summary["kernel_mutation"] is False


def test_open_triage_can_remain_allow_with_visible_deadline_risk():
    row = next(r for r in assessed() if r.case_id == "RCA_OPEN_TRIAGE")

    assert row.expected_gate == "ALLOW"
    assert "ROOT_CAUSE_DEADLINE_WITHIN_7_DAYS" in row.risk_flags


def test_hypothesis_cannot_be_promoted_to_root_cause_for_closure():
    row = next(
        r for r in assessed()
        if r.case_id == "RCA_HYPOTHESIS_ONLY_CLOSURE_REQUESTED"
    )

    assert {
        "ROOT_CAUSE_NOT_CONFIRMED",
        "CLOSURE_REQUESTED_BEFORE_ROOT_CAUSE_PROOF",
    } <= set(row.unknowns)
    assert row.expected_gate == "HOLD"


def test_confirmed_root_cause_without_evidence_holds():
    row = next(
        r for r in assessed()
        if r.case_id == "RCA_CONFIRMED_CAUSE_NO_EVIDENCE"
    )

    assert {
        "ROOT_CAUSE_EVIDENCE_MISSING",
        "ROOT_CAUSE_CONFIRMATION_NOT_AUDITABLE",
    } <= set(row.unknowns)
    assert row.expected_gate == "HOLD"


def test_applied_correction_without_application_proof_holds():
    row = next(
        r for r in assessed()
        if r.case_id == "RCA_CORRECTION_APPLIED_NO_PROOF"
    )

    assert {
        "CORRECTIVE_ACTION_EVIDENCE_MISSING",
        "CORRECTIVE_ACTION_APPLICATION_NOT_AUDITABLE",
    } <= set(row.unknowns)
    assert row.expected_gate == "HOLD"


def test_effective_claim_without_verification_proof_holds():
    row = next(
        r for r in assessed()
        if r.case_id == "RCA_EFFECTIVE_CLAIM_NO_PROOF"
    )

    assert {
        "EFFECTIVENESS_VERIFICATION_EVIDENCE_MISSING",
        "EFFECTIVENESS_CLAIM_NOT_AUDITABLE",
    } <= set(row.unknowns)
    assert row.expected_gate == "HOLD"


def test_recurrence_after_effective_verification_blocks():
    row = next(
        r for r in assessed()
        if r.case_id == "RCA_RECURRENCE_AFTER_EFFECTIVE"
    )

    assert {
        "RECURRENCE_OBSERVED_AFTER_EFFECTIVE_VERIFICATION",
        "EFFECTIVENESS_CLAIM_INVALIDATED_BY_RECURRENCE",
    } <= set(row.contradictions)
    assert row.expected_gate == "BLOCK"


def test_failed_verification_cannot_be_closed():
    row = next(
        r for r in assessed()
        if r.case_id == "RCA_INEFFECTIVE_BUT_CLOSE_REQUESTED"
    )

    assert {
        "CORRECTIVE_ACTION_VERIFIED_INEFFECTIVE",
        "CLOSURE_REQUEST_CONFLICTS_WITH_FAILED_VERIFICATION",
    } <= set(row.contradictions)
    assert row.expected_gate == "BLOCK"


def test_closed_case_without_monitoring_proof_holds():
    row = next(
        r for r in assessed()
        if r.case_id == "RCA_CLOSED_WITHOUT_MONITORING_PROOF"
    )

    assert {
        "RECURRENCE_MONITORING_EVIDENCE_MISSING",
        "NON_RECURRENCE_NOT_AUDITABLE",
    } <= set(row.unknowns)
    assert row.expected_gate == "HOLD"


def test_duplicate_failure_signature_must_link_prior_incident():
    row = next(
        r for r in assessed()
        if r.case_id == "RCA_DUPLICATE_SIGNATURE_UNLINKED"
    )

    assert {
        "RECURRENT_SIGNATURE_NOT_LINKED_TO_PRIOR_INCIDENT",
        "RECURRENCE_HISTORY_INCOMPLETE",
    } <= set(row.unknowns)
    assert row.expected_gate == "HOLD"


def test_hard_root_cause_deadline_missed_blocks():
    row = next(
        r for r in assessed()
        if r.case_id == "RCA_HARD_DEADLINE_MISSED"
    )

    assert {
        "HARD_ROOT_CAUSE_DEADLINE_MISSED",
        "ROOT_CAUSE_STILL_UNRESOLVED_AFTER_DEADLINE",
    } <= set(row.contradictions)
    assert row.expected_gate == "BLOCK"


def test_complete_durable_closure_builds_deterministic_receipt():
    raw = case_raw("RCA_COMPLETE_DURABLE_CLOSURE")
    row = next(
        r for r in assessed()
        if r.case_id == "RCA_COMPLETE_DURABLE_CLOSURE"
    )

    assert row.expected_gate == "ALLOW"

    first = build_recurrence_prevention_receipt_v0(raw, row)
    second = build_recurrence_prevention_receipt_v0(raw, row)

    assert first == second
    assert first["incident_id"] == "RCA_COMPLETE_DURABLE_CLOSURE"
    assert first["root_cause_ref"] == "sim:root-cause:001"
    assert first["corrective_action_ref"] == "sim:corrective-action:001"
    assert first["decision_authority"] == "KX108_ONLY"
    assert first["external_action"] is False
    assert len(first["receipt_sha256"]) == 64


def test_receipt_rejects_non_closed_or_non_allow_cases():
    open_raw = case_raw("RCA_OPEN_TRIAGE")
    open_row = next(r for r in assessed() if r.case_id == "RCA_OPEN_TRIAGE")

    with pytest.raises(ValueError, match="RCA_RECEIPT_REQUIRES_CLOSED_STATE"):
        build_recurrence_prevention_receipt_v0(open_raw, open_row)

    incomplete_raw = case_raw("RCA_CLOSED_WITHOUT_MONITORING_PROOF")
    incomplete_row = next(
        r for r in assessed()
        if r.case_id == "RCA_CLOSED_WITHOUT_MONITORING_PROOF"
    )

    with pytest.raises(
        ValueError,
        match="RCA_RECEIPT_REQUIRES_ALLOW_GATE:HOLD",
    ):
        build_recurrence_prevention_receipt_v0(
            incomplete_raw,
            incomplete_row,
        )


def test_closed_case_with_observed_recurrence_blocks_and_cannot_receipt():
    raw = {
        "id": "RCA_CLOSED_BUT_RECURRED",
        "lifecycle_state": "CLOSED",
        "incident_family": "MATCHDAY",
        "responsible_role": "MANAGER_GENERAL",
        "root_cause_confirmed": True,
        "root_cause_ref": "sim:root-cause:x",
        "root_cause_evidence_refs": ["sim:evidence:root:x"],
        "corrective_action_applied": True,
        "corrective_action_ref": "sim:corrective:x",
        "corrective_action_evidence_refs": ["sim:evidence:corrective:x"],
        "verification_state": "EFFECTIVE",
        "verification_evidence_refs": ["sim:evidence:verification:x"],
        "prevention_control_refs": ["sim:control:x"],
        "monitoring_evidence_refs": ["sim:evidence:monitoring:x"],
        "closure_authority_ref": "sim:authority:x",
        "closure_requested": True,
        "recurrence_observed": True,
        "evidence_refs": ["sim:incident:x"],
    }
    row = assess_root_cause_case_v0(raw, as_of=date(2026, 10, 7))

    assert {
        "RECURRENCE_OBSERVED_AFTER_EFFECTIVE_VERIFICATION",
        "EFFECTIVENESS_CLAIM_INVALIDATED_BY_RECURRENCE",
        "CLOSED_INCIDENT_HAS_OBSERVED_RECURRENCE",
        "DURABLE_CLOSURE_INVALIDATED",
    } <= set(row.contradictions)
    assert row.expected_gate == "BLOCK"

    with pytest.raises(
        ValueError,
        match="RCA_RECEIPT_REQUIRES_ALLOW_GATE:BLOCK",
    ):
        build_recurrence_prevention_receipt_v0(raw, row)


def test_root_cause_cases_route_into_proof_audit_cockpit():
    pack = build_report_pack_v0(
        assessed(),
        load(ROUTING),
        cadence="BIWEEKLY",
        as_of=date(2026, 10, 7),
        truth_class="SIMULATED_NOT_OBSERVED",
    )

    assert len(pack.items) == 11
    assert "DIRECTION_PRESIDENCE" in pack.persona_views
    assert "MANAGER_GENERAL" in pack.persona_views
    assert "RESP_ADMIN" in pack.persona_views
    assert "CLUB_SECRETARIAT" in pack.persona_views
    assert pack.external_delivery_enabled is False


def test_f3g_i_overlay_closes_root_cause_durability_gaps_only():
    overlay = load(OVERLAY)

    assert overlay["status"] == "READONLY_COVERAGE_CLOSURE"
    target = overlay["closed_targets"][0]
    assert target["requirement_id"] == "ROOT_CAUSE_DURABILITY"
    assert set(target["closed_gaps"]) == {
        "INCIDENT_ROOT_CAUSE_WORKFLOW",
        "RECURRENCE_PREVENTION_RECEIPT",
    }
    assert {
        "REAL_INCIDENT_TAXONOMY",
        "REAL_RCA_OWNER_AND_ESCALATION_MATRIX",
        "REAL_CORRECTIVE_ACTION_APPROVAL_CHAIN",
        "REAL_MONITORING_WINDOWS_BY_INCIDENT_TYPE",
    } <= set(target["remaining_before_field_validation"])


def test_overlay_preserves_action_and_field_boundaries():
    assert load(OVERLAY)["boundaries"] == {
        "real_field_evidence": False,
        "external_action": False,
        "decision_authority": "KX108_ONLY",
    }
