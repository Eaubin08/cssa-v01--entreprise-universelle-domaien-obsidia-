import json
from datetime import date
from pathlib import Path

import pytest

from organizations.cssa.matchday_food import (
    assess_buvette_case_v0,
    assess_buvette_catalog_v0,
    build_matchday_reconciliation_receipt_v0,
    buvette_summary_v0,
)
from organizations.cssa.reporting import build_report_pack_v0


ROOT = Path(__file__).resolve().parents[1]
CASES = (
    ROOT / "organizations" / "cssa" / "matchday_food"
    / "buvette_restauration_cases_v0.json"
)
OVERLAY = (
    ROOT / "organizations" / "cssa" / "matchday_food"
    / "f3g_j_coverage_closure_overlay_v0.json"
)
EXTENSION = (
    ROOT / "organizations" / "cssa" / "matchday_food"
    / "operating_map_extension_v0.json"
)
ROUTING = ROOT / "organizations" / "cssa" / "reporting" / "routing_v0.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def assessed():
    return assess_buvette_catalog_v0(
        load(CASES),
        as_of=date(2026, 10, 7),
    )


def raw(case_id):
    return next(
        row for row in load(CASES)["cases"]
        if row["id"] == case_id
    )


def row(case_id):
    return next(r for r in assessed() if r.case_id == case_id)


def test_catalog_is_simulated_not_observed():
    catalog = load(CASES)

    assert catalog["status"] == "SIMULATED_NOT_OBSERVED"
    assert len(catalog["cases"]) == 16


def test_gate_distribution_covers_stock_supplier_shift_readiness_and_cash():
    summary = buvette_summary_v0(assessed())

    assert summary["case_count"] == 16
    assert summary["gate_counts"] == {
        "ALLOW": 6,
        "BLOCK": 6,
        "HOLD": 4,
    }
    assert summary["case_type_counts"] == {
        "CASH_RECONCILIATION": 3,
        "READINESS": 3,
        "SHIFT": 3,
        "STOCK": 4,
        "SUPPLIER": 3,
    }
    assert summary["decision_authority"] == "KX108_ONLY"
    assert summary["external_action"] is False


def test_stock_ready_allows():
    assert row("BUV_STOCK_READY").expected_gate == "ALLOW"


def test_low_stock_buffer_is_risk_not_false_block():
    r = row("BUV_STOCK_LOW_BUFFER")

    assert r.expected_gate == "ALLOW"
    assert "STOCK_BUFFER_BELOW_15_PERCENT" in r.risk_flags


def test_stock_shortage_blocks_requested_opening():
    r = row("BUV_STOCK_SHORTAGE")

    assert {
        "STOCK_BELOW_MATCHDAY_REQUIREMENT",
        "OPENING_REQUESTED_WITH_INSUFFICIENT_STOCK",
    } <= set(r.contradictions)
    assert r.expected_gate == "BLOCK"


def test_perishable_stock_without_expiry_check_holds():
    r = row("BUV_PERISHABLE_NO_EXPIRY_CHECK")

    assert {
        "PERISHABLE_EXPIRY_CHECK_MISSING",
        "PERISHABLE_STOCK_SUITABILITY_UNKNOWN",
    } <= set(r.unknowns)
    assert r.expected_gate == "HOLD"


def test_confirmed_supplier_with_evidence_allows():
    assert row("BUV_SUPPLIER_CONFIRMED").expected_gate == "ALLOW"


def test_cancelled_required_supplier_delivery_blocks():
    r = row("BUV_SUPPLIER_CANCELLED")

    assert {
        "REQUIRED_SUPPLIER_DELIVERY_UNAVAILABLE",
        "MATCHDAY_RESTAURATION_SUPPLY_BROKEN",
    } <= set(r.contradictions)
    assert r.expected_gate == "BLOCK"


def test_unknown_supplier_delivery_status_holds():
    r = row("BUV_SUPPLIER_STATUS_UNKNOWN")

    assert {
        "SUPPLIER_DELIVERY_STATUS_UNKNOWN",
        "MATCHDAY_SUPPLY_READINESS_UNKNOWN",
    } <= set(r.unknowns)
    assert r.expected_gate == "HOLD"


