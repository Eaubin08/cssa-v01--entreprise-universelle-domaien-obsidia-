# F3I CSSA DEPENDENCY PROPAGATION RECEIPT

Date: 2026-10-07
Branch: feat/f3i-cssa-dependency-propagation-v0

## Graph

- fixture roots: 330
- downstream dependency surfaces: 478
- missing required surfaces: 0
- unruled case types: 0

## Annual campaigns

NORMAL:
- ALLOW 319
- HOLD 9
- BLOCK 2
- stale/blocked surfaces 5
- silent inconsistency 0

HARD:
- ALLOW 263
- HOLD 57
- BLOCK 10
- stale/blocked surfaces 144
- silent inconsistency 0

BREAKER:
- ALLOW 165
- HOLD 129
- BLOCK 36
- stale/blocked surfaces 302
- silent inconsistency 0

## Core invariant

Across all campaigns:

\`silent_inconsistency_total = 0\`

## Real Guard

Representative dependency ALLOW/HOLD/BLOCK cases cross real GuardX108.

Preserved:
- KX108_ONLY
- no memory write
- no kernel mutation
- no emits_act
- no world action
- provider only on ALLOW

## First-run defect

Run 1:
- 288 PASS / 1 FAIL
- test expected 218 dependency surfaces
- actual recovered graph contained 478

Cause:
all-team away travel dependencies had been undercounted in the test expectation.

Correction:
actual dependency graph count frozen at 478.

## Closure

Run:
\`37565966143\`

Job:
\`112613622306\`

Result:
\`289 passed in 27.78s\`

Artifact:
\`11458634183\`

## Claim

\`F3I_DEPENDENCY_PROPAGATION_HARDENING_CLOSED\`

No merge to main.
