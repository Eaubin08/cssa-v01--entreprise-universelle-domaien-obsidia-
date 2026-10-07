# F3E CSSA FULL-SEASON SIMULATOR RECEIPT

Date: 2026-10-07
Branch: `feat/f3e-cssa-full-season-simulator-v0`

## Proven synthetic scale

```text
19 team structures
330 fixture/plateau events
904 total organization events
2026-08-01 -> 2027-06-15
24,500 estimated team-route km represented
```

Simulation status everywhere:
`SIMULATED_NOT_OBSERVED`.

## Whole-club coverage

- competitions;
- academy/licences/equipment;
- transport/reconciliation;
- finance;
- partners/hospitality;
- subscribers/ticketing;
- matchday/security-adjacent operations;
- communication;
- staff/volunteers;
- education;
- source/proof freshness;
- privacy-sensitive HR/youth evidence.

## Runtime proof

Representative synthetic season events prove:

- ALLOW -> bounded internal READONLY provider exactly once;
- HOLD -> no provider;
- BLOCK -> no provider;
- sensitive youth/payroll -> stopped before runtime;
- KX108_ONLY;
- memory_write=false;
- kernel_mutation=false;
- emits_act=false;
- world_action_allowed=false.

## Privacy/field contact

Prepared:

- `field_validation/FIRST_TEAM_STAFF_INTERVIEW_V0.md`
- `field_validation/SENSITIVE_HR_PAYROLL_PROTOCOL_V0.md`
- `field_validation/PERSONNEL_EVIDENCE_ABSTRACTION_V0.json`

Raw payroll documents are explicitly forbidden from the public repository.

## CI history

Run 1:
`37557027759`
-> `194 passed, 1 failed`
-> failure was only a 24,499.9 vs 24,500.0 km rounding artifact.

Correction:
per-trip route values are no longer rounded before season aggregation.

Closure:
`37557076230`
job `112585656176`
SUCCESS

```text
195 passed in 0.48s
```

## Verdict

`F3E_FULL_SEASON_SIMULATOR_CLOSED`

No merge to main.
