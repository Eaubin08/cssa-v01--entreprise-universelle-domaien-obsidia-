#!/usr/bin/env python3
"""Generate F3G-A adversarial sensitivity/calibration-prep artifacts."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from organizations.cssa.calibration import adversarial_summary_v0
from organizations.cssa.season_simulation import build_full_season_corpus_v0

MODEL = ROOT / "organizations" / "cssa" / "season" / "public_model_v0.json"
RESOURCES = ROOT / "organizations" / "cssa" / "stress" / "resources_v0.json"
CATALOG = ROOT / "organizations" / "cssa" / "stress" / "stress_scenarios_v0.json"
SPACE = ROOT / "organizations" / "cssa" / "calibration" / "sensitivity_space_v0.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def render_markdown(summary):
    lines = [
        "# F3G-A CSSA — ADVERSARIAL SENSITIVITY REPORT",
        "",
        "Status: SIMULATED_NOT_OBSERVED",
        "Authority: KX108_ONLY",
        "External action: false",
        "",
        "## Attack surface",
        "",
        f"- Exhaustive resource profiles: {summary['resource_grid']['profile_count']}",
        f"- Exhaustive assumption states: {summary['assumption_grid']['profile_count']}",
        f"- Resource-fragile scenarios: {', '.join(summary['resource_grid']['resource_fragile_scenarios'])}",
        "",
        "## Named operating envelopes",
        "",
    ]
    for row in summary["named_profiles"]:
        lines.append(
            f"- {row['profile_id']}: gates={row['gate_counts']} conflicts={row['resource_conflict_count']}"
        )

    lines.extend(["", "## Highest-value field calibration questions", ""])
    for index, row in enumerate(summary["calibration_priorities"][:10], start=1):
        lines.append(
            f"{index}. {row['calibration_id']} ({row['kind']}) — "
            f"gate_flips={row['scenario_gate_flip_count']} "
            f"pressure_range={row['pressure_point_range']}"
        )
        lines.append(f"   - {row['field_question']}")

    lines.extend(
        [
            "",
            "## Interpretation rule",
            "",
            "- Resource relief cannot repair stale truth or missing authority.",
            "- Extreme values are attack inputs, not CSSA facts.",
            "- Calibration should target parameters that actually change gates or pressure.",
            "- No profile authorizes external action.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out-dir",
        default="generated_sensitivity",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    corpus = build_full_season_corpus_v0(load(MODEL))
    summary = adversarial_summary_v0(
        load(CATALOG),
        load(RESOURCES),
        load(SPACE),
        corpus.events,
    )

    (out_dir / "f3g_a_sensitivity.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (out_dir / "f3g_a_sensitivity.md").write_text(
        render_markdown(summary),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "resource_profiles": summary["resource_grid"]["profile_count"],
                "assumption_profiles": summary["assumption_grid"]["profile_count"],
                "resource_fragile_scenarios": summary["resource_grid"]["resource_fragile_scenarios"],
                "top_calibration_target": summary["calibration_priorities"][0]["calibration_id"],
                "authority": summary["authority"],
                "external_action": summary["external_action"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
