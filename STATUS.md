# STATUS

Status: F3G_C_CSSA_PUBLIC_ANCHORED_ENVELOPE_CLOSED
Branch: `feat/f3g-c-cssa-public-anchored-envelope-v0`

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
- real CSSA internal field evidence: OPEN
- external action: HOLD

## Current usable approximation

Three replaceable envelopes:

```text
LOW_CONSTRAINED
  2 ALLOW / 5 BLOCK / 5 HOLD
  9 resource conflicts
  56 season pressure points

CENTRAL_WORKING
  2 ALLOW / 5 BLOCK / 5 HOLD
  5 resource conflicts
  4 season pressure points

HIGH_CAPACITY
  4 ALLOW / 3 BLOCK / 5 HOLD
  1 resource conflict
  3 season pressure points
```

## Truth boundary

- public anchors remain PUBLIC_CONFIRMED / SECONDARY_CORROBORATED
- capacities remain ESTIMATED
- simulation capacity units are not staff headcount
- 8 private facts remain UNKNOWN

## Replaceability

15 estimated parameters can later be replaced by real evidence and the same suite rerun.

No architectural redesign is required merely because a real count/budget/capacity differs.

## CI

- run `37562759225`
- `254 passed in 18.51s`
- artifact `11456744300`
- SUCCESS

## Next

The technical system can now continue without waiting for internal access.

Next useful work:

1. freeze F3G-C as the current approximation baseline;
2. make public-shadow refresh repeatable over time;
3. compare future public observations against this baseline;
4. when field evidence becomes available, replace only affected parameters and rerun.

No merge to main.
