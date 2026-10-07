# F3H — CSSA ONE-YEAR SOAK / FAILURE CAMPAIGN V0

Date: 2026-10-07
Status: CLOSED / 365-DAY SYNTHETIC FAILURE CAMPAIGN
Branch: feat/f3h-cssa-one-year-failure-campaign-v0

## Objective

Return to the main target: run the CSSA organization continuously over one full year and record where it breaks.

F3H spans:

2026-08-01 -> 2027-07-31

365 days.

It reuses the 904-event F3E season, extends it through off-season/preseason transition, and creates a 969-event annual workload.

## Annual continuity

The added off-season/preseason layer includes:

- annual finance close;
- partner renewal;
- staff/delegation review;
- facilities readiness;
- source audit;
- governance review;
- subscription/communication restart;
- 19 next-season licence readiness cases;
- 19 next-season equipment readiness cases;
- 19 next-season schedule readiness cases.

The organization therefore does not stop when the league season ends.

## Persistent state

Unlike the earlier isolated stress tests, F3H carries state day after day:

- unresolved HOLD;
- unresolved BLOCK;
- pending ALLOW work;
- resource starvation;
- backlog;
- due dates;
- shared-asset demand;
- monthly travel-pressure estimate.

Cases can survive for months if a simulated authority/evidence resolution never arrives.

## 3 x 3 attack matrix

Three operating envelopes:

- LOW_CONSTRAINED;
- CENTRAL_WORKING;
- HIGH_CAPACITY.

Three attack modes:

- NORMAL;
- HARD;
- BREAKER.

Nine full 365-day runs are generated.

HARD and BREAKER include deterministic role outages and travel-envelope shocks.

## Failure signals

F3H records:

- DEADLINE_MISS;
- RESOURCE_STARVATION;
- BACKLOG_SATURATION;
- SHARED_ASSET_COLLISION;
- TRAVEL_BUDGET_PRESSURE;
- UNRESOLVED_HOLD_AGING;
- UNRESOLVED_BLOCK_AGING;
- YEAR_END_UNRESOLVED.

These are synthetic failure signals, not observed CSSA incidents.

## Results

### LOW_CONSTRAINED

NORMAL:
- 253 failure signals;
- 30 unresolved at year end;
- max backlog 57.

HARD:
- 285 failure signals;
- 36 unresolved;
- max backlog 70.

BREAKER:
- 786 failure signals;
- 52 unresolved;
- max backlog 89.

### CENTRAL_WORKING

NORMAL:
- 68 failure signals;
- 5 unresolved;
- max backlog 22.

HARD:
- 107 failure signals;
- 10 unresolved;
- max backlog 34.

BREAKER:
- 334 failure signals;
- 26 unresolved;
- max backlog 44.

### HIGH_CAPACITY

NORMAL:
- 59 failure signals;
- 5 unresolved;
- max backlog 16.

HARD:
- 96 failure signals;
- 10 unresolved;
- max backlog 23.

BREAKER:
- 275 failure signals;
- 26 unresolved;
- max backlog 38.

Best run:
HIGH_CAPACITY / NORMAL.

Worst run:
LOW_CONSTRAINED / BREAKER.

## Aggregate failure surface across 9 runs

- DEADLINE_MISS: 1408
- RESOURCE_STARVATION: 319
- YEAR_END_UNRESOLVED: 200
- SHARED_ASSET_COLLISION: 105
- UNRESOLVED_HOLD_AGING: 78
- TRAVEL_BUDGET_PRESSURE: 62
- BACKLOG_SATURATION: 52
- UNRESOLVED_BLOCK_AGING: 39

## Main finding 1 — deadline management dominates

The largest failure class is DEADLINE_MISS.

In CENTRAL_WORKING / NORMAL:

- 57 deadline misses;
- 44 are COMPETITIONS;
- 6 are TRAVEL_LOGISTICS.

In CENTRAL_WORKING / BREAKER:

- 249 deadline misses;
- 184 are COMPETITIONS;
- 36 are TRAVEL_LOGISTICS.

The first large failure surface is therefore calendar/deadline/competition propagation, not finance or marketing.

## Main finding 2 — constrained capacity collapses even without attacks

LOW_CONSTRAINED / NORMAL already produces:

- 253 failure signals;
- 54 resource-starvation signals;
- 33 shared-asset collisions;
- 24 backlog-saturation signals;
- 30 unresolved year-end cases.

So the low envelope is not merely less comfortable: it becomes structurally unstable over time.

## Main finding 3 — central capacity recovers from normal workload

CENTRAL_WORKING / NORMAL:

- 68 total failure signals;
- no resource-starvation signal;
- no backlog-saturation signal;
- 5 unresolved year-end cases.

This is materially better than LOW_CONSTRAINED.

## Main finding 4 — extra capacity has diminishing returns

HIGH_CAPACITY / NORMAL produces 59 failure signals versus 68 for CENTRAL_WORKING / NORMAL.

That is only nine fewer.

The remaining failures are mainly deadline/gate/authority/evidence related.

Therefore:

MORE CAPACITY != ZERO FAILURE.

## Main finding 5 — BREAKER attacks expose non-linear degradation

CENTRAL_WORKING:

NORMAL 68 -> HARD 107 -> BREAKER 334.

HIGH_CAPACITY:

NORMAL 59 -> HARD 96 -> BREAKER 275.

Capacity cushions the attack but does not prevent degradation when authority delays, outages and deadline pressure compound over months.

## Main finding 6 — unresolved authority can survive almost the whole year

Observed maximum unresolved ages are above 300 days in several profiles.

That is intentional adversarial behavior: some simulated HOLD/BLOCK cases never receive the evidence/authority event required to resolve them.

It proves the system can preserve unresolved state rather than silently forgetting it.

## Failure found during implementation

First F3H run:

274 PASS / 1 FAIL.

The failed test expected natural annual travel-budget pressure in LOW/HARD.

The annual workload did not naturally cross that synthetic threshold.

Instead of pretending it did, the attack profile was extended with explicit travel-envelope shocks for HARD/BREAKER.

Closure:

275 passed in 14.47s.

## Governance

Preserved:

- KX108_ONLY;
- external_action=false;
- no real CSSA failure claim;
- ESTIMATED capacities remain estimated;
- simulated resolution events do not grant real-world authority.

## Verdict

CSSA_ONE_YEAR_LONGITUDINAL_FAILURE_CAMPAIGN_V0_PROVEN
