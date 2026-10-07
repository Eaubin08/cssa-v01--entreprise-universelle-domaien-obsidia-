# F3G-A CSSA ADVERSARIAL SENSITIVITY RECEIPT

Date: 2026-10-07
Branch: `feat/f3g-a-cssa-adversarial-sensitivity-v0`

## Scope

Attack synthetic CSSA organizational assumptions and identify what actually needs real calibration.

## Proof volume

```text
15,120 exhaustive resource profiles
64 exhaustive authority/truth states
6 role-capacity multipliers
5 named operating envelopes
904-event season pressure rescans
```

## Named envelope result

```text
CRUSHED      2 ALLOW / 5 BLOCK / 5 HOLD / 12 conflicts
TIGHT        2 ALLOW / 5 BLOCK / 5 HOLD / 7 conflicts
BASE_F3F     2 ALLOW / 5 BLOCK / 5 HOLD / 5 conflicts
COMFORTABLE  5 ALLOW / 2 BLOCK / 5 HOLD / 0 conflicts
ABUNDANT     5 ALLOW / 2 BLOCK / 5 HOLD / 0 conflicts
```

## Capacity-fragile scenarios

Only:

- vehicle collision;
- hospitality double commitment;
- stadium double booking.

## Authority/truth-sensitive scenarios

Seven scenarios can flip when missing authority/truth is explicitly resolved.

Top calibration target:

`DELEGATION_RESOLVED`

It changes two baseline HOLD scenarios.

## Pressure sensitivity

Largest synthetic pressure ranges:

- RESP_ADMIN_DAILY: 275;
- TEAM_MANAGER_DAILY: 254;
- ADMIN_ACCOUNTING_DAILY: 146.

## Coverage defects found

Modeled but currently unexercised:

- TECHNICAL_DIRECTOR_DAILY;
- VOLUNTEER_MATCHDAY_POOL.

These are recorded as simulator blind spots, not silently treated as tested.

## Adversarial input validation

Fail closed for:

- unknown resource override;
- negative capacity;
- infinite capacity;
- NaN capacity;
- unknown resolved-assumption token.

Zero capacity remains valid as an intentional attack input.

## Real Guard proof

A capacity-induced BLOCK -> ALLOW transition was tested through the real GuardX108 path.

Preserved:

- KX108_ONLY;
- READONLY provider only on ALLOW;
- memory_write=false;
- kernel_mutation=false;
- emits_act=false;
- world_action_allowed=false.

## CI

Run:
`37561671909`

```text
232 passed in 26.60s
```

Artifact ID:
`11456987742`

## Verdict

`F3G_A_ADVERSARIAL_SENSITIVITY_CLOSED`

Next:

`F3G-B PUBLIC REALITY SHADOW MODE`

No merge to main.
