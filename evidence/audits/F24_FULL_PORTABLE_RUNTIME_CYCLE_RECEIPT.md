# F2.4 FULL PORTABLE RUNTIME-CYCLE RECEIPT

Date: 2026-10-06
Branch: feat/f2-4-full-portable-runtime-cycle-v0

## Frozen upstream

Repository: Eaubin08/obsidia-x108-proofs
SHA: 48f0c2fbcfe097c213b2783bc7b4d0fba78e6621

Upstream source files were not modified.

## Integration method

The real upstream `run_governed_runtime_cycle()` already resolves domains through two module-level seams:

```text
is_supported_domain(domain)
resolve_domain_pipeline(domain)
```

F2.4 temporarily injects the F2.3 resolver into only those two callables, executes the real upstream cycle, and restores the originals in `finally`.

The injection is process-local and serialized.

## Proven full path

```text
REAL DATA_PURITY_AGENT
 -> REAL AgentResult
 -> REAL ContextPacket
 -> REAL context validation / X108 boundary
 -> portable Administration resolver
 -> DomainStateRefV0 / GovernancePayloadV0
 -> REAL DomainAggregate
 -> REAL GuardX108
 -> REAL CanonicalDecisionEnvelope
 -> REAL agent pre-execution context persistence + verification
 -> REAL KX108 decision-record persistence + verification
 -> REAL OS3 ticket
 -> REAL replay PASS
 -> REAL execution authorization gate
 -> REAL CanonicalRuntimeReceiptFlow
 -> bounded registered provider
 -> REAL sealed receipt
 -> REAL readonly feedback context
```

## CI attempt 1 — useful failure

Run: 37523814473
Job: 112475613470
Result: FAILURE
Suite: 89 passed / 6 failed

Root cause:
`CanonicalCompatibleResolverV0` called `self._runtime.is_supported_domain()` dynamically. During injection that name pointed back to the resolver itself, causing recursion.

Fix:
Snapshot canonical upstream `is_supported_domain`, `resolve_domain_pipeline` and `SUPPORTED_DOMAINS` at resolver construction time. This also strengthens canonical precedence because portable injection can no longer alter what the resolver considers built-in.

## CI attempt 2 — closure

Run: 37523932904
Job: 112476017906
Conclusion: SUCCESS

Result:

```text
95 passed in 0.26s
```

## Validated

- all F1/F2/F2.1/F2.2/F2.3 tests remain green;
- real registered non-sovereign agent creates the packet for Administration;
- real context validation and X108 context boundary pass;
- portable Administration reaches the real Guard inside the real upstream full coordinator;
- clean case -> real ALLOW -> real bounded provider invocation;
- >1 unknown -> real HOLD -> no provider invocation;
- >=2 contradictions -> real BLOCK -> no provider invocation;
- unregistered domain remains refused before any decision;
- canonical pre-execution context is persisted and verified;
- canonical decision record is persisted and verified;
- OS3 ticket is created;
- replay status is PASS;
- execution happens only behind verified ALLOW;
- sealed runtime receipt is produced;
- feedback remains readonly;
- memory_write=false;
- kernel_mutation=false;
- emits_act=false;
- world_action_allowed=false;
- KX108_ONLY preserved;
- upstream resolver functions are restored after success and after exception;
- upstream `SUPPORTED_DOMAINS` is never mutated.

## Claim boundary

`PORTABLE_DOMAIN_FULL_CURRENT_CANONICAL_RUNTIME_CYCLE_PROVEN_BY_RESOLVER_INJECTION`

Not proven:
- first-class portable resolver API merged into upstream main;
- portable registry persisted/configured by upstream runtime itself;
- CSSA/Administration business semantics;
- CSSA external connectors;
- production deployment;
- unrestricted external action.
