# F3H-E — CSSA REAL READONLY Intake Router V0

Date: 2026-10-07

Branch:
`feat/f3h-e-real-readonly-intake-router-v0`

Base:
`feat/cssa-native-ops-bridge-v0`

Draft PR:
`#12`

Main merge:
`NO`

## Purpose

Route real incoming information without turning every email into a task.

The router separates:

- information
- marketing
- personal transactions
- accounting documents
- real operational action requests
- deadlines
- incidents
- unknown CSSA-relevant content

and only promotes trusted operational work toward native CRM/TASKS.

## Real Gmail calibration

Eight real CSSA-related Gmail messages were read in READONLY mode.

Observed structural classes:

```text
CLUB_MATCHDAY_INFORMATION          4
CLUB_MARKETING_COMMUNICATION       1
TICKETING_TRANSACTION_CONFIRMATION 2
ACCOUNTING_DOCUMENT                1
```

All eight came from the connected personal inbox.

Therefore:

```text
real_internal_cssa_evidence = false
canonical_native_promotions = 0
```

No observed personal-inbox message became a native CSSA CASE or TASK.

No raw Gmail id, subject, body or personal recipient address is persisted.

Only privacy-minimized hashes and structural classifications are retained.

## Real routing examples

Observed matchday-information messages:

```text
→ READONLY_SHADOW_INTERACTION_ONLY
```

Observed marketing / merchandise message:

```text
→ READONLY_SHADOW_INTERACTION_ONLY
```

Observed ticket / subscription order confirmations:

```text
→ PERSONAL_TRANSACTION_INTERACTION_ONLY
```

Observed dedicated invoice:

```text
→ PERSONAL_TRANSACTION_INTERACTION_ONLY
```

An order confirmation that also exposes an optional invoice-download link
remains a transaction confirmation. The link alone does not reclassify the
whole message as an accounting document.

## Source authority boundary

The string `CSSA_OPERATIONAL_MAILBOX` is not trusted by itself.

Operational promotion requires a
`CSSA_READONLY_SOURCE_AUTHORITY_V0` binding:

- provider
- SHA-256 mailbox identity
- explicit authority reference
- explicit human approver
- active status
- `is_execution_authority=false`
- `KX108_ONLY`

The raw mailbox identity is not stored.

Without this authority:

```text
source_scope=CSSA_OPERATIONAL_MAILBOX
→ REJECT
```

## Routing contract

### Informational / marketing

```text
MATCHDAY INFORMATION
MARKETING COMMUNICATION
→ READONLY_SHADOW_INTERACTION_ONLY
→ no native task
```

### Personal transaction

```text
TICKETING TRANSACTION
ACCOUNTING DOCUMENT
from PERSONAL_INBOX
→ PERSONAL_TRANSACTION_INTERACTION_ONLY
→ not internal CSSA truth
```

### Actionable content from untrusted source

```text
ACTION REQUEST
DEADLINE
INCIDENT
from PERSONAL_INBOX / untrusted readonly source
→ READONLY_REVIEW_HOLD
→ no native mutation
```

### Trusted operational action

```text
verified CSSA operational source
+ explicit action request
→ NATIVE_CASE_TASK_FOLLOWUP_CANDIDATE
```

### Trusted operational deadline

```text
verified CSSA operational source
+ explicit action request
+ deadline
→ NATIVE_CASE_TASK_CALENDAR_CANDIDATE
```

Calendar remains a candidate only. This router does not create an external
calendar event.

### Unknown CSSA semantics

```text
CSSA-relevant but semantics not proven
→ READONLY_REVIEW_HOLD
```

## Native promotion

The router does not write native CRM/TASKS itself.

For a trusted actionable observation it may build a F3H-D
`CSSANativeIntakePlanV0`.

That candidate then follows the already-proven F3H-D chain:

```text
readonly observation
→ route decision
→ native intake candidate
→ 4 exact native mutations
→ HumanApproval
→ WORLD_ACTION_PRE
→ KX108
→ shadow semantic apply
→ canonical CRM/TASK commit
→ receipts / replay
```

The route is recomputed before promotion. A tampered route cannot grant
`canonical_native_candidate=true`.

A resolved due date is mandatory before creating the native task candidate.

## Real-vs-synthetic truth

Real provider evidence proves only the observed personal-inbox classes.

No real CSSA operational-mailbox message requiring action was found in the
connected mailbox during this calibration.

Therefore action/deadline/incident promotion tests remain synthetic fixtures
and are explicitly not claimed as real internal field evidence.

## Proof

Run:

`37611281272`

Result:

`196 passed in 0.74s`

Conclusion:

`SUCCESS`

The proof includes F3H-E, F3H-D and F3G-G through F3H-C regressions.

## Governance

Preserved:

- KX108_ONLY
- Gmail READONLY for intake calibration
- no Gmail mutation
- no send
- no automatic native promotion from personal inbox
- no fake operational-mailbox authority
- no external SaaS requirement
- no main merge

## Verdict

`CSSA_REAL_READONLY_INTAKE_ROUTER_V0_PROVEN`

## Next

The next meaningful boundary is a real CSSA operational source.

Until one exists, the system can safely:

- read/calibrate personal/public communications
- route them to shadow/read-only classes
- avoid false tasks
- avoid false internal truth

When an authorized CSSA operational mailbox or document source is connected,
the same router can feed real actionable cases into F3H-D without changing the
native CRM/TASK architecture.
