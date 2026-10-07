# CSSA / V0.1 — F3G-I ROOT-CAUSE & RECURRENCE PREVENTION BILAN

Date: 2026-10-07
Branch: `feat/f3g-i-cssa-root-cause-recurrence-v0`
Base: `feat/f3g-h-cssa-institutional-relations-v0`
Main: unchanged
Draft PR: #6 — no merge requested

## Executive result

F3G-I closes the two durability gaps identified in F3G-F:

- `INCIDENT_ROOT_CAUSE_WORKFLOW`
- `RECURRENCE_PREVENTION_RECEIPT`

Initial closure proof:

```text
11 simulated RCA cases
2 ALLOW
6 HOLD
3 BLOCK

343 / 343 tests PASS
run 37589585121
26.96 s
```

## Proven distinctions

The system now keeps these states separate:

```text
incident observed
!= root cause known

root cause hypothesis
!= root cause proven

corrective action applied
!= correction effective

correction effective
!= recurrence prevented

case closed
!= durable closure receipt allowed
```

## Durable receipt

A recurrence-prevention receipt is produced only for a complete, auditable
closure.

The proof includes:

- incident id;
- root-cause reference + evidence;
- corrective-action reference + evidence;
- verification evidence;
- prevention controls;
- monitoring evidence;
- closure authority;
- KX108_ONLY boundary;
- deterministic SHA-256.

## Recurrence invalidates closure

If the same problem recurs after an EFFECTIVE verification claim, the case
BLOCKs.

A CLOSED case with observed recurrence also BLOCKs and cannot produce a
recurrence-prevention receipt.

## Historical trace

F3G-F remains the historical gap snapshot.

F3G-I adds a closure overlay rather than rewriting the original assessment.

## Still unknown

Before real field calibration:

- `REAL_INCIDENT_TAXONOMY`
- `REAL_RCA_OWNER_AND_ESCALATION_MATRIX`
- `REAL_CORRECTIVE_ACTION_APPROVAL_CHAIN`
- `REAL_MONITORING_WINDOWS_BY_INCIDENT_TYPE`

## Governance

Preserved:

- KX108_ONLY
- external_action=false
- memory_write=false
- emits_act=false
- kernel_mutation=false

## Current verdict

`CSSA_ROOT_CAUSE_AND_RECURRENCE_PREVENTION_V0_PROVEN`

## Next

Next F3G-F gap closure target:

`MATCHDAY_BUVETTE_RESTAURATION`

No merge to main.
