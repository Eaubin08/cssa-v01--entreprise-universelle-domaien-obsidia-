# F25_FREEZE_V0 — CSSA / V0.1 UNIVERSAL DOMAIN

Freeze date: 2026-10-06
Status: **FROZEN CANDIDATE / OFF MAIN**

## Upstream dependency

`Eaubin08/obsidia-x108-proofs@feat/f2-5-portable-domain-resolver-seam-v0`

Main is not modified.

## Frozen first-class contract

```text
portable domain registry
 -> domain adapter
 -> DomainStateRefV0
 -> GovernancePayloadV0
 -> resolve_domain_aggregate_builder(domain)
 -> REAL upstream DomainAggregate
 -> REAL upstream GuardX108
 -> CanonicalDecisionEnvelope
 -> canonical runtime lifecycle
```

The extension/domain side does not supply ALLOW/HOLD/BLOCK.

## Security audit closure

During merge-readiness audit, the first F2.5 draft was found too permissive because an extension-supplied full pipeline could theoretically fabricate a dataclass decision envelope.

That draft is rejected.

The frozen contract is aggregate-only and includes an explicit cross-repository forged-envelope rejection test.

## Final focused proof

```text
102 passed in 0.43s
GitHub Actions run 37527394792
job 112487760134
SUCCESS
```

Covered:
- F1 -> F2.5 regression;
- Bank/Trading/Ecom/GPS compatibility;
- portable Administration;
- full canonical runtime;
- ALLOW/HOLD/BLOCK;
- no-resolver fail closed;
- feedback re-entry;
- forged sovereign envelope rejection.

## Upstream native regression

Security-hardened upstream branch:

```text
11 failed, 12451 passed, 46 skipped, 207 deselected
run 37526855143 / job 112485940506
```

Current main baseline:

```text
11 failed, 12443 passed, 46 skipped, 207 deselected
run 37508621493 / job 112423614411
```

Same 11 inherited failures. F2.5 adds eight passes and zero new failure.

Verdict:
`BASELINE_EQUIVALENT_NO_NEW_FAILURES`

## Frozen boundary

F2.5 proves the universal runtime seam. It does not freeze CSSA Administration business semantics.

Still HOLD pending real CSSA field evidence:
- internal mail flows;
- actual role allocation;
- internal tools/files;
- unwritten practices;
- real validation chains;
- match-day administrative reality.

## Change control

Any semantic modification to the portable resolver, authority boundary, aggregate-only rule, Guard invocation, or fail-closed behavior requires a new unfreeze/audit/freeze cycle.

## Main protection

**No push, merge, cherry-pick or fast-forward to `main` is authorized by this freeze.**
