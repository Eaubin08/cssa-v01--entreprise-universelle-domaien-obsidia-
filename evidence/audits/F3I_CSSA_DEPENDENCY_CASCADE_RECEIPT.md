# F3I CSSA DEPENDENCY CASCADE HARDENING RECEIPT

Date: 2026-10-07
Branch: feat/f3i-cssa-dependency-cascade-hardening-v0

## Scope

Attack fixture-state propagation across all dependent operational layers.

## Fixture coverage

330 fixture roots.

## Dependency surface

- transport plan
- travel reconciliation
- FMI
- ticketing
- matchday
- partner hospitality
- volunteers
- communication
- proof receipt

## Campaign results

NORMAL:
- changed fixtures 19
- failures 3
- ALLOW 327
- HOLD 3
- BLOCK 0
- silent stale ALLOW 0

HARD:
- changed fixtures 47
- failures 24
- ALLOW 306
- HOLD 15
- BLOCK 9
- root conflicts 4
- receipt mismatch 11
- missing nodes 2
- order violations 3
- silent stale ALLOW 0

BREAKER:
- changed fixtures 110
- failures 77
- ALLOW 253
- HOLD 24
- BLOCK 53
- root conflicts 22
- receipt mismatch 55
- missing nodes 27
- order violations 67
- silent stale ALLOW 0

## Version hardening

Proven:

- rollback -> BLOCK
- same version/different value -> BLOCK
- version gap -> HOLD
- sequential next version -> ALLOW

## Implementation findings

1. A test incorrectly expected Communication on MONTHLY reporting.
   Correct routing is WEEKLY/BIWEEKLY.

2. Lower-level order/missing/proof evidence could be omitted once a stronger BLOCK contradiction existed.
   Corrected so forensic evidence remains complete.

## Real Guard proof

Representative ALLOW/HOLD/BLOCK assessments cross real GuardX108.

Preserved:

- KX108_ONLY
- memory_write=false
- kernel_mutation=false
- emits_act=false
- world_action_allowed=false
- provider only on ALLOW

## CI

Run:
37566240548

296 passed in 13.83s.

Artifact:
11458378734

## Claim

F3I_FIXTURE_DEPENDENCY_CASCADE_CLOSED

No merge to main.
