# CSSA / V0.1 — F3G-E CONTROLLED SEMANTIC PROMOTION BILAN

Date: 2026-10-07  
Branch: `feat/f3g-e-cssa-controlled-semantic-promotion-v0`  
Main: unchanged  
Draft PR: #1 — proof/CI only, no merge requested

## Executive result

F3G-E closes the gap between "public page changed" and "reviewed semantic state changed".

```text
public watcher delta
→ HOLD
→ explicit human-reviewed packet
→ exact baseline/source/truth validation
→ controlled semantic promotion
→ affected public anchor only
→ stress/sensitivity rerun
→ persona reporting impact
→ NO EXTERNAL ACTION
```

Closure proof:

- 279 / 279 tests PASS
- GitHub Actions run: `37566908293`
- controlled-promotion-proof: SUCCESS
- KX108_ONLY preserved
- external action: false
- memory_write: false
- emits_act: false
- kernel_mutation: false

## What is now proven

### 1. Watch drift cannot promote itself

F3G-D's rule remains intact:

`PAGE CHANGED != SEMANTIC FACT CHANGED`

F3G-E accepts only an explicit packet with:

- `status=REVIEWED_PUBLIC_CHANGE`
- `review_decision=APPROVED`
- known public source
- allowed public truth class
- no unresolved unknown
- no unresolved contradiction
- exact reviewed pre-state

Anything else fails closed.

### 2. Stale review cannot overwrite newer state

The review freezes `expected_before_values`.

Immediately before promotion, F3G-E compares those values with the current
snapshot.

Mismatch:

`REVIEW_BASELINE_MISMATCH`

This prevents an old review from silently overwriting a newer public state.

### 3. Promotion is state-scoped

Only the reviewed `state_key` is replaced.

Unrelated public observations remain byte-for-byte equivalent at the semantic
object level.

The source snapshot is never mutated in place.

### 4. Public anchors and estimated capacities stay separate

A reviewed public fact may update the explicit related PUBLIC anchor.

It cannot write into:

- LOW_CONSTRAINED capacities
- CENTRAL_WORKING capacities
- HIGH_CAPACITY capacities

Attempting `capacity_updates` or `profile_updates` fails closed with:

`PUBLIC_REVIEW_CANNOT_MUTATE_ESTIMATED_CAPACITY`

This preserves the distinction:

```text
public organizational fact
!=
known internal capacity / availability / delegation
```

### 5. Downstream impact is rerun even when nothing operational changes

The proof fixture changes exactly one reviewed manager-state key and one public
anchor.

Result:

- changed semantic states: 1
- changed public anchors: 1
- changed estimated capacities: 0
- stress/sensitivity rerun: YES
- changed stress profiles: 0
- reporting rerun: YES
- promoted event routed to affected personas

"0 changed stress profiles" is a proof result, not a skipped computation.

### 6. Direct helper calls also fail closed

After the first green run (278/278), one boundary was hardened:

`apply_reviewed_anchor_updates_v0` now independently refuses:

- non-reviewed packets
- non-approved reviews
- invalid truth classes
- unresolved unknowns
- unresolved contradictions
- estimated-capacity mutation attempts

Second closure run:

`279 passed in 27.20s`

## Test fixture truth boundary

The current manager review fixture is explicitly:

`SIMULATED_REVIEW_PACKET_NOT_OBSERVED`

It does NOT assert that the real CSSA appointed a manager.

It proves the promotion protocol without fabricating real field evidence.

## Current project meaning

Before F3G-E:

```text
public watch
→ content delta
→ review signal / HOLD
```

After F3G-E:

```text
public watch
→ content delta
→ HOLD
→ reviewed semantic packet
→ controlled public-state promotion
→ explicit downstream impact diff
```

The system can now change its internal public model without either:

- guessing from page drift, or
- contaminating estimated/private operational assumptions.

## What remains unproven

Still OPEN:

- real CSSA internal field evidence
- real staff capacities
- real vehicle pool
- real travel budget
- real volunteer capacity by match
- actual delegation/signature chain
- actual Association/SAS operating split
- actual internal tools/channels
- any external action path

## Next decision

The next useful barrier is no longer another automatic public inference layer.

It is to feed **one real reviewed CSSA fact** through the F3G-D → F3G-E path
and compare its actual downstream impact, while keeping external action disabled.

No merge to main.
