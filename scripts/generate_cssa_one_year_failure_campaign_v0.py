#!/usr/bin/env python3
"""Generate the 365-day CSSA soak/failure campaign matrix."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from organizations.cssa.annual import (
    build_one_year_corpus_v0,
    compare_run_matrix_v0,
    failure_summary_v0,
    run_one_year_soak_v0,
)
from organizations.cssa.estimation import build_profile_resources_v0


MODEL = ROOT / "organizations" / "cssa" / "season" / "public_model_v0.json"
RESOURCES = ROOT / "organizations" / "cssa" / "stress" / "resources_v0.json"
ENVELOPE = (
    ROOT
    / "organizations"
    / "cssa"
    / "estimation"
    / "public_anchored_envelope_v0.json"
)
ATTACKS = (
    ROOT
    / "organizations"
    / "cssa"
    / "annual"
    / "annual_attack_profiles_v0.json"
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def render_markdown(matrix, runs):
    lines = [
        "# CSSA — ONE YEAR SOAK / FAILURE CAMPAIGN V0",
        "",
        "Horizon: 2026-08-01 -> 2027-07-31 (365 days)",
        "Truth: SIMULATED_NOT_OBSERVED",
        "Authority: KX108_ONLY",
        "External action: false",
        "",
        "## Matrix",
        "",
        "| Profile | Attack | Completed | Pending | Fail signals | Max backlog | Max age |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]

    for result in runs:
        summary = failure_summary_v0(result)
        lines.append(
            f"| {summary['profile_id']} | {summary['attack_mode']} | "
            f"{summary['completed_case_count']} | {summary['pending_case_count']} | "
            f"{summary['failure_signal_count']} | {summary['max_backlog']} | "
            f"{summary['max_case_age_days']} |"
        )

    lines.extend(
        [
            "",
            f"Best by failure count: {matrix['best_by_failure_count']}",
            f"Worst by failure count: {matrix['worst_by_failure_count']}",
            "",
            "## Failure types across all runs",
            "",
        ]
    )
    aggregate = Counter()
    for result in runs:
        aggregate.update(
            signal.failure_type for signal in result.failure_signals
        )
    for failure_type, count in aggregate.most_common():
        lines.append(f"- {failure_type}: {count}")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- These are synthetic failure signals, not observed CSSA incidents.",
            "- The useful output is where failures accumulate, persist or recover.",
            "- A passing test suite does not mean the simulated organization had no failures.",
            "- The campaign deliberately records failures while preserving governance invariants.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="generated_one_year")
    args = parser.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    model = load(MODEL)
    base_resources = load(RESOURCES)
    envelope = load(ENVELOPE)
    attacks = load(ATTACKS)
    events = build_one_year_corpus_v0(model)

    runs = []
    for profile_id in ("LOW_CONSTRAINED", "CENTRAL_WORKING", "HIGH_CAPACITY"):
        resources = build_profile_resources_v0(
            envelope,
            base_resources,
            profile_id,
        )
        for attack_mode in ("NORMAL", "HARD", "BREAKER"):
            runs.append(
                run_one_year_soak_v0(
                    events=events,
                    resources=resources,
                    attack_profiles=attacks,
                    profile_id=profile_id,
                    attack_mode=attack_mode,
                )
            )

    matrix = compare_run_matrix_v0(runs)
    payload = {
        "matrix": matrix,
        "runs": [
            {
                "summary": failure_summary_v0(result),
                "monthly_travel_costs": dict(result.monthly_travel_costs),
                "failure_signals": [
                    {
                        "day": signal.day,
                        "failure_type": signal.failure_type,
                        "severity": signal.severity,
                        "case_id": signal.case_id,
                        "resource_id": signal.resource_id,
                        "detail": signal.detail,
                        "truth_class": signal.truth_class,
                    }
                    for signal in result.failure_signals
                ],
            }
            for result in runs
        ],
    }

    (out / "one_year_failure_matrix.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (out / "one_year_failure_report.md").write_text(
        render_markdown(matrix, runs),
        encoding="utf-8",
    )

    print(json.dumps({
        "horizon_days": 365,
        "input_event_count": len(events),
        "run_count": len(runs),
        "best": matrix["best_by_failure_count"],
        "worst": matrix["worst_by_failure_count"],
        "runs": [
            {
                "profile": row.profile_id,
                "attack": row.attack_mode,
                "failures": len(row.failure_signals),
                "pending": row.pending_case_count,
                "max_backlog": row.max_backlog,
                "max_age": row.max_case_age_days,
                "failure_types": failure_summary_v0(row)["failure_types"],
            }
            for row in runs
        ],
        "authority": "KX108_ONLY",
        "external_action": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
