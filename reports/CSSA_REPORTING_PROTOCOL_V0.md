# CSSA / V0.1 — REPORTING PROTOCOL V0

Status: ACTIVE

## Required report after each milestone

Every F3.x milestone must close with a report containing:

1. Objective
2. Inputs / sources
3. What changed
4. Test results
5. Failures discovered
6. Fixes applied
7. Proven claims
8. Non-proven claims
9. Open risks
10. Data/privacy boundary
11. Next decision

## Weekly/global summary format

```text
DONE
BLOCKED
RISKY
NEW FACTS
NEW UNKNOWNs
TEST REGRESSION
ARCHITECTURE IMPACT
FIELD EVIDENCE STATUS
NEXT DECISION
```

## Truth rule

Never mix:

- PUBLIC_CONFIRMED
- SECONDARY_CORROBORATED
- ESTIMATED
- SIMULATED_NOT_OBSERVED
- REAL_FIELD_EVIDENCE
- UNKNOWN_PRIVATE

## Main rule

Reports may document merge-readiness, but no report authorizes a push or merge to main.