def test_complete_shift_plan_allows():
    assert row("BUV_SHIFT_COMPLETE").expected_gate == "ALLOW"


def test_understaffed_shift_blocks_opening():
    r = row("BUV_SHIFT_UNDERSTAFFED")

    assert {
        "SHIFT_UNDERSTAFFED_FOR_OPENING",
        "MATCHDAY_BUVETTE_COVERAGE_INSUFFICIENT",
    } <= set(r.contradictions)
    assert r.expected_gate == "BLOCK"


def test_unknown_shift_assignment_authority_holds():
    r = row("BUV_SHIFT_AUTHORITY_UNKNOWN")

    assert {
        "SHIFT_ASSIGNMENT_AUTHORITY_UNKNOWN",
        "VOLUNTEER_ASSIGNMENT_SCOPE_UNKNOWN",
    } <= set(r.unknowns)
    assert r.expected_gate == "HOLD"


def test_complete_readiness_checklist_allows():
    assert row("BUV_READY_COMPLETE_CHECKLIST").expected_gate == "ALLOW"


def test_ready_state_with_incomplete_checks_blocks():
    r = row("BUV_READY_INCOMPLETE_CHECKLIST")

    assert {
        "MATCHDAY_READINESS_CHECKS_INCOMPLETE",
        "BUVETTE_OPENING_READINESS_NOT_PROVEN",
    } <= set(r.unknowns)
    assert {
        "READY_STATE_WITH_INCOMPLETE_CHECKS",
        "READINESS_STATE_CONFLICTS_WITH_EVIDENCE",
    } <= set(r.contradictions)
    assert r.expected_gate == "BLOCK"


def test_cash_reconciled_with_small_variance_allows_and_flags_risk():
    r = row("BUV_CASH_RECONCILED")

    assert r.expected_gate == "ALLOW"
    assert "CASH_VARIANCE_WITHIN_TOLERANCE" in r.risk_flags


def test_cash_variance_over_tolerance_blocks():
    r = row("BUV_CASH_VARIANCE_OVER_TOLERANCE")

    assert {
        "CASH_VARIANCE_OVER_TOLERANCE",
        "MATCHDAY_CASH_RECONCILIATION_UNRESOLVED",
    } <= set(r.contradictions)
    assert r.expected_gate == "BLOCK"


def test_final_cash_state_without_reconciliation_proof_holds():
    r = row("BUV_CASH_FINAL_NO_EVIDENCE")

    assert {
        "RECONCILIATION_EVIDENCE_MISSING",
        "MATCHDAY_CASH_CLOSURE_NOT_AUDITABLE",
    } <= set(r.unknowns)
    assert r.expected_gate == "HOLD"


def test_venue_configuration_conflict_blocks_buvette_opening():
    r = row("BUV_VENUE_CONFIG_CONFLICT")

    assert {
        "BUVETTE_OPENING_CONFLICTS_WITH_VENUE_CONFIGURATION",
        "MATCHDAY_SERVICE_PLAN_INCONSISTENT",
    } <= set(r.contradictions)
    assert r.expected_gate == "BLOCK"


def test_cash_reconciliation_receipt_is_deterministic_and_non_acting():
    r = row("BUV_CASH_RECONCILED")
    first = build_matchday_reconciliation_receipt_v0(
        raw("BUV_CASH_RECONCILED"),
        r,
    )
    second = build_matchday_reconciliation_receipt_v0(
        raw("BUV_CASH_RECONCILED"),
        r,
    )

    assert first == second
    assert first["match_ref"] == "sim:match:013"
    assert first["decision_authority"] == "KX108_ONLY"
    assert first["external_action"] is False
    assert first["memory_write"] is False
    assert first["emits_act"] is False
    assert first["kernel_mutation"] is False
    assert len(first["receipt_sha256"]) == 64


