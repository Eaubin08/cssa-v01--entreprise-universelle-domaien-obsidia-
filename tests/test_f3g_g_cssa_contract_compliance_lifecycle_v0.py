import json
from datetime import date
from pathlib import Path

import pytest

from organizations.cssa.compliance import (
    assess_compliance_catalog_v0,
    assess_contract_catalog_v0,
    lifecycle_summary_v0,
    validate_contract_transition_v0,
)
from organizations.cssa.reporting import build_report_pack_v0


ROOT = Path(__file__).resolve().parents[1]
CATALOG = (
    ROOT / "organizations" / "cssa" / "compliance"
    / "contract_compliance_cases_v0.json"
)
OVERLAY = (
    ROOT / "organizations" / "cssa" / "compliance"
    / "f3g_g_coverage_closure_overlay_v0.json"
)
ROUTING = ROOT / "organizations" / "cssa" / "reporting" / "routing_v0.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def assessed():
    catalog = load(CATALOG)
    as_of = date(2026, 10, 7)
    return (
        assess_contract_catalog_v0(catalog, as_of=as_of),
        assess_compliance_catalog_v0(catalog, as_of=as_of),
    )


def test_catalog_is_simulated_not_observed():
    catalog = load(CATALOG)

    assert catalog["status"] == "SIMULATED_NOT_OBSERVED"
    assert len(catalog["contracts"]) == 5
    assert len(catalog["compliance_cases"]) == 5


def test_contract_state_machine_allows_only_explicit_transitions():
    validate_contract_transition_v0("DRAFT", "REVIEW")
    validate_contract_transition_v0("REVIEW", "APPROVED")
    validate_contract_transition_v0("APPROVED", "SIGNED")
    validate_contract_transition_v0("SIGNED", "ACTIVE")

    with pytest.raises(
        ValueError,
        match="INVALID_CONTRACT_TRANSITION:DRAFT->ACTIVE",
    ):
        validate_contract_transition_v0("DRAFT", "ACTIVE")

    with pytest.raises(
        ValueError,
        match="INVALID_CONTRACT_TRANSITION:EXPIRED->ACTIVE",
    ):
        validate_contract_transition_v0("EXPIRED", "ACTIVE")


def test_contract_catalog_produces_expected_fail_closed_gates():
    contracts, _ = assessed()
    rows = {row.case_id: row for row in contracts}

    assert rows["CONTRACT_VALID_ACTIVE"].expected_gate == "ALLOW"
    assert rows["CONTRACT_AUTHORITY_UNKNOWN"].expected_gate == "HOLD"
    assert rows["CONTRACT_MULTIPLE_ACTIVE_VERSIONS"].expected_gate == "BLOCK"
    assert rows["CONTRACT_EXPIRED_OPERATION_REQUESTED"].expected_gate == "BLOCK"
    assert rows["CONTRACT_RENEWAL_WINDOW"].expected_gate == "ALLOW"


def test_unknown_signature_authority_is_not_silently_inferred():
    contracts, _ = assessed()
    row = next(
        r for r in contracts if r.case_id == "CONTRACT_AUTHORITY_UNKNOWN"
    )

    assert {
        "SIGNATURE_AUTHORITY_UNKNOWN",
        "AUTHORITY_SCOPE_UNKNOWN",
    } <= set(row.unknowns)
    assert row.expected_gate == "HOLD"


def test_multiple_active_versions_block_until_canonical_version_is_resolved():
    contracts, _ = assessed()
    row = next(
        r for r in contracts
        if r.case_id == "CONTRACT_MULTIPLE_ACTIVE_VERSIONS"
    )

    assert {
        "MULTIPLE_ACTIVE_CONTRACT_VERSIONS",
        "CANONICAL_CONTRACT_VERSION_UNRESOLVED",
    } <= set(row.contradictions)
    assert row.expected_gate == "BLOCK"


def test_expired_contract_cannot_authorize_operational_use():
    contracts, _ = assessed()
    row = next(
        r for r in contracts
        if r.case_id == "CONTRACT_EXPIRED_OPERATION_REQUESTED"
    )

    assert {
        "EXPIRED_CONTRACT_OPERATION_REQUESTED",
        "NO_VALID_ACTIVE_CONTRACT_FOR_OPERATION",
    } <= set(row.contradictions)
    assert row.expected_gate == "BLOCK"


def test_renewal_window_is_a_risk_signal_not_fake_block():
    contracts, _ = assessed()
    row = next(
        r for r in contracts if r.case_id == "CONTRACT_RENEWAL_WINDOW"
    )

    assert "CONTRACT_RENEWAL_WINDOW_OPEN" in row.risk_flags
    assert row.expected_gate == "ALLOW"


