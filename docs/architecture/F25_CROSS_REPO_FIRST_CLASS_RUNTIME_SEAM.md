# F2.5 — CROSS-REPO FIRST-CLASS RUNTIME SEAM PROOF

Date: 2026-10-06

## Upstream candidate

`Eaubin08/obsidia-x108-proofs@feat/f2-5-portable-domain-resolver-seam-v0`

## Difference from F2.4

F2.4 proved the full runtime by temporarily injecting two module-level resolver functions.

F2.5 removes that injection requirement. The upstream runtime candidate exposes:

```text
run_governed_runtime_cycle(..., domain_extension_resolver=...)
run_governed_feedback_cycle(..., domain_extension_resolver=...)
```

The CSSA/V0.1 resolver is passed directly as a dependency.

## Safety property

Built-in canonical pipelines remain first priority in upstream source. The extension is consulted only for a domain absent from `_DOMAIN_PIPELINES`.

Without a resolver, Administration remains unsupported and fail-closed exactly as before.

## Proof target

Use the existing portable Administration registry/resolver from this repository and prove ALLOW/HOLD/BLOCK, decision-record persistence, replay, bounded execution, receipt and feedback directly through the new upstream API.