def test_receipt_rejects_open_or_blocked_reconciliation():
    r = row("BUV_CASH_VARIANCE_OVER_TOLERANCE")

    with pytest.raises(
        ValueError,
        match="MATCHDAY_RECEIPT_REQUIRES_FINAL_STATE",
    ):
        build_matchday_reconciliation_receipt_v0(
            raw("BUV_CASH_VARIANCE_OVER_TOLERANCE"),
            r,
        )


def test_matchday_and_finance_cases_route_to_existing_cockpits():
    pack = build_report_pack_v0(
        assessed(),
        load(ROUTING),
        cadence="WEEKLY",
        as_of=date(2026, 10, 7),
        truth_class="SIMULATED_NOT_OBSERVED",
    )

    assert len(pack.items) == 16
    assert "MATCHDAY_ORGANIZER" in pack.persona_views
    assert "VOLUNTEER" in pack.persona_views
    assert "ADMIN_ACCOUNTING" in pack.persona_views
    assert "MANAGER_GENERAL" in pack.persona_views
    assert pack.external_delivery_enabled is False


def test_operating_map_extension_links_new_objects_to_existing_cssa_model():
    extension = load(EXTENSION)

    assert extension["status"] == (
        "SIMULATED_MODEL_EXTENSION_NOT_REAL_FIELD_EVIDENCE"
    )
    assert {
        "BuvetteStock",
        "SupplierOrder",
        "SupplierDelivery",
        "ShiftPlan",
        "TillSession",
        "CashReconciliation",
        "MatchdayFoodReadiness",
    } <= set(extension["objects"])
    assert {
        "Buvette",
        "VolunteerAssignment",
        "Payment",
        "Reconciliation",
        "Receipt",
    } <= set(extension["links_to_existing"])
    assert extension["boundaries"]["external_action"] is False


def test_f3g_j_overlay_closes_all_four_buvette_restauration_gaps():
    overlay = load(OVERLAY)

    assert overlay["status"] == "READONLY_COVERAGE_CLOSURE"
    target = overlay["closed_targets"][0]
    assert target["requirement_id"] == "MATCHDAY_BUVETTE_RESTAURATION"
    assert set(target["closed_gaps"]) == {
        "BUVETTE_STOCK_WORKFLOW",
        "RESTAURATION_SUPPLIER_WORKFLOW",
        "MATCHDAY_CASH_RECONCILIATION",
        "SHIFT_ASSIGNMENT",
    }
    assert {
        "REAL_BUVETTE_PRODUCT_CATALOG",
        "REAL_STOCK_LEVELS_AND_REORDER_RULES",
        "REAL_SUPPLIER_CONTRACTS_AND_DELIVERY_WINDOWS",
        "REAL_SHIFT_REQUIREMENTS_AND_ASSIGNMENT_AUTHORITY",
        "REAL_CASH_RECONCILIATION_POLICY_AND_TOLERANCE",
    } <= set(target["remaining_before_field_validation"])


def test_overlay_preserves_action_and_field_boundaries():
    assert load(OVERLAY)["boundaries"] == {
        "real_field_evidence": False,
        "external_action": False,
        "decision_authority": "KX108_ONLY",
    }


def test_unlinked_case_holds_instead_of_becoming_generic_matchday_truth():
    r = assess_buvette_case_v0(
        {
            "id": "NO_MATCH_LINK",
            "case_type": "READINESS",
            "reporting_family": "MATCHDAY",
            "lifecycle_state": "OPEN",
            "match_ref": None,
            "responsible_role": "MATCHDAY_ORGANIZER",
            "opening_requested": False,
            "venue_buvette_status": "CLOSED",
            "required_check_ids": [],
            "passed_check_ids": [],
            "evidence_refs": [],
        },
        as_of=date(2026, 10, 7),
    )

    assert {
        "MATCHDAY_REFERENCE_UNKNOWN",
        "BUVETTE_CASE_NOT_LINKED_TO_MATCH",
    } <= set(r.unknowns)
    assert r.expected_gate == "HOLD"
