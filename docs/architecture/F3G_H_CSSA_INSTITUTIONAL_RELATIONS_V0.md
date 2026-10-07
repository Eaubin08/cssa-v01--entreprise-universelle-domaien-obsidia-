# F3G-H — CSSA Institutional Relations V0

Date: 2026-10-07  
Branch: `feat/f3g-h-cssa-institutional-relations-v0`  
Base: `feat/f3g-g-cssa-contract-compliance-lifecycle-v0`  
Main: unchanged

## Purpose

F3G-F identified two remaining institutional-relation gaps:

- `FFF_RELATION_WORKFLOW`
- `VILLE_COLLECTIVITY_RELATION_WORKFLOW`

F3G-H closes those structural gaps without claiming knowledge of the private
CSSA authority, contact, channel or approval matrix.

## Public source boundary

Public sources support only a narrow actor/scope inventory.

### CSSA Manager Général recruitment

Supports that the role maintains relations with:

- Ligue;
- District;
- Fédération;
- Ville de Sedan;
- collectivités.

It does not expose private authority chains, mandatory channels, response
deadlines or approval scopes.

### Ardenne Métropole — Louis-Dugauguez

The current public page identifies Louis-Dugauguez as an enclosure under the
responsibility of Ardenne Métropole and identifies CSSA use of the stadium.

It does not authorize CSSA to self-approve facility changes and does not expose
the current private operating approval chain.

### District des Ardennes / FFF channel

The District public site exposes current CSSA activity on a FFF-linked channel.

This proves an institutional/public relationship surface only, not universal
District or FFF authority over every CSSA subject.

## Institutional lifecycle

Supported states:

```text
DRAFT
READY_TO_SEND
SENT
ACKNOWLEDGED
UNDER_REVIEW
APPROVED
REFUSED
CLOSED
CONTESTED
```

## Critical semantic rule

```text
ACKNOWLEDGED != APPROVED
```

An acknowledgement can prove receipt.

It cannot authorize a downstream action when institutional approval is
required.

## Fail-closed boundaries

Examples proven in F3G-H:

- authority scope unknown -> HOLD;
- wrong institution for subject -> BLOCK;
- required channel mismatch -> BLOCK;
- conflicting institutional instructions -> BLOCK;
- acknowledgement while approval is still required -> HOLD;
- refusal + downstream action request -> BLOCK;
- APPROVED without approval evidence -> HOLD;
- explicit hard deadline missed -> BLOCK;
- known upcoming deadline -> risk signal, no fabricated BLOCK.

## Case catalog

Ten simulated cases:

- FFF approved complete;
- Ville acknowledgement not approval;
- Ardenne Métropole authority scope unknown;
- District wrong channel;
- FFF conflicting instructions;
- Ardenne Métropole refusal + requested action;
- collectivity deadline soon;
- LGEF hard deadline missed;
- Ville approved with missing proof;
- Ville misrouted authority.

Expected distribution:

```text
ALLOW 2
HOLD  3
BLOCK 5
```

All cases are:

`SIMULATED_NOT_OBSERVED`

## Cockpit

Institutional assessments reuse the existing:

`GOVERNANCE_LEGAL`

reporting route.

They are visible to the existing governance/admin personas without enabling any
external correspondence.

## F3G-F closure overlay

Historical F3G-F remains unchanged.

F3G-H closes:

```text
INSTITUTIONAL_RELATIONS
  FFF_RELATION_WORKFLOW
  VILLE_COLLECTIVITY_RELATION_WORKFLOW
```

Still unknown before real field validation:

- real FFF channels by subject;
- real Ville de Sedan case scope;
- real Ardenne Métropole approval chain;
- real collectivity contact/approval matrix.

## Governance

Preserved:

- KX108_ONLY;
- external_action=false;
- memory_write=false;
- emits_act=false;
- kernel_mutation=false;
- public relation evidence != internal authority evidence.
