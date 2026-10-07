# F3H-A — CSSA Decision Execution Contract Dry-Run V0

Date: 2026-10-07
Branch: `feat/f3h-a-cssa-decision-execution-contract-v0`
Base: `feat/f3g-j-cssa-matchday-buvette-restauration-v0`
Main: unchanged

## Purpose

F3G-J closes the final business-workflow gap. The only remaining structural gap
is now:

`DECISION_EXECUTION`

F3H-A opens that phase without enabling any real connector or world action.

Current maximum authority:

`HUMAN_APPROVED_DRY_RUN`

## Reused Obsidia authority model

F3H-A does not create a second sovereign rail.

The upstream Obsidia runtime already proves:

- KX108 is the only decision authority;
- decision records are persisted and verified;
- HOLD/BLOCK do not invoke the provider;
- world action remains dry-run only.

F3H-A uses that existing runtime for CSSA action proposals.

## Action surfaces

Four surfaces are modeled:

- MAIL
- CALENDAR
- CRM
- TASKS

Only proposal/draft operations exist in F3H-A.

No real SEND/CREATE/UPDATE connector operation is available.

## Authority chain

```text
business case
→ immutable ActionProposal
→ proposal SHA-256
→ real KX108 runtime decision
→ verified decision record
→ separate exact HumanApproval evidence
→ target pre-state recheck
→ surface dry-run
→ deterministic dry-run receipt
```

## Critical semantic rules

```text
KX108 ALLOW != permission to skip human approval
HumanApproval != KX108 authority
HumanApproval for proposal A != approval for proposal B
approved pre-state != changed current pre-state
dry-run != world action
```

## ActionProposal binding

The proposal hash binds:

- proposal id;
- surface;
- operation;
- target reference;
- payload;
- source case references;
- evidence references;
- exact expected target-state hash;
- human-approval requirement;
- KX108_ONLY authority boundary.

Any change produces another proposal hash.

## Human approval

Human approval is:

- explicit;
- separately created;
- bound to exact proposal id/hash;
- bound to exact surface/operation/target;
- integrity-hashed;
- non-sovereign.

It cannot replace a KX108 decision.

## Pre-state race protection

Immediately before dry-run, F3H-A compares:

`current_target_state_hash == approved_expected_target_state_hash`

Mismatch:

`REJECTED_NO_EXTERNAL_ACTION`

This prevents an old approval from silently applying to a changed mail thread,
calendar event, CRM record or task board state.

## Dry-run receipts

A successful dry-run receipt records:

- proposal id/hash;
- exact approval/KX108 binding hash;
- surface;
- operation;
- target;
- simulated effect;
- KX108_ONLY;
- external_action=false;
- world_action_allowed=false;
- connector_invoked=false;
- target_mutated=false;
- deterministic SHA-256.

## Real execution still forbidden

F3H-A explicitly does NOT provide:

- MAIL send;
- calendar create/update/cancel;
- CRM mutation;
- external task mutation;
- world-action PRE recheck;
- real connector receipts;
- connector replay/recovery.

These remain the open part of DECISION_EXECUTION.

## Governance

Preserved:

- KX108_ONLY
- external_action=false
- world_action_allowed=false
- connector_invoked=false
- target_mutated=false
- memory_write=false in runtime
- emits_act=false in runtime
- kernel_mutation=false in runtime
