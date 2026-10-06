# STATUS

Status: F2_5_FROZEN_OFF_MAIN
Branch: `feat/f2-5-first-class-runtime-seam-v0`
F0-A: CLOSED
F0-B CSSA field reality: OPEN
F1 universal contract: PASS
F2 isolated conformance: PASS
F2.1 real current-main Guard compatibility: PASS
F2.2 portable new-domain registration: PASS
F2.3 canonical-compatible resolver: PASS
F2.4 full canonical runtime by injection: PASS
F2.5 first-class aggregate-only resolver seam: PASS
Cross-repo hardened CI: 102/102 PASS
Upstream native regression: BASELINE_EQUIVALENT_NO_NEW_FAILURES
Administration semantic freeze: HOLD
Upstream main merge: FORBIDDEN UNTIL EXPLICIT USER DECISION

## Security audit

Merge-readiness audit found one sovereignty issue in the initial F2.5 draft:
an extension-supplied full pipeline could theoretically fabricate a dataclass decision envelope.

That design was rejected before freeze.

Frozen F2.5 contract:

```text
extension
 -> DomainAggregate only
runtime
 -> validates aggregate/domain
 -> REAL GuardX108.decide()
 -> CanonicalDecisionEnvelope
```

Forged-envelope negative test: PASS.

## Evidence

Focused final:
`102 passed in 0.43s`
run `37527394792`, job `112487760134`.

Upstream native hardened branch:
`11 failed, 12451 passed, 46 skipped, 207 deselected`
run `37526855143`, job `112485940506`.

Current main baseline:
`11 failed, 12443 passed, 46 skipped, 207 deselected`.

Same 11 inherited failures; +8 F2.5 passing tests; zero new failures.

## Freeze

`evidence/audits/F25_FREEZE_V0.md`

No semantic change to F2.5 without explicit unfreeze + new audit.

## Next

Universal runtime portability is no longer the blocker.

Remaining work splits into:
1. optional future decision on whether to promote the frozen upstream seam to main;
2. F0-B acquisition of real CSSA field evidence before freezing Administration/CSSA business semantics.

Nothing has been pushed or merged to `main`.
