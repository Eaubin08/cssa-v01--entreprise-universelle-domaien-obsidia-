# F3I — CSSA FIXTURE DEPENDENCY CASCADE HARDENING V0

Date: 2026-10-07
Status: CLOSED / SYNTHETIC CASCADE HARDENING
Branch: feat/f3i-cssa-dependency-cascade-hardening-v0

## Why F3I exists

F3H showed that the largest annual failure surface was not generic finance or marketing.

It was the competition/deadline chain.

F3I therefore attacks one upstream fixture state and follows every dependent layer that can remain stale after a change.

The tested chain is:

fixture state
-> transport plan
-> travel reconciliation
-> FMI
-> ticketing
-> matchday
-> partner hospitality
-> volunteers
-> communication
-> proof receipt

The rule is simple:

one upstream change must not silently leave downstream layers bound to an older version.

## Dependency model

The fixture state is versioned.

Every dependent node records the root fixture version it is based on.

A virtual PROOF_RECEIPT is also version-bound.

The V0 dependency graph lives in:

organizations/cssa/dependency/fixture_dependency_graph_v0.json

Main invariants:

- dependent version must match root version;
- unresolved root cannot silently publish downstream state;
- partial propagation cannot remain invisible;
- proof receipt must bind the current root version;
- rollback/out-of-order version update fails closed;
- same version with a different value is a contradiction;
- version gaps require review.

## Annual coverage

F3I reuses the 365-day F3H corpus.

It indexes all season fixture roots:

330 fixtures.

All three cascade campaigns run against the same 330 roots.

## Attack modes

NORMAL:
- fixture change every 17th root;
- occasional single stale dependent;
- occasional stale proof receipt.

HARD:
- fixture change every 7th root;
- single/multi-layer staleness;
- root conflicts;
- proof mismatch;
- missing nodes;
- update-order violations.

BREAKER:
- fixture change every 3rd root;
- denser stale propagation;
- frequent root conflicts;
- frequent proof mismatch;
- missing nodes;
- order violations.

All values remain SIMULATED_NOT_OBSERVED.

## Gate policy

Full propagation:
ALLOW.

One stale operational dependent:
HOLD.

Stale proof receipt:
HOLD.

Missing dependent:
HOLD unless a stronger contradiction already BLOCKs the case.

Order not proven:
HOLD unless a stronger contradiction already BLOCKs the case.

Two or more stale operational layers:
BLOCK.

Unresolved upstream root conflict:
BLOCK.

The important invariant is:

STALE DEPENDENT STATE MUST NEVER BE ALLOW.

## Version-transition hardening

F3I also tests update mechanics directly.

Current version 5, incoming version 4:
BLOCK / rollback rejected.

Version 5 with one value, another different value also claiming version 5:
BLOCK / identity collision.

Current version 5, incoming version 7:
HOLD / intermediate version and provenance missing.

Current version 5, incoming version 6:
ALLOW.

This prevents the cascade layer from accepting a clean-looking state whose version history is structurally invalid.

## Campaign results

### NORMAL

330 fixture roots.

19 changed fixtures.

Result:

- ALLOW: 327
- HOLD: 3
- BLOCK: 0
- failures: 3
- receipt mismatch: 2
- missing nodes: 0
- order violations: 0
- mean changed propagation completeness: 0.9123
- silent stale ALLOW: 0

### HARD

330 fixture roots.

47 changed fixtures.

Result:

- ALLOW: 306
- HOLD: 15
- BLOCK: 9
- failures: 24
- root conflicts: 4
- receipt mismatches: 11
- missing nodes: 2
- order violations: 3
- mean changed propagation completeness: 0.7896
- silent stale ALLOW: 0

### BREAKER

330 fixture roots.

110 changed fixtures.

Result:

- ALLOW: 253
- HOLD: 24
- BLOCK: 53
- failures: 77
- root conflicts: 22
- receipt mismatches: 55
- missing nodes: 27
- order violations: 67
- mean changed propagation completeness: 0.4517
- silent stale ALLOW: 0

## Most exposed synthetic nodes in BREAKER

- PROOF_RECEIPT: 55 stale
- TRAVEL_RECONCILIATION: 55 stale
- TRANSPORT_PLAN: 26 stale
- FMI: 24 stale
- COMMUNICATION: 8 stale
- MATCHDAY: 4 stale

These counts reflect the deterministic attack pattern. They are not claims that those CSSA functions fail at those rates.

## What was actually hardened

Before F3I, the season model could represent a match change and downstream events, but there was no explicit version contract proving that all downstream layers referred to the same fixture state.

After F3I:

- every cascade assessment knows its root version;
- stale dependents are explicit;
- missing nodes are explicit;
- propagation order is explicit;
- proof receipt version is explicit;
- rollback/version collision/version gap are explicit;
- all cascade findings route into the existing persona cockpit;
- representative ALLOW/HOLD/BLOCK cases cross the real GuardX108.

## Implementation failures found

### Failure 1 — reporting test assumed wrong cadence

The first F3I CI used MONTHLY to assert a Communication persona view.

But Communication is WEEKLY/BIWEEKLY in the routing contract.

The test was wrong, not the routing system.

Corrected to BIWEEKLY.

### Failure 2 — lower-level cascade evidence could be hidden by a stronger BLOCK

When a scenario had both multi-layer stale state and an order violation, the BLOCK contradiction was preserved but the order-violation risk flag was not.

That made the final verdict safe but the forensic explanation incomplete.

F3I was corrected so missing-node, order-violation and receipt-mismatch evidence remains visible even when a stronger BLOCK already wins.

This is important for auditability:

VERDICT SAFETY != EXPLANATION COMPLETENESS.

## Runtime proof

Representative F3I ALLOW/HOLD/BLOCK assessments cross:

F3I cascade
-> Administration adapter
-> F2.5 aggregate-only resolver
-> real DomainAggregate
-> real GuardX108
-> canonical decision lifecycle
-> bounded READONLY provider only on ALLOW

Preserved:

- KX108_ONLY
- memory_write=false
- kernel_mutation=false
- emits_act=false
- world_action_allowed=false
- HOLD/BLOCK never invoke provider

## CI proof

Semantic closure run:

37566240548

Result:

296 passed in 13.83s.

Artifact:

11458378734

## Verdict

CSSA_FIXTURE_DEPENDENCY_CASCADE_HARDENING_V0_PROVEN

The current model now fails closed when a fixture change leaves stale, missing, out-of-order or unproven downstream state.
