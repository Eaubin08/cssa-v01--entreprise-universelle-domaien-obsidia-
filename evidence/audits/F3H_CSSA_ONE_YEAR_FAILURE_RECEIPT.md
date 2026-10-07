# F3H CSSA ONE-YEAR FAILURE CAMPAIGN RECEIPT

Date: 2026-10-07
Branch: feat/f3h-cssa-one-year-failure-campaign-v0

## Horizon

2026-08-01 -> 2027-07-31

365 days.

## Input

969 synthetic annual organization events.

Includes full season plus off-season and next-season transition.

## Matrix

9 complete runs:

LOW_CONSTRAINED:
- NORMAL 253 failures / 30 pending / max backlog 57
- HARD 285 / 36 / 70
- BREAKER 786 / 52 / 89

CENTRAL_WORKING:
- NORMAL 68 / 5 / 22
- HARD 107 / 10 / 34
- BREAKER 334 / 26 / 44

HIGH_CAPACITY:
- NORMAL 59 / 5 / 16
- HARD 96 / 10 / 23
- BREAKER 275 / 26 / 38

Best:
HIGH_CAPACITY/NORMAL.

Worst:
LOW_CONSTRAINED/BREAKER.

## Aggregate failure types

- DEADLINE_MISS 1408
- RESOURCE_STARVATION 319
- YEAR_END_UNRESOLVED 200
- SHARED_ASSET_COLLISION 105
- UNRESOLVED_HOLD_AGING 78
- TRAVEL_BUDGET_PRESSURE 62
- BACKLOG_SATURATION 52
- UNRESOLVED_BLOCK_AGING 39

## First implementation failure

Initial CI:

274 PASS / 1 FAIL.

Cause:
test expected travel-budget pressure without an explicit budget shock.

Correction:
HARD/BREAKER now include deterministic travel-envelope shock attacks.

## Closure

Run:
37564857973

Result:
275 passed in 14.47s.

Artifact:
11458422741

Files:
- one_year_failure_matrix.json
- one_year_failure_report.md

## Governance

- KX108_ONLY
- external_action=false
- SIMULATED_NOT_OBSERVED
- no real CSSA incident claim
- no merge to main

## Claim

F3H_ONE_YEAR_LONGITUDINAL_FAILURE_CAMPAIGN_CLOSED
