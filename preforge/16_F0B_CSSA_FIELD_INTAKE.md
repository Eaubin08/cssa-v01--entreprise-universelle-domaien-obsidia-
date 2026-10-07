# F0-B — CSSA FIELD INTAKE V0

Status: READY_FOR_FIELD / NOT_STARTED

## Objective

Capture how CSSA Administration actually works without forcing public rules or our candidate model onto the club.

## First session — observe before changing

Collect examples, not descriptions only.

Required samples:
- 10-20 recent administrative emails, anonymized where needed;
- one complete match lifecycle from scheduling to post-match closure;
- one late fixture-change case if available;
- one FMI normal case and one technical-exception case if available;
- one referee/official communication chain;
- one commission/LGEF decision received by the club;
- one missing-document or licence issue;
- one recurring reminder/deadline process;
- one case where local practice differed from the written rule.

## Capture for every real case

```text
case_ref
trigger
source
received_at
effective_at
match/team/person/object concerned
who noticed it
who owned it
who could approve
who actually acted
deadline
system/channel used
documents required
missing information
contradictions
exception
final external authority
result
proof/trace left behind
what was remembered only by a human
what failed / nearly failed
```

## Do not ask for broad access first

Start READONLY and sample-based.

Preferred progression:
1. public sources;
2. exported/anonymized examples;
3. read-only mailbox/folder access if club agrees;
4. read-only calendars/Footclubs-adjacent observations;
5. proposal mode;
6. external action only after separate authority review.

## Questions for CSSA staff

- What arrives every week and always needs the same treatment?
- What deadline do you fear missing?
- Which task depends on one person remembering it?
- Which information arrives in the wrong channel?
- Which process changes at the last minute?
- Which documents are often missing or obsolete?
- What requires the official club email rather than a personal address?
- What do you retype between systems?
- Which request needs another club's agreement?
- What looks approved but is not actually homologated?
- What must be checked on match day?
- What do you discover only after something went wrong?

## Field evidence classes

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

`INFERRED_PATTERN` never becomes a rule without validation.

## Privacy / minimization

- prefer role identifiers over personal names;
- do not ingest more personal data than needed;
- isolate medical, disciplinary, financial and minor-related data;
- no training/reuse of club personal data by default;
- preserve source access scope and retention requirements.

## F0-B exit

F0-B can close only when at least:
- 3 different administrative workflow families are observed end-to-end;
- 1 normal + 1 exception path are observed;
- actual role/approval chain is known for those cases;
- source/channel reality is known;
- at least one public-rule-vs-local-practice comparison is documented;
- unknowns remain explicit.
