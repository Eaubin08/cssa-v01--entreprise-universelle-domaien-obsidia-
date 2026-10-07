import json
import os
import sys
from datetime import date
from pathlib import Path

import pytest

from organizations.cssa.field import field_runtime_adapter
from organizations.cssa.reporting import (
    build_report_pack_v0,
    render_markdown_v0,
    render_persona_markdown_v0,
)
from organizations.cssa.shadow import (
    build_shadow_reporting_events_v0,
    detect_public_conflicts_v0,
    load_shadow_events_v0,
    public_shadow_summary_v0,
)
from universal.registry.portable_v0 import (
    PortableDomainRegistrationV0,
    PortableDomainRegistryV0,
)
from universal.runtime.resolver_v0 import (
    CanonicalCompatibleResolverV0,
    PortableRuntimeBindingV0,
)


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = (
    ROOT
    / "organizations"
    / "cssa"
    / "shadow"
    / "public_snapshot_2026-10-07_v0.json"
)
ROUTING = ROOT / "organizations" / "cssa" / "reporting" / "routing_v0.json"

UPSTREAM = Path(os.environ["OBSIDIA_UPSTREAM_ROOT"]).resolve()
for candidate in (UPSTREAM, UPSTREAM / "scripts"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from periphery.common import ActionCandidate  # noqa: E402
from scripts.providers.canonical_runtime_receipt_flow_v1 import (  # noqa: E402
    CanonicalRuntimeReceiptFlow,
)
import obsidia_governed_runtime_cycle_v1 as upstream_runtime  # noqa: E402


AGENT_ID = "DATA_PURITY_AGENT"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def snapshot():
    return load(SNAPSHOT)


def events():
    return load_shadow_events_v0(snapshot())


def conflicts():
    return detect_public_conflicts_v0(events())


def test_snapshot_is_public_shadow_not_internal_field_evidence():
    raw = snapshot()
    summary = public_shadow_summary_v0(raw)

    assert raw["status"] == "PUBLIC_SHADOW_EVIDENCE"
    assert summary["source_count"] == 15
    assert summary["observation_count"] == 35
    assert summary["truth_counts"] == {
        "PUBLIC_CONFIRMED": 10,
        "SECONDARY_CORROBORATED": 25,
    }
    assert summary["external_action"] is False
    assert summary["real_internal_field_evidence"] is False


def test_every_observation_is_backed_by_declared_public_source():
    raw = snapshot()
    source_ids = {row["id"] for row in raw["sources"]}

    for observation in raw["observations"]:
        assert set(observation["source_ids"]) <= source_ids
        assert observation["truth_class"] in {
            "PUBLIC_CONFIRMED",
            "SECONDARY_CORROBORATED",
        }


def test_shadow_detects_three_unresolved_public_conflict_groups():
    rows = conflicts()
    by_key = {row.state_key: row for row in rows}

    assert len(rows) == 3
    assert set(by_key) == {
        "manager_general_public_state",
        "r1:2026-10-18:bogny-sedan:start_time",
        "r2:2026-10-04:rethel-sedan2:start_time",
    }
    assert all(row.expected_gate == "BLOCK" for row in rows)
    assert all("NO_AUTO_RECONCILIATION" in row.risk_flags for row in rows)


def test_same_source_internal_inconsistency_is_detected_without_guessing_time():
    row = next(
        x for x in conflicts()
        if x.state_key == "r1:2026-10-18:bogny-sedan:start_time"
    )

    assert row.source_ids == ("LEBALLONROND_CSSA_2026_10_07",)
    assert "SAME_SOURCE_INTERNAL_INCONSISTENCY" in row.risk_flags
    assert row.canonical_value == "UNRESOLVED_PUBLIC_CONFLICT"
    assert row.expected_gate == "BLOCK"


def test_cross_source_r2_time_conflict_is_preserved():
    row = next(
        x for x in conflicts()
        if x.state_key == "r2:2026-10-04:rethel-sedan2:start_time"
    )

    assert set(row.source_ids) == {
        "CSSA_ASSOCIATION_MIRROR_2026_10_02",
        "DNA_R2_2026_10_07",
    }
    assert "CROSS_SOURCE_PUBLIC_INCONSISTENCY" in row.risk_flags
    assert row.expected_gate == "BLOCK"


def test_manager_public_state_conflict_uses_official_sources_and_stays_unresolved():
    row = next(
        x for x in conflicts()
        if x.state_key == "manager_general_public_state"
    )

    assert row.truth_class == "PUBLIC_CONFIRMED"
    assert len(row.source_ids) == 3
    assert row.expected_gate == "BLOCK"


def test_corroborated_r1_result_is_not_mistaken_for_conflict():
    summary = public_shadow_summary_v0(snapshot())
    row = summary["corroboration"]["r1:2026-10-03:sedan-uckange:result"]

    assert row["observation_count"] == 2
    assert row["distinct_value_count"] == 1
    assert row["values"]["SEDAN_2_1_UCKANGE"]["observation_count"] == 2


def test_recent_public_weekend_exposes_real_multi_team_workload():
    summary = public_shadow_summary_v0(snapshot())

    assert summary["recent_public_workload_count"] == 16


def test_f3g_a_blind_spots_gain_public_coverage_but_capacity_remains_unknown():
    summary = public_shadow_summary_v0(snapshot())

    assert summary["blind_spot_public_coverage"] == [
        "OBS_TECHNICAL_DIRECTION_PUBLIC_STRUCTURE",
        "OBS_VOLUNTEER_PROGRAM_ACTIVE",
    ]
    assert summary["capacity_still_unknown"] == [
        "TECHNICAL_DIRECTOR_DAILY_CAPACITY",
        "VOLUNTEER_MATCHDAY_POOL_COUNT",
    ]


def test_mixed_public_truth_classes_are_preserved_in_reporting_cockpit():
    routing = load(ROUTING)
    public_events = build_shadow_reporting_events_v0(snapshot())
    pack = build_report_pack_v0(
        public_events,
        routing,
        cadence="MONTHLY",
        as_of=date(2026, 10, 7),
        truth_class=None,
    )

    truths = {item.truth_class for item in pack.items}
    assert truths == {"PUBLIC_CONFIRMED", "SECONDARY_CORROBORATED"}
    assert "MANAGER_GENERAL" in pack.persona_views
    assert "RESP_ADMIN" in pack.persona_views
    assert pack.external_delivery_enabled is False

    global_md = render_markdown_v0(pack)
    manager_md = render_persona_markdown_v0(
        pack,
        "MANAGER_GENERAL",
        routing,
    )
    assert "PUBLIC_CONFIRMED" in global_md
    assert "SECONDARY_CORROBORATED" in global_md
    assert "External delivery: DISABLED" in manager_md


def make_resolver():
    registry = PortableDomainRegistryV0()
    registry.register(
        PortableDomainRegistrationV0(
            domain_id="administration",
            adapter_id="cssa.public-shadow.v0",
            schema_ref="organizations/cssa/shadow/public_shadow_v0.py",
            capabilities=("read", "classify", "detect", "propose"),
        ),
        field_runtime_adapter,
    )
    resolver = CanonicalCompatibleResolverV0(
        source_root=UPSTREAM,
        registry=registry,
    )
    resolver.bind_portable_runtime(
        PortableRuntimeBindingV0(
            domain_id="administration",
            confidence_provider_id="cssa.public-shadow.confidence.v0",
        ),
        lambda raw: raw["confidence"],
    )
    return resolver


class CountingProvider:
    def __init__(self):
        self.invocations = 0

    def __call__(self, **kwargs):
        self.invocations += 1
        return {
            "runtime_id": "cssa-public-shadow-readonly",
            "provider": "cssa_public_shadow_readonly",
        }


def run_event(tmp_path, event):
    raw = event.to_runtime_mapping()

    flow = CanonicalRuntimeReceiptFlow()
    provider = CountingProvider()
    flow.register_provider("cssa_public_shadow_readonly", provider)

    action = ActionCandidate(
        action_id=f"f3gb-{event.event_id.lower().replace(':', '-')}",
        domain="administration",
        actor_id="f3g-b-public-shadow",
        intent="evaluate_public_shadow_observation",
        action_type="analysis",
        irreversible=False,
        timestamp_plan="",
        payload={
            "freshness_score": 1.0,
            "source_count": max(2, len(event.source_ids)),
            "clean_json_ready": True,
            "critical": False,
        },
    )

    result = upstream_runtime.run_governed_runtime_cycle(
        AGENT_ID,
        action,
        raw,
        execution_surface=flow,
        mission_id=f"mission-{event.event_id.lower().replace(':', '-')}",
        provider_id="cssa_public_shadow_readonly",
        capability="analysis",
        execution_payload={
            "mode": "READONLY_PUBLIC_SHADOW",
            "event_id": event.event_id,
        },
        agent_context_store_dir=tmp_path / "contexts" / event.event_id.replace(":", "_"),
        decision_store_dir=tmp_path / "decisions" / event.event_id.replace(":", "_"),
        domain_extension_resolver=make_resolver(),
    )
    return result, provider


def test_clean_public_observation_can_cross_real_guard_readonly(tmp_path):
    event = next(
        row for row in events()
        if row.event_id == "OBS_TECHNICAL_DIRECTION_PUBLIC_STRUCTURE"
    )
    result, provider = run_event(tmp_path, event)

    assert result.x108_gate == "ALLOW"
    assert result.provider_invoked is True
    assert provider.invocations == 1
    assert result.decision_authority == "KX108_ONLY"
    assert result.world_action_allowed is False


def test_public_conflict_crosses_real_guard_as_block(tmp_path):
    event = next(
        row for row in conflicts()
        if row.state_key == "r1:2026-10-18:bogny-sedan:start_time"
    )
    result, provider = run_event(tmp_path, event)

    assert result.x108_gate == "BLOCK"
    assert result.provider_invoked is False
    assert provider.invocations == 0
    assert result.decision_authority == "KX108_ONLY"
    assert result.memory_write is False
    assert result.kernel_mutation is False
    assert result.emits_act is False
    assert result.world_action_allowed is False
