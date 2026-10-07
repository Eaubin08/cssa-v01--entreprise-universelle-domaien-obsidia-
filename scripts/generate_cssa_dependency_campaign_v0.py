#!/usr/bin/env python3
"""Generate F3I annual dependency-propagation hardening artifacts."""
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
    build_fixture_dependency_graphs_v0,
    compare_campaigns_v0,
    validate_graph_coverage_v0,
)

MODEL = ROOT / "organizations" / "cssa" / "season" / "public_model_v0.json"
RULES = ROOT / "organizations" / "cssa" / "dependency" / "dependency_rules_v0.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def render_markdown(payload):
    lines = [
        "# CSSA — F3I DEPENDENCY PROPAGATION CAMPAIGN V0",
        "",
        "Truth: SIMULATED_NOT_OBSERVED",
        "Authority: KX108_ONLY",
        "External action: false",
        "",
        "## Graph coverage",
        "",
        f"- Fixture roots: {payload['coverage']['fixture_count']}",
        f"- Dependency edges/surfaces: {payload['coverage']['dependency_count']}",
        f"- Missing required: {len(payload['coverage']['missing_required'])}",
        f"- Unruled case types: {len(payload['coverage']['unruled_case_types'])}",
        "",
        "## Annual propagation attacks",
        "",
        "| Mode | ALLOW | HOLD | BLOCK | stale/blocked surfaces | silent inconsistencies |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for mode in ("NORMAL", "HARD", "BREAKER"):
        row = payload["campaigns"]["campaigns"][mode]
        gates = row["gate_counts"]
        lines.append(
            f"| {mode} | {gates.get('ALLOW',0)} | {gates.get('HOLD',0)} | "
            f"{gates.get('BLOCK',0)} | {row['stale_or_blocked_surface_count']} | "
            f"{row['silent_inconsistency_count']} |"
        )

    lines.extend(
        [
            "",
            "## Core invariant",
            "",
            f"Silent inconsistency total: {payload['campaigns']['silent_inconsistency_count']}",
            "",
            "A dependent surface is never marked ready when:",
            "- it is behind the root revision;",
            "- it is ahead of the root revision;",
            "- the root authority is not final;",
            "- its propagation deadline is exceeded;",
            "- the required dependent surface is missing.",
            "",
            "## Interpretation",
            "",
            "- HOLD/BLOCK here are synthetic governance outcomes, not real CSSA incidents.",
            "- The campaign attacks dependency coherence across the 330 fixture roots.",
            "- The important target is silent_inconsistency_count == 0.",
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
    graphs = build_fixture_dependency_graphs_v0(events)
    rules = load(RULES)
    coverage = validate_graph_coverage_v0(graphs, rules)
    campaigns = compare_campaigns_v0(graphs, rules)

    payload = {
        "coverage": coverage,
        "campaigns": campaigns,
        "authority": "KX108_ONLY",
        "external_action": False,
    }

    (out / "f3i_dependency_campaign.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (out / "f3i_dependency_campaign.md").write_text(
        render_markdown(payload),
        encoding="utf-8",
    )

    print(json.dumps({
        "fixture_count": coverage["fixture_count"],
        "dependency_count": coverage["dependency_count"],
        "missing_required": len(coverage["missing_required"]),
        "campaigns": {
            mode: {
                "gate_counts": campaigns["campaigns"][mode]["gate_counts"],
                "stale_or_blocked_surface_count": campaigns["campaigns"][mode]["stale_or_blocked_surface_count"],
                "silent_inconsistency_count": campaigns["campaigns"][mode]["silent_inconsistency_count"],
            }
            for mode in ("NORMAL", "HARD", "BREAKER")
        },
        "silent_inconsistency_total": campaigns["silent_inconsistency_count"],
        "authority": "KX108_ONLY",
        "external_action": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
