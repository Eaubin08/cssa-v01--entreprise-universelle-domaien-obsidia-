# F3B — CSSA FIELD INTAKE KIT V0

Date: 2026-10-06
Status: FIELD-READY / NO REAL CSSA PRIVATE DATA INGESTED

## Goal

Make the next CSSA meeting/field session immediately usable by Obsidia without pretending to know the club's private workflow in advance.

## What the kit captures

Each real case preserves:
- source/evidence class;
- timestamp and provenance;
- trigger;
- object/match/dossier concerned;
- observed responsible role;
- observed approver;
- external authority;
- deadline;
- channel/tool;
- required documents;
- missing information;
- contradictions;
- exceptions;
- result;
- proof left behind;
- anything dependent only on human memory;
- local-practice references;
- public-rule references;
- whether CSSA itself has validated the captured case.

## Evidence classes

```text
OBSERVED_DIRECTLY
STAFF_STATEMENT
INTERNAL_DOCUMENT
SYSTEM_SCREEN_STATE
EMAIL_THREAD
OFFICIAL_EXTERNAL_DECISION
LOCAL_CHECKLIST
INFERRED_PATTERN
```

`INFERRED_PATTERN` remains evidence. It is not automatically promoted to rule.

## Privacy boundary

V0 stops sources containing MINOR_DATA, HEALTH_DATA, DISCIPLINARY_DATA or FINANCIAL_DATA before runtime ingestion and requires manual privacy review.

All field sources are READONLY in F3B.

## Trust boundary

A captured case that has not been validated by CSSA automatically adds:

`FIELD_CASE_NOT_YET_CSSA_VALIDATED`

to the universal unknowns surface.

This means real-but-unvalidated field observation fails conservatively rather than being silently treated as organizational truth.

## Runtime behavior

- unvalidated case -> expected HOLD;
- CSSA-validated clean case -> may reach ALLOW for bounded internal READONLY analysis;
- no external email/Footclubs/FMI action;
- no memory write;
- no kernel mutation;
- KX108_ONLY.

## Included material

- typed Python intake contracts;
- dict/JSON mapper;
- runtime adapter;
- case-capture YAML template;
- public-rule-vs-local-practice comparison template;
- anonymized fixture-change sample;
- anonymized FMI-exception sample;
- high-sensitivity blocked sample;
- tests through the frozen F2.5 runtime seam.

## F3B closure condition

This kit can be technically frozen before field access, but the actual F3B domain semantics remain open until real CSSA evidence is inserted and validated.
