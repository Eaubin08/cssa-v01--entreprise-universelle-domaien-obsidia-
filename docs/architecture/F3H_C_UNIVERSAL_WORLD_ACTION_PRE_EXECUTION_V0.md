# F3H-C — Universal World Action PRE-Execution Rail V0

Date: 2026-10-07
Branch: `feat/f3h-c-universal-world-action-pre-execution-v0`
Base: `feat/f3h-b-cssa-mail-governed-execution-v0`
Main: unchanged

## Purpose

Close the architectural duplication problem before enabling any real external
connector.

The rail is domain-agnostic:

```text
DOMAIN FACTS
→ DOMAIN EXECUTION ADAPTER
→ UNIVERSAL ACTION PROPOSAL
→ WORLD ACTION OPERATION POLICY
→ EXACT CONNECTOR CALL
→ EXACT HUMAN APPROVAL
→ WORLD_ACTION_PRE_EXECUTION
→ CONNECTOR
→ PROVIDER OUTCOME
→ RECEIPT
→ REPLAY / RECOVERY
```

No domain owns decision authority.

## Operation policy

Each external operation explicitly registers:

- surface;
- operation;
- connector;
- connector action;
- required scope;
- world-call class;
- action-risk class;
- autonomy level;
- retry policy;
- reversibility/irreversibility;
- human-approval policy.

Registration cannot grant ACT.

## Exact action request

`WorldActionRequestV0` binds:

- universal proposal id/hash;
- domain;
- surface/operation;
- connector id/action;
- exact connector arguments;
- connector-call SHA-256;
- target and exact pre-state hash;
- required scope;
- risk/world-call classes;
- autonomy level;
- retry policy;
- deterministic idempotency key.

Changing connector arguments changes the request hash.

## Exact human approval

The human approval is separate from the métier proposal approval.

It binds the exact external request:

- request id/hash;
- proposal hash;
- connector id/action;
- connector-call hash;
- target/pre-state;
- required scope;
- idempotency key.

Therefore:

`approval of proposal != approval of arbitrary connector call`

## Secret boundary

Connector payload field names containing secret/token/password/API-key/private
key style material are rejected before a world-action request is created.

Secrets remain connector/runtime configuration, not agent/action payload.

## WORLD_ACTION_PRE_EXECUTION contract

F3H-C defines the evidence contract expected from the future canonical
external PRE rail.

Required evidence includes:

- decision phase = WORLD_ACTION_PRE_EXECUTION;
- KX108 gate = ALLOW;
- verified decision record identity;
- exact proposal/request/call/pre-state hashes;
- exact human-approval hash;
- required scope;
- world-call/risk/autonomy binding;
- idempotency key;
- sovereign ticket id;
- dry_run_only=false;
- egress_allowed=true.

This contract does not manufacture that evidence.

## Current upstream truth

Current `obsidia-x108-proofs` still exposes:

- SovereignTicket with `dry_run_only=True`;
- ObsidiaGateway with `egress_allowed=False`;
- WorldActionBus append-only local journal;
- WorldExecutorDryRun with `executed=False`;
- `EXTERNAL_WORLD_ACTUATION_NOT_ACTIVATED`;
- `REAL_X108_GATED_EXECUTION_PATH_NOT_ACTIVATED`.

F3H-C reuses and tests compatibility with those components but does not
reinterpret them as live authority.

## Duplicate / partial-effect safety

Every world-action request derives a deterministic idempotency key.

Prior confirmed execution with the same key:

`BLOCK duplicate`

Prior unknown outcome with the same key:

`BLOCK retry → reconciliation required`

Unknown connector/provider outcome never auto-retries.

Explicit proven no-effect can only permit retry when operation policy is
idempotent-after-reconciliation.

## Critical class safety

`CRITICAL_WORLD_CALL` and `FORBIDDEN_WORLD_CALL` are blocked by the generic
rail even in a synthetic activated-runtime test.

## Provider receipt

A confirmed real provider receipt cannot be constructed unless the caller
provides a matching `PRE_EXECUTION_READY` object containing:

- request hash;
- connector-call hash;
- idempotency key;
- sovereign-ticket id;
- decision-record id;
- KX108_ONLY.

Receipt replay verifies exact request/call/idempotency integrity.

## Multi-domain proof

The rail is exercised with:

- administration / MAIL;
- logistics / CALENDAR;
- e-commerce / CRM;
- trading / TASKS;
- finance operations / PAYMENT;
- GPS-defense-aviation / DEVICE.

The DEVICE critical case is blocked generically.

These are fixtures, not an exhaustive domain list.

## CSSA integration

CSSA MAIL is bridged through:

`organizations/cssa/execution/world_action_bridge_v0.py`

Its exact mail plan becomes the same universal WorldActionRequest used by
other métier domains.

Current result remains fail-closed because upstream external actuation is not
active.

## Proof

Initial proof:

```text
461 / 461 PASS
run 37596840226
27.67 s
```

## Verdict

`UNIVERSAL_WORLD_ACTION_PRE_EXECUTION_CONTRACT_V0_PROVEN`

and simultaneously:

`REAL_EXTERNAL_WORLD_ACTUATION_NOT_YET_PROVEN`

## Next architectural step

Implement the canonical `WORLD_ACTION_PRE_EXECUTION` producer in an Obsidia
upstream feature branch, preserving the current dry-run path as default and
requiring explicit activation for any real connector.
