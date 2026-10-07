# F2 CONFORMANCE TEST RECEIPT

Date: 2026-10-06
Scope: F1 + F2 contract/conformance tests
External Obsidia kernel: NOT CALLED
Current-main runtime: NOT IMPORTED / NOT EXECUTED

## Local isolated run

Command: python -m pytest -q
Result: 32 passed in 0.07s

## GitHub Actions run

Workflow: f2-universal-conformance
Run id: 37520147402
Job id: 112463165631
Conclusion: SUCCESS
Command: python -m pytest tests/test_f1_universal_contract_v0.py tests/test_f2_universal_conformance_v0.py -q
Result: 32 passed in 0.07s

Validated:
- all 11 F1 contract tests;
- four current-main domain profile fixtures: bank, trading, ecom, gps_defense_aviation;
- arbitrary synthetic administration domain accepted at Universal-contract level only;
- domain-specific fields ignored rather than promoted;
- 10 authority/write leak variants fail closed;
- October UDIP candidate mapping preserves unknowns, contradictions, risks, evidence and provenance;
- October UDIP authority leaks are rejected;
- advisory/pre-Guard market_verdict=ACT never becomes a universal decision.

Claim boundary:
F1_F2_CONFORMANCE_TESTED_CI

Not claimed:
- direct import/test against obsidia-x108-proofs main;
- current-main Administration support;
- KX108 runtime integration;
- Binder integration;
- CSSA business correctness;
- external action;
- production readiness.
