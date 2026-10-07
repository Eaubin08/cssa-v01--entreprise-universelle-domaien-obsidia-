import json
from pathlib import Path

import pytest

from organizations.cssa.season.logistics_v0 import (
    BASE,
    HIGH,
    LOW,
    fuel_only_reference_v0,
    season_cost_envelope_v0,
)


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "organizations" / "cssa" / "season" / "public_model_v0.json"
PERSONAS = ROOT / "organizations" / "cssa" / "season" / "personas_v0.json"
FM = ROOT / "organizations" / "cssa" / "season" / "fm_management_primitives_v0.json"
SOURCES = ROOT / "evidence" / "source_manifest" / "F3D_CSSA_SEASON_PUBLIC_SOURCES_V0.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_official_public_structure_has_19_role_team_structures():
    model = load(MODEL)
    teams = model["organization"]["teams"]
    assert model["organization"]["public_team_structures_count"] == 19
    assert len(teams) == 19
    assert len({team["id"] for team in teams}) == 19
    assert "U20_R1" in {team["id"] for team in teams}


def test_r1_and_r2_groups_have_expected_season_sizes():
    groups = load(MODEL)["senior_groups"]
    assert len(groups["R1_A"]["clubs"]) == 14
    assert groups["R1_A"]["league_matches"] == 26
    assert groups["R1_A"]["away_league_matches"] == 13
    assert len(groups["R2_A"]["clubs"]) == 12
    assert groups["R2_A"]["league_matches"] == 22
    assert groups["R2_A"]["away_league_matches"] == 11


def test_travel_estimate_is_explicitly_estimated_and_sums_regular_ranges():
    travel = load(MODEL)["travel_estimates"]
    assert travel["certainty"] == "ESTIMATED"

    lows = sum(v[0] for v in travel["team_route_km_ranges"].values())
    highs = sum(v[1] for v in travel["team_route_km_ranges"].values())

    assert lows == 20_000
    assert highs == 29_000
    assert travel["league_and_regular_total_km"] == [20_000, 29_000]
    assert travel["season_scenario_total_team_route_km"] == [22_000, 36_250]


def test_travel_cost_envelope_is_scenario_not_accounting():
    envelope = season_cost_envelope_v0()
    assert envelope["low_eur"] == 15_400.00
    assert envelope["base_eur"] == 32_765.62
    assert envelope["high_eur"] == 65_250.00

    assert LOW.vehicle_km == 44_000
    assert HIGH.vehicle_km == 108_750
    assert BASE.name == "BASE_SIMULATION"


def test_fuel_reference_does_not_hide_non_fuel_costs():
    assert fuel_only_reference_v0(22_000) == 6_050.00
    with pytest.raises(ValueError):
        fuel_only_reference_v0(-1)


def test_partner_count_never_becomes_partner_revenue():
    commercial = load(MODEL)["commercial_public"]
    assert commercial["partners_active"]["value_min"] == 50
    assert commercial["partner_revenue_eur"]["value"] is None
    assert commercial["partner_revenue_eur"]["certainty"] == "UNKNOWN_PRIVATE"


def test_subscriber_snapshots_are_not_promoted_to_final_count():
    subscribers = load(MODEL)["commercial_public"]["subscribers"]
    assert subscribers["official_snapshot_2026_27"]["value"] == 800
    assert subscribers["official_snapshot_2026_27"]["final_count"] is False
    assert subscribers["secondary_later_snapshot"]["value"] == 855
    assert subscribers["final_season_count"]["value"] is None
    assert subscribers["final_season_count"]["certainty"] == "UNKNOWN_PRIVATE"


def test_legal_association_sas_operating_split_remains_unknown():
    legal = load(MODEL)["legal_ecosystem"]
    assert legal["association_cssa"]["status"] == "ACTIVE"
    assert legal["sas_cssa"]["status"].startswith("ACTIVE")
    relation = legal["association_sas_operational_relation_2026"]
    assert relation["value"] is None
    assert relation["certainty"] == "UNKNOWN_PRIVATE"


def test_public_coherence_findings_are_preserved_without_auto_reconciliation():
    findings = load(MODEL)["public_source_coherence_findings"]
    ids = {finding["id"] for finding in findings}
    assert {
        "STALE_MANAGER_GENERAL",
        "STALE_RESERVE_LABEL",
        "HOME_MATCH_MARKETING_MISMATCH",
        "WEBSITE_FRESHNESS_WARNING",
    } <= ids


def test_lgef_tariffs_are_public_references_not_invented_club_totals():
    finance = load(MODEL)["public_financial_rules"]
    assert finance["lgef_2026_2027_license_tariffs_eur"]["SENIOR_U20"] == 30.49
    assert finance["lgef_2026_2027_license_tariffs_eur"]["U9_U8_U7_U6"] == 14.25
    assert finance["lgef_selected_admin_tariffs_eur"]["APPEAL_PROCEDURE"] == 159.71


def test_personas_are_role_based_and_cover_full_club_ecosystem():
    personas = load(PERSONAS)
    ids = {persona["id"] for persona in personas["personas"]}
    assert len(ids) >= 25
    assert {
        "MANAGER_GENERAL",
        "RESP_ADMIN",
        "ADMIN_ACCOUNTING",
        "CLUB_SECRETARIAT",
        "TECHNICAL_DIRECTOR",
        "TEAM_EDUCATOR",
        "PARENT_GUARDIAN",
        "MATCHDAY_ORGANIZER",
        "MATCHDAY_SECURITY",
        "VOLUNTEER",
        "PARTNERSHIP_MANAGER",
        "PARTNER_CONTACT",
        "SUPPORTER_SUBSCRIBER",
        "LGEF_DISTRICT_FFF",
        "CLUB_AFFILIATED_REFEREE",
        "SCHOOL_SECTION_MABILLON",
        "SUPPORTER_MEDIA_DVCR",
    } <= ids
    assert "ROLE_NOT_PERSON_IDENTITY" in personas["rules"]


def test_football_manager_is_reference_abstraction_only():
    fm = load(FM)
    assert fm["status"] == "ABSTRACTIONS_ONLY_NOT_GAME_TRUTH"
    primitive_ids = {item["id"] for item in fm["allowed_primitives"]}
    assert "RESPONSIBILITY_MATRIX" in primitive_ids
    assert "DELEGATION_ROUTING" in primitive_ids
    assert "YOUTH_PIPELINE" in primitive_ids
    assert "GAME_FINANCIAL_FORMULAS_AS_REAL_CLUB_ACCOUNTS" in fm["forbidden_imports"]


def test_source_manifest_has_explicit_certainty_and_urls():
    manifest = load(SOURCES)
    assert len(manifest["sources"]) >= 25
    assert all(source["certainty"] for source in manifest["sources"])
    assert all(source["url"].startswith("http") for source in manifest["sources"])
