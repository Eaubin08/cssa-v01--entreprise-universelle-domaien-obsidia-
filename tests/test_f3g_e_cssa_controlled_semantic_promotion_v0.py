import json
from copy import deepcopy
from datetime import date
from pathlib import Path

import pytest

from organizations.cssa.promotion import (
    PROMOTION_STATUS,
    apply_reviewed_anchor_updates_v0,
    build_promoted_event_v0,
    promote_and_propagate_v0,
    promote_reviewed_public_change_v0,
    validate_review_packet_v0,
)
from organizations.cssa.season_simulation import build_full_season_corpus_v0


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = (
    ROOT / "organizations" / "cssa" / "shadow"
    / "public_snapshot_2026-10-07_v0.json"
)
ENVELOPE = (
    ROOT / "organizations" / "cssa" / "estimation"
    / "public_anchored_envelope_v0.json"
)
REVIEW = (
    ROOT / "organizations" / "cssa" / "promotion"
    / "reviewed_change_manager_general_fixture_v0.json"
)
MODEL = ROOT / "organizations" / "cssa" / "season" / "public_model_v0.json"
RESOURCES = ROOT / "organizations" / "cssa" / "stress" / "resources_v0.json"
CATALOG = (
    ROOT / "organizations" / "cssa" / "stress" / "stress_scenarios_v0.json"
)
ROUTING = ROOT / "organizations" / "cssa" / "reporting" / "routing_v0.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def corpus():
    return build_full_season_corpus_v0(load(MODEL))


def full_propagation():
    return promote_and_propagate_v0(
        snapshot=load(SNAPSHOT),
        envelope=load(ENVELOPE),
        review=load(REVIEW),
        base_resources=load(RESOURCES),
        stress_catalog=load(CATALOG),
        season_events=corpus().events,
        routing=load(ROUTING),
        as_of=date(2026, 10, 7),
    )


def test_review_fixture_is_explicitly_simulated_not_observed():
    review = load(REVIEW)
    assert review["fixture_status"] == "SIMULATED_REVIEW_PACKET_NOT_OBSERVED"
    assert review["status"] == "REVIEWED_PUBLIC_CHANGE"
    assert review["review_decision"] == "APPROVED"


def test_review_must_be_explicitly_approved():
    snapshot = load(SNAPSHOT)
    review = load(REVIEW)
    review["review_decision"] = "REJECTED"

    with pytest.raises(ValueError, match="REVIEW_NOT_APPROVED"):
        validate_review_packet_v0(snapshot, review)


def test_review_source_must_already_exist_in_public_snapshot():
    snapshot = load(SNAPSHOT)
    review = load(REVIEW)
    review["source_ids"] = ["UNKNOWN_PUBLIC_SOURCE"]

    with pytest.raises(ValueError, match="REVIEW_SOURCE_NOT_IN_SNAPSHOT"):
        validate_review_packet_v0(snapshot, review)


def test_review_is_rejected_if_baseline_changed_after_human_review():
    snapshot = load(SNAPSHOT)
    review = load(REVIEW)
    review["expected_before_values"] = ["STALE_EXPECTATION"]

    with pytest.raises(ValueError, match="REVIEW_BASELINE_MISMATCH"):
        validate_review_packet_v0(snapshot, review)


def test_unresolved_semantic_review_cannot_be_promoted():
    snapshot = load(SNAPSHOT)
    review = load(REVIEW)
    review["unresolved_unknowns"] = ["IS_THIS_STILL_CURRENT"]

    with pytest.raises(ValueError, match="REVIEW_HAS_UNRESOLVED_UNKNOWNS"):
        promote_reviewed_public_change_v0(snapshot, review)


