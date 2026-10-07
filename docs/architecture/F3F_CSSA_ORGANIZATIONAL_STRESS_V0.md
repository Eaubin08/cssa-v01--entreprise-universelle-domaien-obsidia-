# F3F — CSSA ORGANIZATIONAL STRESS V0

Date: 2026-10-07
Status: IMPLEMENTED / SYNTHETIC RESOURCE MODEL / NO EXTERNAL ACTION

## Objective

F3F tests whether the CSSA/V0.1 organization model remains coherent when valid cases compete for the same people, time, vehicles, budget, facilities and authorities.

This phase is not an optimizer with execution authority.

It is a non-sovereign stress-analysis layer feeding the existing Administration/KX108 governance path and the reporting cockpit.

## Inputs

F3F consumes:

- F3E full-season corpus: 904 synthetic organization events;
- F3D whole-club personas and operating domains;
- F3E reporting/persona-routing layer;
- a synthetic resource-capacity model;
- 12 explicit organizational collision scenarios.

All F3F resource capacities are:

`SIMULATED_NOT_OBSERVED`

They are test parameters, not claims about CSSA real staffing, vehicle fleet, budget or facilities.

## Synthetic shared resources

The V0 model includes:

- daily capacity for Administration;
- daily Finance/Admin Accounting capacity;
- Manager Général capacity;
- Direction Technique capacity;
- Formation coordination capacity;
- Team Manager/Intendance capacity;
- Matchday organization capacity;
- Partnerships capacity;
- Communication capacity;
- Ticketing capacity;
- 2 simulated vehicle-equivalents;
- 1 hospitality activation slot;
- 1 main-stadium slot;
- 5,000 EUR simulated monthly travel envelope;
- 30 simulated matchday volunteer slots.

## Priority policy

F3F generates a priority order but does not authorize the work.

Priority is deterministic:

1. safety-critical cases;
2. regulatory cases;
3. immediate deadlines;
4. near deadlines;
5. proof/audit and competition tie-breakers.

This is an information-ordering policy only.

`PRIORITY != AUTHORITY`

## Hard resource conflicts

A hard double allocation of a physical/shared asset produces structural contradictions.

Examples:

- 3 vehicle-equivalent demands for capacity 2;
- 2 hospitality commitments for capacity 1;
- 2 uses of the same stadium slot.

Those cases feed contradictions to the real GuardX108 and fail closed to BLOCK.

## Soft organizational pressure

Role overload or budget pressure does not automatically become a sovereign BLOCK.

It produces:

- pressure risk flags;
- unknown approvals/reallocations where appropriate;
- HOLD when information/authority is missing;
- a priority order for human/organizational handling.

## Explicit stress catalog

F3F includes 12 scenarios:

1. three away teams / two vehicle-equivalents;
2. admin absence + urgent LGEF work;
3. travel budget pressure;
4. late match change cascading into transport/ticketing contradiction;
5. double partner hospitality commitment;
6. FMI backlog + new deadline;
7. stale-source contradiction;
8. absence with no validated delegation;
9. twenty simultaneous valid cases;
10. normal multi-case day within capacity;
11. safety vs partner priority under shared role pressure;
12. stadium double booking.

Expected governance surface:

```text
ALLOW  2
HOLD   5
BLOCK  5
```

## Full-season pressure scan

All 904 F3E events are also scanned against simulated daily role capacity.

Closure run detected:

`4 synthetic capacity-pressure points`

This is significant because those pressure points emerge from the already-generated season workload rather than only from hand-written stress scenarios.

They are not claims about real CSSA overload.

## Safety-first discovery

The first F3F CI exposed an incorrect test expectation.

The 20-valid-case queue test initially expected an urgent regulatory case to rank first.

The engine ranked a safety-critical matchday case first.

The implementation was internally consistent; the test assumption was wrong.

F3F therefore made the policy explicit:

`SAFETY > REGULATORY > DEADLINE`

and froze that expected ordering in the scenario catalog.

## Runtime governance proof

Representative ALLOW / HOLD / BLOCK stress assessments cross:

```text
F3F stress assessment
 -> Administration field adapter
 -> F2.5 aggregate-only resolver
 -> REAL DomainAggregate
 -> REAL GuardX108
 -> canonical decision lifecycle
 -> bounded READONLY provider only on ALLOW
```

Verified invariants:

- KX108_ONLY;
- decision record verified;
- memory_write = false;
- kernel_mutation = false;
- emits_act = false;
- world_action_allowed = false;
- HOLD/BLOCK never invoke provider.

## Reporting cockpit integration

F3F assessments are now fed into the existing reporting layer as:

`ORGANIZATIONAL_STRESS`

The reporting route sends cross-layer findings to relevant recurring personas, including:

- Direction/Présidence;
- Manager Général;
- Administration;
- Finance;
- Direction Technique;
- Team Manager/Intendance;
- Matchday;
- Ticketing;
- Partnerships;
- Communication.

The F3F workflow now generates:

- stress JSON artifact;
- weekly stress-aware report pack;
- biweekly stress-aware report pack;
- monthly stress-aware report pack;
- persona-specific views.

External delivery remains disabled.

## Architectural result

The system now has three distinct layers:

```text
SEASON EVENTS
      ↓
RESOURCE / DEADLINE / DEPENDENCY PRESSURE
      ↓
NON-SOVEREIGN STRESS ASSESSMENT
      ↓
KX108 GOVERNANCE
      ↓
REPORTING / PERSONA ROUTING
      ↓
HUMAN / ORGANIZATIONAL DECISION
```

The stress layer can propose ordering and identify impossible allocations.

It cannot act, book, spend, send, reassign or override authority.
