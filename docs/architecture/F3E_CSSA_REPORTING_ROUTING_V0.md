# CSSA / V0.1 — REPORTING & ROUTING V0

Date: 2026-10-07
Status: IMPLEMENTED ON FEATURE BRANCH / NO EXTERNAL DELIVERY
Branch: `feat/f3e-cssa-reporting-routing-v0`

## Objective

Turn the CSSA/V0.1 model into a recurring internal information system.

The system must not produce one generic report for everybody. It must:

- collect relevant events;
- preserve their truth class;
- classify urgency through the governed event state;
- route each event to the roles that need it;
- generate weekly, biweekly and monthly report packs;
- create a separate view for each recurring persona;
- redact sensitive HR/youth cases;
- keep all outbound delivery disabled in V0.

## Cadences

### Weekly

Window:
- previous 7 days;
- current day;
- next 7 days.

Purpose:
- operational deadlines;
- match/competition work;
- travel;
- licences/equipment;
- ticketing;
- matchday;
- partner activation;
- communications;
- blockers and immediate dependencies.

### Biweekly

Window:
- previous 14 days;
- next 14 days.

Purpose:
- cross-layer review;
- dependency drift;
- source freshness;
- role overload;
- resource conflicts;
- model corrections;
- unresolved unknowns.

Biweekly anchor:
`2026-10-19`, then every 14 days.

### Monthly

Window:
- previous 31 days;
- next 31 days.

Purpose:
- governance;
- finance/capacity;
- budget pressure;
- partner/commercial commitments;
- operational risk;
- architecture/model updates;
- next-month decisions.

## Persona routing

The routing matrix lives in:

`organizations/cssa/reporting/routing_v0.json`

It maps operating families to role personas and then limits each persona to the cadences they actually need.

Examples:

- Direction/Présidence: biweekly + monthly;
- Manager Général: weekly + biweekly + monthly;
- Administration: all three;
- Secrétariat: weekly + biweekly;
- Finance/Admin Accounting: all three;
- Direction Technique: weekly + biweekly;
- Formation / Foot 5-8: weekly + biweekly;
- Team Manager/Intendance: weekly;
- Matchday Organizer: weekly + biweekly;
- Security: weekly;
- Ticketing/Boutique: weekly + biweekly;
- Partnerships: weekly + biweekly + monthly;
- Communication: weekly + biweekly;
- School Section: biweekly + monthly.

The same global event can therefore appear in several role-specific views without giving those roles the same authority.

## Truth classes

Every routed item retains exactly one truth class:

- PUBLIC_CONFIRMED
- SECONDARY_CORROBORATED
- ESTIMATED
- SIMULATED_NOT_OBSERVED
- REAL_FIELD_EVIDENCE
- UNKNOWN_PRIVATE

The reporting layer never silently promotes one class into another.

## Sensitive cases

`PRIVACY_SENSITIVE` is routed only to:

- MANAGER_GENERAL
- RESP_ADMIN

and only as metadata.

The report hides source IDs, target references, amounts, evidence references and provenance references.

A payroll or youth-health event can therefore be visible as:

`SENSITIVE CASE / PRE_RUNTIME_BLOCK`

without exposing the document itself.

## Generated artifacts

CLI:

`python scripts/generate_cssa_reporting_v0.py`

For each cadence the generator produces:

```text
generated_reports/
  YYYY-MM-DD/
    weekly|biweekly|monthly/
      global.md
      summary.json
      personas/
        manager_general.md
        resp_admin.md
        ...
```

The files are internal artifacts only.

## Automation

Repository workflow:

`.github/workflows/cssa-reporting-routing-v0.yml`

The workflow:

1. runs the full regression through F3E + reporting tests;
2. generates deterministic proof reports on push/manual run;
3. uploads the report pack as a GitHub Actions artifact;
4. contains a daily schedule hook that asks the repository scheduler which cadence is due.

Important GitHub behavior:
scheduled workflows execute from the default branch. Since this branch is deliberately not merged to `main`, the recurring cron is currently READY BUT DORMANT.

No merge to main is implied or authorized.

## External delivery

V0 does not:

- email staff;
- send Slack/WhatsApp messages;
- mutate a CRM;
- publish to the CSSA website;
- send partner communications;
- notify supporters.

The layer only decides who SHOULD receive each internal information item and produces the corresponding artifact.

A later delivery layer can consume those persona reports after explicit authorization.

## Architectural position

```text
sources / events
      ↓
truth classification
      ↓
Administration / governed state
      ↓
report window
      ↓
family routing
      ↓
persona cadence filter
      ↓
privacy redaction
      ↓
global report + persona views
      ↓
ARTIFACT ONLY
```

Reporting does not alter KX108 authority.

`KX108_ONLY` remains unchanged.
