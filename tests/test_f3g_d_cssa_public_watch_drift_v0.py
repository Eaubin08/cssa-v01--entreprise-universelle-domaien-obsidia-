import json
from datetime import date
from pathlib import Path

import pytest

from organizations.cssa.reporting import build_report_pack_v0
from organizations.cssa.watch import (
    capture_source_v0,
    compare_capture_sets_v0,
    compare_captures_v0,
    delta_to_signal_v0,
    due_sources_v0,
    fingerprint_bytes_v0,
    structured_snapshot_drift_v0,
    watch_summary_v0,
)


ROOT = Path(__file__).resolve().parents[1]
WATCHLIST = ROOT / "organizations" / "cssa" / "watch" / "watchlist_v0.json"
ROUTING = ROOT / "organizations" / "cssa" / "reporting" / "routing_v0.json"
SNAPSHOT = (
    ROOT
    / "organizations"
    / "cssa"
    / "shadow"
    / "public_snapshot_2026-10-07_v0.json"
)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_watchlist_is_readonly_https_and_explicit():
    watchlist = load(WATCHLIST)

    assert watchlist["status"] == "READONLY_PUBLIC_WATCH"
    assert len(watchlist["sources"]) == 14
    assert all(row["url"].startswith("https://") for row in watchlist["sources"])
    assert {
        row["truth_class"] for row in watchlist["sources"]
    } <= {"PUBLIC_CONFIRMED", "SECONDARY_CORROBORATED"}


def test_due_source_schedule_weekly_biweekly_monthly():
    watchlist = load(WATCHLIST)

    weekly = due_sources_v0(watchlist, as_of=date(2026, 10, 12))
    assert weekly
    assert all(row["cadence"] == "WEEKLY" for row in weekly)

    biweekly_monday = due_sources_v0(
        watchlist,
        as_of=date(2026, 10, 19),
    )
    assert {"WEEKLY", "BIWEEKLY"} == {
        row["cadence"] for row in biweekly_monday
    }

    month_first = due_sources_v0(
        watchlist,
        as_of=date(2026, 11, 1),
    )
    assert month_first
    assert all(row["cadence"] == "MONTHLY" for row in month_first)


def test_visible_text_fingerprint_ignores_script_only_change():
    a = b"<html><body><h1>Sedan</h1><script>token=1</script></body></html>"
    b = b"<html><body><h1>Sedan</h1><script>token=999</script></body></html>"

    fa = fingerprint_bytes_v0(a)
    fb = fingerprint_bytes_v0(b)

    assert fa["raw_sha256"] != fb["raw_sha256"]
    assert fa["visible_text_sha256"] == fb["visible_text_sha256"]


def test_capture_uses_get_only_fetcher_contract_and_records_fingerprint():
    source = load(WATCHLIST)["sources"][0]
    seen = []

    def fake_fetcher(url):
        seen.append(url)
        return b"<html><body>CSSA public page</body></html>"

    capture = capture_source_v0(
        source,
        observed_at="2026-10-07",
        fetcher=fake_fetcher,
    )

    assert seen == [source["url"]]
    assert capture["status"] == "OK"
    assert capture["raw_bytes"] > 0
    assert len(capture["visible_text_sha256"]) == 64


def test_non_https_source_fails_closed():
    source = {
        "id": "BAD",
        "url": "http://example.com",
        "truth_class": "PUBLIC_CONFIRMED",
        "cadence": "WEEKLY",
    }

    with pytest.raises(ValueError, match="NON_HTTPS_WATCH_SOURCE"):
        capture_source_v0(
            source,
            observed_at="2026-10-07",
            fetcher=lambda _url: b"x",
        )


def test_visible_content_change_creates_hold_review_signal():
    source = load(WATCHLIST)["sources"][0]

    before = capture_source_v0(
        source,
        observed_at="2026-10-01",
        fetcher=lambda _url: b"<html><body>Old public state</body></html>",
    )
    after = capture_source_v0(
        source,
        observed_at="2026-10-07",
        fetcher=lambda _url: b"<html><body>New public state</body></html>",
    )

    delta = compare_captures_v0(before, after)
    signal = delta_to_signal_v0(delta)

    assert delta["status"] == "VISIBLE_CONTENT_CHANGED_REVIEW_REQUIRED"
    assert signal is not None
    assert signal.expected_gate == "HOLD"
    assert signal.family == "PROOF_AUDIT"
    assert "SEMANTIC_CHANGE_NOT_REVIEWED" in signal.unknowns


def test_raw_only_change_does_not_create_review_signal():
    source = load(WATCHLIST)["sources"][0]
    before = capture_source_v0(
        source,
        observed_at="2026-10-01",
        fetcher=lambda _url: b"<body>Same<script>a=1</script></body>",
    )
    after = capture_source_v0(
        source,
        observed_at="2026-10-07",
        fetcher=lambda _url: b"<body>Same<script>a=2</script></body>",
    )

    delta = compare_captures_v0(before, after)

    assert delta["status"] == "RAW_CHANGED_VISIBLE_UNCHANGED"
    assert delta_to_signal_v0(delta) is None


