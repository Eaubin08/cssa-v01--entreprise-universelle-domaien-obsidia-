# 13 — F0 BASELINE DECISION

Status: F0_GIT_AUDIT_CLOSED / PUBLIC_DOMAIN_AUDIT_OPEN

## Decision

The CSSA/V0.1 project will **not** fork the old UDIP branch and will **not** rebuild Universal from scratch.

It will work from a reconciled baseline:

```text
CURRENT MAIN RUNTIME FACTS
+
LATEST OCTOBER UNIVERSAL CONTRACT CANDIDATES
+
ONTOLOGY/LAYER DOCTRINE
+
REAL CSSA SOURCES
```

## F1 entry candidate

The strongest current technical candidate for F1 is the narrow contract family:

```text
DomainStateRef
GovernancePayload
unknowns
contradictions
risk_flags
evidence_refs
provenance_refs
KX108_ONLY
```

with the existing main runtime kept external/canonical rather than copied into this repo.

## Open design question

`WorldStateV0` is valuable and already implemented on the October branch, but F0 does not yet decree that every CSSA administrative input must traverse MMonde.

CSSA may expose:
- document/message observations;
- organization state;
- administrative state;
- match-day state;
- human-provided context.

The correct translation boundary will be decided only after public and field source audit.

## F0 remaining work

Before PRE-FORGE FREEZE:

1. audit CSSA public mission surface;
2. audit LGEF / FFF administrative sources relevant to CSSA;
3. define source authority/freshness classes;
4. map first real workflows;
5. distinguish football-specific objects from Administration candidates;
6. freeze claim boundary.

No runtime build is authorized yet.
