# Universal Decision-Execution Contract V0

Date: 2026-10-07

## Purpose

Provide one reusable governance contract for execution across arbitrary métier
domains without moving business semantics into the universal layer.

The universal layer knows only:

```text
DOMAIN FACTS
→ DOMAIN EXECUTION ADAPTER
→ UNIVERSAL ACTION PROPOSAL
→ REGISTERED EXECUTION SURFACE
→ KX108
→ HUMAN APPROVAL WHEN REQUIRED
→ TARGET PRE-STATE RECHECK
→ EXECUTION READINESS
→ PROVIDER RECEIPT
→ REPLAY
```

It does not know football, trading, GNSS, products, contracts, suppliers,
players, portfolios, shipments, or any other domain vocabulary.

## Core contracts

### ExecutionSurfaceRegistrationV0

A surface registration describes:

- surface id;
- allowed operation ids;
- effect class;
- connector id when external;
- human-approval policy.

It cannot grant:

- decision authority;
- action authority;
- ACT;
- kernel mutation;
- memory write.

### UniversalActionProposalV0

A proposal binds:

- proposal id;
- domain id;
- surface id;
- operation id;
- target ref;
- exact payload;
- source-case refs;
- evidence refs;
- exact expected target pre-state hash;
- effect class;
- connector;
- human-approval requirement;
- KX108_ONLY.

The canonical proposal SHA-256 changes if any bound field changes.

### ExecutionDomainAdapterRegistrationV0

A métier domain registers:

- its domain id;
- one adapter id;
- the execution surfaces it may propose.

The adapter translates métier facts into UniversalActionProposalV0.

It cannot:
- change domain identity;
- use an unregistered surface;
- widen its allowed surface set;
- decide;
- act.

## Effect classes

```text
INTERNAL_BOUNDED
EXTERNAL_COMMUNICATION
EXTERNAL_DATA_MUTATION
EXTERNAL_FINANCIAL
EXTERNAL_PHYSICAL
```

External surfaces require an explicit connector registration.

## Human approval

Approval binds the exact universal proposal:

- proposal id/hash;
- domain;
- surface;
- operation;
- target;
- expected target pre-state.

Human approval is evidence, not sovereign authority.

`HumanApproval != KX108`

## Readiness

The generic readiness gate requires:

1. KX108 ALLOW;
2. verified KX108 decision record;
3. required exact human approval;
4. unchanged exact target pre-state;
5. for external effects, an activated upstream world-action runtime.

If upstream external world actuation is not activated:

`EXECUTION_NOT_READY`

with:

`EXTERNAL_WORLD_ACTUATION_NOT_ACTIVATED`

## Provider receipt / replay

The universal receipt binds:

- proposal id/hash;
- domain;
- surface;
- operation;
- execution-call hash;
- provider-result identity;
- whether real execution is actually proven.

A receipt never upgrades a simulation into real execution.

Replay verifies proposal identity and receipt integrity.

## Domains exercised by proof suite

The same universal contract is exercised with:

- administration;
- trading;
- e-commerce;
- GPS / defense / aviation;
- logistics;
- finance operations;
- an internal research/local-work surface.

These are proof fixtures. The contract is not limited to them.

## CSSA compatibility

The existing F3H-A CSSA proposals are mapped to the universal contract by:

`organizations/cssa/execution/universal_bridge_v0.py`

for:

- MAIL;
- CALENDAR;
- CRM;
- TASKS.

The bridge preserves:
- target;
- payload;
- source refs;
- evidence refs;
- expected pre-state;
- non-sovereignty.

## Current upstream boundary

The current Obsidia upstream source explicitly reports:

- `EXTERNAL_WORLD_ACTUATION_NOT_ACTIVATED`;
- `REAL_X108_GATED_EXECUTION_PATH_NOT_ACTIVATED`;
- WorldActionBus dry-run only.

Therefore the universal contract is ready for external execution integration,
but cannot truthfully declare real world execution active.

## Governance

- KX108_ONLY
- domain adapter != authority
- surface registration != authority
- proposal != authority
- human approval != decision authority
- provider receipt != proof of execution unless real execution evidence exists
