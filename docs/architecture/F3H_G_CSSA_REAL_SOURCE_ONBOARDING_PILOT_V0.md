# F3H-G — CSSA Real Operational Source Onboarding Pilot V0

Date: 2026-10-07

Branch:
`feat/f3h-g-real-source-onboarding-pilot-v0`

Base:
`feat/f3h-f-operational-source-registry-v0`

Draft PR:
`#14`

Main merge:
`NO`

## Purpose

Close the software gap between:

```text
a connector can see a source
```

and:

```text
CSSA is allowed to treat that exact source as an internal operational source
```

No external source is automatically promoted.

## Two-key onboarding boundary

### Key 1 — observed source candidate

`ObservedSourceCandidateV0` binds what the connector actually exposes:

- source kind
- provider
- source identity SHA-256
- observed capabilities
- connector reference
- observation timestamp
- raw source identity not persisted
- credentials not persisted
- no internal CSSA claim
- no decision authority
- no action authority
- KX108_ONLY

### Key 2 — human operational authorization

`HumanOperationalSourceAuthorizationV0` binds an explicit human claim to the
exact observed candidate:

- candidate id/hash
- exact source identity SHA-256
- approved READONLY capabilities
- authority reference
- human approver
- authorization timestamp
- internal_cssa_source=true
- readonly_only=true
- is_execution_authority=false
- KX108_ONLY

The authorization may only reduce the connector-observed capability set.

It can never add a capability that the observed candidate did not expose.

## Drift protection

A change in any of these invalidates the previous authorization:

- source/account identity
- observed capability set
- candidate hash

Therefore switching Gmail accounts, Drive folders, providers or capability
surfaces requires a new explicit onboarding.

## Activation

Exact candidate + exact human authorization can produce:

`OperationalSourceRegistrationV0`

through the already-proven F3H-F registry.

For MAILBOX:

```text
Observed mailbox
→ Human operational authorization
→ F3H-F registration
→ F3H-E SourceAuthority
→ READONLY intake ready
```

For DOCUMENT_REPOSITORY:

```text
Observed folder/repository
→ Human operational authorization
→ F3H-F registration
→ privacy-safe READONLY source items
```

No mailbox send/write/delete capability is created.

## Activation receipt

`OperationalSourceActivationReceiptV0` binds:

- candidate hash
- authorization hash
- registration hash
- source id
- source kind
- provider
- active state
- readonly state
- external_mutation_allowed=false
- mailbox F3H-E authority readiness
- activation timestamp
- KX108_ONLY
- receipt hash

## Current real-world source state

The connected Gmail account remains the personal inbox already calibrated in
F3H-E.

It is not reclassified as a CSSA operational mailbox.

Drive discovery found a historical CSSA folder tree, but the terminal CSSA
folder checked in this pilot is empty and the tree is not treated as a current
internal club repository.

Therefore:

```text
REAL_CSSA_OPERATIONAL_MAILBOX_CONNECTED = FALSE
REAL_INTERNAL_DOCUMENT_REPOSITORY_CONNECTED = FALSE
```

No source has been fabricated or auto-promoted.

## Proof

Run:

`37615616327`

Result:

`156 passed in 0.62s`

Conclusion:

`SUCCESS`

The proof covers:

- candidate non-sovereignty
- exact human authorization
- machine authorization refusal
- capability escalation refusal
- account/source identity drift invalidation
- capability drift invalidation
- mailbox activation
- document-repository activation
- F3H-F registration
- F3H-E mailbox authority readiness
- candidate tamper detection
- authorization tamper detection
- activation receipt tamper detection
- prior source-registry/router/native-bridge regressions

## Governance

Preserved:

- KX108_ONLY
- no source self-claim
- no automatic internal-source promotion
- no credentials persistence
- no raw identity persistence
- READONLY only
- no connector mutation
- no external execution authority
- no main merge

## Verdict

`CSSA_REAL_SOURCE_ONBOARDING_PILOT_V0_PROVEN`

## Next

No additional architecture is required before the first real source pilot.

The next external step is:

```text
connect one real CSSA mailbox
OR
provide one real internal CSSA document repository
```

Then execute the already-proven onboarding chain against the exact observed
identity.

Mailbox remains the preferred first pilot because the F3H-E mail classifier,
native CRM/TASK bridge and Calendar/Gmail action surfaces are already proven.
