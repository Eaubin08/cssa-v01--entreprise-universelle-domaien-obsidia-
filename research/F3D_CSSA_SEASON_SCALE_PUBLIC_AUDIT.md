# F3D — CSSA SEASON-SCALE PUBLIC AUDIT V0

Date: 2026-10-07
Status: AUDIT IMPLEMENTED / ESTIMATES EXPLICIT / PRIVATE REALITY OPEN

## 1. Why F3D

F3C proved isolated realistic scenarios. F3D widens the model to the real scale of a football club over a season before generating the long-running synthetic corpus.

The audit deliberately separates:

- PUBLIC_CONFIRMED;
- SECONDARY_CORROBORATED;
- ESTIMATED;
- UNKNOWN_PRIVATE.

No estimated number is promoted to a CSSA accounting fact.

## 2. Organization scale

The official 2026-2027 academy organization exposes 19 team structures:

- Seniors R1;
- Seniors R2;
- U20 R1;
- U17 R1;
- U16 R1;
- U15 R1;
- U15 D1;
- Senior women;
- U18F R2;
- U13 Fanion;
- U13/U12 Espoir;
- U12 Avenir;
- U11 Fanion;
- U11/U10 Espoir;
- U10 Avenir;
- U9;
- U8;
- U7;
- U6.

SportCorico exposes 11 currently tracked competitive team entries. This is not interpreted as a contradiction: lower youth structures use plateaux/phases and the public systems do not expose the same organizational granularity.

The U20 R1 is now a real 2026-2027 structure and belongs to the development bridge toward R2/R1.

## 3. Administration and operating personas

The public organization plus the Manager Général recruitment description supports a much wider operational map than a simple secretariat.

F3D now models role personas for:

- governance/direction;
- Manager Général;
- administration;
- accounting/treasury;
- club secretariat;
- technical direction;
- formation/preformation/foot 5-8 coordination;
- team educators and team operations;
- parents/guardians and licence holders;
- matchday organization and security;
- volunteers;
- ticketing/boutique;
- partnerships;
- partner contacts;
- communication;
- supporters/subscribers;
- LGEF/District/FFF;
- club-affiliated referees;
- municipality/collectivity;
- school section;
- equipment supplier;
- ticketing/payment provider;
- independent supporter media.

These are roles, not frozen human identities.

## 4. Public-source coherence is already an administrative problem

The audit found four useful current-source issues:

1. The Association organigramme still shows Teddy Pellerin as Manager Général while the official 10 September communiqué announces his departure.
2. A public standings page still labels R1/R3 while the reserve is currently tracked in R2.
3. The partners page advertises "+12 home matches/year" while the 2026-2027 subscription explicitly covers 13 R1 home league matches.
4. The homepage itself warns that the site is undergoing an update to bring information up to date.

These become source-version/freshness scenarios. They are not automatically treated as mistakes by the kernel; provenance and date matter.

## 5. Licence and academy administration

Public CSSA pack prices:

- U6-U9: 180 EUR;
- U10-U18: 240 EUR;
- U20-Seniors: 300 EUR.

Public pack workflow includes licence, personalized Kappa equipment and an R1 season ticket, with family/female/Pass'Sport reductions and separate payment/evidence paths.

The 2026-2027 LGEF financial statute also exposes external tariffs for licences, discipline and procedures. F3D records these as public external tariff references rather than pretending to know CSSA's final accounting treatment.

A press profile reports approximately 500k EUR budget and 300+ licence holders. These remain SECONDARY_CORROBORATED, not certified 2026-2027 accounts.

## 6. Supporters, subscribers and partners

Public/secondary snapshots are kept separately:

- 800 season subscribers, partners included: official/reposted snapshot while campaign was still open;
- 855: later supporter-media claim attributed to CSSA;
- final current subscriber count: UNKNOWN.

The model never replaces this with an unsourced 1,000.

Public commercial claims include:

- 50+ active partners;
- 100k+ / 110k+ social audience depending page;
- 30k+ annual stadium spectators/reach;
- 2,500+ exposure per match in the partner pitch.

Partner revenue is UNKNOWN_PRIVATE. Fifty partners cannot be converted into revenue without contract tiers and actual commitments.

There is also an active separate "Ardennes Club des Partenaires du CSSA" association. That entity belongs in the ecosystem map, but its operational relationship with current club partnership sales is not assumed.

## 7. Legal entity boundary

Current public registers show:

- Association CSSA: active;
- SAS CSSA: active, collective-procedure status reported;
- historical SA: radiated 2025-10-28;
- Ardennes Club des Partenaires: active;
- Drapeau Vert / Carton Rouge: active.

The exact 2026 operational split between Association and SAS is UNKNOWN_PRIVATE.

Historical professional/amateur separation is therefore not projected onto the current club.

## 8. Season travel scale

The current season groups and calendars allow a bounded travel model even though exact CSSA transport choices are private.

F3D estimates regular team-route kilometres by team/category. "Team-route km" means the road distance of the team trip, not the number of cars multiplied by distance.

Regular/championship envelope:

- approximately 20,000-29,000 team-route km across the modeled competitive structures.

With a 10%-25% scenario uplift for cups, friendlies and tournaments:

- approximately 22,000-36,250 team-route km over a full synthetic season.

This is deliberately an ESTIMATE.

A useful external scale check exists: independent CSSA media association DVCR publicly reports 15 covered away trips and 3,208 km in the previous R1 season. That is a media-volunteer travel benchmark, not a CSSA team expense.

## 9. Travel cost simulation, not accounting

F3D exposes configurable scenarios rather than claiming a CSSA cost/km.

Low simulation:
- 22,000 team-route km;
- 2 vehicle equivalents;
- 0.35 EUR/vehicle-km;
- 15,400 EUR.

Base simulation:
- 29,125 team-route km;
- 2.5 vehicle equivalents;
- 0.45 EUR/vehicle-km;
- approximately 32,766 EUR.

High simulation:
- 36,250 team-route km;
- 3 vehicle equivalents;
- 0.60 EUR/vehicle-km;
- 65,250 EUR.

This excludes hired coaches, hotels, meals, parking and any actual club reimbursement policy.

It exists only so the future season simulator can stress budget, approval, invoice and reimbursement workflows.

## 10. What we take from Football Manager

Only management abstractions:

- staff responsibility matrix;
- delegation routing;
- task inbox;
- cost centers / budgets;
- team planner;
- youth pipeline;
- staff capability mapping;
- calendar workload;
- board objectives;
- finance overview.

We do not import hidden ratings, fictional values, game formulas or game-derived authority.

## 11. What this changes for the simulation

F3E should no longer simulate a single match or even only six weeks.

Target:

```text
SEASON 2026-2027
  19 team structures
  hundreds of licence/member cases
  regional + district fixtures
  cups / friendlies / plateaux
  travel and reimbursements
  equipment orders
  FFF/LGEF/District decisions
  discipline and procedural fees
  partners and hospitality
  season tickets and ticketing
  matchday volunteers/security
  public communications
  source freshness/conflicts
  school/academy coordination
  accounting evidence
  delayed/missing/contradictory cases
```

The simulator must generate simultaneous workloads and collisions, not independent one-off examples.

## 12. Still unknown

Do not invent:

- exact 2026-2027 CSSA budget;
- exact licence-holder count by category;
- exact current final subscriber count;
- partner contribution amounts;
- player/staff compensation;
- actual travel reimbursement policy;
- coach/minibus contracts;
- current facility financial agreement;
- exact Association/SAS operating split;
- real internal approval chain.

These remain field or private evidence requirements.
