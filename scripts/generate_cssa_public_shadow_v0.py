#!/usr/bin/env python3
"""Generate F3G-B CSSA public shadow audit and persona cockpit."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from organizations.cssa.reporting import (
    build_report_pack_v0,
    render_markdown_v0,
    render_persona_markdown_v0,
    report_summary_v0,
)
from organizations.cssa.shadow import (
    build_shadow_reporting_events_v0,
    public_shadow_summary_v0,
)

SNAPSHOT = (
    ROOT
    / "organizations"
    / "cssa"
    / "shadow"
    / "public_snapshot_2026-10-07_v0.json"
)
ROUTING = ROOT / "organizations" / "cssa" / "reporting" / "routing_v0.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def safe_name(value: str) -> str:
    return value.lower().replace("/", "_").replace(" ", "_")


def render_shadow_markdown(summary):
    lines = [
        "# F3G-B CSSA — PUBLIC REALITY SHADOW REPORT",
        "",
        f"As-of: {summary['as_of']}",
        "Status: PUBLIC_SHADOW_EVIDENCE",
        "External action: false",
        "Real internal field evidence: false",
        "",
        "## Public evidence surface",
        "",
        f"- Sources: {summary['source_count']}",
        f"- Observations: {summary['observation_count']}",
        f"- Truth classes: {summary['truth_counts']}",
        f"- Recent multi-team workload observations: {summary['recent_public_workload_count']}",
        "",
        "## Unresolved public conflicts",
        "",
    ]
    for conflict_id in summary["public_conflict_ids"]:
        lines.append(f"- {conflict_id}")

    lines.extend(
        [
            "",
            "## F3G-A blind-spot progress",
            "",
            f"- Public coverage observed: {summary['blind_spot_public_coverage']}",
            f"- Capacity still unknown: {summary['capacity_still_unknown']}",
            "",
            "## Boundary",
            "",
            "- Public evidence is not internal CSSA field evidence.",
            "- Conflicting public values are not auto-reconciled.",
            "- No public observation authorizes an external club action.",
            "- KX108_ONLY remains the decision authority.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="generated_shadow")
    args = parser.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    snapshot = load(SNAPSHOT)
    routing = load(ROUTING)
    summary = public_shadow_summary_v0(snapshot)
    events = build_shadow_reporting_events_v0(snapshot)

    (out / "shadow_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (out / "shadow_report.md").write_text(
        render_shadow_markdown(summary),
        encoding="utf-8",
    )

    as_of = date.fromisoformat(snapshot["as_of"])
    for cadence in ("WEEKLY", "BIWEEKLY", "MONTHLY"):
        pack = build_report_pack_v0(
            events,
            routing,
            cadence=cadence,
            as_of=as_of,
            truth_class=None,
        )
        target = out / cadence.lower()
        persona_dir = target / "personas"
        persona_dir.mkdir(parents=True, exist_ok=True)
        (target / "global.md").write_text(
            render_markdown_v0(pack),
            encoding="utf-8",
        )
        (target / "summary.json").write_text(
            json.dumps(
                report_summary_v0(pack),
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        for persona in sorted(pack.persona_views):
            (persona_dir / f"{safe_name(persona)}.md").write_text(
                render_persona_markdown_v0(pack, persona, routing),
                encoding="utf-8",
            )

    print(
        json.dumps(
            {
                "source_count": summary["source_count"],
                "observation_count": summary["observation_count"],
                "public_conflict_count": summary["public_conflict_count"],
                "recent_public_workload_count": summary["recent_public_workload_count"],
                "blind_spot_public_coverage": summary["blind_spot_public_coverage"],
                "external_action": summary["external_action"],
                "real_internal_field_evidence": summary["real_internal_field_evidence"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
