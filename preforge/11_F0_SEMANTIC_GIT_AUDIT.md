# 11 — F0 SEMANTIC GIT AUDIT

Date: 2026-10-06
Scope: V0.1 enterprise / universal-domain / administration / CSSA
Mode: READ-ONLY against source repositories

## Executive verdict

Git distance is not used as semantic truth.

The current finding is:

1. `obsidia-x108-proofs@main` is the operational/runtime baseline.
2. The historical `codex/udip-domain-packs-v0` branch contains an important architectural specification that was **not** simply promoted to main under the same contract/file.
3. The newer `feat/premiere-mise-au-monde-udip-v0` branch contains a **minimal executable UDIP bridge candidate** that is not on main.
4. `feat/premiere-mise-au-monde-proof-v0` is a strict descendant of the UDIP/governed-world chain and adds decision-proof binding.
5. `docs/obsidia-ontology-layer-contracts-v0` contains doctrine complementary to main and not present under the same canonical document.
6. The eight commits by which these October branches are behind main are display/terminal-color changes only; they do not supersede the semantic contracts audited here.

Therefore:

```text
MAIN = canonical runtime baseline
+
OCTOBER V0 BRANCHES = semantically newer/complementary contract candidates
+
OLD UDIP BRANCH = architecture/reference source, not runtime source
```

No whole branch should be merged or copied wholesale.

---

## A. Current main baseline

Repository:
`Eaubin08/obsidia-x108-proofs`

Current main SHA audited:
`48f0c2fbcfe097c213b2783bc7b4d0fba78e6621`

### What main already proves/contains

- V0.1 product doctrine: connect an organization, reconstruct its real operation, propose/simulate/prove/govern transformations.
- Domain Integration Layer doctrine.
- Domain Packs doctrine.
- Four canonical runtime domains:
  - bank
  - trading
  - ecom
  - gps_defense_aviation
- Sigma multi-domain registry and bridges.
- Existing chain:
  `State -> Agents -> Aggregation -> MetaAgents -> GuardX108 -> CanonicalDecisionEnvelope`
- KX108_ONLY preserved.
- Real bounded internal governed provider execution exists.
- Cross-domain isolation is tested.
- External-world actuation remains false/dry-run.
- Unsupported domains are refused before a verdict.
- Current domain support is still concretely enumerated/hard-wired around existing bridges.

### Important consequence

Main proves a **real multi-domain governed runtime**.

Main does **not yet prove** that a new arbitrary domain can be plugged in only by supplying a domain pack without additional runtime work.

That gap is exactly relevant to CSSA / V0.1 Enterprise.

Verdict:
`CANONICAL_RUNTIME_BASELINE`

---

## B. Historical UDIP branch

Branch:
`codex/udip-domain-packs-v0`

Key source:
`docs/UNIVERSAL_DOMAIN_INTEGRATION_PROTOCOL_V0.md`

Historical self-status:
- SPEC_ONLY
- architectural readiness: YES
- implementation readiness: NO

Important concepts preserved there:

- DomainIdentity
- DomainObjectMap
- DomainSignal
- CanonicalDomainContract
- GovernancePayload
- SourceProvenance
- KX108AuthorityBoundary
- BinderPermissionBoundary
- ExecutionAdapterBoundary
- ExecutionOutcome boundary
- Receipt / Proof / Replay surfaces
- strict Domain/Core separation
- explicit do-not-generalize list

The branch also contains:
`domains/administration/`

But Administration is explicitly:
- NEW_DOMAIN_SCAFFOLD
- SCAFFOLD_ONLY
- no audited business source
- no object model
- no tests

### Semantic finding

The old UDIP specification remains useful because its architectural distinctions are not fully reproduced as one unified contract on main.

However, its implementation-readiness statement is now historically stale for part of the problem, because later October branches implement a smaller executable bridge.

Its migration snapshots and runtime copies must not be treated as current source.

Verdict:
`KEEP_AS_REFERENCE + PARTIAL_PROMOTION_CANDIDATE`

Do not import:
- migration snapshots;
- old runtime copies;
- branch-local Brody/runtime code merely because they live beside UDIP.

Administration scaffold verdict:
`HISTORICAL_PLACEHOLDER_ONLY`

---

## C. Ontology / layer doctrine branch

Branch:
`docs/obsidia-ontology-layer-contracts-v0`

Key source:
`docs/architecture/OBSIDIA_ONTOLOGY_AND_LAYER_CONTRACTS_V0.md`

Important doctrine:

```text
each layer speaks its own language
translation is explicit
no silent semantic loss

DATA != EXPERIENCE != LEARNING != KNOWLEDGE != MEMORY
MEMORY != COGNITION
COGNITION != DATA
INTELLIGENCE != AUTHORITY
CAPABILITY != PERMISSION
WORLD_STATE != MEMORY
OBSERVATION != TRUTH
EXPERIENCE != GENERAL TRUTH
PROPOSAL != DECISION
DECISION != ACTION
ACTION -> PROOF
```

