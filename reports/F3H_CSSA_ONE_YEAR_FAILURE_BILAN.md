# CSSA / V0.1 — F3H ONE-YEAR FAILURE BILAN

Date: 2026-10-07
Main: unchanged

## Executive result

This is the one-year test we originally wanted.

- 365 days
- 969 annual events
- 9 complete runs
- LOW / CENTRAL / HIGH
- NORMAL / HARD / BREAKER
- persistent backlog and unresolved state
- 275 tests PASS

The purpose was not to get zero failures. The purpose was to see where failure accumulates.

## The clearest result

CENTRAL_WORKING is a useful operating baseline.

NORMAL:
- 68 failure signals
- 5 cases still unresolved at year end
- max backlog 22

HARD:
- 107 failures
- 10 unresolved
- max backlog 34

BREAKER:
- 334 failures
- 26 unresolved
- max backlog 44

The system degrades but does not immediately collapse.

## Where it really breaks

### 1. Competition/deadline chain

This is the dominant failure surface.

Central NORMAL deadline misses:
- 44 competition
- 6 travel

Central BREAKER:
- 184 competition
- 36 travel

So if we want to improve the simulated organization first, the priority is calendar/competition/deadline propagation.

### 2. Low capacity

LOW_CONSTRAINED already fails heavily in NORMAL mode.

It creates resource starvation, shared-asset collisions and backlog saturation before we even start the serious attacks.

That envelope is not resilient.

### 3. Repeated outages

BREAKER increases failures massively:

CENTRAL: 68 -> 334.
HIGH: 59 -> 275.

The system survives better with capacity, but repeated outages plus delayed evidence produce cumulative damage.

### 4. Authority/evidence

HIGH capacity does not eliminate year-end unresolved cases.

NORMAL:
CENTRAL 5 unresolved.
HIGH 5 unresolved.

So these are not mainly "we need more people" failures.

They are unresolved-state / authority / evidence failures.

## Aggregate failure inventory

Across all nine annual runs:

- 1408 deadline misses
- 319 starvation signals
- 200 year-end unresolved
- 105 shared-asset collisions
- 78 aging HOLD
- 62 travel-budget pressure
- 52 backlog saturation
- 39 aging BLOCK

## Important caveat

None of those numbers says "Sedan really had X failures".

They describe the synthetic organization under the current replaceable LOW/CENTRAL/HIGH assumptions.

When a real parameter arrives later, we replace it and rerun the exact same campaign.

## Next engineering target

Do not go back to public-watch expansion as the main line.

Use F3H failure evidence to attack the biggest weakness:

ANNUAL DEADLINE / DEPENDENCY PROPAGATION.

The next phase should trace one failure through all dependent layers.

Example:

fixture change
-> transport
-> FMI
-> ticketing
-> matchday
-> partner hospitality
-> communication
-> proof/receipt

Then verify that one late/incorrect upstream state cannot silently leave six downstream states inconsistent.

That should be F3I.
