"""CSSA persona-routed reporting engine V0.

Generates internal report artifacts only. It never sends messages or performs
external actions.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Iterable, Mapping


TRUTH_CLASSES = {
    "PUBLIC_CONFIRMED",
    "SECONDARY_CORROBORATED",
    "ESTIMATED",
    "SIMULATED_NOT_OBSERVED",
    "REAL_FIELD_EVIDENCE",
    "UNKNOWN_PRIVATE",
}

SEVERITY_ORDER = {
    "PRE_RUNTIME_BLOCK": 0,
    "BLOCK": 1,
    "HOLD": 2,
    "ALLOW": 3,
}


@dataclass(frozen=True)
class RoutedReportItemV0:
    event_id: str
    event_date: str
    family: str
    case_type: str
    expected_gate: str
    recipients: tuple[str, ...]
    truth_class: str
    team_id: str | None = None
    risk_flags: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    redacted: bool = False
    phase: str = "WINDOW"

    def __post_init__(self) -> None:
        if self.truth_class not in TRUTH_CLASSES:
            raise ValueError(f"unknown truth_class: {self.truth_class}")


@dataclass(frozen=True)
class CSSAReportPackV0:
    cadence: str
    as_of: str
    window_start: str
    window_end: str
    items: tuple[RoutedReportItemV0, ...]
    persona_views: Mapping[str, tuple[RoutedReportItemV0, ...]]
    external_delivery_enabled: bool = False

    def __post_init__(self) -> None:
        if self.external_delivery_enabled:
            raise ValueError("V0 external report delivery must remain disabled")


def _phase(event_day: date, as_of: date) -> str:
    if event_day < as_of:
        return "LOOKBACK"
    if event_day == as_of:
        return "TODAY"
    return "LOOKAHEAD"


def _redacted_item(event: Any, recipients: tuple[str, ...], truth_class: str, as_of: date) -> RoutedReportItemV0:
    return RoutedReportItemV0(
        event_id=event.event_id,
        event_date=event.event_date,
        family=event.family,
        case_type=event.case_type,
        expected_gate=event.expected_gate,
        recipients=recipients,
        truth_class=truth_class,
        team_id=event.team_id,
        risk_flags=("SENSITIVE_METADATA_ONLY",),
        unknowns=(),
        contradictions=(),
        redacted=True,
        phase=_phase(date.fromisoformat(event.event_date), as_of),
    )


def route_event_v0(
    event: Any,
    routing: Mapping[str, Any],
    *,
    truth_class: str,
    as_of: date,
) -> RoutedReportItemV0:
    if truth_class not in TRUTH_CLASSES:
        raise ValueError(f"unknown truth_class: {truth_class}")

    routes = routing["family_routes"]
    if event.family not in routes:
        raise ValueError(f"UNROUTED_FAMILY:{event.family}")

    recipients = tuple(routes[event.family])
    if event.family == "PRIVACY_SENSITIVE":
        return _redacted_item(event, recipients, truth_class, as_of)

    return RoutedReportItemV0(
        event_id=event.event_id,
        event_date=event.event_date,
        family=event.family,
        case_type=event.case_type,
        expected_gate=event.expected_gate,
        recipients=recipients,
        truth_class=truth_class,
        team_id=event.team_id,
        risk_flags=tuple(event.risk_flags),
        unknowns=tuple(event.unknowns),
        contradictions=tuple(event.contradictions),
        redacted=False,
        phase=_phase(date.fromisoformat(event.event_date), as_of),
    )


def build_report_pack_v0(
    events: Iterable[Any],
    routing: Mapping[str, Any],
    *,
    cadence: str,
    as_of: date,
    truth_class: str = "SIMULATED_NOT_OBSERVED",
) -> CSSAReportPackV0:
    cadence_cfg = routing["cadences"].get(cadence)
    if cadence_cfg is None:
        raise ValueError(f"unknown cadence: {cadence}")

    start = as_of - timedelta(days=int(cadence_cfg["backward_days"]))
    end = as_of + timedelta(days=int(cadence_cfg["forward_days"]))

    items: list[RoutedReportItemV0] = []
    persona_views: dict[str, list[RoutedReportItemV0]] = defaultdict(list)

    for event in events:
        event_day = date.fromisoformat(event.event_date)
        if not (start <= event_day <= end):
            continue

        item = route_event_v0(
            event,
            routing,
            truth_class=truth_class,
            as_of=as_of,
        )
        items.append(item)

        for recipient in item.recipients:
            persona_cfg = routing["persona_views"].get(recipient)
            if persona_cfg is None:
                # Some narrowly operational/external roles can be routed from
                # families but do not receive a recurring report view.
                continue
            if cadence not in persona_cfg["cadences"]:
                continue
            persona_views[recipient].append(item)

    items.sort(
        key=lambda x: (
            SEVERITY_ORDER.get(x.expected_gate, 99),
            x.event_date,
            x.event_id,
        )
    )
    frozen_views = {
        persona: tuple(
            sorted(
                view,
                key=lambda x: (
                    SEVERITY_ORDER.get(x.expected_gate, 99),
                    x.event_date,
                    x.event_id,
                ),
            )
        )
        for persona, view in sorted(persona_views.items())
    }

    return CSSAReportPackV0(
        cadence=cadence,
        as_of=as_of.isoformat(),
        window_start=start.isoformat(),
        window_end=end.isoformat(),
        items=tuple(items),
        persona_views=frozen_views,
    )


def report_summary_v0(pack: CSSAReportPackV0) -> dict[str, Any]:
    gates = Counter(item.expected_gate for item in pack.items)
    phases = Counter(item.phase for item in pack.items)
    families = Counter(item.family for item in pack.items)
    truths = Counter(item.truth_class for item in pack.items)

    return {
        "cadence": pack.cadence,
        "as_of": pack.as_of,
        "window_start": pack.window_start,
        "window_end": pack.window_end,
        "item_count": len(pack.items),
        "persona_count": len(pack.persona_views),
        "gate_counts": dict(sorted(gates.items())),
        "phase_counts": dict(sorted(phases.items())),
        "family_counts": dict(sorted(families.items())),
        "truth_counts": dict(sorted(truths.items())),
        "external_delivery_enabled": pack.external_delivery_enabled,
    }


def _format_item(item: RoutedReportItemV0) -> str:
    suffix = " [REDACTED]" if item.redacted else ""
    team = f" / {item.team_id}" if item.team_id else ""
    risks = f" risks={','.join(item.risk_flags)}" if item.risk_flags else ""
    unknowns = f" unknowns={','.join(item.unknowns)}" if item.unknowns else ""
    contradictions = (
        f" contradictions={','.join(item.contradictions)}"
        if item.contradictions
        else ""
    )
    return (
        f"- [{item.expected_gate}] {item.event_date} {item.family}/{item.case_type}"
        f"{team}{suffix} | {item.truth_class}{risks}{unknowns}{contradictions}"
    )


def render_markdown_v0(pack: CSSAReportPackV0) -> str:
    summary = report_summary_v0(pack)
    lines = [
        f"# CSSA {pack.cadence} REPORT",
        "",
        f"As-of: {pack.as_of}",
        f"Window: {pack.window_start} -> {pack.window_end}",
        "External delivery: DISABLED",
        "",
        "## Executive summary",
        "",
        f"- Items: {summary['item_count']}",
        f"- Personas with routed view: {summary['persona_count']}",
        f"- Gates: {summary['gate_counts']}",
        f"- Phases: {summary['phase_counts']}",
        f"- Truth classes: {summary['truth_counts']}",
        "",
        "## Global priorities",
        "",
    ]

    if pack.items:
        lines.extend(_format_item(item) for item in pack.items[:20])
    else:
        lines.append("- No routed items in window.")

    for persona, items in pack.persona_views.items():
        lines.extend(["", f"## Persona — {persona}", ""])
        if items:
            lines.extend(_format_item(item) for item in items[:30])
        else:
            lines.append("- No routed items.")

    lines.extend(
        [
            "",
            "## Governance boundary",
            "",
            "- This artifact is reporting/routing only.",
            "- It does not send email, mutate club systems or authorize external action.",
            "- Decision authority remains KX108_ONLY.",
            "",
        ]
    )
    return "\n".join(lines)
