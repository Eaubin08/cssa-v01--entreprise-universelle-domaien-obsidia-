# STATUS

Status: F3I_CSSA_DEPENDENCY_PROPAGATION_CLOSED
Branch: feat/f3i-cssa-dependency-propagation-v0

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
- F3I dependency propagation hardening: PASS
- real CSSA internal field evidence: OPEN
- external action: HOLD

## F3H failure baseline

Across 9 annual runs:

- DEADLINE_MISS: 1408
- RESOURCE_STARVATION: 319
- YEAR_END_UNRESOLVED: 200
- SHARED_ASSET_COLLISION: 105
- UNRESOLVED_HOLD_AGING: 78
- TRAVEL_BUDGET_PRESSURE: 62
- BACKLOG_SATURATION: 52
- UNRESOLVED_BLOCK_AGING: 39

Dominant weakness:
competition/deadline propagation.

## F3I dependency graph

Recovered from the existing annual corpus:

- 330 fixture roots
- 478 downstream dependency surfaces
- 0 missing required surfaces
- 0 unruled dependency case types

Main downstream surfaces:

- travel
- travel proof/reconciliation
- FMI
- communication
- matchday
- partners/hospitality
- volunteers
- ticketing

## F3I invariant

A dependent surface cannot be READY if:

- its revision is behind the fixture root
- its revision is ahead of the fixture root
- root authority is not final
- propagation deadline is exceeded
- required dependent surface is missing

One stale required surface is enough to fail closed to HOLD.

Structural revision/authority contradictions BLOCK.

## Annual propagation attack

NORMAL:
- ALLOW 319
- HOLD 9
- BLOCK 2
- stale/blocked surfaces 5

HARD:
- ALLOW 263
- HOLD 57
- BLOCK 10
- stale/blocked surfaces 144

BREAKER:
- ALLOW 165
- HOLD 129
- BLOCK 36
- stale/blocked surfaces 302

Across all attacks:

\`silent_inconsistency_total = 0\`

## First F3I finding

First run:
- 288 PASS / 1 FAIL

The test expected 218 dependency surfaces.

Actual existing annual graph:
- 478 surfaces

Reason:
the previous expectation undercounted travel-plan and travel-reconciliation dependencies across all team structures.

Correction:
freeze the actual 478-surface graph.

## Runtime governance

Representative ALLOW/HOLD/BLOCK propagation cases cross real GuardX108.

Preserved:

- KX108_ONLY
- provider only on ALLOW
- no memory write
- no kernel mutation
- no emits_act
- no world action
- external delivery disabled

## CI closure

- run 37565966143
- job 112613622306
- 289 passed in 27.78s
- artifact 11458634183
- SUCCESS

## Verdict

\`CSSA_DEPENDENCY_PROPAGATION_ZERO_SILENT_INCONSISTENCY_V0_PROVEN\`

F3I prevents dependency inconsistency from remaining silent.

It does not yet prove that the F3H annual deadline count is reduced.

## Next

F3J — longitudinal dependency-aware scheduling comparison.

Run the 365-day campaign twice:

1. existing F3H priority/deadline behavior
2. dependency-aware behavior using the F3I graph

Measure whether dependency-aware anticipation reduces:

- DEADLINE_MISS
- RESOURCE_STARVATION
- BACKLOG_SATURATION
- YEAR_END_UNRESOLVED

without:

- creating silent inconsistency
- bypassing HOLD/BLOCK
- inventing authority
- increasing external action

No merge to main.
