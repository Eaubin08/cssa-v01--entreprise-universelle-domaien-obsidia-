# CSSA FIELD DATA SECURITY V0

Status: REQUIRED FOR F3B

This repository is public. Real CSSA private data must never be committed here.

## Forbidden in Git

- real mailbox exports;
- private/internal email threads;
- personal data;
- minors data;
- health data;
- disciplinary data;
- financial records;
- credentials/tokens;
- Footclubs/FMI credentials;
- internal phone lists;
- private staff documents;
- raw screenshots containing private data.

## Local-only folders

Use a local ignored folder such as:

```text
field_private/
local_intake/
private_intake/
```

The repository `.gitignore` blocks these names and common `*.private.*` files.

## What may be committed

- anonymized synthetic fixtures;
- public-source references;
- schemas/templates;
- redacted examples with no recoverable personal/private information;
- receipts containing only hashes/refs, never raw private contents.

## Runtime ingestion

F3B V0 is READONLY.

High-sensitivity classes (`MINOR_DATA`, `HEALTH_DATA`, `DISCIPLINARY_DATA`, `FINANCIAL_DATA`) are blocked before runtime ingestion and require manual privacy review.

## Secrets

Secrets stay outside Git and outside fixtures. Use local environment/secrets management only when a later authorized connector phase exists.

## Rule

If there is any doubt whether a file is safe to publish, do not commit it.
