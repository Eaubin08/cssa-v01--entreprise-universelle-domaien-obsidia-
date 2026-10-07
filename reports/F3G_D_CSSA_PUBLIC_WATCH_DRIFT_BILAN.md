# CSSA / V0.1 — F3G-D PUBLIC WATCH & DRIFT BILAN

Date: 2026-10-07
Branch: feat/f3g-d-cssa-public-watch-drift-v0
Main: unchanged

## Executive result

The public reality layer is now repeatable instead of a one-off audit.

- 14 public sources watched
- WEEKLY / BIWEEKLY / MONTHLY cadence
- GET only
- SHA-256 raw + visible-text fingerprints
- review signals -> persona cockpit
- 266 tests PASS
- external action = false

## What this changes

Before:
manual public snapshot -> shadow analysis.

Now:
public source watch -> fingerprint delta -> review if visible change -> reviewed semantic snapshot -> structured state drift -> shadow + reports.

## Important rule

A web page changing is not enough to mutate the CSSA model.

A visible-content change only says:
something public changed and the affected meaning is not yet reviewed.

The system keeps that as HOLD instead of guessing.

## Recurring state

The workflow can keep the previous public capture through GitHub Actions cache and compare the next run against it.

On scheduled/manual runs it can create:
- watch summary;
- per-source deltas;
- HOLD review signals;
- weekly/biweekly/monthly persona reports when due.

The schedule is currently dormant because the work is intentionally off-main.

## Defect found

Initial CI:
265 PASS / 1 FAIL.

Cause:
missing defaultdict import in the structured semantic drift comparator.

Fixed.

Closure:
266 / 266 PASS.

## Current project meaning

Truth layers are now explicit:

PUBLIC WATCH SIGNAL
-> reviewed PUBLIC_CONFIRMED / SECONDARY_CORROBORATED
-> ESTIMATED replaceable operating envelope
-> later REAL_FIELD_EVIDENCE

No layer is silently promoted.

## Next

F3G-E should connect reviewed watch changes back into the public snapshot and operating envelope through a controlled promotion/delta process.

Goal:
- update only affected assumptions;
- rerun stress/sensitivity;
- show exactly what changed in the cockpit;
- preserve KX108_ONLY and READONLY boundaries.
