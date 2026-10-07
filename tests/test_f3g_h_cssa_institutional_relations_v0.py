import json
from datetime import date
from pathlib import Path

from organizations.cssa.institutions import (
    assess_institutional_catalog_v0,
    institutional_summary_v0,
)
from organizations.cssa.reporting import build_report_pack_v0


ROOT = Path(__file__).resolve().parents[1]
CASES = (
    ROOT / "organizations" / "cssa" / "institutions"
    / "institutional_cases_v0.json"
)
SOURCES = (
    ROOT / "organizations" / "cssa" / "institutions"
    / "public_sources_v0.json"
)
OVERLAY = (
    ROOT / "organizations" / "cssa" / "institutions"
    / "f3g_h_coverage_closure_overlay_v0.json"
)
ROUTING = ROOT / "organizations" / "cssa" / "reporting" / "routing_v0.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def assessed():
    return assess_institutional_catalog_v0(
        load(CASES),
        as_of=date(2026, 10, 7),
    )


def test_public_source_scope_is_explicit_and_non_private():
    src = load(SOURCES)

    assert src["status"] == "PUBLIC_SOURCE_SCOPE_ONLY"
    assert len(src["sources"]) == 3
    assert src["boundaries"] == {
        "real_internal_workflow": False,
        "external_action": False,
        "decision_authority": "KX108_ONLY",
    }

    manager = next(
        row for row in src["sources"]
        if row["id"] == "CSSA_MANAGER_GENERAL_RECRUITMENT_2026"
    )
    assert {
        "RELATION_WITH_FFF",
        "RELATION_WITH_VILLE_DE_SEDAN",
        "RELATION_WITH_COLLECTIVITIES",
    } <= set(manager["supports"])
    assert {
        "PRIVATE_AUTHORITY_CHAIN",
        "PRIVATE_REQUIRED_CHANNELS",
        "PRIVATE_APPROVAL_SCOPE",
    } <= set(manager["does_not_support"])


def test_ardenne_metropole_source_has_narrow_facility_scope():
    src = load(SOURCES)
    row = next(
        item for item in src["sources"]
        if item["id"] == "ARDENNE_METROPOLE_DUGAUGUEZ_CURRENT_PAGE"
    )

    assert {
        "DUGAUGUEZ_UNDER_ARDENNE_METROPOLE_RESPONSIBILITY",
        "CSSA_USES_DUGAUGUEZ",
    } <= set(row["supports"])
    assert "CSSA_CAN_SELF_APPROVE_FACILITY_CHANGES" in row["does_not_support"]


def test_case_catalog_is_simulated_not_observed():
    catalog = load(CASES)

    assert catalog["status"] == "SIMULATED_NOT_OBSERVED"
    assert len(catalog["cases"]) == 10


def test_institutional_catalog_expected_gate_distribution():
    rows = {row.case_id: row for row in assessed()}

    assert rows["INST_COMPLETE_FFF_CASE"].expected_gate == "ALLOW"
    assert rows["INST_ACK_NOT_APPROVAL"].expected_gate == "HOLD"
    assert rows["INST_ARDENNE_METROPOLE_SCOPE_UNKNOWN"].expected_gate == "HOLD"
    assert rows["INST_WRONG_CHANNEL"].expected_gate == "BLOCK"
    assert rows["INST_CONFLICTING_INSTRUCTIONS"].expected_gate == "BLOCK"
    assert rows["INST_REFUSED_BUT_ACTION_REQUESTED"].expected_gate == "BLOCK"
    assert rows["INST_COLLECTIVITY_DEADLINE_SOON"].expected_gate == "ALLOW"
    assert rows["INST_HARD_DEADLINE_MISSED"].expected_gate == "BLOCK"
    assert rows["INST_APPROVED_NO_PROOF"].expected_gate == "HOLD"
    assert rows["INST_MISROUTED_AUTHORITY"].expected_gate == "BLOCK"


def test_acknowledgement_never_becomes_approval():
    row = next(
        r for r in assessed() if r.case_id == "INST_ACK_NOT_APPROVAL"
    )

    assert {
        "INSTITUTIONAL_APPROVAL_NOT_RECEIVED",
        "NON_FINAL_INSTITUTIONAL_STATE_CANNOT_AUTHORIZE_ACTION",
    } <= set(row.unknowns)
    assert row.expected_gate == "HOLD"


def test_unknown_institution_authority_scope_holds():
    row = next(
        r for r in assessed()
        if r.case_id == "INST_ARDENNE_METROPOLE_SCOPE_UNKNOWN"
    )

    assert {
        "INSTITUTION_AUTHORITY_SCOPE_UNKNOWN",
        "INSTITUTIONAL_BINDING_SCOPE_UNKNOWN",
    } <= set(row.unknowns)
    assert row.expected_gate == "HOLD"


def test_wrong_channel_blocks_when_required_channel_is_explicit():
    row = next(r for r in assessed() if r.case_id == "INST_WRONG_CHANNEL")

    assert {
        "INSTITUTIONAL_CHANNEL_MISMATCH",
        "INSTITUTIONAL_SUBMISSION_NOT_ON_REQUIRED_CHANNEL",
    } <= set(row.contradictions)
    assert row.expected_gate == "BLOCK"


