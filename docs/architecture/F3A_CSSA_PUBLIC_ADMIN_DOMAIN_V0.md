# F3A — CSSA PUBLIC ADMINISTRATION DOMAIN V0

Date: 2026-10-06
Status: PUBLIC_SOURCE_IMPLEMENTATION_CANDIDATE

## Purpose

Start the real CSSA domain without inventing private club practice.

F3A uses only public CSSA/FFF/LGEF facts and keeps all internal CSSA workflow semantics explicitly unknown.

## Public CSSA organization surface

The CSSA public association chart exposes distinct functional slots for administration, treasury/accounting, club secretariat, match-day organization/event operations and match-day security.

The model stores roles as organization slots rather than freezing current people as domain identity.

## Public regulatory workflows modeled

### Fixture modification — LGEF Article 20.7

- at least 10 days before the match: request/validation via Footclubs;
- after that deadline: clubs agree using official email;
- only the LGEF competition service in relation with the regional competition commission homologates date/time.

### FMI — LGEF Article 24

- receiving club uses FMI when mandatory;
- transmission due by the next day before 10:00;
- paper fallback exists if FMI cannot be used;
- the exception is reviewable by the competent commission and can create sanction risk.

### Official correspondence — LGEF Article 1

- League/District mail to clubs uses the official registered address;
- club mail to League/District must use the official club address.

### Club information changes — LGEF Article 3.3

- changes to required club information are notified to the League within 10 days.

### Referee designation — LGEF Article 42

- regional competition referees are designated by the CRA;
- this external authority is not modeled as CSSA authority.

## CSSA -> Administration boundary

CSSA-specific business fields remain local:

```text
fixture
Footclubs
FMI
referee designation
LGEF homologation
match-day context
```

The portable Administration state receives only:

```text
case/state ref
time
unknowns
contradictions
risk flags
evidence refs
provenance refs
```

## Runtime proof target

A real public CSSA fixture-change case is translated by the CSSA adapter, enters the portable Administration domain, then crosses the frozen F2.5 first-class runtime seam.

The only provider used by F3A is bounded internal analysis. No email, Footclubs, FMI or other external write is authorized.

## Claim boundary

F3A proves public-source structure and universal/runtime compatibility.

It does not claim to know:
- how CSSA actually distributes work;
- who has which credentials;
- local mailbox/folder structure;
- internal checklists;
- unwritten exceptions;
- actual response habits;
- human approval chain;
- match-day handoffs.

Those remain F0-B field evidence.
