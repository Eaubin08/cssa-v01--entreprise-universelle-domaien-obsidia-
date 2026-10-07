# F2.5 — CROSS-REPO FIRST-CLASS RUNTIME SEAM PROOF

Date: 2026-10-06
Status: FREEZE-CANDIDATE / NOT MAIN

## Upstream candidate

`Eaubin08/obsidia-x108-proofs@feat/f2-5-portable-domain-resolver-seam-v0`

## Difference from F2.4

F2.4 proved the full runtime by temporarily injecting module-level resolver functions.

F2.5 exposes an explicit upstream dependency:

```text
run_governed_runtime_cycle(..., domain_extension_resolver=...)
run_governed_feedback_cycle(..., domain_extension_resolver=...)
```

No monkey-patching is required.

## Security audit correction before freeze

The first F2.5 draft let an extension resolve a full pipeline returning a decision envelope. Audit identified this as too permissive because a Python extension could fabricate a dataclass-shaped `CanonicalDecisionEnvelope(ALLOW)`.

That draft is NOT the frozen contract.

The hardened contract is aggregate-only:

```text
resolver.is_supported_domain(domain)
resolver.resolve_domain_aggregate_builder(domain)
    -> builder(state, packet)
    -> REAL DomainAggregate only

upstream runtime validates aggregate + domain binding
upstream runtime invokes REAL GuardX108 itself
GuardX108 -> CanonicalDecisionEnvelope
```

A forged envelope returned by an extension is explicitly tested and rejected before decision persistence or provider execution.

## Safety properties

- canonical built-in pipelines always win;
- extension cannot shadow canonical domains;
- extension cannot provide ALLOW/HOLD/BLOCK through the supported API;
- no resolver means the original unsupported-domain fail-closed behavior;
- business fields stop at the domain adapter boundary;
- KX108_ONLY remains the decision authority;
- feedback cycles receive the same resolver but require a new decision.

## Trust boundary

The resolver is explicit trusted host configuration. F2.5 does not add plugin auto-discovery, remote code loading or sandboxing of arbitrary third-party Python.

## Proof target

Direct cross-repo proof must cover clean ALLOW, unknown HOLD, contradiction BLOCK, no-resolver refusal, feedback re-entry and forged-envelope rejection.
