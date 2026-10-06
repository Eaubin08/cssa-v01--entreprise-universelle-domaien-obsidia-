# F2.2 — PORTABLE DOMAIN REGISTRATION V0

Status: IMPLEMENTATION_CANDIDATE
Date: 2026-10-06

## Question

Can a new domain be registered outside KX108, translated through the universal contract, and judged by the existing real GuardX108 without putting its business semantics into the kernel?

F2.2 tests exactly this.

## Contract

```text
PortableDomainRegistrationV0
  domain_id
  adapter_id
  schema_ref
  descriptive capabilities
  KX108_ONLY
  all authority flags false
```

The registry is routing/descriptive only. It never auto-loads arbitrary code and never grants Binder, execution, memory, verdict or kernel authority.

## Candidate path

```text
raw domain input
  -> explicitly registered domain adapter
  -> DomainStateRefV0
  -> GovernancePayloadV0
  -> portable domain identity token
  -> REAL upstream DomainAggregate
  -> REAL upstream GuardX108
  -> REAL CanonicalDecisionEnvelope
```

Business semantics stop at the adapter boundary.

## Critical architectural fact

Current `GuardX108` does not inspect the global Domain enum to decide policy. At its decision surface it consumes the aggregate's uncertainty/risk/confidence fields and uses `aggregate.domain.value` as identity when creating the envelope.

Therefore a small non-sovereign identity carrier can represent a registered new domain at the Guard boundary without modifying GuardX108.

F2.2 treats this as a compatibility fact, not as permission to bypass the canonical runtime.

## What this does NOT do

- it does not mutate `obsidia-x108-proofs`;
- it does not add Administration to current `_DOMAIN_PIPELINES`;
- it does not claim canonical runtime registration;
- it does not wire Binder/execution for the new domain;
- it does not auto-discover plugins;
- it does not trust adapter-provided decisions;
- it does not freeze CSSA/Administration business semantics.

## Exit proof target

At least two unrelated newly registered domains must reach the same real GuardX108 with no kernel modification; unknowns must HOLD, contradictions must BLOCK, unregistered domains must fail before Guard, and all existing F1/F2/F2.1 tests must remain green.
