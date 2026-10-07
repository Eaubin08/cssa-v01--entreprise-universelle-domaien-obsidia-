# CSSA / V0.1 — F3H-B MAIL PREFLIGHT + UNIVERSAL EXECUTION BILAN

Date: 2026-10-07
Branch: `feat/f3h-b-cssa-mail-governed-execution-v0`
Base: `feat/f3h-a-cssa-decision-execution-contract-v0`
Main: unchanged
Draft PR: #9 — no merge requested

## Executive result

F3H-B advances DECISION_EXECUTION in two directions at once:

1. CSSA MAIL is prepared up to an exact Gmail connector-call candidate;
2. the execution-governance contract is extracted into a reusable universal
   layer for arbitrary métier domains.

Proof after adding the universal métier-adapter registry:

```text
437 / 437 tests PASS
run 37595017825
27.38 s
```

## CSSA live mail calibration

Readonly live inspection established three useful structural mail classes:

- club matchday information;
- ticketing transaction confirmation;
- event marketing campaign.

Repository persistence is privacy-minimized:

- no Gmail message ids;
- no raw mail bodies;
- no personal recipient data.

The currently connected Gmail account is not accepted as a CSSA operational
sender mailbox.

## MAIL preflight proven

F3H-B now binds:

- exact mail action proposal;
- exact recipients;
- exact subject/body;
- exact reply target when applicable;
- exact sender-mailbox ref;
- exact target pre-state;
- explicit human approval;
- mailbox operational-authority evidence;
- exact Gmail SEND_EMAIL call candidate.

No Gmail call is executed.

## Critical upstream discovery

During implementation, upstream audit showed that the current Obsidia
`AGENT_PRE_EXECUTION` rail is explicitly:

`INTERNAL_BOUNDED_PROVIDER_EXECUTION`

and explicitly states it does not authorize external-world actuation.

Canonical upstream runtime facts still report:

- `EXTERNAL_WORLD_ACTUATION_NOT_ACTIVATED`
- `REAL_X108_GATED_EXECUTION_PATH_NOT_ACTIVATED`

The real WorldActionBus is:

- dry-run only;
- `world_action_allowed=false`;
- no external API;
- no email send.

F3H-B therefore fails closed instead of relabelling internal PRE_EXECUTION as
external action authority.

## Current MAIL verdict

Even if proposal, human approval, target state and mailbox authority are
structurally valid:

`MAIL_LIVE_SEND_BLOCKED`

until the generic world-action rail exists.

This is the correct result.

## Universal Decision-Execution

New universal modules:

- `universal/execution/contract_v0.py`
- `universal/execution/domain_adapter_v0.py`

The universal layer defines:

- execution-surface registration;
- universal action proposal;
- exact SHA-256 proposal binding;
- human approval;
- target pre-state recheck;
- KX108 readiness requirement;
- effect classes;
- provider receipt/replay contract;
- métier-domain adapter registry.

## Multi-domain proof

The same universal contract is exercised with:

- administration;
- trading;
- e-commerce;
- GPS / defense / aviation;
- logistics;
- finance operations.

An additional internal bounded surface proves that external-world blockers do
not incorrectly block local internal work.

## Domain adapter isolation

Proven:

- adapter registration grants no authority;
- a domain cannot change its domain identity;
- a domain cannot propose a surface outside its allowed set;
- unregistered surface -> fail closed;
- unregistered operation -> fail closed;
- human approval from one proposal/domain cannot be transplanted to another.

## CSSA compatibility

The existing CSSA F3H-A action proposals map losslessly to the universal
contract for:

- MAIL;
- CALENDAR;
- CRM;
- TASKS.

Therefore Sedan remains the concrete validation domain while the governance
architecture is reusable.

## What remains open

Generic:
- external world-action PRE_EXECUTION rail;
- real X108-gated external execution path;
- real external receipt/replay lifecycle.

MAIL-specific:
- authorized CSSA operational mailbox connection/evidence;
- one human-approved real send pilot;
- sent-mail reconciliation for unknown outcomes.

Other surfaces:
- CALENDAR real connector;
- CRM real connector;
- TASKS real connector.

## Current verdict

`UNIVERSAL_DECISION_EXECUTION_CONTRACT_V0_PROVEN`

and:

`CSSA_MAIL_GOVERNED_PREFLIGHT_V0_PROVEN_LIVE_SEND_BLOCKED`

This does NOT claim real external execution.
