# F3E — CSSA FULL-SEASON SYNTHETIC OPERATING SIMULATOR V0

Date: 2026-10-07
Status: CLOSED / SYNTHETIC ONLY

## Objective

Move from isolated CSSA cases to a time-evolving whole-club synthetic season.

F3E does not claim to reproduce CSSA internal reality. It stress-tests the F3D organization/scale model over a complete 2026-2027 synthetic operating cycle.

## Corpus

The deterministic corpus spans:

```text
2026-08-01 -> 2027-06-15
19 public team structures
330 synthetic fixtures / plateaux
904 total operating events
24,500 estimated team-route km
```

The fixture counts for R1/R2 follow the public group structure; youth/female/lower-category counts are explicit simulation profiles, not claimed real calendars.

## Operating families

Events cross the club in parallel:

- academy membership/licences/equipment;
- competitions/FMI;
- away travel and post-trip reconciliation;
- finance/accounting;
- partnerships/hospitality;
- supporter ticketing;
- matchday configuration;
- communication;
- people/HR/volunteers;
- education/school coordination;
- proof/source freshness;
- privacy-sensitive evidence.

## First-team lifecycle

For the synthetic R1 season F3E generates:

- 26 fixture-state cases;
- 13 away-trip plans;
- 13 post-trip reconciliations;
- 26 FMI cases;
- 26 publication candidates;
- 13 home matchday configurations;
- 13 hospitality activations;
- 13 volunteer plans;
- 13 home ticketing states.

## Governance stress

Distributed deterministic anomalies create realistic pressure across the season:

- >1 missing facts -> HOLD;
- >=2 contradictions -> BLOCK;
- high-sensitivity HR/youth evidence -> PRE_RUNTIME_BLOCK;
- clean cases -> ALLOW only for bounded internal READONLY analysis.

Explicit stress events include:

- Manager Général vacancy/delegation uncertainty;
- stale public organigramme contradiction;
- late fixture change awaiting agreement/homologation;
- FMI technical failure;
- youth health data privacy stop;
- employee payroll privacy stop;
- partner invoice without known contract value;
- forbidden subscriber-revenue inference from headcount.

## Route-cost truth boundary

The simulator carries F3D estimated route distances but does not claim actual CSSA vehicle use or expenses.

Team-route kilometres are counted once at trip planning. Post-trip reconciliation is evidence/accounting workflow, not extra travel.

## Real runtime proof

Representative ALLOW/HOLD/BLOCK season events traverse:

```text
F3E synthetic event
 -> F3B generic Administration adapter
 -> F2.5 aggregate-only resolver
 -> REAL DomainAggregate
 -> REAL GuardX108
 -> REAL canonical runtime lifecycle
 -> bounded READONLY provider only on ALLOW
```

Privacy-blocked events never enter runtime.

## Field-contact preparation

A current first-team staff contact can materially improve the model, especially around:

- employing legal entity;
- contract type;
- reporting/validation chain;
- weekly planning;
- travel booking;
- staff expenses;
- mileage/meal/travel allowance process;
- tools/channels;
- administrative contact;
- difference between first-team and Association workflows.

Raw payslips are not needed for the proof and are forbidden in the public repo.

If voluntarily used, only a manually redacted/abstracted record should survive.

## CI

Initial run:
- run 37557027759;
- 194 PASS / 1 FAIL;
- only failure: 0.10 km rounding drift in season aggregation.

Fix:
- preserve per-trip route precision until final season aggregation.

Closure run:
- run 37557076230;
- job 112585656176;
- SUCCESS;
- `195 passed in 0.48s`.

## Claim boundary

`CSSA_FULL_SEASON_SYNTHETIC_OPERATING_CORPUS_PROVEN_V0`

Not claimed:

- real CSSA internal workflow fidelity;
- real payroll/contract data;
- exact real youth calendars;
- actual transport invoices;
- production action authority.
