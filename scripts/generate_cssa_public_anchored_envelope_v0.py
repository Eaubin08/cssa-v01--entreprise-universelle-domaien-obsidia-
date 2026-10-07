#!/usr/bin/env python3
"""Generate F3G-C public-anchored estimated operating envelope artifacts."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from organizations.cssa.estimation import robust_vs_fragile_v0
from organizations.cssa.season_simulation import build_full_season_corpus_v0

MODEL = ROOT / "organizations" / "cssa" / "season" / "public_model_v0.json"
RESOURCES = ROOT / "organizations" / "cssa" / "stress" / "resources_v0.json"
CATALOG = ROOT / "organizations" / "cssa" / "stress" / "stress_scenarios_v0.json"
ENVELOPE = (
    ROOT
    / "organizations"
    / "cssa"
    / "estimation"
    / "public_anchored_envelope_v0.json"
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def render_markdown(result):
    lines = [
        "# F3G-C CSSA — PUBLIC-ANCHORED OPERATING ENVELOPE",
        "",
        "Status: ESTIMATED_PUBLIC_ANCHORED",
        "Truth class: ESTIMATED",
        "External action: false",
        "",
        "## Profiles",
        "",
    ]
    for row in result["profiles"]:
        lines.append(
            f"- {row['profile_id']}: gates={row['gate_counts']} "
            f"conflicts={row['resource_conflict_count']} "
            f"season_pressure={row['season_pressure_point_count']} "
            f"blind_spot_pressure={row['blind_spot_pressure']}"
        )

    lines.extend(
        [
            "",
            "## Still unknown",
            "",
        ]
    )
    for unknown in result["assumptions_kept_unknown"]:
        lines.append(f"- {unknown}")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- These are replaceable simulation envelopes, not CSSA headcounts/accounts.",
            "- Public anchors constrain the model but do not manufacture private facts.",
            "- Later field evidence replaces parameter values without changing the governance architecture.",
            "- KX108_ONLY remains unchanged.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="generated_estimation")
    args = parser.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    corpus = build_full_season_corpus_v0(load(MODEL))
    result = robust_vs_fragile_v0(
        load(ENVELOPE),
        load(RESOURCES),
        load(CATALOG),
        corpus.events,
    )

    (out / "public_anchored_envelope.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (out / "public_anchored_envelope.md").write_text(
        render_markdown(result),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "profiles": {
                    row["profile_id"]: {
                        "gate_counts": row["gate_counts"],
                        "resource_conflict_count": row["resource_conflict_count"],
                        "season_pressure_point_count": row["season_pressure_point_count"],
                        "blind_spot_pressure": row["blind_spot_pressure"],
                    }
                    for row in result["profiles"]
                },
                "unknown_count": len(result["assumptions_kept_unknown"]),
                "public_anchor_count": result["public_anchor_count"],
                "replaceable_parameter_count": result["replaceable_parameter_count"],
                "authority": result["authority"],
                "external_action": result["external_action"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
