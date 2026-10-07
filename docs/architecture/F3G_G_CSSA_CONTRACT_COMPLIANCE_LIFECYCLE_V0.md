# F3G-G — CSSA Contract & Compliance Lifecycle V0

Date: 2026-10-07  
Branch: `feat/f3g-g-cssa-contract-compliance-lifecycle-v0`  
Base: `feat/f3g-f-cssa-announced-role-coverage-v0`  
Main: unchanged

## Purpose

F3G-F identified two explicit gaps inside the announced daily administration
scope:

- `CONTRACT_LIFECYCLE_WORKFLOW`
- `GENERIC_COMPLIANCE_CASE_WORKFLOW`

F3G-G closes those two structural gaps without claiming knowledge of the real
CSSA contract inventory, signature authority chain or compliance catalog.

## Contract lifecycle

Explicit states:

```text
DRAFT
→ REVIEW
→ APPROVED
→ SIGNED
→ ACTIVE
→ EXPIRING
→ EXPIRED

SIGNED / ACTIVE / EXPIRING
→ TERMINATED
```

Only declared transitions are accepted.

Examples of fail-closed conditions:

- signature authority unknown -> HOLD;
- authority scope unknown -> HOLD;
- signature evidence missing -> HOLD;
- multiple active versions -> BLOCK;
- active state before effective date -> BLOCK;
- active state after end date -> BLOCK;
- expired/terminated contract requested for operation -> BLOCK.

A renewal window is a risk signal, not a fabricated BLOCK.

## Compliance lifecycle

Explicit states:

```text
NOT_ASSESSED
APPLICABILITY_REVIEW
OPEN
EVIDENCE_PENDING
SATISFIED
OVERDUE
CONTESTED
CLOSED
```

Fail-closed examples:

- applicability unknown -> HOLD;
- authority/source of obligation unknown -> HOLD;
- owner/escalation route unknown -> HOLD;
- mandatory deadline missed while still open -> BLOCK;
- contested unresolved requirement -> BLOCK;
- SATISFIED/CLOSED without auditable evidence -> HOLD.

A known upcoming deadline can remain ALLOW while surfacing a risk flag.

## Truth boundary

The case catalog is:

`SIMULATED_NOT_OBSERVED`

F3G-G does not claim:

- actual CSSA contract types;
- actual contract values;
- actual signatures;
- actual internal signatories;
- actual legal authority scopes;
- actual compliance obligation inventory.

These remain field-calibration targets.

## Cockpit integration

Contract and compliance assessments expose the existing reporting-event surface:

```text
GOVERNANCE_LEGAL
→ MANAGER_GENERAL
→ RESP_ADMIN
→ CLUB_SECRETARIAT
→ other existing routed roles
```

This is reporting only.

No mail, filing, signature, calendar mutation, CRM update or task execution is
performed.

## F3G-F closure overlay

The historical F3G-F matrix is not rewritten.

F3G-G adds a separate closure overlay:

```text
ADMINISTRATION_DAILY
  closed:
    CONTRACT_LIFECYCLE_WORKFLOW
    GENERIC_COMPLIANCE_CASE_WORKFLOW

  still unknown before field validation:
    REAL_INTERNAL_CONTRACT_TYPES
    REAL_SIGNATURE_AUTHORITY_CHAIN
    REAL_COMPLIANCE_OBLIGATION_CATALOG
```

This preserves the audit trail from detected gap to later closure.

## Governance

Invariant:

```text
DOMAIN STRUCTURES
KX108 ONLY DECIDES
EXTERNAL ACTION = FALSE
MEMORY WRITE = FALSE
EMITS_ACT = FALSE
KERNEL MUTATION = FALSE
```
