# F3G-F — CSSA ANNOUNCED MANAGER ROLE COVERAGE RECEIPT

Date: 2026-10-07

## Branch

`feat/f3g-f-cssa-announced-role-coverage-v0`

Base:

`feat/f3g-e-cssa-controlled-semantic-promotion-v0`

Main mutation:

`NO`

Merge:

`NO`

## Source contract

Official CSSA Manager Général recruitment page:

`https://cs-sedan.fr/recrutement-manager-general`

Truth class:

`PUBLIC_CONFIRMED`

Use:

`PUBLIC_ROLE_DESCRIPTION_NOT_INTERNAL_FIELD_EVIDENCE`

## Implemented surfaces

- `organizations/cssa/coverage/announced_manager_role_coverage_v0.json`
- `organizations/cssa/coverage/announced_role_coverage_v0.py`
- `organizations/cssa/coverage/announced_role_stress_v0.json`
- `organizations/cssa/coverage/__init__.py`
- `tests/test_f3g_f_cssa_announced_role_coverage_v0.py`
- `.github/workflows/f3g-f-cssa-announced-role-coverage.yml`

## Proof

GitHub Actions:

`run 37568479749`

Job:

`announced-role-coverage-proof`

Result:

`291 passed in 27.11s`

Conclusion:

`SUCCESS`

## Coverage

- total announced requirements: 11
- structurally covered: 5
- partial: 4
- open gaps: 2

Open gaps:

1. `MATCHDAY_BUVETTE_RESTAURATION`
2. `DECISION_EXECUTION`

## Announcement-derived stress proof

- scenarios: 4
- ALLOW: 1
- HOLD: 1
- BLOCK: 2
- safety priority preserved
- hard double allocation still BLOCKs
- unresolved delegation still HOLDs

## Preserved invariants

- KX108_ONLY
- external_action = false
- memory_write = false
- emits_act = false
- kernel_mutation = false
- public role description != internal field evidence
- future MAIL/CALENDAR/CRM/TASKS are demand-map only, not active actions

## Closure verdict

`CSSA_ANNOUNCED_MANAGER_ROLE_COVERAGE_V0_PROVEN`
