# F2.5 FIRST-CLASS RUNTIME SEAM RECEIPT

Date: 2026-10-06
Branch: feat/f2-5-first-class-runtime-seam-v0

## Upstream candidate

Repository: Eaubin08/obsidia-x108-proofs
Branch: feat/f2-5-portable-domain-resolver-seam-v0

Source-level candidate API:

```text
run_governed_runtime_cycle(..., domain_extension_resolver=None)
run_governed_feedback_cycle(..., domain_extension_resolver=None)
```

Canonical built-in domains keep strict precedence. The extension is consulted only when the domain is absent from the current canonical `_DOMAIN_PIPELINES` table.

## Difference from F2.4

F2.4 required process-local resolver injection.
F2.5 passes the portable resolver directly as an explicit runtime dependency.

## Cross-repo GitHub Actions proof

Workflow: f2-5-first-class-runtime-seam
Run id: 37524651160
Job id: 112478457034
Conclusion: SUCCESS
Result: `101 passed in 0.46s`

Validated:
- F1 through F2.4 remain green against the F2.5 upstream branch;
- the first-class upstream API exposes `domain_extension_resolver` on t0 and feedback cycles;
- portable Administration reaches the real full canonical lifecycle without monkey-patching/injection;
- clean -> real ALLOW -> bounded provider executes;
- >1 unknown -> real HOLD -> provider untouched;
- >=2 contradictions -> real BLOCK -> provider untouched;
- no resolver -> Administration remains unsupported and refused before decision;
- feedback t1 receives the same explicit resolver and obtains a fresh KX108 decision;
- KX108_ONLY and non-sovereignty remain intact.

## Native upstream regression comparison

F2.5 branch X108 Periphery CI:
- run 37524473637 / job 112477856271;
- `11 failed, 12450 passed, 46 skipped, 207 deselected`.

Current main baseline:
- run 37508621493 / job 112423614411;
- `11 failed, 12443 passed, 46 skipped, 207 deselected`.

The same 11 baseline failures occur in both runs. F2.5 adds seven tests and the pass count increases by exactly seven.

Verdict:
`BASELINE_EQUIVALENT_NO_NEW_FAILURES`

The upstream workflow is red because main is already red on those same environment/baseline tests; F2.5 introduces no additional failure.

## Claim boundary

`FIRST_CLASS_PORTABLE_DOMAIN_RESOLVER_SEAM_PROVEN_NO_NEW_REGRESSION`

Not claimed:
- merge into upstream main;
- CSSA/Administration business-semantic freeze;
- production deployment;
- unrestricted external action.
