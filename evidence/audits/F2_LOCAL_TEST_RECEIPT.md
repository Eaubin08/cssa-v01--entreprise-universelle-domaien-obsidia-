# F2 LOCAL TEST RECEIPT

Date: 2026-10-06
Scope: F1 + F2 isolated contract/conformance tests
External Obsidia kernel: NOT CALLED
Current-main runtime: NOT IMPORTED / NOT EXECUTED

Command:

python -m pytest -q

Result:

32 passed in 0.07s

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
ISOLATED_F1_F2_CONFORMANCE_TESTED

Not claimed:
- direct import/test against obsidia-x108-proofs main;
- current-main Administration support;
- KX108 runtime integration;
- Binder integration;
- CSSA business correctness;
- external action;
- production readiness.

CI note:
A GitHub Actions workflow was added on the F2 branch. At receipt creation time, no GitHub Actions run was yet visible through the repository API; the 32/32 result above comes from an isolated local execution of the committed F1/F2 logic.
