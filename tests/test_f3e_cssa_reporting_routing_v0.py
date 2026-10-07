import json
from datetime import date
from pathlib import Path

from organizations.cssa.reporting import (
    build_report_pack_v0,
    due_cadences_v0,
    render_markdown_v0,
    render_persona_markdown_v0,
    report_summary_v0,
    route_event_v0,
)
from organizations.cssa.season_simulation import build_full_season_corpus_v0


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "organizations" / "cssa" / "season" / "public_model_v0.json"
ROUTING = ROOT / "organizations" / "cssa" / "reporting" / "routing_v0.json"
PERSONAS = ROOT / "organizations" / "cssa" / "season" / "personas_v0.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def build_corpus():
    return build_full_season_corpus_v0(load(MODEL))


def test_scheduler_weekly_biweekly_monthly():
    assert due_cadences_v0(date(2026, 10, 12)) == ("WEEKLY",)
    assert due_cadences_v0(date(2026, 10, 19)) == ("WEEKLY", "BIWEEKLY")
    assert due_cadences_v0(date(2026, 11, 1)) == ("MONTHLY",)
    assert due_cadences_v0(date(2026, 11, 2)) == ("WEEKLY", "BIWEEKLY")
    assert due_cadences_v0(date(2026, 11, 3)) == ()


def test_all_routing_recipients_exist_in_persona_model():
    routing = load(ROUTING)
    personas = {p["id"] for p in load(PERSONAS)["personas"]}

    recipients = {
        recipient
        for route in routing["family_routes"].values()
        for recipient in route
    }
    recurring = set(routing["persona_views"])

    assert recipients <= personas
    assert recurring <= personas


def test_all_full_season_event_families_have_routes():
    routing = load(ROUTING)
    corpus = build_corpus()
    event_families = {event.family for event in corpus.events}

    assert event_families <= set(routing["family_routes"])


def test_weekly_pack_routes_to_operational_personas():
    routing = load(ROUTING)
    corpus = build_corpus()
    pack = build_report_pack_v0(
        corpus.events,
        routing,
        cadence="WEEKLY",
        as_of=date(2026, 10, 7),
    )

    assert pack.external_delivery_enabled is False
    assert pack.window_start == "2026-09-30"
    assert pack.window_end == "2026-10-14"
    assert len(pack.items) > 0

    assert "MANAGER_GENERAL" in pack.persona_views
    assert "RESP_ADMIN" in pack.persona_views
    assert "TECHNICAL_DIRECTOR" in pack.persona_views
    assert "DIRECTION_PRESIDENCE" not in pack.persona_views


def test_monthly_pack_routes_governance_and_finance():
    routing = load(ROUTING)
    corpus = build_corpus()
    pack = build_report_pack_v0(
        corpus.events,
        routing,
        cadence="MONTHLY",
        as_of=date(2026, 10, 1),
    )

    assert "DIRECTION_PRESIDENCE" in pack.persona_views
    assert "MANAGER_GENERAL" in pack.persona_views
    assert "ADMIN_ACCOUNTING" in pack.persona_views


def test_privacy_sensitive_case_is_redacted_and_narrowly_routed():
    routing = load(ROUTING)
    corpus = build_corpus()
    event = next(e for e in corpus.events if e.event_id == "STRESS-PAYROLL")

    item = route_event_v0(
        event,
        routing,
        truth_class="SIMULATED_NOT_OBSERVED",
        as_of=date(2027, 2, 28),
    )

    assert item.redacted is True
    assert item.recipients == ("MANAGER_GENERAL", "RESP_ADMIN")
    assert item.risk_flags == ("SENSITIVE_METADATA_ONLY",)
    assert item.unknowns == ()
    assert item.contradictions == ()
    assert item.expected_gate == "PRE_RUNTIME_BLOCK"


def test_truth_class_is_preserved_and_not_silently_promoted():
    routing = load(ROUTING)
    corpus = build_corpus()
    event = next(e for e in corpus.events if e.family == "COMMUNICATION")

    item = route_event_v0(
        event,
        routing,
        truth_class="SIMULATED_NOT_OBSERVED",
        as_of=date.fromisoformat(event.event_date),
    )
    assert item.truth_class == "SIMULATED_NOT_OBSERVED"


def test_global_and_persona_markdown_are_separate_artifacts():
    routing = load(ROUTING)
    corpus = build_corpus()
    pack = build_report_pack_v0(
        corpus.events,
        routing,
        cadence="WEEKLY",
        as_of=date(2026, 10, 7),
    )

    global_md = render_markdown_v0(pack)
    manager_md = render_persona_markdown_v0(
        pack,
        "MANAGER_GENERAL",
        routing,
    )
    communication_md = render_persona_markdown_v0(
        pack,
        "COMMUNICATION",
        routing,
    )

    assert "# CSSA WEEKLY REPORT" in global_md
    assert "# CSSA WEEKLY — MANAGER_GENERAL" in manager_md
    assert "# CSSA WEEKLY — COMMUNICATION" in communication_md
    assert "External delivery: DISABLED" in global_md
    assert "KX108_ONLY" in manager_md


def test_report_summary_keeps_gate_phase_family_and_truth_counts():
    routing = load(ROUTING)
    corpus = build_corpus()
    pack = build_report_pack_v0(
        corpus.events,
        routing,
        cadence="BIWEEKLY",
        as_of=date(2026, 10, 19),
    )
    summary = report_summary_v0(pack)

    assert summary["item_count"] == len(pack.items)
    assert summary["persona_count"] == len(pack.persona_views)
    assert sum(summary["gate_counts"].values()) == len(pack.items)
    assert sum(summary["phase_counts"].values()) == len(pack.items)
    assert sum(summary["family_counts"].values()) == len(pack.items)
    assert summary["truth_counts"] == {
        "SIMULATED_NOT_OBSERVED": len(pack.items)
    }


def test_external_delivery_is_disabled_in_config():
    routing = load(ROUTING)
    assert routing["external_delivery"]["enabled"] is False
    assert routing["external_delivery"]["decision_authority"] == "KX108_ONLY"
