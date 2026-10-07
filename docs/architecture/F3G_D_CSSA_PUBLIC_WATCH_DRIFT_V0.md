# F3G-D — CSSA PUBLIC WATCH & DRIFT V0

Date: 2026-10-07
Status: CLOSED / READONLY PUBLIC WATCH
Branch: feat/f3g-d-cssa-public-watch-drift-v0

## Objective

Make the public-shadow layer repeatable over time without turning page changes into invented facts.

F3G-D adds a GET-only watch system over the public sources already used by F3G-B.

It can:
- fetch whitelisted public pages;
- compute raw and visible-text fingerprints;
- compare them with the previous capture;
- distinguish raw HTML noise from visible content change;
- surface unreachable/recovered sources;
- create review signals;
- route those signals into the weekly / biweekly / monthly persona cockpit.

A page change is not interpreted as a semantic CSSA fact.

## Watchlist

organizations/cssa/watch/watchlist_v0.json

Current V0:
- 14 explicit HTTPS public sources;
- PUBLIC_CONFIRMED or SECONDARY_CORROBORATED only;
- WEEKLY / BIWEEKLY / MONTHLY cadence;
- criticality metadata;
- no arbitrary URL discovery.

## GET-only boundary

The live watcher implements HTTP GET only.

Constraints:
- HTTPS required;
- 5 MB body ceiling;
- explicit source allowlist;
- read-only artifact/state output;
- no CSSA system mutation;
- no email/CRM/site publication.

## Fingerprints

Each successful capture stores:
- raw SHA-256;
- visible-text SHA-256;
- raw byte count;
- visible text length;
- observed date.

Scripts/styles/noscript/svg text are ignored for the visible-text fingerprint.

This distinguishes RAW_CHANGED_VISIBLE_UNCHANGED from VISIBLE_CONTENT_CHANGED_REVIEW_REQUIRED.

## Review signals

A visible-content change creates a PROOF_AUDIT signal with:
- SEMANTIC_CHANGE_NOT_REVIEWED;
- AFFECTED_STATE_UNKNOWN.

Current Guard semantics therefore produce HOLD for the review signal.

An unreachable source similarly creates a HOLD review signal.

## Structured snapshot drift

Reviewed semantic snapshots can be compared for:
- ADDED_STATE;
- REMOVED_STATE;
- VALUE_SET_CHANGED;
- TRUTH_CLASS_SET_CHANGED;
- UNCHANGED.

PAGE CHANGED != SEMANTIC FACT CHANGED.

A reviewed extraction step remains between the two.

## Recurring automation

Workflow:
.github/workflows/f3g-d-cssa-public-watch-drift.yml

It includes:
- full F1 -> F3G-D regression;
- daily cron hook;
- manual workflow dispatch;
- previous watch-state restoration through GitHub Actions cache;
- GET-only live capture on schedule/manual runs;
- updated state save;
- generated review/report artifacts.

Scheduled workflows execute from the default branch.

Because this implementation remains off-main, the cron is READY_BUT_DORMANT_OFF_MAIN.

## Failure found during implementation

First F3G-D CI run:
265 passed / 1 failed.

Cause:
structured_snapshot_drift_v0 used defaultdict without importing it.

Correction:
explicit collections.defaultdict import.

Closure run:
266 passed in 27.05s.

## Verdict

CSSA_REPEATABLE_PUBLIC_WATCH_AND_DRIFT_V0_PROVEN

Not proven:
- permanent reachability of every public site;
- semantic meaning of any visible page change;
- internal CSSA truth;
- external action authority.
