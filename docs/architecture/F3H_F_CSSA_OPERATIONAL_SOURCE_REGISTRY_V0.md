# F3H-F — CSSA Operational Source Registry V0

Date: 2026-10-07

Branch:
`feat/f3h-f-operational-source-registry-v0`

Base:
`feat/f3h-e-real-readonly-intake-router-v0`

Draft PR:
`#13`

Main merge:
`NO`

## Purpose

Define the source-trust boundary that must exist before F3H-E may treat any
mailbox, document repository, calendar, form inbox or API as a real internal
CSSA operational source.

The registry is provider-neutral and READONLY by construction.

Supported source kinds:

- MAILBOX
- DOCUMENT_REPOSITORY
- CALENDAR
- FORM_INBOX
- API_READONLY

## Core rule

```text
external source
→ explicit registration
→ human approval
→ exact source identity SHA-256
→ READONLY capability set
→ active registry state
→ optional source-item observation
→ F3H-E router
```

Registration never grants execution authority.

## Read-only capability set

Accepted capabilities include:

- LIST
- SEARCH
- READ_MESSAGE
- READ_THREAD
- READ_ATTACHMENT
- READ_DOCUMENT
- READ_FILE_METADATA
- READ_EVENT
- READ_FORM_RESPONSE
- READ_API_RESOURCE

Write-like capabilities are rejected structurally.

Forbidden semantics include:

- WRITE
- SEND
- CREATE
- UPDATE
- DELETE
- TRASH
- ARCHIVE
- MOVE
- REPLY
- FORWARD
- UPLOAD
- MUTATE
- EXECUTE

Therefore F3H-F cannot silently become an action connector.

## Source registration

`OperationalSourceRegistrationV0` binds:

- source id
- source kind
- provider
- exact source-identity SHA-256
- allowed READONLY capabilities
- human authority reference
- human approver
- registration timestamp
- active state
- readonly=true
- internal_cssa_source=true
- external_mutation_allowed=false
- is_execution_authority=false
- KX108_ONLY
- registration hash

Registration is immutable.

A second different registration using the same source id is rejected.

## Revocation

Revocation is an append-only overlay.

A revoked source:

```text
registry.is_active(source) = false
```

and can no longer feed the F3H-E operational route.

Revocation binds:

- source id
- registration hash
- reason
- human revoker
- timestamp
- KX108_ONLY
- revocation hash

## Mailbox bridge

An active registered MAILBOX can be converted to the F3H-E
`ReadonlySourceAuthorityV0`.

The F3H-E authority is derived from the exact registration hash.

A revoked mailbox is rejected.

A non-mailbox source cannot forge mailbox authority.

Thus:

```text
registered MAILBOX
→ F3H-F registry authority
→ F3H-E operational source authority
→ F3H-E readonly observation
→ classification
→ optional native candidate
```

## Provider-neutral source items

`ReadonlySourceItemV0` supports non-mail sources without prematurely
inventing métier classifiers.

It stores only:

- source registration hash
- hashed provider item id
- content SHA-256
- metadata SHA-256
- observed timestamp
- provider/source kind
- non-sovereign flags
- item hash

It explicitly does not persist:

- raw provider item id
- raw content
- raw source identity

It cannot decide or act.

## Real-world truth boundary

F3H-F proves the contract and registry behavior only.

No real CSSA operational mailbox, internal Drive, calendar, form source or API
has yet been connected and registered.

Therefore:

`REAL_CSSA_OPERATIONAL_SOURCE_CONNECTED = FALSE`

The current personal Gmail remains outside internal CSSA truth.

## Proof

Run:

`37613151103`

Result:

`221 passed in 0.88s`

Conclusion:

`SUCCESS`

Coverage includes:

- F3H-F source registry
- write-capability rejection
- human authority requirement
- immutable registration
- tamper detection
- revocation
- revoked-source refusal
- mailbox bridge into F3H-E
- generic document/calendar/form/API registrations
- privacy-safe source items
- F3H-E/F3H-D and execution regressions

## Governance

Preserved:

- KX108_ONLY
- READONLY source registration
- no external mutation
- no send
- no fake internal source
- no raw source identity persistence
- no main merge

## Verdict

`CSSA_OPERATIONAL_SOURCE_REGISTRY_V0_PROVEN`

## Next

The architecture is now ready for one real operational source to be connected.

Recommended first pilot:

```text
one real CSSA operational mailbox OR one internal document repository
→ explicit F3H-F registration
→ READONLY capture
→ F3H-E classification
→ human review
→ F3H-D CRM/TASK intake only when warranted
```

Until such a source is available, no real internal case should be fabricated.
