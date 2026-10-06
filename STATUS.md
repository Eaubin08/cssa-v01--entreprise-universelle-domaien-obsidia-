# STATUS

Status: F2_5_FIRST_CLASS_RUNTIME_SEAM_CLOSED
Branch: feat/f2-5-first-class-runtime-seam-v0
F0-A: CLOSED
F0-B CSSA field reality: OPEN
F1 universal contract: PASS
F2 isolated conformance: PASS
F2.1 real current-main Guard compatibility: PASS
F2.2 portable new-domain registration: PASS
F2.3 canonical-compatible resolver: PASS
F2.4 full canonical runtime by injection: PASS
F2.5 first-class upstream resolver seam: PASS
Cross-repo CI: 101/101 PASS
Upstream native regression: BASELINE_EQUIVALENT_NO_NEW_FAILURES
Administration semantic freeze: HOLD
Upstream main merge: NOT_DONE

## Proven now

`obsidia-x108-proofs` has a dedicated F2.5 branch where the real governed runtime accepts an optional `domain_extension_resolver` directly.

No monkey-patching is required for the F2.5 path.

Resolution is:
1. canonical current-main pipeline;
2. optional extension only for an absent canonical domain;
3. fail closed.

Administration traverses the full real lifecycle through that first-class seam:
- registered non-sovereign agent;
- ContextPacket and boundary;
- real GuardX108;
- CanonicalDecisionEnvelope;
- pre-execution context;
- persisted/verified decision record;
- OS3 ticket;
- replay;
- execution gate;
- bounded provider;
- sealed receipt;
- readonly feedback.

Observed:
- clean -> ALLOW -> provider executes once;
- unknown threshold -> HOLD -> no execution;
- contradiction threshold -> BLOCK -> no execution;
- resolver absent -> Administration refused before decision;
- feedback t1 requires a fresh KX108 decision through the same explicit resolver.

## Regression truth

Dedicated CSSA cross-repo suite:
`101 passed in 0.46s`.

Upstream all-tests branch run:
`11 failed, 12450 passed, 46 skipped, 207 deselected`.

Current main baseline:
`11 failed, 12443 passed, 46 skipped, 207 deselected`.

The same 11 failures exist on main. F2.5 adds seven passing tests and no new failure.

## Universal-runtime conclusion

- UNIVERSAL CONTRACT = PASS;
- PORTABLE DOMAIN REGISTRATION = PASS;
- REAL KX108 = PASS;
- FULL CANONICAL RUNTIME LIFECYCLE = PASS;
- FIRST-CLASS RESOLVER SEAM = PASS ON DEDICATED UPSTREAM BRANCH;
- MERGE TO MAIN = NOT YET DONE.

## Next gate

The universal runtime blocker is no longer technical proof of portability.

Before merging/promoting to main, perform a focused merge-readiness audit of the F2.5 branch and decide whether this seam belongs in current main now or remains a V0.1 branch contract.

In parallel, F0-B remains required before freezing real Administration/CSSA semantics.
