# F2.2 PORTABLE DOMAIN REGISTRATION RECEIPT

Date: 2026-10-06
Branch: feat/f2-2-portable-domain-registration-v0

## Frozen upstream

Repository: Eaubin08/obsidia-x108-proofs
SHA: 48f0c2fbcfe097c213b2783bc7b4d0fba78e6621

No upstream kernel/runtime file was modified or copied into this repository.

## New contract

`PortableDomainRegistrationV0`

Registration is descriptive/routing-only:
- domain_id;
- adapter_id;
- schema_ref;
- descriptive capabilities;
- KX108_ONLY;
- all authority/write flags forced false.

## Proven candidate path

```text
raw domain input
 -> explicit registered adapter
 -> DomainStateRefV0
 -> GovernancePayloadV0
 -> non-sovereign PortableDomainValueV0
 -> REAL upstream DomainAggregate
 -> REAL upstream GuardX108
 -> REAL upstream CanonicalDecisionEnvelope
```

## GitHub Actions proof

Workflow: f2-2-portable-domain-registration
Run id: 37521371473
Job id: 112467330628
Conclusion: SUCCESS

Result:

```text
64 passed in 0.22s
```

## Validated

- all F1/F2/F2.1 tests remain green;
- multiple unrelated portable domains can coexist in one registry;
- registration cannot grant decision/Binder/action/memory/kernel authority;
- duplicate and unregistered domains fail closed;
- adapter/domain identity mismatch fails closed;
- current main remains unmodified and still does not list Administration;
- registered `administration` reaches the REAL current GuardX108 outside the canonical runtime coordinator;
- a second arbitrary registered domain (`warehouse`) reaches the same REAL GuardX108;
- clean registered input -> real ALLOW;
- >1 unknown -> real HOLD;
- >=2 contradictions -> real BLOCK;
- business-only fields stop at the domain adapter boundary;
- provenance survives into the real upstream aggregate evidence surface;
- pre-Guard market verdict remains HOLD.

## Architectural finding

The current GuardX108 decision surface uses `aggregate.domain.value` as domain identity and does not require that identity to originate from the global `Domain` enum.

Therefore a validated, non-sovereign portable domain identity can reach the existing Guard without kernel modification.

This is a compatibility fact, not a canonical-runtime bypass authorization.

## Claim boundary

`PORTABLE_NEW_DOMAIN_TO_REAL_GUARD_PROVEN_OUTSIDE_CANONICAL_RUNTIME_COORDINATOR`

Not proven:
- canonical runtime registration;
- Binder/execution for portable domains;
- current-main `_DOMAIN_PIPELINES` replacement;
- CSSA business correctness;
- Administration business-model freeze;
- external action;
- production readiness.
