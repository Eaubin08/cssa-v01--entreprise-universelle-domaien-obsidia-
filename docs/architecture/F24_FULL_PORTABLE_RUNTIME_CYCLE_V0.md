# F2.4 — FULL PORTABLE GOVERNED RUNTIME CYCLE V0

Status: IMPLEMENTATION_CANDIDATE
Date: 2026-10-06

## Objective

Exercise a portable new domain through the real current upstream `run_governed_runtime_cycle()` without changing upstream source files.

## Injection boundary

The current function resolves domains through two module-level callables:

```text
is_supported_domain(domain)
resolve_domain_pipeline(domain)
```

F2.4 temporarily injects the F2.3 overlay resolver into only those two names, calls the real upstream cycle, and restores both functions in `finally`.

The injection is explicit, process-local and serialized by a lock.

## Full path under test

```text
REAL registered non-sovereign agent
 -> REAL AgentResult
 -> REAL ContextPacket
 -> REAL context validation / X108 boundary
 -> F2.3 portable resolver
 -> F1 universal contracts
 -> REAL GuardX108
 -> REAL CanonicalDecisionEnvelope
 -> REAL frozen pre-execution context
 -> REAL KX108 decision-record persistence + verification
 -> REAL OS3 ticket
 -> REAL replay
 -> REAL execution authorization gate
 -> REAL CanonicalRuntimeReceiptFlow
 -> bounded registered provider
 -> REAL sealed receipt
 -> REAL readonly feedback context
```

## What remains unchanged

- upstream source SHA;
- `_DOMAIN_PIPELINES`;
- `SUPPORTED_DOMAINS`;
- Domain enum;
- GuardX108;
- decision store;
- OS3 ticket/replay;
- execution authorization logic;
- receipt flow.

## Expected gates

- clean Administration candidate -> real ALLOW -> bounded provider executes;
- >1 unknown -> real HOLD -> provider untouched;
- >=2 contradictions -> real BLOCK -> provider untouched;
- unregistered domain -> refused before decision -> provider untouched.

## Claim boundary

A green F2.4 proves that the current canonical runtime lifecycle is technically compatible with a portable domain resolver injected at its existing domain-resolution seam.

It does not yet prove that upstream main has adopted this seam as a first-class dependency/configuration API. Source-level canonicalization/upstream promotion remains a separate decision.

It also does not freeze CSSA/Administration business semantics.