def test_unreachable_source_creates_hold_signal_not_fake_fact():
    source = load(WATCHLIST)["sources"][0]

    def broken(_url):
        raise TimeoutError("simulated timeout")

    current = capture_source_v0(
        source,
        observed_at="2026-10-07",
        fetcher=broken,
    )
    delta = compare_captures_v0(None, current)
    # First observation still establishes baseline metadata even if unavailable.
    assert delta["status"] == "NEW_BASELINE"

    previous = {
        "source_id": source["id"],
        "url": source["url"],
        "truth_class": source["truth_class"],
        "cadence": source["cadence"],
        "observed_at": "2026-10-01",
        "status": "OK",
        "raw_sha256": "a",
        "visible_text_sha256": "b",
    }
    delta = compare_captures_v0(previous, current)
    signal = delta_to_signal_v0(delta)

    assert delta["status"] == "UNREACHABLE"
    assert signal is not None
    assert signal.expected_gate == "HOLD"
    assert "CURRENT_SOURCE_STATE_UNKNOWN" in signal.unknowns


def test_capture_set_comparison_is_source_stable():
    previous = [
        {
            "source_id": "A",
            "truth_class": "PUBLIC_CONFIRMED",
            "observed_at": "2026-10-01",
            "status": "OK",
            "raw_sha256": "1",
            "visible_text_sha256": "1",
        }
    ]
    current = [
        {
            "source_id": "A",
            "truth_class": "PUBLIC_CONFIRMED",
            "observed_at": "2026-10-07",
            "status": "OK",
            "raw_sha256": "2",
            "visible_text_sha256": "2",
        },
        {
            "source_id": "B",
            "truth_class": "SECONDARY_CORROBORATED",
            "observed_at": "2026-10-07",
            "status": "OK",
            "raw_sha256": "3",
            "visible_text_sha256": "3",
        },
    ]

    deltas = compare_capture_sets_v0(previous, current)
    assert [row["source_id"] for row in deltas] == ["A", "B"]
    assert deltas[0]["status"] == "VISIBLE_CONTENT_CHANGED_REVIEW_REQUIRED"
    assert deltas[1]["status"] == "NEW_BASELINE"


def test_structured_snapshot_drift_detects_reviewed_semantic_change():
    previous = load(SNAPSHOT)
    current = json.loads(json.dumps(previous))
    current["as_of"] = "2026-10-14"

    row = next(
        obs for obs in current["observations"]
        if obs.get("state_key")
        == "r1:2026-10-18:bogny-sedan:start_time"
        and obs["extraction_path"] == "MATCH_TABLE"
    )
    row["canonical_value"] = "16:00"

    drift = structured_snapshot_drift_v0(previous, current)

    assert drift["changed_state_count"] == 1
    assert drift["changes"][0]["kind"] == "VALUE_SET_CHANGED"
    assert drift["changes"][0]["state_key"] == (
        "r1:2026-10-18:bogny-sedan:start_time"
    )


def test_watch_signals_flow_to_existing_reporting_without_external_action():
    routing = load(ROUTING)
    signal = delta_to_signal_v0(
        {
            "source_id": "CSSA_HOME",
            "status": "VISIBLE_CONTENT_CHANGED_REVIEW_REQUIRED",
            "truth_class": "PUBLIC_CONFIRMED",
            "criticality": "MEDIUM",
            "previous_observed_at": "2026-10-01",
            "current_observed_at": "2026-10-07",
        }
    )
    assert signal is not None

    pack = build_report_pack_v0(
        (signal,),
        routing,
        cadence="WEEKLY",
        as_of=date(2026, 10, 7),
        truth_class=None,
    )

    assert len(pack.items) == 1
    assert pack.items[0].expected_gate == "HOLD"
    assert pack.items[0].truth_class == "PUBLIC_CONFIRMED"
    assert "RESP_ADMIN" in pack.persona_views
    assert pack.external_delivery_enabled is False


def test_watch_summary_separates_noise_from_review_signals():
    deltas = (
        {
            "source_id": "A",
            "status": "UNCHANGED",
            "truth_class": "PUBLIC_CONFIRMED",
            "current_observed_at": "2026-10-07",
        },
        {
            "source_id": "B",
            "status": "RAW_CHANGED_VISIBLE_UNCHANGED",
            "truth_class": "PUBLIC_CONFIRMED",
            "current_observed_at": "2026-10-07",
        },
        {
            "source_id": "C",
            "status": "VISIBLE_CONTENT_CHANGED_REVIEW_REQUIRED",
            "truth_class": "PUBLIC_CONFIRMED",
            "current_observed_at": "2026-10-07",
        },
    )

    summary = watch_summary_v0(deltas)

    assert summary["delta_count"] == 3
    assert summary["signal_count"] == 1
    assert summary["hold_signal_count"] == 1
    assert summary["external_action"] is False
