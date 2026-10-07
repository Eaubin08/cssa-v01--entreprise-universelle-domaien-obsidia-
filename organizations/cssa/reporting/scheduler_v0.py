"""CSSA reporting cadence scheduler V0."""
from __future__ import annotations

from datetime import date

BIWEEKLY_ANCHOR = date(2026, 10, 19)


def due_cadences_v0(day: date) -> tuple[str, ...]:
    due: list[str] = []

    # Weekly operational report every Monday.
    if day.weekday() == 0:
        due.append("WEEKLY")

    # Biweekly cross-layer review, anchored to 2026-10-19.
    if day >= BIWEEKLY_ANCHOR and (day - BIWEEKLY_ANCHOR).days % 14 == 0:
        due.append("BIWEEKLY")

    # Monthly governance review on first calendar day.
    if day.day == 1:
        due.append("MONTHLY")

    return tuple(due)
