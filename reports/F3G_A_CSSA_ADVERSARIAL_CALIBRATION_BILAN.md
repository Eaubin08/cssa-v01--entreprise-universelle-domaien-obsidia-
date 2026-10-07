# CSSA / V0.1 — F3G-A ADVERSARIAL CALIBRATION BILAN

Date: 2026-10-07
Branch: `feat/f3g-a-cssa-adversarial-sensitivity-v0`
Main: unchanged

## Executive result

We intentionally tried to break the current CSSA simulator by moving its assumptions to extreme values.

Attack volume:

```text
15,120 resource-capacity profiles
64 authority/truth profiles
904 season events rescanned across role-capacity extremes
232 tests PASS
```

The system did not silently invent negative capacity, unknown resources, non-finite values or new authority.

## Main finding 1 — resources are not the core of every failure

Going from a near-collapsed synthetic organization to an abundant one changes:

```text
BASE/CRUSHED:
ALLOW 2
BLOCK 5
HOLD 5

ABUNDANT:
ALLOW 5
BLOCK 2
HOLD 5
```

So large synthetic resource relief fixes three physical double-allocation problems.

It does not fix:

- missing delegation;
- missing budget authority;
- unresolved FMI state;
- unresolved human reallocation;
- stale truth;
- unpropagated match-state contradictions.

The model therefore does not collapse into:

`more people/money = everything ALLOW`.

## Main finding 2 — delegation is currently the most valuable real fact

Resolving one real-world question:

> Who takes over when the responsible person is absent, and what can that substitute actually validate/sign?

changes two separate modeled HOLDs.

No other single tested truth assumption changes two scenarios.

So when real staff access becomes available, delegation/substitution should be asked before exact salary, exact vehicle count or exact budget.

## Main finding 3 — Administration capacity is a major pressure lever

It does not directly change the KX gate in the current model, but it changes season workload pressure dramatically:

```text
admin capacity 0%   -> 278 pressure points
25%                 -> 129
50%                 -> 28
100%                -> 4
200%                -> 4
400%                -> 3
```

This is important.

The governance kernel can remain correct while the organization around it is operationally drowning.

Therefore the cockpit must continue exposing capacity pressure separately from decision authority.

## Main finding 4 — three physical shared resources really change verdicts

Capacity alone can flip governance in the current explicit tests for:

- vehicles;
- hospitality space;
- stadium slot.

Across 15,120 profiles:

```text
vehicle scenario:
ALLOW 6,048 / BLOCK 9,072

hospitality scenario:
ALLOW 7,560 / BLOCK 7,560

stadium scenario:
ALLOW 5,040 / BLOCK 10,080
```

This gives us actual synthetic thresholds to recalibrate later instead of redesigning the logic.

## Main finding 5 — two parts of our model were not really being tested

The adversarial coverage audit found:

```text
TECHNICAL_DIRECTOR_DAILY
VOLUNTEER_MATCHDAY_POOL
```

Both existed as resource concepts but nothing in the current workload/stress model actually exercised them.

This is a useful failure of coverage.

It means we must not claim that F3F/F3G-A validated technical-direction or volunteer capacity behavior.

Those layers need extra public/shadow scenarios later.

## What we can extrapolate now

Without pretending it is the real CSSA, we now have defensible synthetic envelopes:

- collapsed/constrained operation;
- current baseline;
- comfortable operation;
- abundant-capacity operation.

That lets us run future scenarios approximately even before field access.

When a real number later arrives, we do not rebuild the architecture.

We replace the parameter and rerun the same tests.

## Calibration order if real information becomes available

Highest-value facts first:

1. delegation/substitution authority;
2. travel overrun/budget authority;
3. FMI ownership/closure;
4. hospitality capacity;
5. facility/stadium conflict arbitration;
6. safety-vs-partner arbitration;
7. match-change propagation chain;
8. authoritative source hierarchy;
9. actual shared transport capacity;
10. administrative overflow capacity.

## Current conclusion

The simulator is now useful even with imperfect estimates because the important assumptions are explicit and replaceable.

The next step is not to wait for private CSSA data.

The next step is F3G-B:

`PUBLIC REALITY SHADOW MODE`

Use live/public CSSA + LGEF/FFF reality as observations, let Obsidia produce the same governed/cockpit outputs, and compare public reality against the synthetic model without taking any external action.
