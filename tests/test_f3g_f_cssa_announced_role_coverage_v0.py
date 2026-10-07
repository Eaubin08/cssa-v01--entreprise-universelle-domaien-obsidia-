import json
from pathlib import Path

from organizations.cssa.coverage import (
    action_surface_requirements_v0,
    coverage_summary_v0,
    manager_route_coverage_v0,
    operationalization_queue_v0,
    proof_ref_set_v0,
    validate_announced_role_coverage_v0,
)
from organizations.cssa.stress import assess_catalog_v0, catalog_summary_v0


ROOT = Path(__file__).resolve().parents[1]
COVERAGE = (
    ROOT / "organizations" / "cssa" / "coverage"
    / "announced_manager_role_coverage_v0.json"
)
STRESS = (
    ROOT / "organizations" / "cssa" / "coverage"
    / "announced_role_stress_v0.json"
)
ROUTING = ROOT / "organizations" / "cssa" / "reporting" / "routing_v0.json"
PERSONAS = ROOT / "organizations" / "cssa" / "season" / "personas_v0.json"
OPERATING_MAP = (
    ROOT / "organizations" / "cssa" / "season" / "operating_map_v0.json"
)
RESOURCES = ROOT / "organizations" / "cssa" / "stress" / "resources_v0.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_official_announced_role_contract_is_readonly_public_source():
    model = load(COVERAGE)
    validate_announced_role_coverage_v0(model)

    assert model["source"]["url"] == (
        "https://cs-sedan.fr/recrutement-manager-general"
    )
    assert model["source"]["truth_class"] == "PUBLIC_CONFIRMED"
    assert model["source"]["scope"] == (
        "PUBLIC_ROLE_DESCRIPTION_NOT_INTERNAL_FIELD_EVIDENCE"
    )
    assert model["global_boundaries"]["real_field_evidence"] is False
    assert model["global_boundaries"]["external_action"] is False
    assert model["global_boundaries"]["decision_authority"] == "KX108_ONLY"


def test_announced_role_has_11_explicit_requirements_with_honest_coverage():
    summary = coverage_summary_v0(load(COVERAGE))

    assert summary["requirement_count"] == 11
    assert summary["coverage_counts"] == {
        "OPEN_GAP": 2,
        "PARTIAL": 4,
        "STRUCTURALLY_COVERED": 5,
    }
    assert summary["open_gap_ids"] == [
        "MATCHDAY_BUVETTE_RESTAURATION",
        "DECISION_EXECUTION",
    ]
    assert summary["real_field_evidence"] is False
    assert summary["external_action"] is False


def test_every_declared_proof_reference_exists_in_repository():
    refs = proof_ref_set_v0(load(COVERAGE))

    assert refs
    missing = [ref for ref in refs if not (ROOT / ref).exists()]
    assert missing == []


def test_manager_general_receives_all_routable_announced_families():
    result = manager_route_coverage_v0(load(COVERAGE), load(ROUTING))

    assert result["required_family_count"] >= 10
    assert result["missing_manager_routes"] == []
    assert result["complete"] is True


def test_manager_persona_matches_announced_cross_pole_role_shape():
    personas = load(PERSONAS)["personas"]
    manager = next(row for row in personas if row["id"] == "MANAGER_GENERAL")

    assert {
        "structure club",
        "coordinate poles",
        "institutional relations",
        "matchday operations",
    } <= set(manager["goals"])
    assert {
        "admin cases",
        "contracts",
        "licences",
        "staff status",
        "matchday plan",
    } <= set(manager["inputs"])
    assert {
        "delegation",
        "coordination",
        "escalation",
    } <= set(manager["outputs"])