def test_conflicting_institutional_instructions_block():
    row = next(
        r for r in assessed()
        if r.case_id == "INST_CONFLICTING_INSTRUCTIONS"
    )

    assert {
        "CONFLICTING_INSTITUTIONAL_INSTRUCTIONS",
        "CANONICAL_INSTITUTIONAL_INSTRUCTION_UNRESOLVED",
    } <= set(row.contradictions)
    assert row.expected_gate == "BLOCK"


def test_refusal_cannot_authorize_downstream_action():
    row = next(
        r for r in assessed()
        if r.case_id == "INST_REFUSED_BUT_ACTION_REQUESTED"
    )

    assert {
        "INSTITUTIONAL_REQUEST_REFUSED",
        "DOWNSTREAM_ACTION_CONFLICTS_WITH_REFUSAL",
    } <= set(row.contradictions)
    assert row.expected_gate == "BLOCK"


def test_known_near_deadline_is_risk_not_false_block():
    row = next(
        r for r in assessed()
        if r.case_id == "INST_COLLECTIVITY_DEADLINE_SOON"
    )

    assert "INSTITUTIONAL_DEADLINE_WITHIN_7_DAYS" in row.risk_flags
    assert row.expected_gate == "ALLOW"


def test_explicit_hard_deadline_missed_blocks():
    row = next(
        r for r in assessed()
        if r.case_id == "INST_HARD_DEADLINE_MISSED"
    )

    assert {
        "HARD_INSTITUTIONAL_DEADLINE_MISSED",
        "INSTITUTIONAL_CASE_UNRESOLVED_AFTER_DEADLINE",
    } <= set(row.contradictions)
    assert row.expected_gate == "BLOCK"


def test_approved_state_without_proof_holds():
    row = next(
        r for r in assessed() if r.case_id == "INST_APPROVED_NO_PROOF"
    )

    assert {
        "INSTITUTIONAL_APPROVAL_EVIDENCE_MISSING",
        "INSTITUTIONAL_APPROVAL_NOT_AUDITABLE",
        "FINAL_INSTITUTIONAL_STATE_EVIDENCE_MISSING",
        "FINAL_INSTITUTIONAL_STATE_NOT_AUDITABLE",
    } <= set(row.unknowns)
    assert row.expected_gate == "HOLD"


def test_wrong_authority_scope_blocks_misrouted_case():
    row = next(
        r for r in assessed() if r.case_id == "INST_MISROUTED_AUTHORITY"
    )

    assert {
        "INSTITUTION_NOT_AUTHORIZED_FOR_REQUEST",
        "INSTITUTIONAL_CASE_MISROUTED",
    } <= set(row.contradictions)
    assert row.expected_gate == "BLOCK"


def test_summary_is_non_acting_and_kx108_only():
    summary = institutional_summary_v0(assessed())

    assert summary["case_count"] == 10
    assert summary["gate_counts"] == {
        "ALLOW": 2,
        "BLOCK": 5,
        "HOLD": 3,
    }
    assert summary["decision_authority"] == "KX108_ONLY"
    assert summary["external_action"] is False
    assert summary["memory_write"] is False
    assert summary["emits_act"] is False
    assert summary["kernel_mutation"] is False


def test_cases_route_into_existing_governance_cockpit():
    pack = build_report_pack_v0(
        assessed(),
        load(ROUTING),
        cadence="WEEKLY",
        as_of=date(2026, 10, 7),
        truth_class="SIMULATED_NOT_OBSERVED",
    )

    assert len(pack.items) == 10
    assert "MANAGER_GENERAL" in pack.persona_views
    assert "RESP_ADMIN" in pack.persona_views
    assert "CLUB_SECRETARIAT" in pack.persona_views
    assert pack.external_delivery_enabled is False


def test_f3g_h_overlay_closes_only_institutional_relation_gaps():
    overlay = load(OVERLAY)

    assert overlay["status"] == "READONLY_COVERAGE_CLOSURE"
    target = overlay["closed_targets"][0]
    assert target["requirement_id"] == "INSTITUTIONAL_RELATIONS"
    assert set(target["closed_gaps"]) == {
        "FFF_RELATION_WORKFLOW",
        "VILLE_COLLECTIVITY_RELATION_WORKFLOW",
    }
    assert {
        "REAL_FFF_CASE_CHANNELS_BY_SUBJECT",
        "REAL_VILLE_DE_SEDAN_CASE_SCOPE",
        "REAL_ARDENNE_METROPOLE_APPROVAL_CHAIN",
        "REAL_COLLECTIVITY_CONTACT_AND_APPROVAL_MATRIX",
    } <= set(target["remaining_before_field_validation"])


def test_overlay_preserves_action_and_field_boundaries():
    assert load(OVERLAY)["boundaries"] == {
        "real_field_evidence": False,
        "external_action": False,
        "decision_authority": "KX108_ONLY",
    }
