# F3D CSSA SEASON-SCALE AUDIT RECEIPT

Date: 2026-10-07
Branch: `feat/f3d-cssa-season-scale-audit-v0`

## Scope

F3D expands the CSSA model from isolated simulated cases to the public/estimated scale required for a full-season simulator.

## Public structure

Validated public organizational model:

- 19 team structures from Seniors R1/R2/U20 to U6;
- administrative/accounting/secretariat roles;
- technical and academy coordination;
- matchday organization/security;
- partnerships/merchandising/communication;
- school-section and external-authority interfaces.

## Economic/admin public parameters

Recorded as PUBLIC_CONFIRMED where applicable:

- CSSA licence packs: 180 / 240 / 300 EUR;
- family / female / Pass'Sport discount parameters;
- LGEF 2026-2027 licence tariffs;
- selected LGEF discipline/procedure tariffs;
- 13 R1 home league matches in season subscription;
- +50 active-partner marketing claim;
- 800 subscriber official/reposted snapshot, partners included;
- public partner/audience metrics.

Explicitly kept UNKNOWN_PRIVATE:

- final subscriber count;
- partner revenue;
- partner contract tiers;
- certified current club budget;
- exact category headcounts;
- actual transport reimbursement policy;
- staff/player compensation;
- current Association/SAS operating split.

## Travel scale model

Regular team-route estimate:
`20,000-29,000 km`.

Full season simulation envelope with cups/tournaments/friendlies:
`22,000-36,250 team-route km`.

The model explicitly distinguishes team-route km from vehicle-km.

Configurable cost scenarios:

- LOW: 15,400 EUR;
- BASE: 32,765.62 EUR;
- HIGH: 65,250 EUR.

These are simulation values only, not CSSA accounts.

DVCR previous-season public benchmark is preserved separately:
15 covered away trips / 3,208 km.
It is an independent media-volunteer travel benchmark, not a CSSA team cost.

## Public-source coherence findings

Captured without silent reconciliation:

- stale Manager Général organigramme vs official departure communiqué;
- stale R3 reserve label vs current R2 competition;
- +12 home-matches marketing wording vs 13 league home matches in subscription;
- official website freshness/update warning.

## Personas

The role model now covers at least 25 whole-club personas/interfaces, including:

- direction;
- Manager Général;
- administration/accounting/secretariat;
- technical/academy staff;
- team operations;
- guardians/licence holders;
- matchday/security/volunteers;
- ticketing;
- partnerships/partner contacts;
- communication/supporters;
- LGEF/District/FFF;
- referees;
- municipality;
- school section;
- suppliers;
- independent supporter media.

## Football Manager reference

Only management abstractions are retained:

- responsibilities;
- delegation;
- task inbox;
- budgets/cost centers;
- team planner;
- youth pipeline;
- staff capability;
- calendar workload;
- board objectives;
- finance overview.

Game formulas, hidden ratings and fictional values are explicitly forbidden as real-world facts.

## Guardrails

Finance helpers refuse to infer:

- subscription revenue from subscriber count alone;
- partner revenue from partner count alone.

Explicit product mix/contract values are required.

## CI

Workflow: `f3d-cssa-season-scale-audit`
Run: `37555962749`
Job: `112582133606`
Conclusion: SUCCESS

```text
183 passed in 0.65s
```

## Claim boundary

`CSSA_SEASON_SCALE_PUBLIC_AUDIT_AND_SIMULATION_PARAMETERS_PROVEN_V0`

Not proven:

- real internal CSSA workflows;
- real current operating budget;
- exact season travel invoices;
- actual Association/SAS division of responsibilities;
- production integration.

## Next

F3E — build the long-running synthetic CSSA season corpus using the F3D scale model and generate simultaneous cases across the whole organization.
