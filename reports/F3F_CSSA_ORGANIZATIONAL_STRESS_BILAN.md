# CSSA / V0.1 — F3F ORGANIZATIONAL STRESS BILAN

Date: 2026-10-07
Branch: `feat/f3f-cssa-organizational-stress-v0`
Main: unchanged

## Executive result

F3F is no longer asking whether Administration can process one correct case.

It asks whether the CSSA model remains coherent when several correct cases compete for the same limited resources.

Current result:

```text
12 explicit collision scenarios
2  ALLOW
5  HOLD
5  BLOCK

904 season events scanned
4 synthetic capacity-pressure points detected

217 tests PASS
weekly / biweekly / monthly stress-aware cockpit generated
KX108_ONLY preserved
external action = false
```

## What F3F proves

### 1. Hard double allocation is detected

The system catches impossible simultaneous allocation of a shared resource.

Examples proven:

- vehicle pool capacity 2 vs demand 3 -> BLOCK;
- hospitality capacity 1 vs demand 2 -> BLOCK;
- stadium slot capacity 1 vs demand 2 -> BLOCK.

The stress engine does not silently choose two users for one resource.

### 2. Missing authority produces HOLD, not invented delegation

Examples:

- Admin owner unavailable while urgent LGEF work arrives;
- substitute not known;
- signature scope not known;
- budget overrun approval not known;
- partner alternative not known.

Those cases remain HOLD until authority/evidence is supplied.

### 3. Cascading stale state is detected

A late match change can invalidate more than one downstream surface.

The synthetic cascade proves a BLOCK when the new official state conflicts simultaneously with:

- transport state;
- public/ticketing state.

This is the organizational form of the same provenance/coherence problem already seen in the public CSSA audit.

### 4. Backlog can become a dependency risk

An unresolved FMI exception plus a new deadline does not disappear because a new case arrives.

The old unresolved state stays visible and forces HOLD when closure/commission status is unknown.

### 5. Priority can be generated without becoming authority

The 20-case simultaneous workload produces a complete deterministic priority queue without false BLOCK.

No item is lost and no duplicated identifier appears.

The important discovery was that the safety-critical matchday case ranks before urgent regulatory work.

This produced the first F3F CI failure because the test expectation was wrong.

The corrected policy is now explicit:

`SAFETY > REGULATORY > DEADLINE`

Priority remains advisory.

### 6. The base synthetic season already contains pressure

Scanning the existing 904-event F3E season against the simulated daily capacity model produces 4 pressure points without injecting the 12 hand-built collision scenarios.

That means the season model is sufficiently dense for resource-pressure testing.

This does NOT prove that the real CSSA is overloaded four times.

It proves the simulator naturally creates some cross-case pressure.

## Defects / corrections during F3F

### First run

Result:

`216 PASS / 1 FAIL`

Failure:

the test expected CASE_01 or CASE_02, both regulatory, to rank first in the 20-case queue.

Observed:

`CASE_09` ranked first because it was safety-critical.

Assessment:

engine policy was correct; test assumption was incorrect.

Correction:

- freeze CASE_09 as expected first priority;
- document safety-first priority policy.

### Closure run

`217 passed in 0.97s`

Stress artifact generated.

Stress-aware reporting cockpit generated.

## What remains synthetic

Not proven with real CSSA evidence:

- actual number of vehicles;
- actual staff capacity;
- actual work units/day;
- real travel envelope;
- actual hospitality capacity;
- real substitution/delegation rules;
- real priority policy used by staff;
- real budget approval chain.

These parameters should later be calibrated with field evidence.

## What this changes in the project

Before F3F:

`case -> governance -> report`

After F3F:

`many cases -> shared resource pressure -> priority/conflict -> governance -> persona reports`

The system is moving from document/case governance toward organization-level coherence.

## Next decision

The next useful phase is F3G FIELD CALIBRATION.

Use real staff evidence to replace the most consequential synthetic assumptions first:

1. employing entity / actual administrative boundary;
2. reporting and validation chain;
3. travel organization and expense workflow;
4. real shared vehicle/transport behavior;
5. staff absence/substitution practice;
6. actual tools/channels;
7. real approval/delegation points.

A first-team staff contact can validate several of these without needing access to the whole club.
