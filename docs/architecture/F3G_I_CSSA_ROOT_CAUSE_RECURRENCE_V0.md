# F3G-I — CSSA Root-Cause & Recurrence Prevention V0

Date: 2026-10-07
Branch: `feat/f3g-i-cssa-root-cause-recurrence-v0`
Base: `feat/f3g-h-cssa-institutional-relations-v0`
Main: unchanged

## Purpose

F3G-F identified two durability gaps:

- `INCIDENT_ROOT_CAUSE_WORKFLOW`
- `RECURRENCE_PREVENTION_RECEIPT`

F3G-I closes them structurally without claiming the real CSSA incident taxonomy,
approval chain, RCA owners or monitoring windows.

## Lifecycle

```text
OPEN
→ CONTAINED
→ ROOT_CAUSE_ANALYSIS
→ ROOT_CAUSE_CONFIRMED
→ CORRECTIVE_ACTION_DEFINED
→ CORRECTIVE_ACTION_APPLIED
→ VERIFICATION_PENDING
→ VERIFIED_EFFECTIVE
→ RECURRENCE_MONITORING
→ CLOSED
```

The lifecycle is evidence-sensitive.

## Critical semantic rules

```text
HYPOTHESIS != PROVEN ROOT CAUSE
APPLIED CORRECTION != VERIFIED EFFECTIVE CORRECTION
VERIFIED EFFECTIVE != DURABLE NON-RECURRENCE
CLOSED != RECEIPT ELIGIBLE
```

## Fail-closed behavior

- closure requested before root-cause proof -> HOLD;
- confirmed root cause without evidence -> HOLD;
- corrective action claimed applied without proof -> HOLD;
- effective verification without evidence -> HOLD;
- recurrence after effective verification -> BLOCK;
- ineffective correction + closure request -> BLOCK;
- closed case without recurrence monitoring proof -> HOLD;
- recurrent failure signature not linked to prior incident -> HOLD;
- hard RCA deadline missed -> BLOCK.

A normal open triage case can remain ALLOW while surfacing an RCA deadline risk.

## Durable recurrence-prevention receipt

A receipt is generated only when all of the following are proven:

- lifecycle state = CLOSED;
- gate = ALLOW;
- root cause confirmed with evidence;
- corrective action applied with evidence;
- verification = EFFECTIVE with evidence;
- prevention controls identified;
- monitoring evidence present;
- closure authority present;
- no recurrence observed.

The receipt contains a deterministic SHA-256 over the canonical payload.

It is proof metadata only.

It does not apply the corrective action.

## Case catalog

11 synthetic cases:

```text
ALLOW 2
HOLD  6
BLOCK 3
```

All are:

`SIMULATED_NOT_OBSERVED`

## Cockpit

Cases route through:

`PROOF_AUDIT`

into the existing governance/admin reporting views.

No external delivery is enabled.

## F3G-F closure overlay

Historical F3G-F remains unchanged.

F3G-I closes:

```text
ROOT_CAUSE_DURABILITY
  INCIDENT_ROOT_CAUSE_WORKFLOW
  RECURRENCE_PREVENTION_RECEIPT
```

Still unknown before field validation:

- real incident taxonomy;
- real RCA owner/escalation matrix;
- real corrective-action approval chain;
- real monitoring windows by incident type.

## Governance

Preserved:

- KX108_ONLY;
- external_action=false;
- memory_write=false;
- emits_act=false;
- kernel_mutation=false;
- no corrective action execution;
- no invented field evidence.
