# F3C CSSA SIMULATED FIELD RECEIPT

Date: 2026-10-07
Branch: `feat/f3c-cssa-simulated-field-v0`

## Scope

F3C exercises realistic-but-synthetic CSSA administrative/matchday cases before access to real internal club data.

Every scenario is explicitly:
`SIMULATED_NOT_OBSERVED`.

No raw Gmail message, user email address or Gmail message ID is committed.

## Scenario matrix

15 scenarios:
- 4 expected ALLOW for bounded internal READONLY analysis;
- 5 expected HOLD;
- 5 expected BLOCK;
- 1 pre-runtime privacy block.

Covered families:
- matchday configuration;
- fixture change / homologation;
- cross-channel coherence;
- ticketing/subscriber access;
- transactional purchase confirmation;
- FMI normal + exception;
- official correspondence;
- source interpretation;
- publication governance;
- youth/high-sensitivity privacy.

## Important boundary from real CSSA outputs

Sanitized supporter communications are used only as output-pattern inspiration:
- kickoff time;
- door opening;
- ticket-office opening;
- stand availability;
- subscriber access;
- parking/buvette/practical information;
- ticketing links / confirmations.

They are NOT treated as evidence of CSSA internal process.

## Runtime proof

All runtime-eligible scenarios cross:

```text
synthetic CSSA scenario
 -> F3B-compatible field mapping
 -> Administration
 -> frozen F2.5 aggregate-only resolver
 -> REAL DomainAggregate
 -> REAL GuardX108
 -> REAL canonical runtime lifecycle
 -> bounded simulated READONLY provider if ALLOW
```

Expected governance is asserted scenario-by-scenario.

## CI

Workflow: `f3c-cssa-simulated-field`
Run: 37552286365
Job: 112570342673
Conclusion: SUCCESS

Result:
`168 passed in 0.61s`

## Validated

- clean coherent synthetic cases may ALLOW bounded READONLY analysis;
- two unresolved unknowns produce HOLD;
- two contradictions produce BLOCK;
- high-sensitivity youth data is stopped before runtime;
- automatic ticket confirmation remains a transactional output, not authority;
- visible differences between communication channels do not become an inferred internal migration;
- CSSA internal reality is not claimed or frozen;
- KX108_ONLY preserved;
- no memory write;
- no kernel mutation;
- no world action.

## Claim boundary

`CSSA_SIMULATED_FIELD_STRESS_BASELINE_PROVEN`

Not claimed:
- real CSSA internal workflow accuracy;
- real staff roles/permissions;
- real mailbox/tool topology;
- external-write authorization;
- production readiness.
