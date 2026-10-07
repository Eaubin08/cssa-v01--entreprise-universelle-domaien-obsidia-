#!/usr/bin/env python3
"""Generate the F3F organizational stress audit artifact."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from organizations.cssa.season_simulation import build_full_season_corpus_v0
from organizations.cssa.stress import (
    assess_catalog_v0,
    catalog_summary_v0,
    season_workload_pressure_v0,
)

MODEL = ROOT / "organizations" / "cssa" / "season" / "public_model_v0.json"
RESOURCES = ROOT / "organizations" / "cssa" / "stress" / "resources_v0.json"
CATALOG = ROOT / "organizations" / "cssa" / "stress" / "stress_scenarios_v0.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="generated_stress/f3f_stress_report.json")
    args = parser.parse_args()

    model = load(MODEL)
    resources = load(RESOURCES)
    catalog = load(CATALOG)
    corpus = build_full_season_corpus_v0(model)
    rows = assess_catalog_v0(catalog, resources)

    payload = {
        "catalog": catalog_summary_v0(rows),
        "season_pressure": season_workload_pressure_v0(corpus.events, resources),
        "scenarios": [
            {
                "scenario_id": row.scenario_id,
                "title": row.title,
                "event_date": row.event_date,
                "expected_gate": row.expected_gate,
                "priority_order": list(row.priority_order),
                "unknowns": list(row.unknowns),
                "contradictions": list(row.contradictions),
                "risk_flags": list(row.risk_flags),
                "conflicts": [
                    {
                        "resource_id": c.resource_id,
                        "capacity": c.capacity,
                        "demand": c.demand,
                        "overload": c.overload,
                        "item_ids": list(c.item_ids),
                    }
                    for c in row.conflicts
                ],
            }
            for row in rows
        ],
        "authority": "KX108_ONLY",
        "external_action": False,
        "simulation_status": "SIMULATED_NOT_OBSERVED",
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "out": str(out),
        "scenario_count": payload["catalog"]["scenario_count"],
        "gate_counts": payload["catalog"]["gate_counts"],
        "pressure_point_count": payload["season_pressure"]["pressure_point_count"],
        "authority": payload["authority"],
        "external_action": payload["external_action"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