def test_matchday_announced_objects_exist_but_buvette_has_no_false_workflow_claim():
    domains = {
        row["id"]: set(row["objects"])
        for row in load(OPERATING_MAP)["operating_domains"]
    }

    assert "Ticket" in domains["SUPPORTERS_TICKETING"]
    assert {
        "SecurityPlan",
        "HospitalitySpace",
        "Buvette",
        "VolunteerAssignment",
    } <= domains["MATCHDAY"]

    model = load(COVERAGE)
    buvette = next(
        row for row in model["requirements"]
        if row["id"] == "MATCHDAY_BUVETTE_RESTAURATION"
    )
    assert buvette["coverage_level"] == "OPEN_GAP"
    assert {
        "BUVETTE_STOCK_WORKFLOW",
        "RESTAURATION_SUPPLIER_WORKFLOW",
        "MATCHDAY_CASH_RECONCILIATION",
        "SHIFT_ASSIGNMENT",
    } <= set(buvette["open_gaps"])


def test_decision_execution_gap_points_to_next_operational_surfaces():
    model = load(COVERAGE)
    queue = operationalization_queue_v0(model)

    assert queue[0]["requirement_id"] == "DECISION_EXECUTION"
    assert queue[0]["coverage_level"] == "OPEN_GAP"
    assert set(queue[0]["future_surfaces"]) == {
        "MAIL",
        "CALENDAR",
        "CRM",
        "TASKS",
    }
    assert queue[0]["external_action_enabled"] is False

    for surface in ("MAIL", "CALENDAR", "CRM", "TASKS"):
        assert "DECISION_EXECUTION" in action_surface_requirements_v0(
            model,
            surface,
        )


def test_action_surfaces_are_demand_map_not_enabled_execution():
    model = load(COVERAGE)
    summary = coverage_summary_v0(model)
    routing = load(ROUTING)

    assert set(summary["future_surface_demand"]) == {
        "MAIL",
        "CALENDAR",
        "CRM",
        "TASKS",
    }
    assert routing["external_delivery"]["enabled"] is False
    assert routing["external_delivery"]["decision_authority"] == "KX108_ONLY"


def test_announced_role_stress_suite_is_explicitly_simulated():
    stress = load(STRESS)
    assert stress["status"] == "SIMULATED_NOT_OBSERVED"
    assert len(stress["scenarios"]) == 4


def test_announced_role_stress_suite_closes_expected_gates():
    assessments = assess_catalog_v0(load(STRESS), load(RESOURCES))
    rows = {row.scenario_id: row for row in assessments}

    assert rows["F3GF_S01_MATCHDAY_MULTI_SURFACE_COLLISION"].expected_gate == (
        "BLOCK"
    )
    assert (
        rows["F3GF_S01_MATCHDAY_MULTI_SURFACE_COLLISION"].priority_order[0]
        == "SECURITY_INCIDENT"
    )
    assert rows["F3GF_S02_MANAGER_ABSENT_REGULATORY_HANDOFF"].expected_gate == (
        "HOLD"
    )
    assert rows["F3GF_S03_INSTITUTIONAL_INSTRUCTION_CONFLICT"].expected_gate == (
        "BLOCK"
    )
    assert rows["F3GF_S04_COMPLETE_DELEGATED_HANDOFF"].expected_gate == "ALLOW"


def test_announced_role_stress_summary_preserves_safety_and_fail_closed_logic():
    assessments = assess_catalog_v0(load(STRESS), load(RESOURCES))
    summary = catalog_summary_v0(assessments)

    assert summary["scenario_count"] == 4
    assert summary["gate_counts"] == {
        "ALLOW": 1,
        "BLOCK": 2,
        "HOLD": 1,
    }
    assert summary["resource_conflict_count"] >= 1
    assert summary["priority_orders_generated"] == 4


def test_no_announced_requirement_claims_real_field_proof_or_live_action():
    model = load(COVERAGE)

    assert all(row.get("field_proven") is not True for row in model["requirements"])
    assert model["global_boundaries"] == {
        "real_field_evidence": False,
        "external_action": False,
        "decision_authority": "KX108_ONLY",
        "memory_write": False,
        "emits_act": False,
        "kernel_mutation": False,
    }
