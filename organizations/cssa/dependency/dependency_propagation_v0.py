"""F3I — fixture/dependency propagation hardening V0.

Builds a dependency graph from the synthetic season and proves that a changed
fixture state cannot silently leave downstream surfaces on another revision.

This layer is non-sovereign. It detects coherence failures and emits governed
signals; it does not edit ticketing, transport, FMI, matchday or communication.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Iterable, Mapping


STATUS = "SIMULATED_NOT_OBSERVED"
FAMILY = "DEPENDENCY_PROPAGATION"


@dataclass(frozen=True)
class DependencyNodeV0:
    event_id: str
    fixture_ref: str
    family: str
    case_type: str
    event_date: str
    team_id: str | None
    root: bool = False


@dataclass(frozen=True)
class FixtureDependencyGraphV0:
    fixture_ref: str
    root: DependencyNodeV0
    dependents: tuple[DependencyNodeV0, ...]

    @property
    def surface_count(self) -> int:
        return len(self.dependents)


@dataclass(frozen=True)
class PropagationSurfaceStateV0:
    event_id: str
    fixture_ref: str
    case_type: str
    surface: str
    root_revision: int
    observed_revision: int
    ready: bool
    final_authority_seen: bool
    propagation_delay_hours: float
    stale_reason: str | None = None


@dataclass(frozen=True)
class PropagationAssessmentV0:
    assessment_id: str
    event_date: str
    fixture_ref: str
    title: str
    surfaces: tuple[PropagationSurfaceStateV0, ...]
    unknowns: tuple[str, ...] = ()
    contradictions: tuple[str, ...] = ()
    risk_flags: tuple[str, ...] = ()
    truth_class: str = STATUS
    family: str = FAMILY
    case_type: str = "fixture_dependency_propagation"
    team_id: str | None = None

    @property
    def event_id(self) -> str:
        return self.assessment_id

    @property
    def source_ids(self) -> tuple[str, ...]:
        return tuple(
            sorted({surface.event_id for surface in self.surfaces})
        )

    @property
    def expected_gate(self) -> str:
        if len(self.contradictions) >= 2:
            return "BLOCK"
        if len(self.unknowns) > 1:
            return "HOLD"
        return "ALLOW"

    @property
    def silent_inconsistency_count(self) -> int:
        return sum(
            1
            for surface in self.surfaces
            if surface.ready
            and (
                surface.observed_revision != surface.root_revision
                or not surface.final_authority_seen
            )
        )

    def to_runtime_mapping(self, *, confidence: float = 0.92) -> dict[str, Any]:
        return {
            "case_ref": f"cssa-dependency:{self.assessment_id}",
            "valid_at": f"{self.event_date}T12:00:00Z",
            "source_ref": f"cssa-dependency-source:{self.fixture_ref}",
            "unknowns": self.unknowns,
            "contradictions": self.contradictions,
            "risk_flags": self.risk_flags,
            "evidence_refs": self.source_ids,
            "provenance_refs": ("F3I_SIMULATION_ONLY",),
            "confidence": float(confidence),
            "simulation_status": STATUS,
            "fixture_ref": self.fixture_ref,
            "silent_inconsistency_count": self.silent_inconsistency_count,
        }


def build_fixture_dependency_graphs_v0(
    events: Iterable[Any],
) -> tuple[FixtureDependencyGraphV0, ...]:
    grouped: dict[str, list[Any]] = defaultdict(list)
    for event in events:
        for ref in getattr(event, "target_refs", ()) or ():
            if str(ref).startswith("fixture:"):
                grouped[str(ref)].append(event)

    graphs = []
    for fixture_ref, rows in sorted(grouped.items()):
        roots = [row for row in rows if row.case_type == "fixture_state"]
        if len(roots) != 1:
            raise ValueError(
                f"FIXTURE_ROOT_CARDINALITY:{fixture_ref}:{len(roots)}"
            )
        root_event = roots[0]
        root = DependencyNodeV0(
            event_id=root_event.event_id,
            fixture_ref=fixture_ref,
            family=root_event.family,
            case_type=root_event.case_type,
            event_date=root_event.event_date,
            team_id=root_event.team_id,
            root=True,
        )
        dependents = tuple(
            DependencyNodeV0(
                event_id=row.event_id,
                fixture_ref=fixture_ref,
                family=row.family,
                case_type=row.case_type,
                event_date=row.event_date,
                team_id=row.team_id,
                root=False,
            )
            for row in sorted(rows, key=lambda r: (r.event_date, r.event_id))
            if row.case_type != "fixture_state"
        )
        graphs.append(
            FixtureDependencyGraphV0(
                fixture_ref=fixture_ref,
                root=root,
                dependents=dependents,
            )
        )
    return tuple(graphs)


def dependency_rule_index_v0(
    rules: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    rows = {
        str(row["case_type"]): row
        for row in rules["dependency_rules"]
    }
    if len(rows) != len(rules["dependency_rules"]):
        raise ValueError("DUPLICATE_DEPENDENCY_RULE")
    return rows


def _fixture_event_time(graph: FixtureDependencyGraphV0) -> datetime:
    return datetime.fromisoformat(f"{graph.root.event_date}T12:00:00")


def _is_required_surface(
    graph: FixtureDependencyGraphV0,
    case_type: str,
) -> bool:
    team = graph.root.team_id
    fixture_number = int(graph.fixture_ref.rsplit(":", 1)[1])
    is_home = fixture_number % 2 == 1
    if case_type == "away_trip_plan":
        return not is_home
    if case_type == "travel_reconciliation":
        return not is_home
    if case_type == "fmi_post_match":
        return team in {"SENIORS_R1", "SENIORS_R2", "U20_R1"}
    if case_type == "match_publication_candidate":
        return team == "SENIORS_R1"
    if case_type in {
        "venue_configuration",
        "hospitality_activation",
        "matchday_volunteer_assignment",
        "home_match_ticketing_state",
    }:
        return team == "SENIORS_R1" and is_home
    return False


def validate_graph_coverage_v0(
    graphs: Iterable[FixtureDependencyGraphV0],
    rules: Mapping[str, Any],
) -> dict[str, Any]:
    graph_rows = tuple(graphs)
    rule_index = dependency_rule_index_v0(rules)
    missing_required = []
    orphan_case_types = set()
    dependency_count = 0

    for graph in graph_rows:
        present = {node.case_type for node in graph.dependents}
        dependency_count += len(graph.dependents)
        for case_type in rule_index:
            if _is_required_surface(graph, case_type) and case_type not in present:
                missing_required.append(
                    f"{graph.fixture_ref}:{case_type}"
                )
        for case_type in present:
            if case_type not in rule_index:
                orphan_case_types.add(case_type)

    return {
        "fixture_count": len(graph_rows),
        "dependency_count": dependency_count,
        "missing_required": sorted(missing_required),
        "unruled_case_types": sorted(orphan_case_types),
    }


def assess_revision_state_v0(
    *,
    graph: FixtureDependencyGraphV0,
    rules: Mapping[str, Any],
    assessment_id: str,
    root_revision: int,
    root_final_authority: bool,
    surface_revisions: Mapping[str, int] | None = None,
    surface_delays_hours: Mapping[str, float] | None = None,
    missing_surfaces: Iterable[str] = (),
) -> PropagationAssessmentV0:
    if root_revision < 1:
        raise ValueError("ROOT_REVISION_MUST_BE_POSITIVE")
    rule_index = dependency_rule_index_v0(rules)
    revisions = dict(surface_revisions or {})
    delays = dict(surface_delays_hours or {})
    missing = set(str(v) for v in missing_surfaces)

    surfaces = []
    unknowns = []
    contradictions = []
    risks = []

    present_nodes = {node.case_type: node for node in graph.dependents}

    for case_type, rule in rule_index.items():
        required = _is_required_surface(graph, case_type)
        node = present_nodes.get(case_type)
        if not required and node is None:
            continue

        if required and (node is None or case_type in missing):
            unknowns.extend(
                (
                    f"MISSING_DEPENDENT:{case_type}",
                    f"PROPAGATION_STATUS_UNKNOWN:{case_type}",
                )
            )
            risks.append(f"MISSING_REQUIRED_SURFACE:{case_type}")
            continue

        if node is None:
            continue

        observed_revision = int(revisions.get(case_type, root_revision))
        delay_hours = float(delays.get(case_type, 0.0))
        max_hours = float(rule["max_propagation_hours"])

        final_seen = bool(root_final_authority)
        ready = (
            final_seen
            and observed_revision == root_revision
            and delay_hours <= max_hours
        )
        stale_reason = None

        if observed_revision > root_revision:
            contradictions.extend(
                (
                    f"DEPENDENT_AHEAD_OF_ROOT:{case_type}",
                    f"ILLEGAL_REVISION_ORDER:{case_type}",
                )
            )
            stale_reason = "DEPENDENT_AHEAD_OF_ROOT"
            ready = False
        elif observed_revision < root_revision:
            risks.append(f"STALE_DEPENDENT:{case_type}")
            unknowns.extend(
                (
                    f"DEPENDENT_REFRESH_PENDING:{case_type}",
                    f"DEPENDENT_STATE_NOT_CURRENT:{case_type}",
                )
            )
            stale_reason = "STALE_REVISION"
            ready = False

        if not root_final_authority:
            contradictions.extend(
                (
                    f"ROOT_NOT_FINAL_BUT_DEPENDENT_EXISTS:{case_type}",
                    f"AUTHORITY_NOT_FINAL:{case_type}",
                )
            )
            stale_reason = "ROOT_NOT_FINAL"
            ready = False

        if delay_hours > max_hours:
            risks.append(f"PROPAGATION_DEADLINE_MISS:{case_type}")
            unknowns.extend(
                (
                    f"DEPENDENCY_OVERDUE:{case_type}",
                    f"DEPENDENCY_CURRENT_STATE_UNCONFIRMED:{case_type}",
                )
            )
            stale_reason = "PROPAGATION_DELAY"
            ready = False

        surfaces.append(
            PropagationSurfaceStateV0(
                event_id=node.event_id,
                fixture_ref=graph.fixture_ref,
                case_type=case_type,
                surface=str(rule["surface"]),
                root_revision=root_revision,
                observed_revision=observed_revision,
                ready=ready,
                final_authority_seen=final_seen,
                propagation_delay_hours=delay_hours,
                stale_reason=stale_reason,
            )
        )

    assessment = PropagationAssessmentV0(
        assessment_id=assessment_id,
        event_date=graph.root.event_date,
        fixture_ref=graph.fixture_ref,
        title=f"Dependency propagation for {graph.fixture_ref}",
        surfaces=tuple(surfaces),
        unknowns=tuple(dict.fromkeys(unknowns)),
        contradictions=tuple(dict.fromkeys(contradictions)),
        risk_flags=tuple(dict.fromkeys(risks)),
        team_id=graph.root.team_id,
    )

    if assessment.silent_inconsistency_count:
        raise ValueError(
            f"SILENT_INCONSISTENCY_DETECTED:{assessment.assessment_id}"
        )
    return assessment


def attack_graph_v0(
    graph: FixtureDependencyGraphV0,
    rules: Mapping[str, Any],
    *,
    mode: str,
    ordinal: int,
) -> PropagationAssessmentV0:
    attack = rules["attack_modes"].get(mode)
    if attack is None:
        raise ValueError(f"UNKNOWN_PROPAGATION_ATTACK_MODE:{mode}")

    root_revision = 2 if ordinal % int(attack["revision_modulo"]) == 0 else 1
    root_final = not (
        root_revision > 1
        and ordinal % int(attack["authority_not_final_modulo"]) == 0
    )
    revisions = {}
    delays = {}
    missing = []

    rule_index = dependency_rule_index_v0(rules)
    for index, node in enumerate(graph.dependents, start=1):
        rule = rule_index.get(node.case_type)
        if rule is None:
            continue
        if (
            root_revision > 1
            and (ordinal + index) % int(attack["missing_surface_modulo"]) == 0
        ):
            missing.append(node.case_type)
            continue

        if root_revision <= 1:
            revisions[node.case_type] = root_revision
            delays[node.case_type] = 0.0
            continue

        if (ordinal + index) % int(attack["ahead_revision_modulo"]) == 0:
            revisions[node.case_type] = root_revision + 1
        elif (ordinal + index) % int(attack["wrong_revision_modulo"]) == 0:
            revisions[node.case_type] = root_revision - 1
        else:
            revisions[node.case_type] = root_revision

        delays[node.case_type] = (
            float(rule["max_propagation_hours"])
            * float(attack["propagation_lag_multiplier"])
            * (1.0 + ((ordinal + index) % 3) / 4.0)
        )

    return assess_revision_state_v0(
        graph=graph,
        rules=rules,
        assessment_id=f"PROP-{mode}-{ordinal:03d}",
        root_revision=root_revision,
        root_final_authority=root_final,
        surface_revisions=revisions,
        surface_delays_hours=delays,
        missing_surfaces=missing,
    )


def annual_propagation_campaign_v0(
    graphs: Iterable[FixtureDependencyGraphV0],
    rules: Mapping[str, Any],
    *,
    mode: str,
) -> dict[str, Any]:
    rows = tuple(
        attack_graph_v0(graph, rules, mode=mode, ordinal=index)
        for index, graph in enumerate(graphs, start=1)
    )
    gate_counts = Counter(row.expected_gate for row in rows)
    risk_counts = Counter(
        risk
        for row in rows
        for risk in row.risk_flags
    )
    unknown_count = sum(len(row.unknowns) for row in rows)
    contradiction_count = sum(len(row.contradictions) for row in rows)
    stale_surface_count = sum(
        1
        for row in rows
        for surface in row.surfaces
        if not surface.ready
    )
    silent = sum(row.silent_inconsistency_count for row in rows)

    return {
        "simulation_status": STATUS,
        "mode": mode,
        "fixture_count": len(rows),
        "gate_counts": dict(sorted(gate_counts.items())),
        "unknown_count": unknown_count,
        "contradiction_count": contradiction_count,
        "stale_or_blocked_surface_count": stale_surface_count,
        "silent_inconsistency_count": silent,
        "risk_counts": dict(sorted(risk_counts.items())),
        "assessment_ids": [row.assessment_id for row in rows],
        "external_action": False,
        "authority": "KX108_ONLY",
    }


def compare_campaigns_v0(
    graphs: Iterable[FixtureDependencyGraphV0],
    rules: Mapping[str, Any],
) -> dict[str, Any]:
    graph_rows = tuple(graphs)
    results = {
        mode: annual_propagation_campaign_v0(
            graph_rows,
            rules,
            mode=mode,
        )
        for mode in ("NORMAL", "HARD", "BREAKER")
    }
    return {
        "simulation_status": STATUS,
        "fixture_count": len(graph_rows),
        "campaigns": results,
        "silent_inconsistency_count": sum(
            row["silent_inconsistency_count"]
            for row in results.values()
        ),
        "external_action": False,
        "authority": "KX108_ONLY",
    }
