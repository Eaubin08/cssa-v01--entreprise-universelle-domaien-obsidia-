# STATUS

Status: F3I_CSSA_DEPENDENCY_CASCADE_HARDENING_CLOSED
Branch: feat/f3i-cssa-dependency-cascade-hardening-v0

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
- F3G-C public-anchored estimated envelope: PASS
- F3G-D public watch/drift: PASS / auxiliary
- F3H one-year longitudinal failure campaign: PASS
- F3I fixture dependency cascade hardening: PASS
- real CSSA internal field evidence: OPEN
- external action: HOLD

## F3H finding carried forward

Largest annual failure surface:

competition / deadline propagation.

F3I targets that failure directly.

## F3I dependency graph

Fixture root version propagates to:

- transport
- travel reconciliation
- FMI
- ticketing
- matchday
- partner hospitality
- volunteers
- communication
- proof receipt

## Cascade campaigns

All campaigns cover the same 330 fixture roots.

NORMAL:
- 19 changed fixtures
- 3 failures
- 327 ALLOW / 3 HOLD / 0 BLOCK
- silent stale ALLOW = 0

HARD:
- 47 changed
- 24 failures
- 306 ALLOW / 15 HOLD / 9 BLOCK
- root conflicts 4
- proof mismatch 11
- missing nodes 2
- order violations 3
- silent stale ALLOW = 0

BREAKER:
- 110 changed
- 77 failures
- 253 ALLOW / 24 HOLD / 53 BLOCK
- root conflicts 22
- proof mismatch 55
- missing nodes 27
- order violations 67
- silent stale ALLOW = 0

## Propagation completeness

Mean completeness for changed fixtures:

- NORMAL 0.9123
- HARD 0.7896
- BREAKER 0.4517

## Version invariants

- rollback -> BLOCK
- same version + different value -> BLOCK
- unexplained version gap -> HOLD
- next sequential version -> ALLOW

## Important invariant

STALE DEPENDENT STATE MUST NEVER BE ALLOW.

Current proof:

0 silent stale ALLOW across NORMAL/HARD/BREAKER.

## Forensic improvement

During F3I, higher-severity BLOCK conditions were found to hide some lower-level propagation evidence in risk flags.

Corrected:

missing-node, order-violation and proof-mismatch evidence remains visible even when another contradiction already determines BLOCK.

VERDICT SAFETY != EXPLANATION COMPLETENESS.

## Governance

Preserved:

- KX108_ONLY
- no external action
- no world action
- no kernel mutation
- no memory write
- no emits_act
- all campaign events SIMULATED_NOT_OBSERVED
- no real CSSA incident claim

## CI

Semantic closure run:

37566240548

- 296 passed in 13.83s
- artifact 11458378734
- SUCCESS

## Next

F3J — dependency recovery / governed revalidation.

Question:

after a cascade is detected and the correct upstream fixture state becomes available, can the system:

- identify every affected dependent;
- order revalidation by dependency;
- preserve HOLD/BLOCK until prerequisites are current;
- prove each dependent was rebound to the correct root version;
- close the cascade without external autonomous action?

No merge to main.
