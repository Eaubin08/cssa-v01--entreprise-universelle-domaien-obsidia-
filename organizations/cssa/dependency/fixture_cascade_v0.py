"""F3I — fixture dependency cascade hardening V0.

The purpose is to prevent one upstream fixture-state change from silently
leaving transport, FMI, ticketing, matchday, partners, communication or proof
bound to an obsolete version.

This layer is non-sovereign. It detects coherence failures and emits governed
assessment packets. It does not update any club system.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Mapping


STATUS = "SIMULATED_NOT_OBSERVED"


@dataclass(frozen=True)
class DependencyNodeStateV0:
    node_id: str
    source_event_id: str
    root_version: int
    node_version: int
    criticality: str
    stale: bool
    missing: bool = False


@dataclass(frozen=True)
class VersionTransitionAssessmentV0:
    current_version: int
    incoming_version: int
    allowed: bool
    expected_gate: str
    unknowns: tuple[str, ...]
    contradictions: tuple[str, ...]
    risk_flags: tuple[str, ...]


def validate_state_transition_v0(
    *,
    current_version: int,
    current_fingerprint: str,
    incoming_version: int,
    incoming_fingerprint: str,
) -> VersionTransitionAssessmentV0:
    if current_version < 0 or incoming_version < 0:
        raise ValueError("VERSION_MUST_BE_NONNEGATIVE")

    unknowns: list[str] = []
    contradictions: list[str] = []
    risks: list[str] = []

    if incoming_version < current_version:
        contradictions.extend((
            "OUT_OF_ORDER_VERSION_ROLLBACK",
            "INCOMING_STATE_OLDER_THAN_CURRENT",
        ))
        risks.append("VERSION_ROLLBACK_REJECTED")
    elif (
        incoming_version == current_version
        and incoming_fingerprint != current_fingerprint
    ):
        contradictions.extend((
            "SAME_VERSION_DIFFERENT_VALUE",
            "VERSION_IDENTITY_COLLISION",
        ))
        risks.append("DUPLICATE_VERSION_CONFLICT")
    elif incoming_version > current_version + 1:
        unknowns.extend((
            "INTERMEDIATE_VERSION_MISSING",
            "VERSION_GAP_PROVENANCE_UNKNOWN",
        ))
        risks.append("VERSION_GAP_REQUIRES_REVIEW")

    gate = (
        "BLOCK"
        if len(contradictions) >= 2
        else "HOLD"
        if len(unknowns) > 1
        else "ALLOW"
    )
    return VersionTransitionAssessmentV0(
        current_version=current_version,
        incoming_version=incoming_version,
        allowed=gate == "ALLOW",
        expected_gate=gate,
        unknowns=tuple(unknowns),
        contradictions=tuple(contradictions),
        risk_flags=tuple(risks),
    )


@dataclass(frozen=True)
class CascadeAssessmentV0:
    event_id: str
    event_date: str
    family: str
    case_type: str
    fixture_ref: str
    team_id: str | None
    root_version: int
    nodes: tuple[DependencyNodeStateV0, ...]
    stale_nodes: tuple[str, ...]
    missing_nodes: tuple[str, ...]
    order_violations: tuple[str, ...]
    receipt_mismatch: bool
    root_conflict: bool
    unknowns: tuple[str, ...]
    contradictions: tuple[str, ...]
    risk_flags: tuple[str, ...]
    propagation_completeness: float
    simulation_status: str = STATUS

    @property
    def expected_gate(self) -> str:
        if len(self.contradictions) >= 2:
            return "BLOCK"
        if len(self.unknowns) > 1:
            return "HOLD"
        return "ALLOW"

    @property
    def expected_provider_invoked(self) -> bool:
        return self.expected_gate == "ALLOW"

    @property
    def source_ids(self) -> tuple[str, ...]:
        refs = [f"sim:cascade-root:{self.fixture_ref}"]
        refs.extend(f"sim:cascade-node:{node.source_event_id}" for node in self.nodes)
        return tuple(dict.fromkeys(refs))

    def to_runtime_mapping(self, *, confidence: float = 0.92) -> dict[str, Any]:
        return {
            "case_ref": f"cssa-cascade:{self.fixture_ref}:{self.event_id}",
            "valid_at": f"{self.event_date}T12:00:00Z",
            "source_ref": f"cssa-cascade-source:{self.fixture_ref}",
            "unknowns": self.unknowns,
            "contradictions": self.contradictions,
            "risk_flags": self.risk_flags,
            "evidence_refs": self.source_ids,
            "provenance_refs": ("F3I_SIMULATION_ONLY",),
            "confidence": float(confidence),
            "simulation_status": self.simulation_status,
            "fixture_ref": self.fixture_ref,
            "root_version": self.root_version,
            "stale_nodes": self.stale_nodes,
            "missing_nodes": self.missing_nodes,
            "propagation_completeness": self.propagation_completeness,
        }


def _fixture_ref(event: Any) -> str | None:
    for ref in getattr(event, "target_refs", ()):
        if str(ref).startswith("fixture:"):
            return str(ref)
    return None


def build_fixture_dependency_index_v0(
    events: Iterable[Any],
    graph: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    node_types = graph["node_types"]
    groups: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"root": None, "nodes": []}
    )

    for event in events:
        fixture_ref = _fixture_ref(event)
        if fixture_ref is None:
            continue
        if event.case_type == graph["root"]["case_type"]:
            if groups[fixture_ref]["root"] is not None:
                raise ValueError(f"DUPLICATE_FIXTURE_ROOT:{fixture_ref}")
            groups[fixture_ref]["root"] = event
        elif event.case_type in node_types:
            groups[fixture_ref]["nodes"].append(event)

    orphaned = [
        fixture_ref
        for fixture_ref, row in groups.items()
        if row["root"] is None and row["nodes"]
    ]
    if orphaned:
        raise ValueError(f"ORPHAN_DEPENDENCY_GROUPS:{sorted(orphaned)[:5]}")

    return {
        fixture_ref: {
            "root": row["root"],
            "nodes": tuple(
                sorted(row["nodes"], key=lambda event: event.event_id)
            ),
        }
        for fixture_ref, row in sorted(groups.items())
        if row["root"] is not None
    }


def _node_id(event: Any, graph: Mapping[str, Any]) -> str:
    return str(graph["node_types"][event.case_type]["id"])


def _node_criticality(event: Any, graph: Mapping[str, Any]) -> str:
    return str(graph["node_types"][event.case_type]["criticality"])


def _attack_plan(
    *,
    ordinal: int,
    mode: Mapping[str, Any],
    node_ids: tuple[str, ...],
) -> dict[str, Any]:
    changed = ordinal % int(mode["change_every"]) == 0
    if not changed:
        return {
            "changed": False,
            "root_conflict": False,
            "stale_nodes": (),
            "receipt_stale": False,
            "missing_node": None,
            "order_violation": None,
        }

    root_conflict_every = int(mode.get("root_conflict_every", 0))
    root_conflict = (
        root_conflict_every > 0
        and ordinal % root_conflict_every == 0
    )

    stale: list[str] = []
    multi_every = int(mode.get("multi_stale_every", 0))
    single_every = int(mode.get("single_stale_every", 0))

    if multi_every > 0 and ordinal % multi_every == 0 and node_ids:
        stale.extend(node_ids[: min(3, len(node_ids))])
    elif single_every > 0 and ordinal % single_every == 0 and node_ids:
        stale.append(node_ids[0])

    receipt_every = int(mode.get("receipt_stale_every", 0))
    receipt_stale = receipt_every > 0 and ordinal % receipt_every == 0

    missing_every = int(mode.get("missing_node_every", 0))
    missing_node = (
        node_ids[-1]
        if missing_every > 0
        and ordinal % missing_every == 0
        and node_ids
        else None
    )

    order_every = int(mode.get("order_violation_every", 0))
    order_violation = (
        node_ids[0]
        if order_every > 0
        and ordinal % order_every == 0
        and node_ids
        else None
    )

    return {
        "changed": True,
        "root_conflict": root_conflict,
        "stale_nodes": tuple(dict.fromkeys(stale)),
        "receipt_stale": receipt_stale,
        "missing_node": missing_node,
        "order_violation": order_violation,
    }


def assess_fixture_cascade_v0(
    fixture_ref: str,
    row: Mapping[str, Any],
    graph: Mapping[str, Any],
    *,
    ordinal: int,
    mode_name: str,
) -> CascadeAssessmentV0:
    mode = graph["campaign_modes"].get(mode_name)
    if mode is None:
        raise ValueError(f"UNKNOWN_CASCADE_MODE:{mode_name}")

    root = row["root"]
    node_events = tuple(row["nodes"])
    node_ids = tuple(
        _node_id(event, graph)
        for event in node_events
    )
    attack = _attack_plan(
        ordinal=ordinal,
        mode=mode,
        node_ids=node_ids,
    )

    root_version = 2 if attack["changed"] else 1
    stale_targets = set(attack["stale_nodes"])

    nodes: list[DependencyNodeStateV0] = []
    missing_nodes: list[str] = []
    for event in node_events:
        node_id = _node_id(event, graph)
        if node_id == attack["missing_node"]:
            missing_nodes.append(node_id)
            continue
        node_version = (
            root_version - 1
            if node_id in stale_targets
            else root_version
        )
        nodes.append(
            DependencyNodeStateV0(
                node_id=node_id,
                source_event_id=event.event_id,
                root_version=root_version,
                node_version=node_version,
                criticality=_node_criticality(event, graph),
                stale=node_version != root_version,
            )
        )

    # Proof receipt is always required virtually.
    receipt_version = (
        root_version - 1
        if attack["receipt_stale"]
        else root_version
    )
    nodes.append(
        DependencyNodeStateV0(
            node_id="PROOF_RECEIPT",
            source_event_id=f"virtual-proof:{fixture_ref}",
            root_version=root_version,
            node_version=receipt_version,
            criticality="HIGH",
            stale=receipt_version != root_version,
        )
    )

    stale_nodes = tuple(
        node.node_id for node in nodes if node.stale
    )
    order_violations = (
        (str(attack["order_violation"]),)
        if attack["order_violation"] is not None
        else ()
    )
    contradictions: list[str] = []
    unknowns: list[str] = []
    risks: list[str] = []

    if attack["root_conflict"]:
        contradictions.extend(
            (
                f"ROOT_FIXTURE_STATE_CONFLICT:{fixture_ref}",
                f"ROOT_PROVENANCE_CONFLICT:{fixture_ref}",
            )
        )
        risks.append("UPSTREAM_ROOT_UNRESOLVED")

    operational_stale = tuple(
        node_id for node_id in stale_nodes
        if node_id != "PROOF_RECEIPT"
    )
    if len(operational_stale) >= 2:
        contradictions.extend(
            (
                f"MULTI_LAYER_STALE_STATE:{fixture_ref}",
                f"PROPAGATION_SPLIT_BRAIN:{fixture_ref}",
            )
        )
        risks.append("MULTIPLE_DEPENDENTS_ON_OLD_FIXTURE_VERSION")
    elif len(operational_stale) == 1:
        unknowns.extend(
            (
                f"DEPENDENT_REVALIDATION_REQUIRED:{operational_stale[0]}",
                f"PROPAGATION_COMPLETION_UNKNOWN:{fixture_ref}",
            )
        )
        risks.append("SINGLE_STALE_DEPENDENT")

    if missing_nodes:
        unknowns.extend((
            f"REQUIRED_DEPENDENT_MISSING:{missing_nodes[0]}",
            f"PROPAGATION_NODE_COMPLETENESS_UNKNOWN:{fixture_ref}",
        ))
        risks.append("REQUIRED_DEPENDENT_MISSING")

    if order_violations:
        unknowns.extend((
            f"DEPENDENCY_ORDER_VIOLATION:{order_violations[0]}",
            f"PREDECESSOR_CONFIRMATION_UNKNOWN:{fixture_ref}",
        ))
        risks.append("PROPAGATION_ORDER_NOT_PROVEN")

    receipt_mismatch = "PROOF_RECEIPT" in stale_nodes
    if receipt_mismatch:
        unknowns.extend(
            (
                f"PROOF_RECEIPT_VERSION_MISMATCH:{fixture_ref}",
                f"PROPAGATION_PROOF_INCOMPLETE:{fixture_ref}",
            )
        )
        risks.append("PROOF_NOT_BOUND_TO_CURRENT_ROOT_VERSION")

    total_nodes = len(nodes) + len(missing_nodes)
    current_nodes = sum(1 for node in nodes if not node.stale)
    completeness = (
        1.0 if total_nodes == 0 else round(current_nodes / total_nodes, 4)
    )

    return CascadeAssessmentV0(
        event_id=f"CASCADE-{mode_name}-{ordinal:03d}",
        event_date=root.event_date,
        family="DEPENDENCY_CASCADE",
        case_type="fixture_dependency_cascade",
        fixture_ref=fixture_ref,
        team_id=getattr(root, "team_id", None),
        root_version=root_version,
        nodes=tuple(nodes),
        stale_nodes=stale_nodes,
        missing_nodes=tuple(missing_nodes),
        order_violations=tuple(order_violations),
        receipt_mismatch=receipt_mismatch,
        root_conflict=bool(attack["root_conflict"]),
        unknowns=tuple(dict.fromkeys(unknowns)),
        contradictions=tuple(dict.fromkeys(contradictions)),
        risk_flags=tuple(dict.fromkeys(risks)),
        propagation_completeness=completeness,
    )


def run_cascade_campaign_v0(
    events: Iterable[Any],
    graph: Mapping[str, Any],
    *,
    mode_name: str,
) -> tuple[CascadeAssessmentV0, ...]:
    index = build_fixture_dependency_index_v0(events, graph)
    return tuple(
        assess_fixture_cascade_v0(
            fixture_ref,
            row,
            graph,
            ordinal=ordinal,
            mode_name=mode_name,
        )
        for ordinal, (fixture_ref, row) in enumerate(
            index.items(),
            start=1,
        )
    )


def cascade_summary_v0(
    assessments: Iterable[CascadeAssessmentV0],
) -> dict[str, Any]:
    rows = tuple(assessments)
    gates = Counter(row.expected_gate for row in rows)
    changed = [row for row in rows if row.root_version > 1]
    failed = [row for row in rows if row.expected_gate != "ALLOW"]
    stale_counter = Counter(
        node
        for row in rows
        for node in row.stale_nodes
    )
    completeness = [
        row.propagation_completeness
        for row in changed
    ]

    return {
        "status": STATUS,
        "fixture_count": len(rows),
        "changed_fixture_count": len(changed),
        "failure_count": len(failed),
        "gate_counts": dict(sorted(gates.items())),
        "root_conflict_count": sum(1 for row in rows if row.root_conflict),
        "receipt_mismatch_count": sum(
            1 for row in rows if row.receipt_mismatch
        ),
        "missing_node_count": sum(
            len(row.missing_nodes) for row in rows
        ),
        "order_violation_count": sum(
            len(row.order_violations) for row in rows
        ),
        "stale_node_counts": dict(sorted(stale_counter.items())),
        "mean_changed_propagation_completeness": (
            round(sum(completeness) / len(completeness), 4)
            if completeness else 1.0
        ),
        "silent_stale_allow_count": sum(
            1
            for row in rows
            if row.stale_nodes and row.expected_gate == "ALLOW"
        ),
        "external_action": False,
        "authority": "KX108_ONLY",
    }