Main contains several compatible ideas, but the exact unified doctrine above is not present on main under the same contract.

Verdict:
`COMPLEMENTARY / PROMOTE_DOCTRINE_REFERENCE`

Runtime status:
`NONE — doctrine only`

---

## D. October executable UDIP candidate

Branch:
`feat/premiere-mise-au-monde-udip-v0`

Compared to current main:
- ahead: 6 commits
- behind: 8 commits
- merge base: `553df13d7bc8746ba582649d08a07a7f1478d081`

Added semantic/runtime surfaces:

- `periphery/mmonde/contracts_v0.py`
- `periphery/udip/contracts_v0.py`
- `tests/periphery/test_mmonde_contracts_v0.py`
- `tests/periphery/test_udip_contracts_v0.py`
- `docs/architecture/MMONDE_V0_CONTRACT.md`
- `docs/architecture/UDIP_MMONDE_BRIDGE_V0.md`

Minimal implemented path:

```text
WorldStateV0
 -> DomainStateRefV0
 -> GovernancePayloadV0
 -> KX108 authority boundary
```

Properties enforced in code/tests:

- world/domain cannot decide;
- world/domain cannot act;
- GovernancePayload cannot contain a decision;
- GovernancePayload cannot grant Binder permission;
- unknowns preserved;
- contradictions preserved;
- risk flags preserved;
- evidence refs preserved;
- provenance refs preserved;
- KX108_ONLY enforced;
- domain-specific semantics are not invented by the bridge.

### Relation to old UDIP

This branch does **not** implement the entire old UDIP V0 specification.

It implements a narrower and cleaner executable slice.

Examples not fully provided by this minimal contract:
- complete DomainObjectMap model;
- full adapter API;
- universal execution outcome schema;
- full Binder contract;
- compensation semantics;
- full universal receipt schema;
- general promotion rules.

Verdict:
`BRANCH_NEWER_SEMANTIC / PROMOTE_CANDIDATE`

---

## E. Governed-world + proof descendant

Branch:
`feat/premiere-mise-au-monde-proof-v0`

Relative to `feat/premiere-mise-au-monde-udip-v0`:
- strict descendant
- +12 commits

Relative to `feat/premiere-mise-au-monde-governed-world-v0`:
- strict descendant
- +3 commits
- only added:
  - governed-world decision proof spec
  - governed-world decision proof runtime
  - tests

Full relevant path:

```text
WorldStateV0
 -> DomainStateRefV0
 -> GovernancePayloadV0
 -> DomainAggregate
 -> GuardX108
 -> CanonicalDecisionEnvelope
 -> GovernedWorldDecisionProofV0
```

Important property:
the adapter forces pre-Guard verdict to HOLD; only GuardX108 may create ALLOW/HOLD/BLOCK.

The proof hash-binds:
- world-state reference;
- domain-state reference;
- evidence/provenance;
- proposal reference;
- decision id;
- trace id;
- gate;
- reason;
- canonical decision-envelope projection.

Proof authority remains false.
Execution authority remains false.

Verdict:
`LATEST_RELEVANT_IMPLEMENTATION_CANDIDATE`

For CSSA:
- useful as a source of universal boundary contracts;
- not automatically adopted wholesale;
- CSSA must not be forced through MMonde if a cleaner organizational-domain input contract is justified.

---

## F. The eight "behind main" commits

The eight main commits after the semantic branches' merge base were audited.

They are limited to display/terminal-color changes and their reverts:

- Trading terminal colors
- GPS/Aviation terminal colors
- Brody terminal colors
- Uvicorn/API launcher colors
- corresponding display-only reverts

Files touched:
- `connectors/trading_live.py`
- `connectors/aviation_robo.py`
- `scripts/run_brody_terminal_enriched.ps1`
- `scripts/runtime/start_api.ps1`

Conclusion:

`BEHIND_BY_8 != SEMANTICALLY_STALE`

For the audited universal/domain contracts, these eight commits provide no superseding architecture.

---

## G. F0 truth boundary

What is true now:

```text
MULTI_DOMAIN_RUNTIME = REAL
UNIVERSAL_NEW_DOMAIN_PLUG_AND_PLAY = NOT_YET_PROVEN
UDIP_ARCHITECTURAL_DOCTRINE = EXISTS
UDIP_MINIMAL_EXECUTABLE_BRIDGE = EXISTS_ON_BRANCH
ADMINISTRATION_DOMAIN = NOT_BUILT
CSSA_DOMAIN = NOT_BUILT
CSSA_FIELD_WORKFLOWS = NOT_AUDITED
```

This is the baseline for the new CSSA repository.
