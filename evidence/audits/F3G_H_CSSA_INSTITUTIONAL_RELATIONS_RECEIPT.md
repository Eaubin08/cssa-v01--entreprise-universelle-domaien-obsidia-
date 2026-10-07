# F3G-H — CSSA INSTITUTIONAL RELATIONS RECEIPT

Date: 2026-10-07

## Branch

`feat/f3g-h-cssa-institutional-relations-v0`

Base:

`feat/f3g-g-cssa-contract-compliance-lifecycle-v0`

Main mutation: `NO`  
Merge: `NO`  
Draft PR: `#5`

## Implemented surfaces

- `organizations/cssa/institutions/institutional_relations_v0.py`
- `organizations/cssa/institutions/public_sources_v0.json`
- `organizations/cssa/institutions/institutional_cases_v0.json`
- `organizations/cssa/institutions/f3g_h_coverage_closure_overlay_v0.json`
- `organizations/cssa/institutions/__init__.py`
- `tests/test_f3g_h_cssa_institutional_relations_v0.py`
- `.github/workflows/f3g-h-cssa-institutional-relations.yml`

## Initial proof

Run:

`37570792978`

Result:

`325 passed in 27.25s`

Conclusion:

`SUCCESS`

## Cases

- 10 simulated institutional cases
- 2 ALLOW
- 3 HOLD
- 5 BLOCK

## Proven boundaries

- acknowledgement != approval
- unknown authority scope -> HOLD
- wrong authority scope -> BLOCK
- wrong required channel -> BLOCK
- conflicting instructions -> BLOCK
- refusal + downstream action -> BLOCK
- final state without proof -> HOLD
- explicit hard deadline missed -> BLOCK
- near deadline -> risk only

## F3G-F gaps closed

- `FFF_RELATION_WORKFLOW`
- `VILLE_COLLECTIVITY_RELATION_WORKFLOW`

## Still unknown

- `REAL_FFF_CASE_CHANNELS_BY_SUBJECT`
- `REAL_VILLE_DE_SEDAN_CASE_SCOPE`
- `REAL_ARDENNE_METROPOLE_APPROVAL_CHAIN`
- `REAL_COLLECTIVITY_CONTACT_AND_APPROVAL_MATRIX`

## Invariants

- KX108_ONLY
- external_action=false
- memory_write=false
- emits_act=false
- kernel_mutation=false
- public sources != private authority proof
- catalog = SIMULATED_NOT_OBSERVED

## Verdict

`CSSA_INSTITUTIONAL_RELATIONS_V0_PROVEN`


## Final frozen-HEAD verification

- run 37570923893
- 325 passed in 26.94s
- SUCCESS
- verified after architecture/report/receipt/status freeze
