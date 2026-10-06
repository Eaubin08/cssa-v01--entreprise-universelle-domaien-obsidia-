# 14 — F0 PUBLIC FOOTBALL SOURCE AUDIT

Date: 2026-10-06
Status: PUBLIC_SOURCE_BASELINE_ESTABLISHED / FIELD_SOURCES_MISSING

This audit does not pretend to reconstruct CSSA internal practice. It establishes the public regulatory and operational surface that a future CSSA Administration domain must be able to reference.

## 1. Source hierarchy

### A — Federal authority: FFF

Canonical public entry:
https://www.fff.fr/11-les-reglements/151-les-statuts-et-reglements-de-la-fff.html

The FFF publishes for season 2026-2027:
- FFF statutes;
- FFF General Regulations;
- licence procedure guide;
- disciplinary regulations;
- financial annexes;
- Statut de l'Arbitrage;
- other federal statutes/regulations.

Initial role:
`FEDERAL_NORMATIVE_SOURCE`

A federal rule is not treated as current merely because it exists in memory. Version/season and publication date must be preserved.

---

### B — Regional authority: LGEF

Public documents / commissions:
https://lgef.fff.fr/documents/?cid=36

The LGEF public surface exposes current 2026-2027 commission records including:
- Commission Régionale Compétitions;
- CR Statut de l'Arbitrage;
- Commission Régionale d'Arbitrage;
- Terrains et Installations;
- Comité Directeur.

Initial role:
`REGIONAL_DECISION_AND_CASE_SOURCE`

Important consequence:
a commission decision can be more specific than a general regulation for the case it decides.

Therefore:

```text
GENERAL_RULE
!=
CASE_SPECIFIC_DECISION
```

The system must preserve scope before applying precedence.

---

### C — LGEF 2026-2027 competition regulations

Source:
https://lgef.fff.fr/wp-content/uploads/sites/14/2026/05/Reglements-Particuliers-de-la-LGEF-26-27.pdf

Audited examples relevant to Administration:

#### Match date/time/place modification

Article 20.7 states that requests to change date, time or venue must be sent and validated via Footclubs at least 10 days before the match.

After the deadline:
- clubs must agree by email using their official address;
- only the competitions service in relation with the Commission Régionale des Compétitions can homologate the time/date.

This creates a real workflow with:
- deadline;
- channel;
- required agreement;
- official identity;
- final authority;
- late-case branch.

Candidate mapping:

```text
FixtureChangeRequest              CSSA / football
Deadline                          Administration candidate
OfficialCommunicationChannel      Administration candidate
CounterpartyAgreement              Administration candidate
HomologationAuthority              domain-specific authority reference
FinalDecisionRef                   UDIP/provenance candidate
```

#### FMI

Article 24:
- FMI is established on the receiving club's tablet when mandatory;
- receiving club must transmit FMI no later than the next day before 10:00;
- exceptional paper fallback exists when FMI cannot be used;
- paper substitute has its own deadline;
- failure may be reviewed/sanctioned.

This provides:
- normal path;
- technical exception path;
- deadlines;
- proof/document requirement;
- sanctions;
- responsibility assignment.

#### Referee / match administration

The same rules contain explicit distinctions between:
- referee observations;
- club responsibilities;
- commission authority;
- match reports;
- pre-match and post-match formalities;
- official absence fallback order.

This is a strong source of human/authority gray zones.

---

### D — LGEF calendar operational updates

Example current source:
https://lgef.fff.fr/simple/championnats-regionaux-les-calendriers-detailles-26-27/

The LGEF publishes detailed 2026-2027 regional calendars and reminds clubs that date/hour modifications require Footclubs agreement.

Initial role:
`REGIONAL_OPERATIONAL_SOURCE`

Important:
calendar/article update != regulation.
The system must preserve source type.

---

### E — FMI / Footclubs operational guidance

FFF ecosystem guidance for 2026-2027 confirms that:
- FMI and Footclubs require user/team configuration;
- users must hold the proper habilitations;
- FMI operational versions and credentials can change by season;
- clubs must prepare before match day.

Initial role:
`OPERATIONAL_SYSTEM_GUIDANCE`

Operational guidance may explain how to comply but must not silently override a normative rule.

---

### F — CSSA public source

CSSA public contact page:
https://cs-sedan.fr/contact

Observed public classes:
- general club contact;
- partnerships;
- boutique/ticketing;
- academy recruitment;
- senior recruitment;
- official club communication channels.

Initial role:
`ORGANIZATION_PUBLIC_SOURCE`

Operator-provided recruitment source:
https://cs-sedan.fr/recrutement-service-civique-secretariat-administratif

Status:
`OPERATOR_PROVIDED_URL / AUTOMATED_CAPTURE_PENDING`

It must be captured/archived before its wording is used as a frozen requirement.

---

### G — District des Ardennes

Public entry:
https://districtfoot08.fff.fr/

Potential source roles:
- departmental competitions;
- local club guidance;
- local arbitration;
- club-management notices;
- local service-civique/club support information.

Initial role:
`DEPARTMENTAL_AUTHORITY_SOURCE`

District scope must never be confused with LGEF regional scope.

---

## 2. Preliminary source classes

```text
FEDERAL_NORMATIVE
REGIONAL_NORMATIVE
DEPARTMENTAL_NORMATIVE
CASE_SPECIFIC_DECISION
OPERATIONAL_SYSTEM_GUIDANCE
CALENDAR_OPERATIONAL
ORGANIZATION_PUBLIC
ORGANIZATION_INTERNAL
HUMAN_STATEMENT
HUMAN_OBSERVED_PRACTICE
SYSTEM_EVENT
DERIVED_INFERENCE
```

These are source classes, not truth scores.

---

## 3. Required source metadata candidate

Every ingested source should preserve at minimum:

```text
source_id
source_class
issuer
scope
season_or_version
published_at
effective_from
effective_to
retrieved_at
canonical_url_or_internal_ref
case_ref
target_objects
supersedes_ref
superseded_by_ref
provenance
freshness_status
content_hash
```

Candidate only; schema is not frozen.

---

## 4. Rule-resolution warning

Do not build a naive hierarchy like:

```text
FFF > LGEF > District > Club
```

without scope.

Correct resolution must consider:

```text
competence
+ scope
+ competition
+ season
+ effective date
+ case specificity
+ later decision
+ explicit exception
```

Example:
a current case-specific commission decision may control one fixture even though a general rule exists.

---

## 5. First public-source workflows now proven worth modelling

### W1 — match modification
```text
request
-> identify fixture
-> determine deadline
-> Footclubs path if on time
-> official-email agreement path if late
-> competitions/commission homologation
-> final state
-> trace
```

### W2 — FMI lifecycle
```text
match
-> receiving-club responsibility
-> FMI preparation
-> match
-> transmission deadline
-> technical exception?
-> paper fallback
-> commission review / sanction risk
-> closure
```

### W3 — referee / official administration
```text
designation / availability
-> match context
-> pre-match formalities
-> event/exception
-> report obligation
-> commission processing
```

These are public models only. Real CSSA practice remains unobserved.

---

## 6. F0 public-source conclusion

Public sources already prove that CSSA Administration is not a simple "email assistant" problem.

It contains:
- multiple authorities;
- scoped rules;
- current vs obsolete texts;
- case-specific decisions;
- hard deadlines;
- official communication channels;
- technical fallback procedures;
- sanctions;
- proof/report obligations;
- human exceptions.

This validates Administration as a serious V0.1 domain candidate.

It does **not** validate any automation level yet.
