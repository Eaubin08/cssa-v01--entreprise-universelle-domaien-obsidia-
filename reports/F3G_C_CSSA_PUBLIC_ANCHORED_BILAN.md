# CSSA / V0.1 — F3G-C PUBLIC-ANCHORED EXTRAPOLATION BILAN

Date: 2026-10-07
Main: unchanged

## Executive result

We now have a usable approximate Sedan operating model without pretending the unknowns are real facts.

```text
6 public anchors
15 replaceable estimated parameters
3 operating envelopes
8 unknown private facts explicitly preserved
254 tests PASS
```

## What the approximation says

The CENTRAL_WORKING profile is currently the useful working model:

```text
2 ALLOW
5 BLOCK
5 HOLD
5 resource conflicts
4 season pressure points
```

That is intentionally close to F3F baseline.

The LOW profile produces 56 season pressure points.

The HIGH profile drops to 3 pressure points and removes most physical conflicts, but still leaves 5 HOLDs.

So the architecture is not dependent on one lucky parameter choice.

## What matters most later

Real field data should first replace assumptions that F3G-A showed actually matter:

- delegation/substitution;
- administrative capacity;
- transport/shared vehicles;
- travel-budget approval;
- FMI ownership;
- match-change propagation;
- volunteer availability;
- hospitality capacity.

We do not need every detail of the club before improving the model.

## Two previously weak layers

Technical direction and volunteers are now explicitly exercised.

Central approximation:

- technical-direction synthetic crunch: absorbed;
- volunteer synthetic demand of 24 capacity units: pressure remains.

This is NOT a claim that Sedan has 20 volunteers or needs exactly 24.

It tells us what to ask/observe later.

## Practical consequence

We can continue building and testing now.

When your contact or CSSA supplies one real fact, we swap that parameter, rerun, and see whether:

- gates change;
- pressure changes;
- priorities change;
- persona reports change.

That is much cheaper than rebuilding the domain from scratch.
