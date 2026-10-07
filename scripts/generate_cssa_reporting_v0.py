#!/usr/bin/env python3
"""Generate CSSA internal reporting artifacts from the synthetic season corpus.

V0 output is file-only. No external delivery.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from organizations.cssa.reporting import (
    build_report_pack_v0,
    due_cadences_v0,
    render_markdown_v0,
    render_persona_markdown_v0,
    report_summary_v0,
)
from organizations.cssa.season_simulation import build_full_season_corpus_v0


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_MODEL = ROOT / "organizations" / "cssa" / "season" / "public_model_v0.json"
ROUTING = ROOT / "organizations" / "cssa" / "reporting" / "routing_v0.json"


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_filename(value: str) -> str:
    return value.lower().replace("/", "_").replace(" ", "_")


def generate_for_cadence(
    *,
    cadence: str,
    as_of: date,
    out_dir: Path,
) -> Path:
    model = _load_json(PUBLIC_MODEL)
    routing = _load_json(ROUTING)
    corpus = build_full_season_corpus_v0(model)

    pack = build_report_pack_v0(
        corpus.events,
        routing,
        cadence=cadence,
        as_of=as_of,
        truth_class="SIMULATED_NOT_OBSERVED",
    )

    target = out_dir / as_of.isoformat() / cadence.lower()
    persona_dir = target / "personas"
    persona_dir.mkdir(parents=True, exist_ok=True)

    (target / "global.md").write_text(
        render_markdown_v0(pack),
        encoding="utf-8",
    )
    (target / "summary.json").write_text(
        json.dumps(report_summary_v0(pack), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    for persona in sorted(pack.persona_views):
        (persona_dir / f"{_safe_filename(persona)}.md").write_text(
            render_persona_markdown_v0(pack, persona, routing),
            encoding="utf-8",
        )

    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", default=date.today().isoformat())
    parser.add_argument(
        "--cadence",
        choices=("WEEKLY", "BIWEEKLY", "MONTHLY"),
        action="append",
    )
    parser.add_argument("--due", action="store_true")
    parser.add_argument(
        "--out-dir",
        default="generated_reports",
    )
    args = parser.parse_args()

    as_of = date.fromisoformat(args.as_of)
    requested = tuple(args.cadence or ())

    if args.due:
        requested = due_cadences_v0(as_of)

    if not requested:
        requested = ("WEEKLY", "BIWEEKLY", "MONTHLY")

    out_dir = Path(args.out_dir)
    generated = []
    for cadence in requested:
        generated.append(
            str(
                generate_for_cadence(
                    cadence=cadence,
                    as_of=as_of,
                    out_dir=out_dir,
                )
            )
        )

    print(
        json.dumps(
            {
                "as_of": as_of.isoformat(),
                "cadences": list(requested),
                "generated": generated,
                "external_delivery": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
