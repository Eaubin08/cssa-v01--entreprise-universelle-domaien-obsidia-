# F3H-D — CSSA → Native CRM/TASKS Bridge V0

Date: 2026-10-07

Branch:
`feat/cssa-native-ops-bridge-v0`

Base:
`feat/f3h-c-universal-world-action-pre-execution-v0`

Draft PR:
`#11`

Canonical upstream:
`Eaubin08/obsidia-x108-proofs@feat/native-tasks-crm-v0`

Main merge:
`NO`

## Purpose

Connect the CSSA métier domain to Obsidia-owned native CRM and TASKS without
copying or reimplementing the canonical TASKS/CRM models inside the CSSA repo.

CSSA remains responsible for métier translation.

Obsidia native_ops remains responsible for canonical operational state.

## Canonical intake

One CSSA administrative case is translated to:

```text
CSSA case
   ↓
CRM CASE record
   ↓
CRM intake interaction

CSSA case
   ↓
TASKS native task
   ↓
CRM follow-up
      └── task_ref → native task
```

The intake is generic across CSSA workflows.

Proven fixtures:

- CONTRACT_COMPLIANCE
- INSTITUTIONAL_RELATION
- MATCHDAY_OPERATIONS
- INCIDENT_ROOT_CAUSE
- SUPPLIER_FOLLOWUP

All fixtures remain:

`SIMULATED_NOT_OBSERVED`

They are not claimed as real CSSA field evidence.

## Governance

The bridge creates four exact native mutations:

1. CREATE_RECORD / CRM CASE
2. CREATE_TASK
3. APPEND_INTERACTION
4. CREATE_FOLLOWUP

Each mutation is separately translated through the canonical upstream native
bridge into:

```text
NativeMutation
→ exact mutation_hash
→ exact target pre-state hash
→ exact HumanApproval
→ WORLD_ACTION_PRE_EXECUTION
→ real GuardX108
→ immutable KX108 decision record
```

All four must return:

`ALLOW`

before the first canonical native mutation is committed.

## Fail-closed batch boundary

The bridge adds an intake-level transaction boundary:

### Phase 1 — target check

All four canonical targets must be absent.

### Phase 2 — KX108 PRE

All four mutations receive independent KX108 PRE decisions.

If one is HOLD or BLOCK:

```text
canonical_mutation_count = 0
```

No partial CRM/TASK state is created.

### Phase 3 — shadow semantic apply

After all four ALLOW results, the full mutation sequence is applied to an
isolated temporary native store.

This verifies:

- CRM case validity
- TASK validity
- CRM interaction link
- CRM follow-up link
- CRM follow-up → native TASK reference

A semantic failure occurs before canonical state mutation.

### Phase 4 — canonical apply

Every target pre-state is rechecked immediately before canonical apply.

A concurrent state change fails closed with:

`CSSA_NATIVE_PRESTATE_CHANGED_BEFORE_COMMIT`

Each successful mutation produces the upstream native append-only receipt.

## Source-of-truth boundary

The CSSA repository does not contain a second TASKS/CRM implementation.

It consumes:

- `periphery/native_ops/tasks_native_v0.py`
- `periphery/native_ops/crm_native_v0.py`
- `periphery/native_ops/world_action_bridge_v0.py`

from the explicit upstream branch.

Therefore:

```text
CSSA = métier translation
Obsidia native_ops = canonical CRM/TASKS state
KX108 = decision authority
External SaaS = not required
```

## Proven no-SaaS flow

The committed result explicitly reports:

```text
external_action = false
external_saas_required = false
decision_authority = KX108_ONLY
```

Calendar/Gmail remain optional world-facing providers after native case/task
state exists.

## Proof

Run:

`37609707350`

Result:

`181 passed in 0.91s`

Conclusion:

`SUCCESS`

The proof includes the new native bridge plus F3G-G through F3H-C execution
regressions.

## Verdict

`CSSA_NATIVE_CRM_TASKS_BRIDGE_V0_PROVEN`

## Next

The next meaningful step is no longer a TASKS/CRM architecture problem.

It is to feed real CSSA read-only/intake evidence into this bridge:

```text
real CSSA mail / document / calendar / public or internal case
→ classify
→ CSSA case
→ native CRM + TASK
→ KX108 governed follow-up
→ optional Calendar/Gmail provider action
```

Until real internal evidence is available, fixtures remain simulation only.
