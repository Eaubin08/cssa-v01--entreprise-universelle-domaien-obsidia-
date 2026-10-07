# F3G-F — CSSA Announced Manager Général Role Coverage V0

Date: 2026-10-07  
Branch: `feat/f3g-f-cssa-announced-role-coverage-v0`  
Main: unchanged

## Public business contract

Official CSSA source:

`https://cs-sedan.fr/recrutement-manager-general`

Truth class:

`PUBLIC_CONFIRMED`

Boundary:

`PUBLIC_ROLE_DESCRIPTION_NOT_INTERNAL_FIELD_EVIDENCE`

The public role description is used as an external business contract against the
current CSSA model. It is not used to invent private workflows, capacities,
delegation chains or authority.

## Announced responsibility map

The official role description is decomposed into 11 testable responsibilities:

1. daily administration;
2. institutional relations;
3. people management and delegation;
4. cross-pole coordination;
5. matchday ticketing;
6. matchday security;
7. matchday welcome/hospitality;
8. matchday buvette/restauration;
9. written processes and explicit responsibilities;
10. root-cause/durable operation;
11. execution of direction decisions.

## Coverage result

```text
STRUCTURALLY_COVERED  5
PARTIAL               4
OPEN_GAP              2
TOTAL                 11
```

### Structurally covered

- cross-pole coordination;
- matchday ticketing;
- matchday security;
- welcome/hospitality;
- written process/responsibility structure.

"Structurally covered" means the objects, routing, stress logic and/or proof
surfaces exist and are tested.

It does NOT mean the real CSSA internal process has been field-validated.

### Partial

- administration;
- institutional relations;
- people/delegation;
- root-cause/durability.

The architecture exists, but real authority, real internal practice or dedicated
workflow closure is still missing.

### Open gaps

#### 1. Matchday buvette/restauration

`Buvette` exists as an operating object, but there is no proved workflow for:

- stock;
- suppliers/restauration;
- matchday cash reconciliation;
- shifts/assignments.

#### 2. Decision execution

The current chain proves governance and reporting, but intentionally stops
before real-world execution.

Missing future surfaces:

```text
MAIL
CALENDAR
CRM
TASKS
+ ACTION RECEIPT / REPLAY
```

This is the main bridge toward the later operational assistant.

## Announcement-derived stress suite

Four new synthetic tests are derived from the role description.

### F3GF-S01 — multi-surface matchday collision

Security incident + ticketing pressure + two hospitality claims.

Expected:

`BLOCK`

Safety case must rank first.

### F3GF-S02 — manager absence + regulatory handoff

Substitute and delegation scope unknown.

Expected:

`HOLD`

### F3GF-S03 — conflicting institutional instructions

Two official instructions conflict.

Expected:

`BLOCK`

No silent reconciliation.

### F3GF-S04 — complete delegated handoff

Explicit handoff, within capacity, no unresolved authority.

Expected:

`ALLOW`

## Governance boundary

Preserved:

- KX108_ONLY;
- no external action;
- no memory write;
- no emits_act;
- no kernel mutation;
- no claim of real internal CSSA field validation.

## Strategic consequence

The next operational layer should not be a generic CRM project.

It should implement the missing execution boundary exposed by this coverage
audit:

```text
authorized decision
→ action proposal
→ MAIL / CALENDAR / CRM / TASKS
→ external execution only when allowed
→ receipt
→ replay
```

The buvette/restauration workflow can be built either before or inside that
operational phase, but it is now an explicit domain gap rather than an unseen
blind spot.