def test_promotion_replaces_only_reviewed_state_and_does_not_mutate_input():
    snapshot = load(SNAPSHOT)
    original = deepcopy(snapshot)
    review = load(REVIEW)

    promoted = promote_reviewed_public_change_v0(snapshot, review)

    assert snapshot == original
    manager_rows = [
        row for row in promoted["observations"]
        if row.get("state_key") == "manager_general_public_state"
    ]
    assert len(manager_rows) == 1
    assert manager_rows[0]["canonical_value"] == "APPOINTED_PUBLICLY_CONFIRMED"
    assert manager_rows[0]["promotion"]["status"] == PROMOTION_STATUS

    untouched_key = "media_accreditation_minimum_lead_time"
    before = [
        row for row in snapshot["observations"]
        if row.get("state_key") == untouched_key
    ]
    after = [
        row for row in promoted["observations"]
        if row.get("state_key") == untouched_key
    ]
    assert before == after


def test_promotion_records_a_non_acting_audit_ledger():
    promoted = promote_reviewed_public_change_v0(load(SNAPSHOT), load(REVIEW))

    ledger = promoted["promotion_ledger"]
    assert len(ledger) == 1
    assert ledger[0]["review_id"] == "F3GE_REVIEW_MANAGER_GENERAL_001"
    assert ledger[0]["external_action"] is False


def test_public_anchor_can_change_without_touching_estimated_capacities():
    envelope = load(ENVELOPE)
    review = load(REVIEW)
    before_capacities = deepcopy({
        key: value["capacities"]
        for key, value in envelope["profiles"].items()
    })

    promoted = apply_reviewed_anchor_updates_v0(envelope, review)
    anchors = {row["id"]: row for row in promoted["anchors"]}

    assert (
        anchors["PUBLIC_MANAGER_STATE_UNRESOLVED"]["value"]
        == "APPOINTED_PUBLICLY_CONFIRMED"
    )
    assert {
        key: value["capacities"]
        for key, value in promoted["profiles"].items()
    } == before_capacities


def test_direct_anchor_update_also_requires_approved_review():
    envelope = load(ENVELOPE)
    review = load(REVIEW)
    review["review_decision"] = "REJECTED"

    with pytest.raises(ValueError, match="REVIEW_NOT_APPROVED"):
        apply_reviewed_anchor_updates_v0(envelope, review)


def test_public_review_is_forbidden_from_rewriting_estimated_capacity():
    snapshot = load(SNAPSHOT)
    review = load(REVIEW)
    review["capacity_updates"] = {"MANAGER_GENERAL_DAILY": 99}

    with pytest.raises(
        ValueError,
        match="PUBLIC_REVIEW_CANNOT_MUTATE_ESTIMATED_CAPACITY",
    ):
        promote_reviewed_public_change_v0(snapshot, review)


def test_promoted_review_event_is_allow_but_not_action_authority():
    event = build_promoted_event_v0(load(REVIEW))

    assert event.expected_gate == "ALLOW"
    assert event.truth_class == "PUBLIC_CONFIRMED"
    assert event.family == "PEOPLE_HR_VOLUNTEERS"


def test_full_propagation_reruns_stress_and_reports_exact_impact():
    result = full_propagation()
    impact = result["impact"]

    assert impact["status"] == PROMOTION_STATUS
    assert impact["snapshot_drift"]["changed_state_count"] == 1
    assert impact["snapshot_drift"]["changes"][0]["state_key"] == (
        "manager_general_public_state"
    )
    assert len(impact["anchor_changes"]) == 1
    assert impact["capacity_changes"] == []

    rerun = impact["stress_sensitivity_rerun"]
    assert rerun["performed"] is True
    assert rerun["changed_profile_count"] == 0
    assert rerun["profile_changes"] == []
    assert len(rerun["after"]["profiles"]) == 3

    reporting = impact["reporting_rerun"]
    assert reporting["performed"] is True
    assert reporting["after"]["item_count"] == 1
    assert reporting["promoted_event_gate"] == "ALLOW"
    assert reporting["affected_personas"]


def test_full_propagation_preserves_kx108_only_and_non_acting_boundaries():
    impact = full_propagation()["impact"]

    assert impact["authority"] == "KX108_ONLY"
    assert impact["external_action"] is False
    assert impact["memory_write"] is False
    assert impact["emits_act"] is False
    assert impact["kernel_mutation"] is False
