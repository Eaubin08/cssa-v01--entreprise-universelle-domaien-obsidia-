# CSSA / V0.1 — F3G-F ANNOUNCED ROLE COVERAGE BILAN

Date: 2026-10-07  
Branch: `feat/f3g-f-cssa-announced-role-coverage-v0`  
Main: unchanged  
Draft PR: #2 — F3G-F -> F3G-E, no merge requested  
CI trigger PR: #3 — temporary proof surface only, do not merge

## Executive result

The public CSSA Manager Général job description has been converted into a
testable business contract and compared against the current CSSA domain.

Closure proof:

```text
11 announced responsibilities
 5 STRUCTURALLY_COVERED
 4 PARTIAL
 2 OPEN_GAP

4 announcement-derived stress scenarios
 1 ALLOW
 1 HOLD
 2 BLOCK

291 / 291 tests PASS
run 37568479749
external action = false
KX108_ONLY
```

## What the announcement validates

The current model already contains the right large organizational layers:

- administration / competitions / licences;
- institutional relations;
- people / volunteers / delegation;
- ticketing;
- security;
- hospitality;
- cross-pole coordination;
- explicit workflows and responsibilities;
- proof/audit/stress.

The official announcement therefore behaves more like an external validation
target than a contradiction of the current architecture.

## What it exposes as incomplete

### Administration is not fully closed

Public and competition administration are strong.

Still missing as dedicated end-to-end workflows:

- contract lifecycle;
- generic compliance case lifecycle.

### Institutional relations are only partially closed

LGEF/District-style relationships are represented.

Still not individually closed:

- FFF relationship workflow;
- Ville/collectivity workflow.

### Real delegation remains unknown

The model can represent and stress delegation/substitution.

It does not know the real CSSA:

- authority chain;
- substitution chain;
- role capacity.

### Root-cause logic is architectural, not yet a workflow

Unknowns, contradictions, receipts, replay and recurring watch/stress exist.

A dedicated incident -> root cause -> corrective action -> recurrence-prevention
receipt lifecycle does not yet exist.

## Two open gaps

### MATCHDAY_BUVETTE_RESTAURATION

Object exists.

Workflow proof does not.

Missing:

- stock;
- supplier/restauration;
- cash reconciliation;
- shift assignment.

### DECISION_EXECUTION

This is the largest gap and the natural bridge to the later automation layer.

Today:

```text
understand
→ govern
→ decide
→ report
→ STOP before external execution
```

Future:

```text
authorized decision
→ MAIL / CALENDAR / CRM / TASK
→ receipt
→ replay
```

No such external action has been enabled in F3G-F.

## Stress result

The announcement-derived suite proves:

- safety still outranks commercial/matchday convenience;
- hard hospitality double allocation BLOCKs;
- missing delegation authority HOLDs;
- conflicting official instructions BLOCK;
- a complete delegated handoff can ALLOW.

## Current verdict

`CSSA_ANNOUNCED_MANAGER_ROLE_COVERAGE_V0_PROVEN`

This verdict means the coverage model and its gaps are proven against the
current repository.

It does not mean the real internal CSSA operating process is field-proven.

## Next

Before CRM/mail/calendar execution, the remaining test work can continue from
this exact gap map.

The next major operational phase should then target:

`DECISION_EXECUTION`

with MAIL / CALENDAR / CRM / TASKS behind explicit authority and receipts.
