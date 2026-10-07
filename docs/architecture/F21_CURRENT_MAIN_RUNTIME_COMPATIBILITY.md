# F2.1 — DIRECT CURRENT-MAIN RUNTIME COMPATIBILITY

Status: IMPLEMENTATION_CANDIDATE
Date: 2026-10-06

## Objective

Prove the F1 Universal contract against the real current `obsidia-x108-proofs@main` KX108 decision boundary without copying kernel code into this repository.

## Method

GitHub Actions checks out both repositories:

```text
CSSA/V0.1 repo
+
obsidia-x108-proofs @ 48f0c2fbcfe097c213b2783bc7b4d0fba78e6621
```

The F2.1 test imports the real upstream `sigma.contracts.DomainAggregate`, `sigma.contracts.CanonicalDecisionEnvelope` and `sigma.guard.GuardX108`.

The runtime support set is read directly from the real upstream `_DOMAIN_PIPELINES` table in `scripts/obsidia_governed_runtime_cycle_v1.py`.

## Compatibility path

```text
F1 GovernancePayloadV0
   -> F2.1 bounded adapter
   -> REAL upstream DomainAggregate
   -> REAL upstream GuardX108
   -> REAL upstream CanonicalDecisionEnvelope
```

Pre-Guard `market_verdict` is forced to `HOLD`. The universal/domain payload cannot provide ALLOW/HOLD/BLOCK.

## Expected current limitation

`administration` must fail before GuardX108 because current main has no registered governed-runtime Administration pipeline.

This is not a failure of F1. It is the exact plug-in gap F2.1 is intended to expose.

## Claim boundary

If CI passes:
- F1 payload compatibility with the real current-main Guard path is proven for already registered domains;
- uncertainty/contradiction signals are consumed by the real Guard;
- no copied kernel exists in this repo;
- Administration remains unsupported by current-main runtime;
- arbitrary new-domain plug-in remains NOT PROVEN.