def test_compliance_catalog_produces_expected_fail_closed_gates():
    _, compliance = assessed()
    rows = {row.case_id: row for row in compliance}

    assert rows["COMPLIANCE_SATISFIED_VERIFIED"].expected_gate == "ALLOW"
    assert rows["COMPLIANCE_APPLICABILITY_UNKNOWN"].expected_gate == "HOLD"
    assert rows["COMPLIANCE_MISSED_DEADLINE"].expected_gate == "BLOCK"
    assert rows["COMPLIANCE_CONTESTED_REQUIREMENT"].expected_gate == "BLOCK"
    assert rows["COMPLIANCE_DEADLINE_WITHIN_7_DAYS"].expected_gate == "ALLOW"


def test_unknown_applicability_holds_instead_of_guessing_scope():
    _, compliance = assessed()
    row = next(
        r for r in compliance
        if r.case_id == "COMPLIANCE_APPLICABILITY_UNKNOWN"
    )

    assert {
        "COMPLIANCE_APPLICABILITY_UNKNOWN",
        "APPLICABILITY_BASIS_UNKNOWN",
    } <= set(row.unknowns)
    assert row.expected_gate == "HOLD"


def test_missed_mandatory_deadline_blocks_open_requirement():
    _, compliance = assessed()
    row = next(
        r for r in compliance if r.case_id == "COMPLIANCE_MISSED_DEADLINE"
    )

    assert {
        "MANDATORY_COMPLIANCE_DEADLINE_MISSED",
        "OPEN_REQUIREMENT_AFTER_DEADLINE",
    } <= set(row.contradictions)
    assert row.expected_gate == "BLOCK"


def test_upcoming_compliance_deadline_surfaces_risk_without_false_failure():
    _, compliance = assessed()
    row = next(
        r for r in compliance
        if r.case_id == "COMPLIANCE_DEADLINE_WITHIN_7_DAYS"
    )

    assert "COMPLIANCE_DEADLINE_WITHIN_7_DAYS" in row.risk_flags
    assert row.expected_gate == "ALLOW"


def test_lifecycle_summary_is_balanced_and_non_acting():
    contracts, compliance = assessed()
    summary = lifecycle_summary_v0(contracts, compliance)

    assert summary["contract_count"] == 5
    assert summary["compliance_count"] == 5
    assert summary["gate_counts"] == {
        "ALLOW": 4,
        "BLOCK": 4,
        "HOLD": 2,
    }
    assert summary["decision_authority"] == "KX108_ONLY"
    assert summary["external_action"] is False
    assert summary["memory_write"] is False
    assert summary["emits_act"] is False
    assert summary["kernel_mutation"] is False


def test_contract_and_compliance_cases_route_into_existing_governance_cockpit():
    contracts, compliance = assessed()
    routing = load(ROUTING)

    pack = build_report_pack_v0(
        (*contracts, *compliance),
        routing,
        cadence="WEEKLY",
        as_of=date(2026, 10, 7),
        truth_class="SIMULATED_NOT_OBSERVED",
    )

    assert len(pack.items) == 10
    assert "MANAGER_GENERAL" in pack.persona_views
    assert "RESP_ADMIN" in pack.persona_views
    assert "CLUB_SECRETARIAT" in pack.persona_views
    assert pack.external_delivery_enabled is False


def test_f3g_g_overlay_closes_only_the_two_targeted_f3g_f_gaps():
    overlay = load(OVERLAY)

    assert overlay["status"] == "READONLY_COVERAGE_CLOSURE"
    assert len(overlay["closed_targets"]) == 1

    target = overlay["closed_targets"][0]
    assert target["requirement_id"] == "ADMINISTRATION_DAILY"
    assert set(target["closed_gaps"]) == {
        "CONTRACT_LIFECYCLE_WORKFLOW",
        "GENERIC_COMPLIANCE_CASE_WORKFLOW",
    }
    assert {
        "REAL_INTERNAL_CONTRACT_TYPES",
        "REAL_SIGNATURE_AUTHORITY_CHAIN",
        "REAL_COMPLIANCE_OBLIGATION_CATALOG",
    } <= set(target["remaining_before_field_validation"])


def test_f3g_g_overlay_preserves_real_field_and_action_boundaries():
    boundary = load(OVERLAY)["boundaries"]

    assert boundary == {
        "real_field_evidence": False,
        "external_action": False,
        "decision_authority": "KX108_ONLY",
    }
