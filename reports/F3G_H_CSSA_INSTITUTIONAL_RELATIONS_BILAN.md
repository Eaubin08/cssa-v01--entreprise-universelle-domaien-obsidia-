# CSSA / V0.1 — F3G-H INSTITUTIONAL RELATIONS BILAN

Date: 2026-10-07  
Branch: `feat/f3g-h-cssa-institutional-relations-v0`  
Base: `feat/f3g-g-cssa-contract-compliance-lifecycle-v0`  
Main: unchanged  
Draft PR: #5 — no merge requested

## Executive result

F3G-H closes the two institutional gaps identified in F3G-F:

- `FFF_RELATION_WORKFLOW`
- `VILLE_COLLECTIVITY_RELATION_WORKFLOW`

Initial closure proof:

```text
10 simulated institutional cases
2 ALLOW
3 HOLD
5 BLOCK

325 / 325 tests PASS
run 37570792978
27.25 s
```

## Public grounding

The CSSA Manager Général announcement explicitly names the Ligue, District,
Fédération, Ville de Sedan and collectivités as institutional counterparts.

The current Ardenne Métropole Louis-Dugauguez page publicly places the stadium
under Ardenne Métropole responsibility.

The District des Ardennes public site also exposes current CSSA activity on a
FFF-linked public channel.

These sources define actors and public scope only.

They do not define private CSSA authority, mandatory channels or approval
chains.

## Proven semantic boundaries

### Receipt is not authorization

`ACKNOWLEDGED != APPROVED`

A received email/message cannot authorize a downstream club action where an
approval is required.

### Authority is subject-specific

A known institution name does not imply authority over every case.

- unknown scope -> HOLD;
- explicitly wrong scope -> BLOCK.

### Channel compliance is explicit

When a case declares a required channel:

- correct channel can proceed;
- unknown sent channel -> HOLD;
- mismatch -> BLOCK.

No universal channel is invented from public evidence.

### Conflicting instructions fail closed

Two incompatible institutional instructions produce BLOCK until canonical
resolution.

### Refusal is binding for the case model

A refused request cannot be translated into an authorized downstream action.

### Final state requires proof

APPROVED/REFUSED/CLOSED without evidence is not treated as auditable final
truth.

## Cockpit

All cases route through the existing `GOVERNANCE_LEGAL` reporting family.

External delivery remains disabled.

## F3G-F closure

Closed structurally:

- FFF relation workflow;
- Ville/collectivity relation workflow.

Still open for field calibration:

- real FFF channels by subject;
- real Ville case scope;
- real Ardenne Métropole approval chain;
- real collectivity contact/approval matrix.

## Governance

Preserved:

- KX108_ONLY
- external_action=false
- memory_write=false
- emits_act=false
- kernel_mutation=false

## Current verdict

`CSSA_INSTITUTIONAL_RELATIONS_V0_PROVEN`

## Next

Next gap-closure target:

`INCIDENT_ROOT_CAUSE_WORKFLOW + RECURRENCE_PREVENTION_RECEIPT`

No merge to main.


## Final frozen-HEAD verification

- run 37570923893
- 325 passed in 26.94s
- SUCCESS
- verified after architecture/report/receipt/status freeze
