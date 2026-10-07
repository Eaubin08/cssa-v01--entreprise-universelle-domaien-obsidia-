"""F3G-E — controlled semantic promotion and impact propagation V0.

A public page change is not a semantic mutation. This layer accepts only an
explicitly reviewed public change, verifies that the reviewed baseline still
matches the current snapshot, promotes exactly the affected public state, then
re-evaluates downstream estimated/stress/reporting surfaces.

It never authorizes an external action and never lets public evidence silently
rewrite estimated internal capacities.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from typing import Any, Mapping, Iterable

from organizations.cssa.estimation import robust_vs_fragile_v0
from organizations.cssa.reporting import build_report_pack_v0, report_summary_v0
from organizations.cssa.watch import structured_snapshot_drift_v0


PROMOTION_STATUS = "CONTROLLED_SEMANTIC_PROMOTION_V0"
REVIEW_STATUS = "REVIEWED_PUBLIC_CHANGE"
ALLOWED_TRUTH_CLASSES = {"PUBLIC_CONFIRMED", "SECONDARY_CORROBORATED"}


@dataclass(frozen=True)
class PromotedPublicEventV0:
    event_id: str
    event_date: str
    family: str
    case_type: str
    truth_class: str
    source_ids: tuple[str, ...]
    risk_flags: tuple[str, ...] = ("REVIEWED_PUBLIC_STATE_PROMOTION",)
    unknowns: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    team_id: str | None = None

    @property
    def expected_gate(self) -> str:
        if len(self.contradictions) >= 2:
            return "BLOCK"
        if len(self.unknowns) > 1:
            return "HOLD"
        return "ALLOW"


def _state_values(snapshot: Mapping[str, Any], state_key: str) -> tuple[str, ...]:
    return tuple(sorted({
        str(row.get("canonical_value"))
        for row in snapshot["observations"]
        if str(row.get("state_key")) == state_key
    }))


def _source_ids(snapshot: Mapping[str, Any]) -> set[str]:
    return {str(row["id"]) for row in snapshot["sources"]}


def validate_review_packet_v0(
    snapshot: Mapping[str, Any],
    review: Mapping[str, Any],
) -> None:
    if review.get("status") != REVIEW_STATUS:
        raise ValueError("REVIEW_PACKET_STATUS_REQUIRED")
    if review.get("review_decision") != "APPROVED":
        raise ValueError("REVIEW_NOT_APPROVED")
    if review.get("truth_class") not in ALLOWED_TRUTH_CLASSES:
        raise ValueError("INVALID_REVIEW_TRUTH_CLASS")
    if review.get("resolution_mode") != "REPLACE_REVIEWED_STATE_SET":
        raise ValueError("UNSUPPORTED_REVIEW_RESOLUTION_MODE")

    review_id = str(review.get("review_id", "")).strip()
    state_key = str(review.get("state_key", "")).strip()
    if not review_id:
        raise ValueError("REVIEW_ID_REQUIRED")
    if not state_key:
        raise ValueError("STATE_KEY_REQUIRED")

    unresolved = tuple(review.get("unresolved_unknowns", ()))
    contradictions = tuple(review.get("unresolved_contradictions", ()))
    if unresolved:
        raise ValueError("REVIEW_HAS_UNRESOLVED_UNKNOWNS")
    if contradictions:
        raise ValueError("REVIEW_HAS_UNRESOLVED_CONTRADICTIONS")

    if review.get("capacity_updates") or review.get("profile_updates"):
        raise ValueError("PUBLIC_REVIEW_CANNOT_MUTATE_ESTIMATED_CAPACITY")

    known_sources = _source_ids(snapshot)
    packet_sources = {str(v) for v in review.get("source_ids", ())}
    if not packet_sources:
        raise ValueError("REVIEW_SOURCE_REQUIRED")
    missing_sources = sorted(packet_sources - known_sources)
    if missing_sources:
        raise ValueError(
            "REVIEW_SOURCE_NOT_IN_SNAPSHOT:" + ",".join(missing_sources)
        )

    expected_before = tuple(sorted(str(v) for v in review.get(
        "expected_before_values", ()
    )))
    actual_before = _state_values(snapshot, state_key)
    if expected_before != actual_before:
        raise ValueError(
            "REVIEW_BASELINE_MISMATCH:"
            f"expected={expected_before}:actual={actual_before}"
        )

    if not str(review.get("canonical_value", "")).strip():
        raise ValueError("REVIEW_CANONICAL_VALUE_REQUIRED")
    date.fromisoformat(str(review["event_date"]))
    date.fromisoformat(str(review["reviewed_at"]))


def promote_reviewed_public_change_v0(
    snapshot: Mapping[str, Any],
    review: Mapping[str, Any],
) -> dict[str, Any]:
    """Promote exactly one reviewed state without mutating the input snapshot."""
    validate_review_packet_v0(snapshot, review)
    out = deepcopy(snapshot)
    state_key = str(review["state_key"])

    out["observations"] = [
        row for row in out["observations"]
        if str(row.get("state_key")) != state_key
    ]
    out["observations"].append({
        "id": f"PROMOTED:{review['review_id']}",
        "event_date": str(review["event_date"]),
        "family": str(review["family"]),
        "case_type": str(review["case_type"]),
        "truth_class": str(review["truth_class"]),
        "source_ids": [str(v) for v in review["source_ids"]],
        "state_key": state_key,
        "canonical_value": str(review["canonical_value"]),
        "temporal_kind": str(review.get("temporal_kind", "STATE")),
        "tags": ["F3G_E_REVIEWED_PROMOTION"],
        "promotion": {
            "status": PROMOTION_STATUS,
            "review_id": str(review["review_id"]),
            "reviewed_at": str(review["reviewed_at"]),
            "reviewer_role": str(review.get("reviewer_role", "UNSPECIFIED")),
            "resolution_mode": str(review["resolution_mode"]),
        },
    })
    out["as_of"] = str(review["reviewed_at"])

    doctrine = list(out.get("doctrine", ()))
    for rule in (
        "PUBLIC_CHANGE_REQUIRES_EXPLICIT_REVIEW_BEFORE_PROMOTION",
        "REVIEW_BASELINE_MUST_MATCH_CURRENT_STATE",
        "PUBLIC_REVIEW_CANNOT_MUTATE_ESTIMATED_CAPACITY",
        "NO_EXTERNAL_ACTION",
    ):
        if rule not in doctrine:
            doctrine.append(rule)
    out["doctrine"] = doctrine

    ledger = list(out.get("promotion_ledger", ()))
    ledger.append({
        "review_id": str(review["review_id"]),
        "state_key": state_key,
        "before_values": list(review.get("expected_before_values", ())),
        "after_value": str(review["canonical_value"]),
        "reviewed_at": str(review["reviewed_at"]),
        "truth_class": str(review["truth_class"]),
        "external_action": False,
    })
    out["promotion_ledger"] = ledger
    return out


def apply_reviewed_anchor_updates_v0(
    envelope: Mapping[str, Any],
    review: Mapping[str, Any],
) -> dict[str, Any]:
    """Update only explicitly reviewed public anchors.

    Profile capacities remain ESTIMATED and immutable through this function.
    """
    if review.get("status") != REVIEW_STATUS:
        raise ValueError("REVIEW_PACKET_STATUS_REQUIRED")
    if review.get("review_decision") != "APPROVED":
        raise ValueError("REVIEW_NOT_APPROVED")
    if review.get("truth_class") not in ALLOWED_TRUTH_CLASSES:
        raise ValueError("INVALID_REVIEW_TRUTH_CLASS")
    if review.get("unresolved_unknowns"):
        raise ValueError("REVIEW_HAS_UNRESOLVED_UNKNOWNS")
    if review.get("unresolved_contradictions"):
        raise ValueError("REVIEW_HAS_UNRESOLVED_CONTRADICTIONS")
    if review.get("capacity_updates") or review.get("profile_updates"):
        raise ValueError("PUBLIC_REVIEW_CANNOT_MUTATE_ESTIMATED_CAPACITY")

    out = deepcopy(envelope)
    anchors = {str(row["id"]): row for row in out["anchors"]}
    packet_sources = {str(v) for v in review.get("source_ids", ())}

    for update in review.get("anchor_updates", ()):
        anchor_id = str(update["anchor_id"])
        if anchor_id not in anchors:
            raise ValueError(f"UNKNOWN_PUBLIC_ANCHOR:{anchor_id}")
        anchor = anchors[anchor_id]
        if anchor.get("truth_class") not in ALLOWED_TRUTH_CLASSES:
            raise ValueError(f"NON_PUBLIC_ANCHOR_UPDATE_FORBIDDEN:{anchor_id}")

        refs = {str(v) for v in update.get("evidence_refs", ())}
        if not refs:
            raise ValueError(f"ANCHOR_EVIDENCE_REQUIRED:{anchor_id}")
        if not refs <= packet_sources:
            raise ValueError(f"ANCHOR_EVIDENCE_OUTSIDE_REVIEW:{anchor_id}")

        anchor["value"] = update["value"]
        anchor["truth_class"] = str(review["truth_class"])
        anchor["evidence_refs"] = sorted(refs)
        anchor["review_id"] = str(review["review_id"])

    out["as_of"] = str(review["reviewed_at"])
    out["last_public_promotion_review_id"] = str(review["review_id"])
    return out


def build_promoted_event_v0(review: Mapping[str, Any]) -> PromotedPublicEventV0:
    return PromotedPublicEventV0(
        event_id=f"PROMOTED:{review['review_id']}",
        event_date=str(review["event_date"]),
        family=str(review["family"]),
        case_type=str(review["case_type"]),
        truth_class=str(review["truth_class"]),
        source_ids=tuple(str(v) for v in review["source_ids"]),
    )


def _anchor_map(envelope: Mapping[str, Any]) -> dict[str, tuple[str, str]]:
    return {
        str(row["id"]): (
            str(row.get("truth_class")),
            str(row.get("value")),
        )
        for row in envelope["anchors"]
    }


def _capacity_map(envelope: Mapping[str, Any]) -> dict[str, dict[str, float]]:
    return {
        str(profile_id): {
            str(resource_id): float(value)
            for resource_id, value in profile["capacities"].items()
        }
        for profile_id, profile in envelope["profiles"].items()
    }


def _profile_metrics(result: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {
        str(row["profile_id"]): row
        for row in result["profiles"]
    }


def build_promotion_impact_v0(
    *,
    before_snapshot: Mapping[str, Any],
    after_snapshot: Mapping[str, Any],
    before_envelope: Mapping[str, Any],
    after_envelope: Mapping[str, Any],
    review: Mapping[str, Any],
    base_resources: Mapping[str, Any],
    stress_catalog: Mapping[str, Any],
    season_events: Iterable[Any],
    routing: Mapping[str, Any],
    as_of: date,
) -> dict[str, Any]:
    """Re-evaluate downstream surfaces and expose only actual differences."""
    events = tuple(season_events)
    before_eval = robust_vs_fragile_v0(
        before_envelope,
        base_resources,
        stress_catalog,
        events,
    )
    after_eval = robust_vs_fragile_v0(
        after_envelope,
        base_resources,
        stress_catalog,
        events,
    )

    before_profiles = _profile_metrics(before_eval)
    after_profiles = _profile_metrics(after_eval)
    profile_changes = []
    for profile_id in sorted(before_profiles):
        b = before_profiles[profile_id]
        a = after_profiles[profile_id]
        changed = {}
        for field in (
            "gate_counts",
            "resource_conflict_count",
            "season_pressure_point_count",
            "season_max_overload",
            "blind_spot_pressure",
        ):
            if b[field] != a[field]:
                changed[field] = {"before": b[field], "after": a[field]}
        if changed:
            profile_changes.append({
                "profile_id": profile_id,
                "changes": changed,
            })

    before_anchors = _anchor_map(before_envelope)
    after_anchors = _anchor_map(after_envelope)
    anchor_changes = []
    for anchor_id in sorted(set(before_anchors) | set(after_anchors)):
        if before_anchors.get(anchor_id) != after_anchors.get(anchor_id):
            anchor_changes.append({
                "anchor_id": anchor_id,
                "before": before_anchors.get(anchor_id),
                "after": after_anchors.get(anchor_id),
            })

    before_capacities = _capacity_map(before_envelope)
    after_capacities = _capacity_map(after_envelope)
    capacity_changes = []
    for profile_id in sorted(before_capacities):
        for resource_id in sorted(before_capacities[profile_id]):
            before_value = before_capacities[profile_id][resource_id]
            after_value = after_capacities[profile_id][resource_id]
            if before_value != after_value:
                capacity_changes.append({
                    "profile_id": profile_id,
                    "resource_id": resource_id,
                    "before": before_value,
                    "after": after_value,
                })

    promoted_event = build_promoted_event_v0(review)
    before_report = build_report_pack_v0(
        (),
        routing,
        cadence="WEEKLY",
        as_of=as_of,
        truth_class=None,
    )
    after_report = build_report_pack_v0(
        (promoted_event,),
        routing,
        cadence="WEEKLY",
        as_of=as_of,
        truth_class=None,
    )

    return {
        "status": PROMOTION_STATUS,
        "review_id": str(review["review_id"]),
        "snapshot_drift": structured_snapshot_drift_v0(
            before_snapshot,
            after_snapshot,
        ),
        "anchor_changes": anchor_changes,
        "capacity_changes": capacity_changes,
        "stress_sensitivity_rerun": {
            "performed": True,
            "changed_profile_count": len(profile_changes),
            "profile_changes": profile_changes,
            "before": before_eval,
            "after": after_eval,
        },
        "reporting_rerun": {
            "performed": True,
            "before": report_summary_v0(before_report),
            "after": report_summary_v0(after_report),
            "affected_personas": sorted(after_report.persona_views),
            "promoted_event_gate": promoted_event.expected_gate,
        },
        "authority": "KX108_ONLY",
        "external_action": False,
        "memory_write": False,
        "emits_act": False,
        "kernel_mutation": False,
    }


def promote_and_propagate_v0(
    *,
    snapshot: Mapping[str, Any],
    envelope: Mapping[str, Any],
    review: Mapping[str, Any],
    base_resources: Mapping[str, Any],
    stress_catalog: Mapping[str, Any],
    season_events: Iterable[Any],
    routing: Mapping[str, Any],
    as_of: date,
) -> dict[str, Any]:
    promoted_snapshot = promote_reviewed_public_change_v0(snapshot, review)
    promoted_envelope = apply_reviewed_anchor_updates_v0(envelope, review)
    impact = build_promotion_impact_v0(
        before_snapshot=snapshot,
        after_snapshot=promoted_snapshot,
        before_envelope=envelope,
        after_envelope=promoted_envelope,
        review=review,
        base_resources=base_resources,
        stress_catalog=stress_catalog,
        season_events=season_events,
        routing=routing,
        as_of=as_of,
    )
    return {
        "snapshot": promoted_snapshot,
        "envelope": promoted_envelope,
        "impact": impact,
    }
