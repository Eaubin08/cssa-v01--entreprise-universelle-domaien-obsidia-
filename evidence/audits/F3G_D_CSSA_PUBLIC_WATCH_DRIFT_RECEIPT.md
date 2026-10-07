# F3G-D CSSA PUBLIC WATCH & DRIFT RECEIPT

Date: 2026-10-07
Branch: feat/f3g-d-cssa-public-watch-drift-v0

## Scope

Make F3G-B public shadow repeatable over time.

## Watch surface

- 14 HTTPS allowlisted public sources
- WEEKLY / BIWEEKLY / MONTHLY cadence
- GET only
- 5 MB body ceiling
- raw SHA-256
- visible-text SHA-256

## Delta states

Supported:
- NEW_BASELINE
- UNCHANGED
- RAW_CHANGED_VISIBLE_UNCHANGED
- VISIBLE_CONTENT_CHANGED_REVIEW_REQUIRED
- UNREACHABLE
- RECOVERED

## Governance

Visible semantic-unknown change:
SEMANTIC_CHANGE_NOT_REVIEWED + AFFECTED_STATE_UNKNOWN -> HOLD.

Unreachable source:
CURRENT_SOURCE_STATE_UNKNOWN + FRESHNESS_CONFIRMATION_UNAVAILABLE -> HOLD.

No page change is auto-promoted to CSSA semantic truth.

## Structured semantic drift

Reviewed snapshots can detect:
- added state
- removed state
- value-set change
- truth-class-set change

## Failure / correction

Initial run:
265 PASS / 1 FAIL.

Cause:
missing defaultdict import.

Closure run:
266 passed in 27.05s.

Workflow run:
37564085921

## Schedule boundary

Daily cron hook exists.

Because scheduled workflows run from the default branch and this work is off-main:
CRON_READY_BUT_DORMANT_OFF_MAIN.

## Claim

F3G_D_PUBLIC_WATCH_AND_DRIFT_CLOSED

No merge to main.
