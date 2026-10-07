# F3I — CSSA DEPENDENCY PROPAGATION HARDENING V0

Date: 2026-10-07
Status: CLOSED / ONE-YEAR FIXTURE DEPENDENCY CAMPAIGN
Branch: feat/f3i-cssa-dependency-propagation-v0

## Objective

Attack the largest F3H failure surface: deadline / competition propagation.

Target chain:

fixture state
-> travel
-> FMI
-> ticketing
-> matchday
-> partner hospitality
-> volunteers
-> communication
-> proof

The goal is not to make every attacked fixture ALLOW.

The goal is stronger:

a changed upstream fixture state must never silently leave a downstream surface marked ready on another revision.

## Dependency graph recovered from the one-year corpus

The annual corpus contains:

- 330 fixture roots;
- 478 downstream dependency surfaces;
- 0 missing required surfaces in the current synthetic graph;
- 0 unruled dependency case types.

The graph is derived from the existing fixture target references rather than a second manually duplicated season.

## Root / dependent revision invariant

Every fixture has a root revision.

Each downstream surface must satisfy:

- observed revision == root revision;
- final root authority seen;
- propagation deadline respected;
- dependency belongs to the same fixture;
- required dependent surface exists.

A dependent cannot be READY if one of those conditions is false.

## Fail-closed states

### Stale dependent

One required surface behind the root revision produces two explicit unknowns:

- DEPENDENT_REFRESH_PENDING;
- DEPENDENT_STATE_NOT_CURRENT.

Therefore a single stale required surface produces HOLD under current Guard semantics.

### Missing required surface

Produces:

- MISSING_DEPENDENT;
- PROPAGATION_STATUS_UNKNOWN.

Result: HOLD.

### Propagation deadline exceeded

Produces:

- DEPENDENCY_OVERDUE;
- DEPENDENCY_CURRENT_STATE_UNCONFIRMED.

Result: HOLD.

### Dependent ahead of root

Produces structural contradictions:

- DEPENDENT_AHEAD_OF_ROOT;
- ILLEGAL_REVISION_ORDER.

Result: BLOCK.

### Root authority not final

A dependent cannot be public/operationally ready before final upstream authority.

This creates contradictions and BLOCK.

## Annual attack campaigns

All 330 fixture roots are attacked in three deterministic modes.

### NORMAL

\`\`\`text
ALLOW 319
HOLD    9
BLOCK   2
stale/blocked surfaces 5
silent inconsistencies 0
\`\`\`

### HARD

\`\`\`text
ALLOW 263
HOLD   57
BLOCK  10
stale/blocked surfaces 144
silent inconsistencies 0
\`\`\`

### BREAKER

\`\`\`text
ALLOW 165
HOLD  129
BLOCK  36
stale/blocked surfaces 302
silent inconsistencies 0
\`\`\`

## Core result

Across all three campaigns:

\`SILENT_INCONSISTENCY_COUNT = 0\`

Even under BREAKER, no downstream state is allowed to remain marked READY while:

- using an old revision;
- using an impossible future revision;
- depending on non-final upstream authority;
- exceeding its propagation deadline.

The system can fail loudly as HOLD/BLOCK, but not silently pass an inconsistent dependent surface.

## Real Guard proof

Representative ALLOW / HOLD / BLOCK dependency assessments traverse:

\`\`\`text
F3I dependency assessment
 -> Administration adapter
 -> F2.5 aggregate-only resolver
 -> REAL DomainAggregate
 -> REAL GuardX108
 -> canonical decision lifecycle
\`\`\`

Verified:

- ALLOW can reach bounded READONLY provider;
- HOLD does not invoke provider;
- BLOCK does not invoke provider;
- KX108_ONLY;
- no memory write;
- no kernel mutation;
- no emits_act;
- no world action.

## Reporting

New family:

\`DEPENDENCY_PROPAGATION\`

It routes dependency failures to affected personas, including:

- Direction / Présidence;
- Manager Général;
- Administration;
- Secrétariat;
- Finance;
- Direction Technique;
- Team Manager / Intendance;
- Matchday;
- Ticketing;
- Partnerships;
- Communication.

This does not grant any of those roles new execution authority.

## Implementation finding

First F3I run:

\`288 PASS / 1 FAIL\`

Cause:

the expected dependency-edge count in the test was incomplete.

The test expected 218 surfaces but the existing season actually contains 478 because travel plan/reconciliation dependencies exist across all 330 team fixtures, not only R1/R2/U20.

The model was broader than the test assumption.

Correction:

freeze the observed 478-edge graph.

Closure:

\`289 passed in 27.78s\`

## Verdict

\`CSSA_DEPENDENCY_PROPAGATION_ZERO_SILENT_INCONSISTENCY_V0_PROVEN\`

This proves coherence detection/hardening.

It does not prove that every deadline is met or that every downstream system is automatically updated in the real club.
