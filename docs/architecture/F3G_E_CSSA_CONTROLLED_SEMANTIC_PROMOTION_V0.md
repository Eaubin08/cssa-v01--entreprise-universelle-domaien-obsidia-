# F3G-E — CSSA Controlled Semantic Promotion & Impact Propagation V0

Date: 2026-10-07  
Branch: `feat/f3g-e-cssa-controlled-semantic-promotion-v0`  
Main: unchanged

## Purpose

F3G-D proved that public pages can be watched repeatedly without silently
turning HTML drift into truth.

F3G-E closes the next gap:

```text
PUBLIC PAGE DELTA
        ↓
HOLD / semantic review required
        ↓
EXPLICIT REVIEW PACKET
        ↓
baseline / source / truth / unresolved checks
        ↓
CONTROLLED PUBLIC STATE PROMOTION
        ↓
affected public anchor only
        ↓
stress + sensitivity rerun
        ↓
persona reporting impact
        ↓
NO EXTERNAL ACTION
```

## Hard invariants

1. A changed page never promotes itself.
2. `review_decision=APPROVED` is mandatory.
3. The reviewed source must already exist in the public snapshot.
4. The reviewed `expected_before_values` must still equal the current state.
   A stale human review therefore fails closed instead of overwriting newer data.
5. Unresolved unknowns or contradictions block promotion.
6. Public evidence may update an explicit PUBLIC anchor.
7. Public evidence may not silently rewrite ESTIMATED internal capacities.
8. Promotion never mutates the source snapshot/envelope objects in place.
9. Every promotion produces a review ledger entry and an exact semantic diff.
10. Stress/sensitivity and reporting are rerun even when the result is
    "no downstream operational metric changed".
11. `KX108_ONLY`, `memory_write=False`, `emits_act=False`,
    `kernel_mutation=False`, `external_action=False`.

## Current proof fixture

`reviewed_change_manager_general_fixture_v0.json` is deliberately marked:

`SIMULATED_REVIEW_PACKET_NOT_OBSERVED`

It does **not** assert that CSSA has appointed a manager.

It proves the mechanism against a realistic reviewed change shape:

- reviewed public state key: `manager_general_public_state`;
- exact pre-review value set is frozen;
- one official source is referenced;
- one public anchor is updated;
- the 15 estimated capacity parameters remain untouched;
- the stress/sensitivity engine is rerun;
- the promoted event is routed to affected internal personas.

## Expected behavior of the fixture

Public semantic state:

```text
before:
  FORMER_MANAGER_STILL_LISTED
  VACANT_OR_SUCCESSOR_NOT_PUBLICLY_CONFIRMED

after:
  APPOINTED_PUBLICLY_CONFIRMED
```

Envelope:

```text
PUBLIC_MANAGER_STATE_UNRESOLVED
    → reviewed public value changes

LOW / CENTRAL / HIGH estimated capacities
    → unchanged
```

Impact:

```text
changed semantic states: 1
changed public anchors: 1
changed estimated capacities: 0
stress/sensitivity rerun: YES
expected changed stress profiles: 0
reporting rerun: YES
external action: NO
```

## Why zero stress change is meaningful

The public fact "manager state changed" is not equivalent to an internal
capacity fact such as `MANAGER_GENERAL_DAILY=5`.

F3G-E therefore refuses this invalid shortcut:

```text
public title/person exists
    ≠
known internal availability/capacity/delegation
```

A future REAL_FIELD_EVIDENCE packet can replace a capacity parameter through a
separate calibrated path. Public semantic promotion alone cannot.

## Files

- `organizations/cssa/promotion/controlled_semantic_promotion_v0.py`
- `organizations/cssa/promotion/reviewed_change_manager_general_fixture_v0.json`
- `tests/test_f3g_e_cssa_controlled_semantic_promotion_v0.py`
- `.github/workflows/f3g-e-cssa-controlled-semantic-promotion.yml`

## Boundary

This phase remains READONLY with respect to real CSSA systems.

No email send.  
No calendar mutation.  
No CRM mutation.  
No website mutation.  
No automatic truth promotion from watcher output.  
No merge to main.
