"""F3G-B — public reality shadow mode V0.

Public observations are real/public evidence, not internal CSSA field evidence.
This module observes, preserves provenance, detects public contradictions and
feeds the governed READONLY/reporting surfaces. It never mutates a club system.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Mapping


ALLOWED_TRUTH_CLASSES = {
    "PUBLIC_CONFIRMED",
    "SECONDARY_CORROBORATED",
}
SHADOW_STATUS = "PUBLIC_SHADOW_EVIDENCE"


@dataclass(frozen=True)
class PublicShadowEventV0:
    event_id: str
    event_date: str
    family: str
    case_type: str
    truth_class: str
    source_ids: tuple[str, ...]
    state_key: str | None = None
    canonical_value: str | None = None
    temporal_kind: str = "EVENT"
    risk_flags: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    shadow_status: str = SHADOW_STATUS
    team_id: str | None = None

    def __post_init__(self) -> None:
        if self.truth_class not in ALLOWED_TRUTH_CLASSES:
            raise ValueError(f"INVALID_PUBLIC_TRUTH_CLASS:{self.truth_class}")
        if self.shadow_status != SHADOW_STATUS:
            raise ValueError("PUBLIC_SHADOW_STATUS_REQUIRED")

    @property
    def expected_gate(self) -> str:
        if len(self.contradictions) >= 2:
            return "BLOCK"
        if len(self.unknowns) > 1:
            return "HOLD"
        return "ALLOW"

    def to_runtime_mapping(self, *, confidence: float | None = None) -> dict[str, Any]:
        if confidence is None:
            confidence = 0.95 if self.truth_class == "PUBLIC_CONFIRMED" else 0.72
        return {
            "case_ref": f"cssa-public-shadow:{self.event_id}",
            "valid_at": f"{self.event_date}T12:00:00Z",
            "source_ref": f"cssa-public-shadow-source:{self.event_id}",
            "unknowns": self.unknowns,
            "contradictions": self.contradictions,
            "risk_flags": self.risk_flags,
            "evidence_refs": self.source_ids,
            "provenance_refs": self.source_ids,
            "confidence": float(confidence),
            "truth_class": self.truth_class,
            "shadow_status": self.shadow_status,
            "state_key": self.state_key,
            "canonical_value": self.canonical_value,
        }


def _source_index(snapshot: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    rows = {str(row["id"]): row for row in snapshot["sources"]}
    if len(rows) != len(snapshot["sources"]):
        raise ValueError("DUPLICATE_PUBLIC_SOURCE_ID")
    return rows


def load_shadow_events_v0(
    snapshot: Mapping[str, Any],
) -> tuple[PublicShadowEventV0, ...]:
    if snapshot.get("status") != SHADOW_STATUS:
        raise ValueError("PUBLIC_SHADOW_SNAPSHOT_STATUS_REQUIRED")

    sources = _source_index(snapshot)
    events = []
    seen: set[str] = set()
    for raw in snapshot["observations"]:
        event_id = str(raw["id"])
        if event_id in seen:
            raise ValueError(f"DUPLICATE_PUBLIC_OBSERVATION_ID:{event_id}")
        seen.add(event_id)

        source_ids = tuple(str(v) for v in raw["source_ids"])
        missing_sources = set(source_ids) - set(sources)
        if missing_sources:
            raise ValueError(
                f"UNKNOWN_PUBLIC_SOURCE_REF:{event_id}:{sorted(missing_sources)}"
            )

        truth_class = str(raw["truth_class"])
        source_truths = {
            str(sources[source_id]["truth_class"])
            for source_id in source_ids
        }
        if truth_class not in source_truths:
            raise ValueError(
                f"OBSERVATION_TRUTH_NOT_SUPPORTED_BY_SOURCE:{event_id}"
            )

        events.append(
            PublicShadowEventV0(
                event_id=event_id,
                event_date=str(raw["event_date"]),
                family=str(raw["family"]),
                case_type=str(raw["case_type"]),
                truth_class=truth_class,
                source_ids=source_ids,
                state_key=raw.get("state_key"),
                canonical_value=(
                    None
                    if raw.get("canonical_value") is None
                    else str(raw["canonical_value"])
                ),
                temporal_kind=str(raw.get("temporal_kind", "EVENT")),
                risk_flags=tuple(str(v) for v in raw.get("risk_flags", ())),
                unknowns=tuple(str(v) for v in raw.get("unknowns", ())),
                contradictions=tuple(
                    str(v) for v in raw.get("contradictions", ())
                ),
                tags=tuple(str(v) for v in raw.get("tags", ())),
                team_id=raw.get("team_id"),
            )
        )

    return tuple(events)


def detect_public_conflicts_v0(
    events: Iterable[PublicShadowEventV0],
) -> tuple[PublicShadowEventV0, ...]:
    grouped: dict[str, list[PublicShadowEventV0]] = defaultdict(list)
    for event in events:
        if event.state_key and event.canonical_value is not None:
            grouped[event.state_key].append(event)

    findings = []
    for state_key, rows in sorted(grouped.items()):
        values = {row.canonical_value for row in rows}
        if len(values) <= 1:
            continue

        source_ids = tuple(
            sorted({
                source_id
                for row in rows
                for source_id in row.source_ids
            })
        )
        truth_class = (
            "PUBLIC_CONFIRMED"
            if any(row.truth_class == "PUBLIC_CONFIRMED" for row in rows)
            else "SECONDARY_CORROBORATED"
        )
        same_source_conflict = len(source_ids) == 1
        findings.append(
            PublicShadowEventV0(
                event_id=f"PUBLIC-CONFLICT:{state_key}",
                event_date=max(row.event_date for row in rows),
                family="PROOF_AUDIT",
                case_type="public_source_value_conflict",
                truth_class=truth_class,
                source_ids=source_ids,
                state_key=state_key,
                canonical_value="UNRESOLVED_PUBLIC_CONFLICT",
                temporal_kind="STATE",
                risk_flags=(
                    "SAME_SOURCE_INTERNAL_INCONSISTENCY"
                    if same_source_conflict
                    else "CROSS_SOURCE_PUBLIC_INCONSISTENCY",
                    "NO_AUTO_RECONCILIATION",
                ),
                contradictions=(
                    f"PUBLIC_VALUE_CONFLICT:{state_key}",
                    f"PUBLIC_PROVENANCE_COHERENCE_CONFLICT:{state_key}",
                ),
                tags=("SHADOW_CONFLICT_FINDING",),
            )
        )
    return tuple(findings)


def corroboration_map_v0(
    events: Iterable[PublicShadowEventV0],
) -> dict[str, Any]:
    grouped: dict[str, list[PublicShadowEventV0]] = defaultdict(list)
    for event in events:
        if event.state_key and event.canonical_value is not None:
            grouped[event.state_key].append(event)

    out = {}
    for state_key, rows in sorted(grouped.items()):
        values = defaultdict(list)
        for row in rows:
            values[row.canonical_value].append(row)
        out[state_key] = {
            "observation_count": len(rows),
            "distinct_value_count": len(values),
            "values": {
                value: {
                    "observation_count": len(value_rows),
                    "source_ids": sorted({
                        source_id
                        for row in value_rows
                        for source_id in row.source_ids
                    }),
                    "truth_classes": sorted({
                        row.truth_class
                        for row in value_rows
                    }),
                }
                for value, value_rows in sorted(values.items())
            },
        }
    return out


def public_shadow_summary_v0(
    snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    events = load_shadow_events_v0(snapshot)
    conflicts = detect_public_conflicts_v0(events)
    truth_counts = Counter(event.truth_class for event in events)
    family_counts = Counter(event.family for event in events)
    recent_workload = [
        event
        for event in events
        if "RECENT_PUBLIC_WORKLOAD" in event.tags
    ]
    blind_spot_coverage = [
        event
        for event in events
        if "F3G_A_BLIND_SPOT_PUBLIC_COVERAGE" in event.tags
    ]

    return {
        "shadow_status": SHADOW_STATUS,
        "as_of": snapshot["as_of"],
        "source_count": len(snapshot["sources"]),
        "observation_count": len(events),
        "truth_counts": dict(sorted(truth_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "public_conflict_count": len(conflicts),
        "public_conflict_ids": [row.event_id for row in conflicts],
        "recent_public_workload_count": len(recent_workload),
        "blind_spot_public_coverage": [
            row.event_id for row in blind_spot_coverage
        ],
        "capacity_still_unknown": [
            "TECHNICAL_DIRECTOR_DAILY_CAPACITY",
            "VOLUNTEER_MATCHDAY_POOL_COUNT",
        ],
        "corroboration": corroboration_map_v0(events),
        "external_action": False,
        "real_internal_field_evidence": False,
    }


def build_shadow_reporting_events_v0(
    snapshot: Mapping[str, Any],
) -> tuple[PublicShadowEventV0, ...]:
    observations = load_shadow_events_v0(snapshot)
    conflicts = detect_public_conflicts_v0(observations)
    return tuple(
        sorted(
            (*observations, *conflicts),
            key=lambda row: (row.event_date, row.event_id),
        )
    )
