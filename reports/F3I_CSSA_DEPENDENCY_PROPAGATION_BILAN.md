# CSSA / V0.1 — F3I DEPENDENCY PROPAGATION BILAN

Date: 2026-10-07
Branch: feat/f3i-cssa-dependency-propagation-v0
Main: unchanged

## Why F3I exists

F3H found that the biggest annual failure surface is competition/deadline propagation.

F3I attacked that exact weakness.

We built the dependency graph around every fixture and checked whether one upstream change can leave transport, FMI, ticketing, matchday, partners, volunteers or communication on stale state.

## Scale

\`\`\`text
330 fixture roots
478 downstream dependency surfaces
3 annual propagation attack modes
289 regression tests
\`\`\`

## Result

NORMAL:
- 319 ALLOW
- 9 HOLD
- 2 BLOCK
- 0 silent inconsistencies

HARD:
- 263 ALLOW
- 57 HOLD
- 10 BLOCK
- 0 silent inconsistencies

BREAKER:
- 165 ALLOW
- 129 HOLD
- 36 BLOCK
- 0 silent inconsistencies

## What changed architecturally

Before:

a fixture could have several related events in the synthetic season, but there was no explicit invariant proving that every dependent surface was on the same fixture revision.

Now:

\`\`\`text
fixture revision N
      ↓
dependency graph
      ↓
travel revision N
FMI revision N
ticketing revision N
matchday revision N
partners revision N
communication revision N
      ↓
anything else = stale / missing / contradictory
      ↓
HOLD or BLOCK
\`\`\`

## Strongest result

The important number is not the number of BLOCKs.

It is:

\`silent inconsistency = 0\`

Under BREAKER, 302 dependent surfaces become stale/blocked during attacks.

They are all detected.

None stays silently READY.

## Useful failure discovered during the build

The first test expected 218 dependency surfaces.

The actual graph contained 478.

Reason:

our earlier mental count focused too much on R1/R2/U20, while F3E already creates travel-plan and travel-reconciliation dependencies for away fixtures across all team structures.

So the test itself undercounted the actual model.

That is a useful audit finding: the dependency graph is broader than the part we were looking at.

## What F3I does NOT solve yet

F3I prevents silent incoherence.

It does not yet reduce the 1,408 annual F3H deadline misses.

In other words:

\`\`\`text
F3H found: "we are late"
F3I proves: "if upstream changes, downstream inconsistency cannot hide"
\`\`\`

The next question is:

> Can we use the dependency graph to propagate priority/deadlines early enough that the annual failure count actually drops?

That should be the next longitudinal comparison rather than another isolated test.
