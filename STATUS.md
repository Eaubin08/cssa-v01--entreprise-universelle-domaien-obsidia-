# STATUS

Status: F3E_CSSA_FULL_SEASON_SIMULATOR_CLOSED
Branch: `feat/f3e-cssa-full-season-simulator-v0`

## Universal / runtime

- F1 universal contract: PASS
- F2 conformance: PASS
- F2.1 real Guard compatibility: PASS
- F2.2 portable registration: PASS
- F2.3 canonical-compatible resolver: PASS
- F2.4 full canonical runtime: PASS
- F2.5 first-class aggregate-only resolver: FROZEN OFF MAIN

## CSSA

- F3A public baseline: PASS
- F3B field intake kit: READY
- F3C isolated synthetic scenarios: PASS
- F3D season-scale audit/model: PASS
- F3E full-season synthetic operating corpus: PASS
- F0-B real CSSA internal field evidence: OPEN
- external action: HOLD

## F3E scale

- 19 team structures
- 330 synthetic fixture/plateau events
- 904 total operating events
- 2026-08-01 -> 2027-06-15
- 24,500 estimated team-route km represented once per trip
- whole-club concurrent administrative workload

## Whole-club event families

- academy/licences/equipment
- competitions/FMI
- travel/reconciliation
- finance/accounting
- partners/hospitality
- supporters/ticketing
- matchday
- communication
- staff/volunteers
- education
- source freshness/proof
- privacy-sensitive HR/youth evidence

## Governance

- clean synthetic cases -> ALLOW for internal READONLY only
- >1 unknown -> HOLD
- >=2 contradictions -> BLOCK
- high-sensitivity youth/payroll -> PRE_RUNTIME_BLOCK
- KX108_ONLY preserved
- no memory write
- no kernel mutation
- no world action

## CI

First run:
- 194 PASS / 1 FAIL
- only failure: 0.10 km aggregation rounding drift

Fixed by preserving route precision before aggregation.

Closure:
- run `37557076230`
- job `112585656176`
- `195 passed in 0.48s`
- SUCCESS

## Real first-team contact path

Prepared field-validation protocols for a current first-team staff contact.

Preferred evidence:
- employing entity
- contract type
- reporting/validation chain
- travel/expense workflow
- tools/channels
- administrative handoffs
- first-team vs Association differences

Raw payslips are not required and are forbidden from the public repo.
Any real payroll evidence must be manually redacted/abstracted first.

## Next

F3F should stress **organizational decisions over the season**, not merely generate events:

- workload collisions
- delegation failures
- budget-pressure propagation
- deadline cascades
- cross-team shared-resource conflicts
- source freshness propagation
- partner/matchday commitments
- transport capacity
- staff absence/substitution
- evidence completeness
- multi-case prioritization

F3F should answer:
"Can Obsidia keep the whole club coherent when many valid cases compete for the same people, money, time and authority?"

No merge to main.
