# F1 — UNIVERSAL DOMAIN CONTRACT V0

Status: IMPLEMENTATION_CANDIDATE
Date: 2026-10-06

## Provenance

Recovered from:
- current `obsidia-x108-proofs@main` authority/runtime invariants;
- historical UDIP V0 architecture;
- `feat/premiere-mise-au-monde-udip-v0` executable candidate;
- ontology/layer doctrine.

## Deliberate delta from October UDIP branch

October candidate required:

```text
WorldStateV0 -> DomainStateRefV0 -> GovernancePayloadV0
```

This repository keeps the useful conservation/authority rules but makes upstream world-state reference optional:

```text
Domain-owned state
   -> DomainStateRefV0
   -> GovernancePayloadV0
```

Optional:
```text
World/organization/source state
   -> upstream_state_ref
```

Reason:
Administration inputs may originate from a mail, document, official decision, internal case or later WorldState. F0 evidence does not justify making MMonde mandatory for all administration.

## Contract boundary

Universal owns:
- references;
- uncertainty;
- contradiction;
- risk flags;
- evidence/provenance references;
- proposal reference;
- non-sovereignty.

Universal does not own:
- CSSA match semantics;
- administrative procedure semantics;
- business policy;
- KX108 decision logic;
- Binder permission;
- execution capability.

## Current test result

Local isolated test run:
`11 passed`

This proves only this small contract behavior. It does not prove integration with the main Obsidia runtime.
