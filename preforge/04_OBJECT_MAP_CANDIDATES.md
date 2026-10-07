# 04 — OBJECT MAP CANDIDATES

No object in this file is frozen.

## CSSA-specific candidates

```text
Match
Team
Competition
Referee
Official
PlayerLicence
MatchSheet
FMIRecord
FootclubsRequest
LeagueNotice
CommissionDecision
MatchProtocol
Venue
ClubContact
FixtureChangeRequest
```

## Administration candidates

```text
AdministrativeCase
Document
Correspondence
Request
Obligation
Deadline
Procedure
ResponsibleRole
Approval
Task
ProcessingState
Exception
AdministrativeAnomaly
EvidenceRef
ReceiptRef
```

## Universal/UDIP candidates already supported historically

```text
DomainIdentity
DomainObjectMap
SourceProvenance
DomainSignal
CanonicalDomainContract
GovernancePayload
EvidenceRefs
ReceiptSurface
ProofReference
ReplayReference
ExecutionOutcomeRef
```

## Promotion rule

An object may move upward only if semantic equivalence survives comparison across multiple domains/organizations.

Example:
```text
Referee -> CSSA only
FixtureChangeRequest -> likely CSSA/football
Deadline -> Administration candidate
Unknown/contradiction/provenance -> Universal candidate
```
