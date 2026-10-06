# STATUS

Status: F1_UNIVERSAL_CONTRACT_ACTIVE
Branch: `feat/f1-universal-contract-recovery-v0`
F0-A: CLOSED
F0-B CSSA field reality: OPEN
F1 isolated contract tests: 11/11 PASS
Main-runtime integration: NOT_STARTED
Administration semantic freeze: HOLD
CSSA action/runtime: NOT_STARTED

## Closed facts

- `obsidia-x108-proofs@main` is the runtime baseline.
- Main has a real governed internal multi-domain runtime.
- New arbitrary domain plug-and-play is not yet proven.
- Historical UDIP is architecture/reference, not runtime truth.
- October `feat/premiere-mise-au-monde-udip-v0` contains a newer executable minimal bridge candidate.
- `feat/premiere-mise-au-monde-proof-v0` is the latest relevant descendant.
- The eight commits these branches trail main are display-only terminal/color changes.
- Public FFF/LGEF sources establish real administrative deadlines, exceptions, authority boundaries and proof obligations.
- Real CSSA internal practice remains unknown until field access.

## F1 implemented

```text
Domain-owned state
  -> DomainStateRefV0
  -> GovernancePayloadV0
```

Preserved:
- domain id;
- state ref;
- optional upstream state ref;
- validity time;
- unknowns;
- contradictions;
- risk flags;
- evidence refs;
- provenance refs;
- optional proposal ref.

Forbidden:
- domain decision;
- Binder permission;
- action authority;
- authority other than KX108_ONLY.

## Current evidence

`evidence/audits/F1_LOCAL_TEST_RECEIPT.md`

Result:
`11 passed in 0.07s`

Claim:
`ISOLATED_CONTRACT_TESTED`

## Next technical step

F2 bounded universal conformance harness against:
- the F1 contract;
- current main domain invariants;
- existing October UDIP candidate semantics.

Administration/CSSA business semantics remain blocked on F0-B field evidence.
