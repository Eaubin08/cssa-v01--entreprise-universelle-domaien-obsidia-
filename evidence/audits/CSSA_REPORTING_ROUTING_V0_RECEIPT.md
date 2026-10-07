# CSSA REPORTING & PERSONA ROUTING V0 — RECEIPT

Date: 2026-10-07
Branch: `feat/f3e-cssa-reporting-routing-v0`

## Goal

Implement recurring CSSA/V0.1 reporting inside the repository, not as ChatGPT task automations.

Required cadences:

- weekly;
- every two weeks;
- monthly.

Required behavior:

- one global report pack;
- role/persona-specific views;
- no one-size-fits-all report;
- preserve truth class;
- redact sensitive HR/youth information;
- no external delivery in V0.

## Implemented

### Routing matrix

`organizations/cssa/reporting/routing_v0.json`

Maps whole-club event families to the roles that need the information.

Covered families:

- governance/legal;
- competitions;
- academy/membership;
- travel/logistics;
- finance/accounting;
- partners/commercial;
- supporters/ticketing;
- matchday;
- communication;
- people/HR/volunteers;
- facilities;
- education;
- proof/audit;
- privacy-sensitive cases.

### Cadence scheduler

`organizations/cssa/reporting/scheduler_v0.py`

Rules:

- WEEKLY: every Monday;
- BIWEEKLY: every 14 days from 2026-10-19;
- MONTHLY: first calendar day.

### Report engine

`organizations/cssa/reporting/report_engine_v0.py`

Produces:

- global report;
- summary JSON;
- separate persona reports;
- lookback / today / lookahead classification;
- gate counts;
- family counts;
- truth-class counts;
- privacy redaction.

### Artifact generator

`scripts/generate_cssa_reporting_v0.py`

Output:

```text
generated_reports/
  YYYY-MM-DD/
    weekly/
    biweekly/
    monthly/
      global.md
      summary.json
      personas/*.md
```

### Repository workflow

`.github/workflows/cssa-reporting-routing-v0.yml`

Behavior:

- runs F1 -> F3E + reporting regression;
- generates all three deterministic proof report packs on push/manual run;
- uploads them as a GitHub Actions artifact;
- contains a daily schedule hook that asks the repo scheduler what cadence is due.

Important:
GitHub scheduled workflows execute from the default branch. Since no merge to main is authorized, the cron is implemented but dormant on this feature branch.

## Privacy boundary

`PRIVACY_SENSITIVE` routes only metadata to:

- MANAGER_GENERAL;
- RESP_ADMIN.

The report hides:

- source IDs;
- target references;
- monetary amounts;
- evidence references;
- provenance references.

No raw payroll/youth-health content is exposed in persona reports.

## Authority boundary

Reporting does not:

- send email;
- send Slack/WhatsApp;
- publish website content;
- mutate ticketing/CRM;
- authorize club action.

`external_delivery.enabled = false`

Decision authority remains:

`KX108_ONLY`

## Defect found and corrected

Initial reporting CI:

- test suite: PASS;
- artifact generation: FAIL;
- cause: direct script execution did not place repository root on `sys.path`;
- failure: `ModuleNotFoundError: organizations`.

Correction:

- generator now inserts repository root before package imports.

## Closure proof

GitHub Actions run:
`37558491140`

Job:
`112590142497`

Result:

```text
205 passed in 0.86s
```

Generated successfully:

- weekly report pack;
- biweekly report pack;
- monthly report pack.

Artifact:

`cssa-reporting-pack-37558491140`

External delivery:

`false`

## Verdict

`CSSA_RECURRING_REPORTING_AND_PERSONA_ROUTING_V0_PROVEN`

This proves internal scheduling/routing/report generation.

It does not prove real-world delivery to CSSA staff.

No merge to main.
