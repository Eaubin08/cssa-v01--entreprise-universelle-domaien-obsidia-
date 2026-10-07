# 12 — F0 PROMOTION MATRIX

Date: 2026-10-06

This matrix controls what may enter the CSSA/V0.1 repository.

| Source | Object / concept | Verdict | Action |
|---|---|---|---|
| main | V0.1 product doctrine | ALREADY_IN_MAIN / CURRENT | Reference as product target |
| main | Domain Integration Layer doctrine | ALREADY_IN_MAIN / CURRENT | Keep as current architecture baseline |
| main | Sigma multi-domain runtime | CURRENT_RUNTIME | Treat as runtime fact, do not fork |
| main | CanonicalDecisionEnvelope / GuardX108 path | CURRENT_RUNTIME | Reuse by contract/reference |
| main | governed internal provider execution | CURRENT_RUNTIME | Reference; CSSA execution remains out of scope initially |
| main | hard-coded 4 canonical domain support | CURRENT_LIMIT | Do not copy as universal design |
| codex/udip-domain-packs-v0 | UDIP V0 spec | COMPLEMENTARY | Keep as architecture source |
| codex/udip-domain-packs-v0 | Administration scaffold | PLACEHOLDER_ONLY | Use only as evidence that Administration was intentionally reserved |
| codex/udip-domain-packs-v0 | migration snapshots | OBSOLETE_FOR_THIS_REPO | Do not import |
| docs/obsidia-ontology-layer-contracts-v0 | layer/ontology doctrine | COMPLEMENTARY | Promote as doctrine reference |
| feat/premiere-mise-au-monde-udip-v0 | WorldStateV0 | BRANCH_NEWER_CANDIDATE | Evaluate for F1 |
| feat/premiere-mise-au-monde-udip-v0 | DomainStateRefV0 | BRANCH_NEWER_CANDIDATE | Strong F1 candidate |
| feat/premiere-mise-au-monde-udip-v0 | GovernancePayloadV0 | BRANCH_NEWER_CANDIDATE | Strong F1 candidate |
| feat/premiere-mise-au-monde-udip-v0 | conservation of unknowns/contradictions/evidence/provenance | BRANCH_NEWER_CANDIDATE | Preserve |
| feat/premiere-mise-au-monde-proof-v0 | Domain -> GuardX108 adapter | LATEST_RELEVANT_CANDIDATE | Evaluate after F1 contract freeze |
| feat/premiere-mise-au-monde-proof-v0 | governed-world decision proof | LATEST_RELEVANT_CANDIDATE | Evaluate for proof surface |
| CSSA public sources | football/admin semantics | PENDING_AUDIT | F0 source work |
| CSSA field observation | real workflows | NOT_AVAILABLE_YET | Required before Administration freeze |

## Do not copy

The following are forbidden as shortcut:

- entire old domain migration trees;
- full source branch snapshots;
- hard-coded bank/trading/ecom/GPS semantics;
- Sigma's existing 4-domain enumeration as "universal";
- CSSA-specific entities into Universal;
- repeated human habits into canonical rules without validation.

## Candidate canonical split for this repo

```text
SOURCE OF RUNTIME TRUTH
    obsidia-x108-proofs@main

SOURCE OF UNIVERSAL CONTRACT CANDIDATES
    feat/premiere-mise-au-monde-proof-v0
    + old UDIP spec as architecture reference

SOURCE OF LAYER DOCTRINE
    docs/obsidia-ontology-layer-contracts-v0

SOURCE OF NEW BUSINESS SEMANTICS
    CSSA public + field sources
```

No source branch is a single source of truth by itself.
