# F3B CSSA FIELD INTAKE KIT RECEIPT

Date: 2026-10-06
Branch: `feat/f3b-cssa-field-intake-kit-v0`

## Scope

Prepare the real CSSA field-acquisition layer without ingesting any private club data.

## Implemented

- typed field-source contract;
- typed field-case contract;
- bundle validation;
- READONLY-only intake boundary;
- evidence classes;
- privacy/sensitivity classes;
- high-sensitivity runtime stop;
- source/case provenance;
- local-practice vs public-rule separation;
- CSSA validation flag;
- field-case -> Administration runtime adapter;
- anonymized fixture-change sample;
- anonymized FMI-exception sample;
- blocked sensitive sample;
- first-session runbook;
- public-rule-vs-local-practice template;
- Git ignore rules for private field data.

## Safety behavior

Unvalidated real field evidence automatically carries:
`FIELD_CASE_NOT_YET_CSSA_VALIDATED`.

Therefore an unvalidated sample reaches the real Guard as uncertainty and produces HOLD rather than silently becoming organizational truth.

High-sensitivity sources containing:
- MINOR_DATA;
- HEALTH_DATA;
- DISCIPLINARY_DATA;
- FINANCIAL_DATA;

are stopped before runtime ingestion and require manual privacy review.

## Runtime proof

Validated clean field case path:

```text
field source bundle
 -> CSSAFieldCaseV0
 -> Administration DomainStateRefV0
 -> frozen F2.5 aggregate-only resolver
 -> REAL DomainAggregate
 -> REAL GuardX108
 -> full canonical runtime
 -> bounded internal READONLY provider
 -> sealed receipt
```

Unvalidated case path:

```text
field case not validated by CSSA
 -> explicit unknown
 -> REAL GuardX108
 -> HOLD
 -> no provider execution
```

## GitHub Actions proof

Workflow: `f3b-cssa-field-intake-kit`
Run: 37530649833
Job: 112498875204
Conclusion: SUCCESS

Result:

```text
120 passed in 0.35s
```

## First failed run

Run 37530422232 failed with 119 PASS / 1 FAIL because the test attempted to read `result.unknowns`, a field not exported by the canonical runtime result object.

The test was corrected to assert the actual Guard reason code (`UNKNOWNS_OR_CONFIDENCE_LOW`) while the unknown itself remains verified at the DomainStateRef level.

No runtime behavior was changed to fix that test.

## Claim boundary

`CSSA_FIELD_INTAKE_KIT_READY`

Not claimed:
- any real CSSA private workflow has been observed;
- any CSSA employee has validated a case;
- any external write is authorized;
- Administration semantics are frozen;
- production deployment.
