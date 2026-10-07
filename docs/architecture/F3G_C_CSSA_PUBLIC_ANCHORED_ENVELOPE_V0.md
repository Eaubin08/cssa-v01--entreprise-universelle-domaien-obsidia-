# F3G-C — CSSA PUBLIC-ANCHORED OPERATING ENVELOPE V0

Date: 2026-10-07
Status: CLOSED / ESTIMATED PUBLIC-ANCHORED
Branch: `feat/f3g-c-cssa-public-anchored-envelope-v0`

## Objective

Keep moving without private CSSA access while refusing fake precision.

F3G-C combines:

- hard public anchors from F3G-B;
- the adversarial sensitivity knowledge from F3G-A;
- the F3F resource/stress model;
- the 904-event F3E season.

It produces replaceable LOW / CENTRAL / HIGH operating envelopes.

## Truth boundary

All operating capacities remain:

`ESTIMATED`

The public facts used to anchor the model remain separately:

- PUBLIC_CONFIRMED;
- SECONDARY_CORROBORATED.

No estimated capacity is promoted to a real CSSA headcount, fleet size, budget or staffing fact.

## Public anchors

The envelope is anchored by six current public facts/observations:

- 19 public team structures;
- unresolved/current Manager Général public state;
- technical-direction structure exists;
- volunteer program exists;
- 13 R1 home league matches in the subscription;
- recent multi-team public workload exists.

## Replaceable parameters

15 resource parameters remain replaceable:

- administration;
- accounting;
- Manager Général function;
- technical direction;
- formation coordination;
- team management/intendance;
- matchday organization;
- partnerships;
- communication;
- ticketing;
- shared vehicles;
- hospitality;
- stadium slot;
- travel envelope;
- volunteer capacity.

Role capacities use abstract SIMULATION_CAPACITY_UNIT.

They are not people counts.

## Three operating envelopes

### LOW_CONSTRAINED

Result:

```text
ALLOW 2 / BLOCK 5 / HOLD 5
9 resource conflicts
56 season pressure points
technical-direction crunch = pressure
volunteer matchday demand = pressure
```

### CENTRAL_WORKING

Result:

```text
ALLOW 2 / BLOCK 5 / HOLD 5
5 resource conflicts
4 season pressure points
technical-direction crunch = no pressure
volunteer matchday demand = pressure
```

### HIGH_CAPACITY

Result:

```text
ALLOW 4 / BLOCK 3 / HOLD 5
1 resource conflict
3 season pressure points
technical-direction crunch = no pressure
volunteer matchday demand = no pressure
```

## Important interpretation

The central envelope reproduces the F3F governance surface while giving us a practical working approximation.

The high-capacity envelope reduces physical/resource conflicts but still leaves five HOLDs.

Therefore the core F3G-A conclusion survives the public-anchored extrapolation:

`MORE CAPACITY DOES NOT RESOLVE MISSING AUTHORITY OR UNKNOWN PRIVATE FACTS`

## Blind-spot extension

F3G-A found technical-direction and volunteer capacity untested.

F3G-B confirmed both structures/workflows publicly exist.

F3G-C now exercises both as estimated pressure scenarios:

- four same-day technical/academy escalations;
- 24 abstract volunteer-capacity units for a synthetic matchday.

The resulting threshold behavior is explicitly profile-dependent and remains ESTIMATED.

## Unknowns deliberately preserved

Eight important facts remain unknown:

- real employee headcount by role;
- real vehicle fleet;
- real travel budget;
- real volunteer count per match;
- real simultaneous hospitality capacity;
- real delegation/signature scope;
- real internal approval chain;
- real Association/SAS operating split.

## Future field adaptation

When real evidence arrives, the intended operation is:

```text
current estimated parameter
        ↓
validated field/public evidence
        ↓
replace parameter value
        ↓
rerun same stress/sensitivity/runtime/reporting suite
        ↓
compare delta
```

The architecture is not redesigned for every new fact.

## CI

Run:
`37562759225`

Result:

```text
254 passed in 18.51s
```

Artifact:
`11456744300`

## Verdict

`CSSA_PUBLIC_ANCHORED_REPLACEABLE_OPERATING_ENVELOPE_V0_PROVEN`
