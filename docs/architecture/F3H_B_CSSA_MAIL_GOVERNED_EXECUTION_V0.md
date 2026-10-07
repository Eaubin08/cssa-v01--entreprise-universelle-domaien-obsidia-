# F3H-B — CSSA MAIL Governed Execution Preflight V0

Date: 2026-10-07
Branch: `feat/f3h-b-cssa-mail-governed-execution-v0`
Base: `feat/f3h-a-cssa-decision-execution-contract-v0`
Main: unchanged

## Purpose

Prepare the first real connector surface without fabricating external-world
authority that the current Obsidia upstream runtime does not yet provide.

## Live calibration

Readonly inspection of real CSSA-related mail observed three useful classes:

- club matchday information;
- ticketing transaction confirmation;
- event marketing campaign.

Only structural classes/fields are retained in the repo.

Not persisted:

- Gmail message ids;
- raw bodies;
- personal recipient data.

The currently connected Gmail account is not treated as a CSSA operational
sender mailbox.

## Exact mail plan

A mail plan binds:

- exact recipients;
- subject;
- body;
- reply message id when present;
- sender-mailbox ref;
- action-proposal id/hash;
- target pre-state hash;
- evidence refs.

Changing message content changes the mail-plan hash.

## Exact human approval

Mail approval binds the exact mail plan including:

- mail-plan hash;
- recipient list;
- subject hash;
- body hash;
- reply/thread target;
- sender mailbox.

Approval is non-sovereign.

## Mailbox authority

A real CSSA send requires evidence that the connector account is:

- an authorized CSSA operational mailbox;
- bound to the expected mailbox ref;
- backed by an explicit operational-authority ref.

A personal mailbox cannot be silently reclassified as the club mailbox.

## Gmail call candidate

F3H-B can construct the exact Gmail SEND_EMAIL call candidate.

Building the call candidate does not invoke Gmail and grants no execution
authority.

## Canonical upstream blocker

Audit of current `obsidia-x108-proofs` shows:

- governed AGENT_PRE_EXECUTION is INTERNAL_BOUNDED only;
- it explicitly says it proves nothing about external actuation;
- runtime-link facts report `EXTERNAL_WORLD_ACTUATION_NOT_ACTIVATED`;
- runtime-link facts report `REAL_X108_GATED_EXECUTION_PATH_NOT_ACTIVATED`;
- WorldActionBus is dry-run only;
- EMAIL_SEND is detected and blocked at that boundary.

Therefore F3H-B deliberately does NOT relabel AGENT_PRE_EXECUTION as a world
action authorization.

## Current result

Even with:

- exact action proposal;
- exact mail plan;
- exact human approval;
- exact CSSA mailbox-authority evidence;
- unchanged target pre-state;

the current result remains:

`MAIL_LIVE_SEND_BLOCKED`

because the generic upstream world-action rail is absent.

## Receipt contract

F3H-B defines the provider-result receipt/replay contract in advance.

Test receipts explicitly carry:

`real_send_proven=false`

and cannot be used as evidence of an actual email send.

Unknown connector outcome must not auto-retry because a timeout can occur after
a provider accepted a message.

## Universalization

F3H-B also introduces the reusable universal Decision-Execution contract and
domain-adapter registry.

Sedan is the first real métier validation case, not a special execution
architecture.

## Governance

- KX108_ONLY
- no Gmail send performed
- no external connector invoked
- no personal mailbox used as CSSA sender
- no fake external PRE authority
- no main merge
