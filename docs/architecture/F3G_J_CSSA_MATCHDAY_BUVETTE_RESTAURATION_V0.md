# F3G-J — CSSA Matchday Buvette / Restauration V0

Date: 2026-10-07
Branch: `feat/f3g-j-cssa-matchday-buvette-restauration-v0`
Base: `feat/f3g-i-cssa-root-cause-recurrence-v0`
Main: unchanged

## Purpose

F3G-F identified one open matchday business gap:

`MATCHDAY_BUVETTE_RESTAURATION`

with four missing workflows:

- `BUVETTE_STOCK_WORKFLOW`
- `RESTAURATION_SUPPLIER_WORKFLOW`
- `SHIFT_ASSIGNMENT`
- `MATCHDAY_CASH_RECONCILIATION`

F3G-J closes these structurally without claiming real CSSA stock, supplier,
staffing or cash-policy data.

## Operating objects

F3G-J extends the existing CSSA model with:

- BuvetteStock
- SupplierOrder
- SupplierDelivery
- ShiftPlan
- TillSession
- CashReconciliation
- MatchdayFoodReadiness

These link to existing:

- Buvette
- VolunteerAssignment
- Payment
- Reconciliation
- Receipt

## Stock

Proven rules:

- sufficient stock -> ALLOW;
- low but sufficient buffer -> risk signal;
- stock below requirement while opening requested -> BLOCK;
- perishable stock without expiry/suitability check -> HOLD.

## Supplier / restauration

Proven rules:

- confirmed delivery with required evidence -> ALLOW;
- required delivery cancelled/refused -> BLOCK;
- delivery status unknown -> HOLD;
- required supplier compliance evidence missing -> HOLD.

No supplier order is placed by this layer.

## Shifts

Proven rules:

- enough assigned slots + known assignment authority -> ALLOW;
- understaffed requested opening -> BLOCK;
- assignment authority unknown -> HOLD;
- volunteer overlap/collision -> BLOCK.

No volunteer is assigned by this layer.

## Matchday readiness

The buvette can only be considered READY when required readiness checks are
complete.

```text
READY + missing checks = BLOCK
```

Venue configuration is authoritative for the simulated case:

```text
opening requested + venue says CLOSED = BLOCK
```

## Cash reconciliation

Cash cases separate:

- expected amount;
- counted amount;
- variance tolerance;
- reconciliation evidence;
- final state.

Proven rules:

- variance within explicit tolerance -> ALLOW + risk signal;
- variance above tolerance -> BLOCK;
- final reconciliation without proof -> HOLD.

A deterministic SHA-256 receipt is generated only for a final ALLOW
reconciliation case.

The receipt is proof metadata only; it does not move money.

## Case catalog

16 synthetic cases:

```text
ALLOW 6
HOLD  4
BLOCK 6
```

All cases are:

`SIMULATED_NOT_OBSERVED`

## Cockpit

Operational stock/supplier/shift/readiness cases route through `MATCHDAY`.

Cash closure cases route through `FINANCE_ACCOUNTING`.

Existing personas therefore receive the correct views:

- MATCHDAY_ORGANIZER
- VOLUNTEER
- MANAGER_GENERAL
- ADMIN_ACCOUNTING

External delivery remains disabled.

## Closure overlay

F3G-J closes:

```text
MATCHDAY_BUVETTE_RESTAURATION
  BUVETTE_STOCK_WORKFLOW
  RESTAURATION_SUPPLIER_WORKFLOW
  SHIFT_ASSIGNMENT
  MATCHDAY_CASH_RECONCILIATION
```

Still unknown before field validation:

- real product catalog;
- real stock/reorder levels;
- real supplier contracts/delivery windows;
- real shift requirements/assignment authority;
- real cash reconciliation policy/tolerance.

## Governance

Preserved:

- KX108_ONLY;
- external_action=false;
- memory_write=false;
- emits_act=false;
- kernel_mutation=false;
- no order placement;
- no volunteer assignment;
- no cash movement;
- no invented real CSSA operational data.
