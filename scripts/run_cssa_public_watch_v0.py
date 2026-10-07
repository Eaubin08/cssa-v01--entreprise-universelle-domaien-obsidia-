#!/usr/bin/env python3
"""Run the CSSA GET-only public source watch and generate review artifacts."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from organizations.cssa.reporting import (
    build_report_pack_v0,
    due_cadences_v0,
    render_markdown_v0,
    render_persona_markdown_v0,
    report_summary_v0,
)
from organizations.cssa.watch import (
    capture_source_v0,
    compare_capture_sets_v0,
    delta_to_signal_v0,
    due_sources_v0,
    watch_summary_v0,
)


WATCHLIST = ROOT / "organizations" / "cssa" / "watch" / "watchlist_v0.json"
ROUTING = ROOT / "organizations" / "cssa" / "reporting" / "routing_v0.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def safe_name(value: str) -> str:
    return value.lower().replace("/", "_").replace(" ", "_")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", default=date.today().isoformat())
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--previous")
    parser.add_argument("--state-dir", default="watch_state")
    parser.add_argument("--out-dir", default="generated_watch")
    args = parser.parse_args()

    as_of = date.fromisoformat(args.as_of)
    watchlist = load(WATCHLIST)
    routing = load(ROUTING)

    previous_rows = []
    if args.previous:
        previous_path = Path(args.previous)
        if previous_path.exists():
            previous_rows = load(previous_path).get("captures", [])

    previous_by_id = {
        row["source_id"]: row
        for row in previous_rows
    }

    sources = (
        tuple(watchlist["sources"])
        if args.all
        else due_sources_v0(watchlist, as_of=as_of)
    )

    current_due = [
        capture_source_v0(
            source,
            observed_at=as_of.isoformat(),
        )
        for source in sources
    ]

    deltas = compare_capture_sets_v0(
        previous_rows,
        current_due,
    )
    signals = tuple(
        signal
        for delta in deltas
        if (signal := delta_to_signal_v0(delta)) is not None
    )

    merged_state = dict(previous_by_id)
    for row in current_due:
        merged_state[row["source_id"]] = row

    state_dir = Path(args.state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / "latest_capture.json"
    state_path.write_text(
        json.dumps(
            {
                "as_of": as_of.isoformat(),
                "captures": [
                    merged_state[key]
                    for key in sorted(merged_state)
                ],
                "external_action": False,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = watch_summary_v0(deltas)
    (out_dir / "watch_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (out_dir / "watch_deltas.json").write_text(
        json.dumps(list(deltas), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    cadences = (
        ("WEEKLY", "BIWEEKLY", "MONTHLY")
        if args.all
        else due_cadences_v0(as_of)
    )
    for cadence in cadences:
        pack = build_report_pack_v0(
            signals,
            routing,
            cadence=cadence,
            as_of=as_of,
            truth_class=None,
        )
        target = out_dir / cadence.lower()
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
                "as_of": as_of.isoformat(),
                "sources_due": len(sources),
                "deltas": len(deltas),
                "signals": len(signals),
                "status_counts": summary["status_counts"],
                "state_path": str(state_path),
                "external_action": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
