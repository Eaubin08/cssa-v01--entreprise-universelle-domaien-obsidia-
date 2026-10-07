"""F3G-D — repeatable public watch and drift detection V0.

This layer performs GET-only observation of explicitly whitelisted public pages,
computes content fingerprints, compares captures and emits review signals.

A page change is NOT interpreted as a semantic fact change.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from hashlib import sha256
from html.parser import HTMLParser
import json
import re
from typing import Any, Callable, Iterable, Mapping
from urllib.request import Request, urlopen


WATCH_STATUS = "READONLY_PUBLIC_WATCH"
ALLOWED_TRUTH_CLASSES = {"PUBLIC_CONFIRMED", "SECONDARY_CORROBORATED"}
ALLOWED_CADENCES = {"WEEKLY", "BIWEEKLY", "MONTHLY"}
MAX_BYTES = 5_000_000


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"} and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self.parts.append(data)


def normalize_visible_text_v0(raw_html: bytes) -> str:
    text = raw_html.decode("utf-8", errors="replace")
    parser = _VisibleTextParser()
    parser.feed(text)
    visible = " ".join(parser.parts)
    visible = re.sub(r"\s+", " ", visible).strip()
    return visible


def fingerprint_bytes_v0(raw_html: bytes) -> dict[str, Any]:
    if len(raw_html) > MAX_BYTES:
        raise ValueError("PUBLIC_SOURCE_BODY_TOO_LARGE")
    visible = normalize_visible_text_v0(raw_html)
    return {
        "raw_sha256": sha256(raw_html).hexdigest(),
        "visible_text_sha256": sha256(visible.encode("utf-8")).hexdigest(),
        "raw_bytes": len(raw_html),
        "visible_chars": len(visible),
    }


def _validate_watchlist(watchlist: Mapping[str, Any]) -> None:
    if watchlist.get("status") != WATCH_STATUS:
        raise ValueError("INVALID_WATCHLIST_STATUS")
    seen = set()
    for row in watchlist["sources"]:
        source_id = str(row["id"])
        if source_id in seen:
            raise ValueError(f"DUPLICATE_WATCH_SOURCE:{source_id}")
        seen.add(source_id)
        if not str(row["url"]).startswith("https://"):
            raise ValueError(f"NON_HTTPS_WATCH_SOURCE:{source_id}")
        if row["truth_class"] not in ALLOWED_TRUTH_CLASSES:
            raise ValueError(f"INVALID_WATCH_TRUTH_CLASS:{source_id}")
        if row["cadence"] not in ALLOWED_CADENCES:
            raise ValueError(f"INVALID_WATCH_CADENCE:{source_id}")


def due_sources_v0(
    watchlist: Mapping[str, Any],
    *,
    as_of: date,
) -> tuple[Mapping[str, Any], ...]:
    """Select sources due for a recurring capture.

    Weekly: Monday.
    Biweekly: every second Monday anchored 2026-10-19.
    Monthly: first calendar day.
    """
    _validate_watchlist(watchlist)
    weekly_due = as_of.weekday() == 0
    biweekly_due = (
        as_of >= date(2026, 10, 19)
        and (as_of - date(2026, 10, 19)).days % 14 == 0
    )
    monthly_due = as_of.day == 1

    out = []
    for row in watchlist["sources"]:
        cadence = row["cadence"]
        if cadence == "WEEKLY" and weekly_due:
            out.append(row)
        elif cadence == "BIWEEKLY" and biweekly_due:
            out.append(row)
        elif cadence == "MONTHLY" and monthly_due:
            out.append(row)
    return tuple(out)


def capture_source_v0(
    source: Mapping[str, Any],
    *,
    observed_at: str,
    fetcher: Callable[[str], bytes] | None = None,
) -> dict[str, Any]:
    source_id = str(source["id"])
    url = str(source["url"])
    if not url.startswith("https://"):
        raise ValueError(f"NON_HTTPS_WATCH_SOURCE:{source_id}")

    if fetcher is None:
        def fetcher(target: str) -> bytes:
            request = Request(
                target,
                method="GET",
                headers={
                    "User-Agent": "CSSA-V0.1-Public-Watch/0.1",
                    "Accept": "text/html,application/xhtml+xml",
                },
            )
            with urlopen(request, timeout=20) as response:
                body = response.read(MAX_BYTES + 1)
            return body

    try:
        raw = fetcher(url)
        fingerprint = fingerprint_bytes_v0(raw)
        return {
            "source_id": source_id,
            "url": url,
            "truth_class": source["truth_class"],
            "cadence": source["cadence"],
            "criticality": source.get("criticality", "MEDIUM"),
            "observed_at": observed_at,
            "status": "OK",
            **fingerprint,
        }
    except Exception as exc:
        return {
            "source_id": source_id,
            "url": url,
            "truth_class": source["truth_class"],
            "cadence": source["cadence"],
            "criticality": source.get("criticality", "MEDIUM"),
            "observed_at": observed_at,
            "status": "UNREACHABLE",
            "error_type": type(exc).__name__,
        }


def compare_captures_v0(
    previous: Mapping[str, Any] | None,
    current: Mapping[str, Any],
) -> dict[str, Any]:
    if previous is None:
        return {
            "source_id": current["source_id"],
            "status": "NEW_BASELINE",
            "truth_class": current["truth_class"],
            "criticality": current.get("criticality", "MEDIUM"),
            "previous_observed_at": None,
            "current_observed_at": current["observed_at"],
        }

    if previous["source_id"] != current["source_id"]:
        raise ValueError("CAPTURE_SOURCE_ID_MISMATCH")

    if current["status"] != "OK":
        return {
            "source_id": current["source_id"],
            "status": "UNREACHABLE",
            "truth_class": current["truth_class"],
            "criticality": current.get("criticality", "MEDIUM"),
            "previous_observed_at": previous.get("observed_at"),
            "current_observed_at": current["observed_at"],
        }

    if previous.get("status") != "OK":
        return {
            "source_id": current["source_id"],
            "status": "RECOVERED",
            "truth_class": current["truth_class"],
            "criticality": current.get("criticality", "MEDIUM"),
            "previous_observed_at": previous.get("observed_at"),
            "current_observed_at": current["observed_at"],
        }

    same_visible = (
        previous.get("visible_text_sha256")
        == current.get("visible_text_sha256")
    )
    same_raw = previous.get("raw_sha256") == current.get("raw_sha256")

    if same_visible and same_raw:
        status = "UNCHANGED"
    elif same_visible:
        status = "RAW_CHANGED_VISIBLE_UNCHANGED"
    else:
        status = "VISIBLE_CONTENT_CHANGED_REVIEW_REQUIRED"

    return {
        "source_id": current["source_id"],
        "status": status,
        "truth_class": current["truth_class"],
        "criticality": current.get("criticality", "MEDIUM"),
        "previous_observed_at": previous.get("observed_at"),
        "current_observed_at": current["observed_at"],
    }


@dataclass(frozen=True)
class PublicWatchSignalV0:
    event_id: str
    event_date: str
    family: str
    case_type: str
    truth_class: str
    source_ids: tuple[str, ...]
    risk_flags: tuple[str, ...]
    unknowns: tuple[str, ...]
    contradictions: tuple[str, ...] = ()
    team_id: str | None = None

    @property
    def expected_gate(self) -> str:
        if len(self.contradictions) >= 2:
            return "BLOCK"
        if len(self.unknowns) > 1:
            return "HOLD"
        return "ALLOW"


def delta_to_signal_v0(
    delta: Mapping[str, Any],
) -> PublicWatchSignalV0 | None:
    status = str(delta["status"])
    if status in {"UNCHANGED", "RAW_CHANGED_VISIBLE_UNCHANGED", "NEW_BASELINE"}:
        return None

    source_id = str(delta["source_id"])
    date_value = str(delta["current_observed_at"])
    truth_class = str(delta["truth_class"])

    if status == "VISIBLE_CONTENT_CHANGED_REVIEW_REQUIRED":
        return PublicWatchSignalV0(
            event_id=f"WATCH-CHANGE:{source_id}:{date_value}",
            event_date=date_value,
            family="PROOF_AUDIT",
            case_type="public_source_content_changed",
            truth_class=truth_class,
            source_ids=(source_id,),
            risk_flags=("SOURCE_CONTENT_CHANGED_REVIEW_REQUIRED",),
            unknowns=(
                "SEMANTIC_CHANGE_NOT_REVIEWED",
                "AFFECTED_STATE_UNKNOWN",
            ),
        )

    if status == "UNREACHABLE":
        return PublicWatchSignalV0(
            event_id=f"WATCH-UNREACHABLE:{source_id}:{date_value}",
            event_date=date_value,
            family="PROOF_AUDIT",
            case_type="public_source_unreachable",
            truth_class=truth_class,
            source_ids=(source_id,),
            risk_flags=("PUBLIC_SOURCE_UNREACHABLE",),
            unknowns=(
                "CURRENT_SOURCE_STATE_UNKNOWN",
                "FRESHNESS_CONFIRMATION_UNAVAILABLE",
            ),
        )

    if status == "RECOVERED":
        return PublicWatchSignalV0(
            event_id=f"WATCH-RECOVERED:{source_id}:{date_value}",
            event_date=date_value,
            family="PROOF_AUDIT",
            case_type="public_source_recovered",
            truth_class=truth_class,
            source_ids=(source_id,),
            risk_flags=("SOURCE_RECOVERED_REVIEW_FRESHNESS",),
            unknowns=(),
        )

    raise ValueError(f"UNKNOWN_WATCH_DELTA_STATUS:{status}")


def compare_capture_sets_v0(
    previous_rows: Iterable[Mapping[str, Any]],
    current_rows: Iterable[Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    previous = {str(row["source_id"]): row for row in previous_rows}
    current = {str(row["source_id"]): row for row in current_rows}
    out = []
    for source_id in sorted(current):
        out.append(compare_captures_v0(previous.get(source_id), current[source_id]))
    return tuple(out)


def structured_snapshot_drift_v0(
    previous_snapshot: Mapping[str, Any],
    current_snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    """Compare reviewed semantic observations between two public snapshots."""
    def index(snapshot):
        rows = defaultdict(list)
        for obs in snapshot["observations"]:
            key = obs.get("state_key")
            if key:
                rows[str(key)].append(obs)
        return rows

    before = index(previous_snapshot)
    after = index(current_snapshot)
    keys = sorted(set(before) | set(after))
    changes = []

    for key in keys:
        b = before.get(key, [])
        a = after.get(key, [])
        b_values = sorted({str(row.get("canonical_value")) for row in b})
        a_values = sorted({str(row.get("canonical_value")) for row in a})
        b_truth = sorted({str(row["truth_class"]) for row in b})
        a_truth = sorted({str(row["truth_class"]) for row in a})

        if not b:
            kind = "ADDED_STATE"
        elif not a:
            kind = "REMOVED_STATE"
        elif b_values != a_values:
            kind = "VALUE_SET_CHANGED"
        elif b_truth != a_truth:
            kind = "TRUTH_CLASS_SET_CHANGED"
        else:
            kind = "UNCHANGED"

        if kind != "UNCHANGED":
            changes.append({
                "state_key": key,
                "kind": kind,
                "before_values": b_values,
                "after_values": a_values,
                "before_truth_classes": b_truth,
                "after_truth_classes": a_truth,
            })

    return {
        "previous_as_of": previous_snapshot.get("as_of"),
        "current_as_of": current_snapshot.get("as_of"),
        "changed_state_count": len(changes),
        "changes": changes,
    }


def watch_summary_v0(
    deltas: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    rows = tuple(deltas)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    signals = [
        signal
        for row in rows
        if (signal := delta_to_signal_v0(row)) is not None
    ]
    return {
        "watch_status": WATCH_STATUS,
        "delta_count": len(rows),
        "status_counts": dict(sorted(counts.items())),
        "signal_count": len(signals),
        "hold_signal_count": sum(
            1 for signal in signals if signal.expected_gate == "HOLD"
        ),
        "external_action": False,
    }
