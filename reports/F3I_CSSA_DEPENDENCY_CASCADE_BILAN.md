# CSSA / V0.1 — F3I DEPENDENCY CASCADE BILAN

Date: 2026-10-07
Main: unchanged

## Result

We attacked the biggest weakness found by the one-year F3H campaign:

competition/deadline propagation.

F3I runs the cascade across all 330 fixture roots and deliberately changes the upstream fixture state while downstream systems are allowed to become stale, missing, out of order or bound to the wrong proof version.

## Main result

The invariant held:

0 stale dependent states were silently ALLOW.

NORMAL:
- 19 fixture changes
- 3 failures
- 0 BLOCK

HARD:
- 47 fixture changes
- 24 failures
- 9 BLOCK

BREAKER:
- 110 fixture changes
- 77 failures
- 53 BLOCK

As the attack density rises, propagation completeness falls:

0.9123 -> 0.7896 -> 0.4517.

## What now fails closed

A fixture state can no longer be treated as coherent when:

- one dependent still points to the previous fixture version;
- several dependent layers disagree with the root;
- the proof receipt is bound to an old version;
- a dependent node disappeared;
- propagation order cannot be proven;
- the upstream fixture root itself is contradictory;
- an incoming version tries to roll back state;
- the same version number carries two different values;
- an incoming version jumps over an unexplained intermediate version.

## The useful architectural finding

F3H said deadlines are the largest annual failure surface.

F3I refines that:

the dangerous thing is not only "a deadline was missed".

It is that one delayed fixture state can create a split-brain organization:

one time in transport,
another state in FMI,
another state in ticketing,
old hospitality information,
old public communication,
and a receipt that proves the wrong version.

That is now modeled as a coherence failure, not six unrelated small mistakes.

## Forensic finding

F3I found an implementation-quality issue during its own tests.

When a case already had enough contradictions to BLOCK, lower-level evidence such as an order violation could disappear from the risk explanation.

The final verdict was safe, but the explanation was incomplete.

That has been corrected.

The system now preserves all relevant cascade evidence even when one higher-severity condition already determines BLOCK.

## What the BREAKER exposes

In the strongest campaign:

- 22 upstream root conflicts
- 55 proof mismatches
- 27 missing dependent nodes
- 67 propagation-order violations
- 55 stale travel reconciliations
- 26 stale transport plans
- 24 stale FMI states

Again, these are attack outputs, not real Sedan incident counts.

## Next

The next useful phase is F3J:

LONGITUDINAL RECOVERY / SELF-HEALING WITHOUT AUTONOMOUS ACTION.

We now know the system detects cascades.

Next question:

when the correct upstream state finally arrives, can every affected dependent layer be identified, queued for revalidation, rechecked in the right order, and closed with proof without silently skipping one?

That is the recovery half of the same problem.
