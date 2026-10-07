# F3G-I — CSSA ROOT-CAUSE & RECURRENCE PREVENTION RECEIPT

Date: 2026-10-07

## Branch

`feat/f3g-i-cssa-root-cause-recurrence-v0`

Base:

`feat/f3g-h-cssa-institutional-relations-v0`

Main mutation: `NO`
Merge: `NO`
Draft PR: `#6`

## Implemented surfaces

- `organizations/cssa/root_cause/root_cause_recurrence_v0.py`
- `organizations/cssa/root_cause/root_cause_cases_v0.json`
- `organizations/cssa/root_cause/f3g_i_coverage_closure_overlay_v0.json`
- `organizations/cssa/root_cause/__init__.py`
- `tests/test_f3g_i_cssa_root_cause_recurrence_v0.py`
- `.github/workflows/f3g-i-cssa-root-cause-recurrence.yml`

## Initial proof

Run:

`37589585121`

Result:

`343 passed in 26.96s`

Conclusion:

`SUCCESS`

## Case distribution

- 11 simulated cases
- 2 ALLOW
- 6 HOLD
- 3 BLOCK

## Proven boundaries

- hypothesis != proven root cause
- applied correction != verified effectiveness
- verified effectiveness != durable non-recurrence
- recurrence after effective verification -> BLOCK
- closed without monitoring proof -> HOLD
- recurrent signature without prior incident linkage -> HOLD
- hard RCA deadline missed -> BLOCK
- durable receipt requires complete ALLOW closure

## F3G-F gaps closed

- `INCIDENT_ROOT_CAUSE_WORKFLOW`
- `RECURRENCE_PREVENTION_RECEIPT`

## Still unknown

- `REAL_INCIDENT_TAXONOMY`
- `REAL_RCA_OWNER_AND_ESCALATION_MATRIX`
- `REAL_CORRECTIVE_ACTION_APPROVAL_CHAIN`
- `REAL_MONITORING_WINDOWS_BY_INCIDENT_TYPE`

## Invariants

- KX108_ONLY
- external_action=false
- memory_write=false
- emits_act=false
- kernel_mutation=false
- catalog = SIMULATED_NOT_OBSERVED

## Verdict

`CSSA_ROOT_CAUSE_AND_RECURRENCE_PREVENTION_V0_PROVEN`
