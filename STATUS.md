# STATUS

Status: F3H_CSSA_ONE_YEAR_FAILURE_CAMPAIGN_CLOSED
Branch: feat/f3h-cssa-one-year-failure-campaign-v0

## Progression

- F3A public baseline: PASS
- F3B field intake kit: READY
- F3C isolated synthetic scenarios: PASS
- F3D season-scale audit/model: PASS
- F3E full-season synthetic corpus: PASS
- F3E recurring reporting/persona routing: PASS
- F3F organizational stress: PASS
- F3G-A adversarial sensitivity: PASS
- F3G-B public reality shadow: PASS
- F3G-C public-anchored estimated operating envelope: PASS
- F3G-D public watch/drift: PASS / auxiliary
- F3H one-year longitudinal failure campaign: PASS
- real CSSA internal field evidence: OPEN
- external action: HOLD

## One-year campaign

Horizon:
2026-08-01 -> 2027-07-31

- 365 days
- 969 annual events
- full season + off-season + next-season transition
- 9 complete runs
- persistent backlog and unresolved state

Profiles:
- LOW_CONSTRAINED
- CENTRAL_WORKING
- HIGH_CAPACITY

Attacks:
- NORMAL
- HARD
- BREAKER

## Annual results

LOW_CONSTRAINED:
- NORMAL: 253 failure signals / 30 unresolved / max backlog 57
- HARD: 285 / 36 / 70
- BREAKER: 786 / 52 / 89

CENTRAL_WORKING:
- NORMAL: 68 / 5 / 22
- HARD: 107 / 10 / 34
- BREAKER: 334 / 26 / 44

HIGH_CAPACITY:
- NORMAL: 59 / 5 / 16
- HARD: 96 / 10 / 23
- BREAKER: 275 / 26 / 38

Best:
HIGH_CAPACITY/NORMAL

Worst:
LOW_CONSTRAINED/BREAKER

## Failure inventory across all nine runs

- DEADLINE_MISS: 1408
- RESOURCE_STARVATION: 319
- YEAR_END_UNRESOLVED: 200
- SHARED_ASSET_COLLISION: 105
- UNRESOLVED_HOLD_AGING: 78
- TRAVEL_BUDGET_PRESSURE: 62
- BACKLOG_SATURATION: 52
- UNRESOLVED_BLOCK_AGING: 39

## Main finding

The dominant failure surface is deadline/competition propagation.

CENTRAL_WORKING / NORMAL:
- 57 deadline misses
- 44 from COMPETITIONS
- 6 from TRAVEL_LOGISTICS

CENTRAL_WORKING / BREAKER:
- 249 deadline misses
- 184 from COMPETITIONS
- 36 from TRAVEL_LOGISTICS

## Capacity finding

LOW_CONSTRAINED is unstable even in NORMAL:
- resource starvation
- shared-asset collisions
- backlog saturation
- 30 year-end unresolved cases

CENTRAL_WORKING is materially more resilient.

HIGH_CAPACITY improves NORMAL only from 68 to 59 failure signals relative to CENTRAL_WORKING.

Therefore extra capacity has diminishing returns and cannot solve missing authority/evidence.

## First implementation failure

Initial F3H CI:
- 274 PASS / 1 FAIL
- expected natural annual travel-budget pressure did not occur

Correction:
- budget pressure is now attacked explicitly through HARD/BREAKER travel-envelope shock profiles

Closure:
- run 37564857973
- 275 passed in 14.47s
- artifact 11458422741
- SUCCESS

## Governance

Preserved:
- KX108_ONLY
- no external action
- no world action
- estimated capacities remain estimated
- failure signals remain SIMULATED_NOT_OBSERVED
- no real CSSA incident claim

## Main line

F3G-D public watch remains useful but auxiliary.

The main technical line is now the 365-day longitudinal failure campaign.

## Next

F3I — dependency cascade / propagation hardening.

Target the largest F3H weakness:

fixture/deadline state
-> transport
-> FMI
-> ticketing
-> matchday
-> partner commitments
-> communication
-> proof

Goal:
prove that one late or contradictory upstream state cannot silently leave dependent layers inconsistent.

No merge to main.
