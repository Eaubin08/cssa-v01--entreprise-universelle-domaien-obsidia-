import json
from pathlib import Path

from organizations.cssa.annual import (
    build_one_year_corpus_v0,
    compare_run_matrix_v0,
    failure_summary_v0,
    run_one_year_soak_v0,
)
from organizations.cssa.estimation import build_profile_resources_v0


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "organizations" / "cssa" / "season" / "public_model_v0.json"
RESOURCES = ROOT / "organizations" / "cssa" / "stress" / "resources_v0.json"
ENVELOPE = (
    ROOT
    / "organizations"
    / "cssa"
    / "estimation"
    / "public_anchored_envelope_v0.json"
)
ATTACKS = (
    ROOT
    / "organizations"
    / "cssa"
    / "annual"
    / "annual_attack_profiles_v0.json"
)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def annual_events():
    return build_one_year_corpus_v0(load(MODEL))


def resources_for(profile_id):
    return build_profile_resources_v0(
        load(ENVELOPE),
        load(RESOURCES),
        profile_id,
    )


def run(profile_id, mode):
    return run_one_year_soak_v0(
        events=annual_events(),
        resources=resources_for(profile_id),
        attack_profiles=load(ATTACKS),
        profile_id=profile_id,
        attack_mode=mode,
    )


def test_one_year_corpus_really_spans_365_days_and_extends_offseason():
    events = annual_events()

    assert len(events) == 969
    assert min(event.event_date for event in events) == "2026-08-01"
    assert max(event.event_date for event in events) <= "2027-07-31"

    preseason_licences = [
        event for event in events
        if event.case_type == "next_season_licence_readiness"
    ]
    preseason_equipment = [
        event for event in events
        if event.case_type == "next_season_equipment_readiness"
    ]
    preseason_schedule = [
        event for event in events
        if event.case_type == "next_season_schedule_readiness"
    ]

    assert len(preseason_licences) == 19
    assert len(preseason_equipment) == 19
    assert len(preseason_schedule) == 19


def test_attack_profiles_define_exact_365_day_campaign():
    attacks = load(ATTACKS)

    assert attacks["horizon"] == {
        "start": "2026-08-01",
        "end": "2027-07-31",
        "days": 365,
    }
    assert set(attacks["modes"]) == {"NORMAL", "HARD", "BREAKER"}
    assert len(attacks["modes"]["NORMAL"]["outage_rules"]) == 0
    assert len(attacks["modes"]["HARD"]["outage_rules"]) == 6
    assert len(attacks["modes"]["BREAKER"]["outage_rules"]) == 9


def test_every_case_is_accounted_for_at_year_end():
    result = run("CENTRAL_WORKING", "HARD")

    assert result.day_count == 365
    assert result.input_event_count == 969
    assert (
        result.completed_case_count
        + result.pending_case_count
        + result.privacy_manual_review_count
        == result.input_event_count
    )
    assert result.privacy_manual_review_count == 2


def test_one_year_run_emits_real_failure_inventory_not_only_pass_fail():
    result = run("CENTRAL_WORKING", "HARD")
    summary = failure_summary_v0(result)

    assert summary["failure_signal_count"] > 0
    assert {
        "DEADLINE_MISS",
        "YEAR_END_UNRESOLVED",
    } <= set(summary["failure_types"])
    assert summary["max_backlog"] > 0
    assert summary["max_case_age_days"] > 0
    assert summary["authority"] == "KX108_ONLY"
    assert summary["external_action"] is False


def test_breaker_attack_is_worse_than_normal_on_same_central_profile():
    normal = failure_summary_v0(run("CENTRAL_WORKING", "NORMAL"))
    breaker = failure_summary_v0(run("CENTRAL_WORKING", "BREAKER"))

    assert breaker["failure_signal_count"] > normal["failure_signal_count"]
    assert breaker["max_backlog"] >= normal["max_backlog"]
    assert breaker["pending_case_count"] >= normal["pending_case_count"]


def test_more_capacity_reduces_or_equalizes_failures_under_normal_attack():
    low = failure_summary_v0(run("LOW_CONSTRAINED", "NORMAL"))
    central = failure_summary_v0(run("CENTRAL_WORKING", "NORMAL"))
    high = failure_summary_v0(run("HIGH_CAPACITY", "NORMAL"))

    assert low["failure_signal_count"] >= central["failure_signal_count"]
    assert central["failure_signal_count"] >= high["failure_signal_count"]


def test_hard_campaign_surfaces_shared_asset_and_budget_pressure():
    low = failure_summary_v0(run("LOW_CONSTRAINED", "HARD"))

    assert "SHARED_ASSET_COLLISION" in low["failure_types"]
    assert "TRAVEL_BUDGET_PRESSURE" in low["failure_types"]


def test_breaker_campaign_creates_resource_starvation_and_backlog_failure():
    result = failure_summary_v0(run("LOW_CONSTRAINED", "BREAKER"))

    assert "RESOURCE_STARVATION" in result["failure_types"]
    assert "BACKLOG_SATURATION" in result["failure_types"]


def test_full_3x3_matrix_produces_nine_comparable_runs():
    rows = [
        run(profile, mode)
        for profile in ("LOW_CONSTRAINED", "CENTRAL_WORKING", "HIGH_CAPACITY")
        for mode in ("NORMAL", "HARD", "BREAKER")
    ]
    matrix = compare_run_matrix_v0(rows)

    assert matrix["run_count"] == 9
    assert len(matrix["runs"]) == 9
    assert matrix["authority"] == "KX108_ONLY"
    assert matrix["external_action"] is False
    assert "/" in matrix["best_by_failure_count"]
    assert "/" in matrix["worst_by_failure_count"]
