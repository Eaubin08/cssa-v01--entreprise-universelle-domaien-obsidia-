#!/usr/bin/env python3
"""Generate F3I annual fixture dependency-cascade failure artifacts."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from organizations.cssa.annual import build_one_year_corpus_v0
from organizations.cssa.dependency import (
    cascade_summary_v0,
    run_cascade_campaign_v0,
)


MODEL = ROOT / "organizations" / "cssa" / "season" / "public_model_v0.json"
GRAPH = (
    ROOT
    / "organizations"
    / "cssa"
    / "dependency"
    / "fixture_dependency_graph_v0.json"
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def render_markdown(summaries, rows_by_mode):
    lines = [
        "# CSSA — F3I DEPENDENCY CASCADE HARDENING V0",
        "",
        "Scope: all 330 season fixture roots inside the 365-day annual corpus",
        "Truth: SIMULATED_NOT_OBSERVED",
        "Authority: KX108_ONLY",
        "External action: false",
        "",
        "## Campaign matrix",
        "",
        "| Mode | Changed fixtures | Failures | ALLOW | HOLD | BLOCK | Root conflicts | Receipt mismatch | Mean propagation |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for mode in ("NORMAL", "HARD", "BREAKER"):
        summary = summaries[mode]
        gates = summary["gate_counts"]
        lines.append(
            f"| {mode} | {summary['changed_fixture_count']} | "
            f"{summary['failure_count']} | {gates.get('ALLOW', 0)} | "
            f"{gates.get('HOLD', 0)} | {gates.get('BLOCK', 0)} | "
            f"{summary['root_conflict_count']} | "
            f"{summary['receipt_mismatch_count']} | "
            f"{summary['mean_changed_propagation_completeness']:.4f} |"
        )

    aggregate_stale = Counter()
    for mode in rows_by_mode:
        for row in rows_by_mode[mode]:
            aggregate_stale.update(row.stale_nodes)

    lines.extend(
        [
            "",
            "## Stale-node exposure across campaigns",
            "",
        ]
    )
    for node, count in aggregate_stale.most_common():
        lines.append(f"- {node}: {count}")

    lines.extend(
        [
            "",
            "## Invariant",
            "",
            "- stale dependent state must never remain ALLOW;",
            "- one stale dependent becomes HOLD/revalidation;",
            "- multiple stale operational layers become BLOCK/split-brain;",
            "- unresolved root conflict becomes BLOCK;",
            "- proof receipt bound to old root version becomes HOLD;",
            "- full current-version propagation can ALLOW;",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="generated_dependency")
    args = parser.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    events = build_one_year_corpus_v0(load(MODEL))
    graph = load(GRAPH)

    rows_by_mode = {
        mode: run_cascade_campaign_v0(
            events,
            graph,
            mode_name=mode,
        )
        for mode in ("NORMAL", "HARD", "BREAKER")
    }
    summaries = {
        mode: cascade_summary_v0(rows)
        for mode, rows in rows_by_mode.items()
    }

    payload = {
        "summaries": summaries,
        "failures": {
            mode: [
                {
                    "event_id": row.event_id,
                    "event_date": row.event_date,
                    "fixture_ref": row.fixture_ref,
                    "team_id": row.team_id,
                    "root_version": row.root_version,
                    "expected_gate": row.expected_gate,
                    "stale_nodes": list(row.stale_nodes),
                    "root_conflict": row.root_conflict,
                    "receipt_mismatch": row.receipt_mismatch,
                    "unknowns": list(row.unknowns),
                    "contradictions": list(row.contradictions),
                    "risk_flags": list(row.risk_flags),
                    "propagation_completeness": row.propagation_completeness,
                }
                for row in rows
                if row.expected_gate != "ALLOW"
            ]
            for mode, rows in rows_by_mode.items()
        },
        "authority": "KX108_ONLY",
        "external_action": False,
        "truth_class": "SIMULATED_NOT_OBSERVED",
    }

    (out / "dependency_cascade_matrix.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (out / "dependency_cascade_report.md").write_text(
        render_markdown(summaries, rows_by_mode),
        encoding="utf-8",
    )

    print(json.dumps({
        "fixture_count": summaries["NORMAL"]["fixture_count"],
        "normal": summaries["NORMAL"],
        "hard": summaries["HARD"],
        "breaker": summaries["BREAKER"],
        "authority": "KX108_ONLY",
        "external_action": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
