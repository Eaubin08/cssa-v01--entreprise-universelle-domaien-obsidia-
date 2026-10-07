# STATUS

Status: F3E_CSSA_REPORTING_ROUTING_CLOSED
Branch: `feat/f3e-cssa-reporting-routing-v0`

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
- F3E reporting/persona routing: PASS
- F0-B real CSSA internal field evidence: OPEN
- external action: HOLD

## Season simulation

- 19 team structures
- 330 synthetic fixture/plateau events
- 904 total operating events
- 2026-08-01 -> 2027-06-15
- 24,500 estimated team-route km

## Reporting system

Cadences:

- WEEKLY: Monday, lookback 7d + lookahead 7d
- BIWEEKLY: every 14 days from 2026-10-19, lookback 14d + lookahead 14d
- MONTHLY: day 1, lookback 31d + lookahead 31d

Outputs:

- global report
- summary JSON
- persona-specific report files

Routing covers:

- Direction/Présidence
- Manager Général
- Administration
- Secrétariat
- Finance/Admin Accounting
- Direction Technique
- Formation / Foot 5-8
- Team Manager/Intendance
- Matchday
- Security
- Volunteers
- Ticketing/Boutique
- Partnerships
- Communication
- School/Education

## Truth boundary

Every report item retains one explicit class:

- PUBLIC_CONFIRMED
- SECONDARY_CORROBORATED
- ESTIMATED
- SIMULATED_NOT_OBSERVED
- REAL_FIELD_EVIDENCE
- UNKNOWN_PRIVATE

No silent promotion is allowed.

## Privacy

Sensitive HR/youth cases:

- metadata-only;
- MANAGER_GENERAL + RESP_ADMIN only;
- source/provenance/amount/detail redacted;
- PRE_RUNTIME_BLOCK preserved.

## Delivery boundary

Repository generates artifacts only.

Disabled:

- email
- Slack/WhatsApp
- CRM mutation
- website publication
- supporter/partner send

`external_delivery = false`

`KX108_ONLY` unchanged.

## CI

Initial reporting implementation:

- 205 tests PASS;
- artifact generation failed because direct script execution could not import the repository package.

Fix:

- repository root added to generator import path.

Closure:

- run `37558491140`
- job `112590142497`
- `205 passed in 0.86s`
- weekly + biweekly + monthly packs generated
- artifact upload SUCCESS

## Automation state

The repository contains a daily GitHub Actions schedule hook.

Because scheduled workflows run from the default branch and this work remains off-main:

`CRON_READY_BUT_DORMANT_OFF_MAIN`

No merge to main is authorized by this status.

## Next

F3F remains the next functional phase:

stress organizational decisions and shared resources across the season:

- workload collisions
- delegation failures
- transport capacity
- budget pressure
- staff absence/substitution
- deadline cascades
- partner/matchday commitments
- source freshness propagation
- multi-case prioritization

Reporting should be used as the observation surface for F3F so every stress run produces:

- weekly operational view;
- biweekly cross-layer view;
- monthly governance view;
- role-specific information packs.

No merge to main.
