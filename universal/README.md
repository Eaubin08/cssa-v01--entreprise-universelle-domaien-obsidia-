# Universal — F1 Contract Recovery

Status: IMPLEMENTATION_CANDIDATE
Authority: KX108_ONLY
Scope: universal domain-to-governance transport only

## Why this exists

Current Obsidia main already has a real multi-domain governed runtime, but its supported domain bridges are concrete.

Historical UDIP described a broader universal protocol.
The October 2026 UDIP branch implemented a narrow executable bridge.

This F1 recovers the smallest common contract without copying domain semantics or the kernel.

## Current path

```text
Domain-owned state
  -> DomainStateRefV0
  -> GovernancePayloadV0
  -> existing Obsidia governance boundary
```

The current repo does not implement KX108, Binder, execution adapters or receipts.

## Preserved fields

- domain identity;
- state reference;
- optional upstream state reference;
- validity time;
- unknowns;
- contradictions;
- risk flags;
- evidence references;
- provenance references;
- optional proposal reference.

## Forbidden authority

The contract cannot:
- decide;
- grant Binder permission;
- authorize action;
- change decision authority away from KX108_ONLY.

## WorldState

A world/situated state can be referenced through `upstream_state_ref`, but is not mandatory.

This is deliberate: CSSA Administration must not be forced through a general world model before evidence proves that boundary useful.
