# F2.3 — CANONICAL-COMPATIBLE PORTABLE RESOLVER V0

Status: IMPLEMENTATION_CANDIDATE
Date: 2026-10-06

## Current upstream boundary

The real governed runtime currently exposes:

```text
is_supported_domain(domain)
resolve_domain_pipeline(domain) -> Callable[[state, packet], envelope]
```

and its canonical `_DOMAIN_PIPELINES` table remains the source of truth for built-in domains.

## F2.3 design

F2.3 adds an overlay resolver with exactly the same pipeline call shape.

Resolution order:

```text
1. real current-main canonical pipeline
2. explicitly bound portable domain pipeline
3. fail closed
```

A portable domain is forbidden from shadowing a canonical current-main domain.

## Portable pipeline

```text
raw domain state + REAL PeripheralSignalPacket
  -> registered domain adapter
  -> DomainStateRefV0
  -> GovernancePayloadV0
  -> conservative peripheral merge
  -> REAL DomainAggregate
  -> REAL GuardX108
  -> REAL CanonicalDecisionEnvelope
```

The packet remains non-sovereign. `recommended_gate` is preserved as evidence/uncertainty semantics, never converted directly into a sovereign gate.

## Confidence boundary

Current GuardX108 requires a confidence value. F1 intentionally did not invent one.

F2.3 therefore requires an explicit domain-side confidence provider at runtime binding. Universal validates only that the resulting value is finite and in [0,1]. It does not compute domain confidence.

## Non-mutation

F2.3 does not mutate:
- `_DOMAIN_PIPELINES`;
- `SUPPORTED_DOMAINS`;
- `Domain` enum;
- GuardX108;
- Binder;
- any upstream file.

## Claim boundary

A green F2.3 proves that a portable registration can expose a canonical-runtime-compatible `(state, packet)` pipeline resolver while preserving built-in precedence and unsupported-domain fail-closed behavior.

It does not yet prove that the unmodified upstream `run_governed_runtime_cycle()` itself consults the overlay resolver. That is the next integration boundary.
