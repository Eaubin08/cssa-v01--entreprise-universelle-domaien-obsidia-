# F2.1 REAL CURRENT-MAIN RUNTIME COMPATIBILITY RECEIPT

Date: 2026-10-06
Branch: feat/f2-1-main-runtime-compat-v0

## Frozen upstream

Repository: Eaubin08/obsidia-x108-proofs
Ref/SHA: 48f0c2fbcfe097c213b2783bc7b4d0fba78e6621

No kernel/runtime code was copied into this repository.
GitHub Actions checked out the upstream repository separately and imported its real runtime types.

## Real upstream surfaces exercised

- sigma.contracts.Domain
- sigma.contracts.DomainAggregate
- sigma.contracts.CanonicalDecisionEnvelope
- sigma.guard.GuardX108
- scripts/obsidia_governed_runtime_cycle_v1.py `_DOMAIN_PIPELINES` source table

## Proven path

```text
F1 GovernancePayloadV0
 -> F2.1 bounded compatibility adapter
 -> REAL upstream DomainAggregate
 -> REAL upstream GuardX108
 -> REAL upstream CanonicalDecisionEnvelope
```

## GitHub Actions proof

Workflow: f2-1-current-main-runtime-compat
Run id: 37520797367
Job id: 112465375493
Conclusion: SUCCESS

Command:

```text
python -m pytest
  tests/test_f1_universal_contract_v0.py
  tests/test_f2_universal_conformance_v0.py
  tests/test_f21_real_current_main_runtime.py
  -q
```

Result:

```text
43 passed in 0.20s
```

## Validated

- F1 and F2 remain green;
- current main governed-runtime domain table is read from the real upstream source;
- bank/trading/ecom/gps_defense_aviation F1 payloads reach the real GuardX108;
- returned decisions are real upstream CanonicalDecisionEnvelope objects;
- clean payload reaches upstream ALLOW through GuardX108 while the pre-Guard market_verdict remains HOLD;
- >1 unknown reaches real HOLD;
- >=2 contradictions reaches real BLOCK;
- provenance is conserved into upstream evidence refs;
- Administration is refused before GuardX108 because no current-main canonical runtime pipeline exists;
- current-main GPS alias is bounded back to canonical gps_defense_aviation when present.

## Claim boundary

`F1_TO_REAL_CURRENT_MAIN_GUARD_COMPATIBILITY_PROVEN_FOR_REGISTERED_DOMAINS`

Not proven:
- generic runtime registration for arbitrary new domains;
- Administration as a current-main runtime domain;
- CSSA business semantics;
- Binder/execution integration for Administration;
- external action;
- production readiness.
