# F3C — CSSA SIMULATED FIELD TESTS V0

Date: 2026-10-07
Status: SIMULATION_ACTIVE / NOT FIELD EVIDENCE

## Why

F3B is ready for real CSSA data, but no internal club dataset is available yet.

F3C therefore creates realistic synthetic cases shaped by two kinds of evidence already available:

1. public FFF/LGEF rules frozen in F3A;
2. sanitized output patterns visible in CSSA supporter communications.

The communication evidence shows supporter-facing outputs such as kickoff time, door opening, ticket-office opening, stand availability, subscriber access, parking/buvette information and ticketing links. It does not expose the club's internal administrative workflow.

## Hard truth boundary

Every F3C case is labeled:

`SIMULATED_NOT_OBSERVED`

No scenario is stored as `validated_by_cssa=True`.

The simulation harness may assume scenario facts are true for test execution, but this assumption is isolated in `to_simulated_runtime_mapping()` and never promoted into F3B real-field evidence.

Raw Gmail content, message IDs and user email addresses are not committed.

## 15 scenarios

1. clean coherent home match;
2. kickoff change before LGEF homologation;
3. official-vs-public kickoff contradiction;
4. stand/VIP configuration contradiction;
5. subscriber-access contradiction;
6. door/ticket-office timing contradiction;
7. automatic ticket-purchase confirmation classified as transactional output;
8. stale information across two public communication channels;
9. late fixture change missing agreement/homologation proof;
10. FMI normal path complete;
11. FMI technical exception unresolved;
12. official correspondence prepared from wrong sender channel;
13. visible channel difference does not prove internal system migration;
14. publication candidate before final match state;
15. youth/high-sensitivity record blocked before runtime.

## Expected governance

Clean, sufficiently evidenced internal-analysis cases may reach ALLOW for the bounded READONLY provider.

Two unresolved unknowns drive HOLD under the current real GuardX108.

Two contradictions drive BLOCK.

High-sensitivity youth data is stopped before runtime.

An ALLOW in F3C authorizes only the configured internal simulated READONLY provider. It does not authorize supporter email, Footclubs, FMI, ticketing mutation or any external club action.

## Purpose

The goal is to stress the Administration/CSSA contract before field access and discover missing objects, boundaries and contradictions without pretending synthetic data is real CSSA practice.
