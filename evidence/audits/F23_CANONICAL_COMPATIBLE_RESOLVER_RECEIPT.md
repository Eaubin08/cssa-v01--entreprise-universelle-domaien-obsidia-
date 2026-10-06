# F2.3 CANONICAL-COMPATIBLE RESOLVER RECEIPT

Date: 2026-10-06
Branch: feat/f2-3-canonical-compatible-resolver-v0

## Frozen upstream

Repository: Eaubin08/obsidia-x108-proofs
SHA: 48f0c2fbcfe097c213b2783bc7b4d0fba78e6621

No upstream runtime/kernel file was modified.

## Proven resolver contract

Resolution order:

```text
1. real current-main canonical pipeline
2. explicitly bound portable domain pipeline
3. fail closed
```

Portable bindings cannot shadow current-main canonical domains.

## Portable canonical-compatible call shape

```text
pipeline(raw_state, PeripheralSignalPacket) -> CanonicalDecisionEnvelope
```

Path:

```text
raw domain state
 + REAL upstream PeripheralSignalPacket
 -> registered domain adapter
 -> DomainStateRefV0
 -> GovernancePayloadV0
 -> conservative peripheral merge
 -> REAL upstream DomainAggregate
 -> REAL GuardX108
 -> REAL CanonicalDecisionEnvelope
```

## GitHub Actions proof

Workflow: f2-3-canonical-compatible-resolver
Run id: 37522045717
Job id: 112469648672
Conclusion: SUCCESS

Result:

```text
88 passed in 0.24s
```

## Validated

- all F1/F2/F2.1/F2.2 tests remain green;
- built-in bank/trading/ecom/gps/gps_defense_aviation resolve to the exact real upstream canonical pipeline functions;
- upstream `_DOMAIN_PIPELINES` and `SUPPORTED_DOMAINS` remain unchanged;
- portable Administration appears only in the overlay resolver;
- canonical-domain shadowing is forbidden;
- unknown unregistered domain fails closed before Guard;
- Administration exposes the same `(state, packet)` pipeline shape as current canonical bridges;
- REAL upstream PeripheralSignalPacket non-sovereignty is enforced;
- packet/domain mismatch fails closed;
- `can_emit_act=True` is rejected;
- periphery unknowns/risk/contradiction/evidence are conserved;
- HOLD hint contributes uncertainty, never a decision;
- BLOCK_CANDIDATE contributes contradiction, never a decision;
- invalid confidence fails closed;
- confidence remains domain-supplied and Universal only bounds it to finite [0,1];
- portable runtime binding cannot grant decision/Binder/action/memory/kernel authority;
- portable Administration reaches REAL GuardX108 and returns REAL CanonicalDecisionEnvelope.

## Claim boundary

`PORTABLE_DOMAIN_CANONICAL_COMPATIBLE_RESOLVER_PROVEN`

Not proven:
- unmodified upstream `run_governed_runtime_cycle()` consulting the overlay resolver;
- portable domain decision-record persistence in the canonical coordinator;
- portable Binder/execution lifecycle;
- CSSA business correctness;
- Administration business freeze;
- external action;
- production readiness.
