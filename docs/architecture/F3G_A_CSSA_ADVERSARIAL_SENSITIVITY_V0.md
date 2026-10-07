# F3G-A — CSSA ADVERSARIAL SENSITIVITY / CALIBRATION PREP V0

Date: 2026-10-07
Status: CLOSED / SYNTHETIC ADVERSARIAL CALIBRATION
Branch: `feat/f3g-a-cssa-adversarial-sensitivity-v0`

## Objective

Attack the synthetic assumptions hard enough to learn which facts actually matter before real field access.

F3G-A is not trying to guess the real CSSA with fake precision.

It deliberately varies resource capacity, authority knowledge and organizational assumptions from near-zero to artificially abundant values, then observes:

- gate changes;
- resource conflicts;
- season pressure;
- priority behavior;
- model blind spots;
- which real-world questions are worth asking first.

All parameter values remain:

`SIMULATED_NOT_OBSERVED`

## Attack surface

Six resource dimensions were varied:

- Administration daily capacity;
- shared vehicle-equivalent pool;
- monthly travel envelope;
- Matchday organizer capacity;
- hospitality capacity;
- main stadium slot capacity.

Resource grid:

`15,120 exhaustive profiles`

Six organizational truth/authority assumptions were also varied independently:

- delegation resolved;
- budget authority resolved;
- FMI status resolved;
- match-change propagation resolved;
- stale-source reconciliation resolved;
- matchday reallocation resolved.

Truth/authority grid:

`64 exhaustive assumption profiles`

The full synthetic season was also rescanned while role capacity was multiplied by:

`0 / 0.25 / 0.5 / 1 / 2 / 4`

Zero is intentionally allowed as an adversarial input.

Negative, non-finite and unknown-resource values fail closed.

## Named operating envelopes

Five synthetic envelopes make the results interpretable:

```text
CRUSHED
TIGHT
BASE_F3F
COMFORTABLE
ABUNDANT
```

Observed gates:

```text
CRUSHED      ALLOW 2 / BLOCK 5 / HOLD 5 / 12 resource conflicts
TIGHT        ALLOW 2 / BLOCK 5 / HOLD 5 / 7 resource conflicts
BASE_F3F     ALLOW 2 / BLOCK 5 / HOLD 5 / 5 resource conflicts
COMFORTABLE  ALLOW 5 / BLOCK 2 / HOLD 5 / 0 resource conflicts
ABUNDANT     ALLOW 5 / BLOCK 2 / HOLD 5 / 0 resource conflicts
```

Important result:

Adding large amounts of synthetic capacity removes some physical-resource BLOCKs, but it does NOT remove the five HOLDs caused by missing authority/knowledge, nor the two remaining truth/coherence BLOCKs.

Therefore:

`MORE RESOURCES != MORE AUTHORITY != BETTER TRUTH`

## Resource-fragile governance scenarios

Across all 15,120 capacity profiles, only three explicit F3F scenarios change gate solely because of physical/shared capacity:

### Vehicles

`F3F_S01_VEHICLE_COLLISION`

Across resource profiles:

- ALLOW: 6,048;
- BLOCK: 9,072.

Threshold in the synthetic scenario:

- capacity below 3 -> conflict;
- capacity at least 3 -> no vehicle double-allocation conflict.

### Hospitality

`F3F_S05_HOSPITALITY_DOUBLE_COMMITMENT`

- ALLOW: 7,560;
- BLOCK: 7,560.

### Stadium slot

`F3F_S12_VENUE_DOUBLE_BOOKING`

- ALLOW: 5,040;
- BLOCK: 10,080.

These thresholds are test mechanics, not CSSA real capacities.

## Authority/truth-sensitive scenarios

Across the 64 truth/authority states, seven scenarios can change gate when a missing fact or authority is resolved:

- admin absence / delegation;
- travel budget approval;
- FMI closure;
- late match change propagation;
- stale source reconciliation;
- role absence/substitution;
- matchday safety vs partner reallocation.

The strongest single calibration variable is:

`DELEGATION_RESOLVED`

because it changes two separate HOLD scenarios.

## Season pressure sensitivity

Resource relief does not necessarily change KX gates, but it radically changes organizational pressure.

Largest observed pressure ranges in the 904-event synthetic season:

```text
RESP_ADMIN_DAILY          range 275 pressure points
TEAM_MANAGER_DAILY        range 254
ADMIN_ACCOUNTING_DAILY    range 146
FORMATION_COORDINATOR     range 27
COMMUNICATION_DAILY       range 26
MANAGER_GENERAL_DAILY     range 26
PARTNERSHIP_MANAGER       range 23
TICKETING_DAILY           range 14
MATCHDAY_ORGANIZER        range 13
TECHNICAL_DIRECTOR        range 0
```

For example, synthetic Administration capacity produces:

```text
0% capacity     -> 278 pressure points
25%             -> 129
50%             -> 28
100% baseline   -> 4
200%            -> 4
400%            -> 3
```

This means the model is highly sensitive to administrative capacity even though that capacity does not directly forge a new KX authority decision.

Therefore:

`GATE COUNT != ORGANIZATIONAL HEALTH`

Pressure must remain visible separately from ALLOW/HOLD/BLOCK.

## Model blind spots discovered

F3G-A found two resources that existed in the F3F resource model but were never exercised by either:

- the season workload map;
- the explicit stress scenarios.

They are:

```text
TECHNICAL_DIRECTOR_DAILY
VOLUNTEER_MATCHDAY_POOL
```

This is a real simulator coverage gap.

It does NOT mean those functions are unimportant at CSSA.

It means our current synthetic model does not yet stress them enough to learn anything from their capacity parameter.

F3G-B / future synthetic expansion should add real/public observations for these layers instead of silently pretending they were tested.

## Highest-value calibration questions

Current order:

1. Who replaces an absent responsible person, and with what signature/validation authority?
2. Who authorizes a travel-budget overrun or reallocation?
3. Who owns an FMI incident until closure and where is closure visible?
4. What is the real hospitality capacity?
5. How are stadium/critical facility conflicts arbitrated?
6. Who arbitrates safety vs partner commitments?
7. Who propagates a validated match change across transport/ticketing/communication?
8. Which source is authoritative when site/organigramme/internal information disagree?
9. What transport/vehicle capacity is actually shared?
10. How much administrative capacity exists and who can absorb urgent overflow?

This is the main purpose of F3G-A: reduce a future field interview from a broad questionnaire to the facts with actual model impact.

## Runtime invariants

Sensitivity-induced gate flips were re-run through the real governed path.

Example:

```text
vehicle capacity 2
 -> resource contradiction
 -> REAL GuardX108
 -> BLOCK

vehicle capacity 3
 -> no hard resource contradiction
 -> REAL GuardX108
 -> ALLOW
 -> bounded READONLY provider only
```

Still preserved:

- KX108_ONLY;
- no memory write;
- no kernel mutation;
- no emits_act;
- no world action;
- no external authority added by sensitivity testing.

## CI closure

Run:

`37561671909`

Result:

```text
232 passed in 26.60s
```

Artifacts:

- JSON sensitivity audit;
- Markdown sensitivity report.

## Verdict

`CSSA_ADVERSARIAL_SENSITIVITY_AND_CALIBRATION_PREP_V0_PROVEN`

F3G-A proves that the model can be attacked over thousands of synthetic operating assumptions without confusing those assumptions with real CSSA facts.
