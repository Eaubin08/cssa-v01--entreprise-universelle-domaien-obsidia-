# F2 — UNIVERSAL CONFORMANCE V0

Status: IMPLEMENTATION_CANDIDATE
Date: 2026-10-06

## Purpose

F2 tests whether current Obsidia domain outputs and the October UDIP candidate can be reduced to the recovered F1 universal contract without:

- importing business semantics into Universal;
- transporting advisory/pre-Guard vocabulary as a decision;
- leaking authority;
- requiring MMonde for every input.

## Sources confronted

Current main has a real governed internal multi-domain runtime and four canonical runtime domains: bank, trading, ecom, gps_defense_aviation.

Common fields visible in current main DomainAggregate include domain, contradictions, unknowns, risk_flags and evidence_refs.

Fields intentionally not universalized here include market_verdict, confidence, agent_votes, extra_metrics and domain-specific state fields.

The October UDIP candidate uses domain_id, world_state_ref, valid_at, unknowns, contradictions, risk_flags, evidence_refs, provenance_refs and KX108_ONLY.

F2 provides a compatibility adapter preserving the October domain-state reference convention while making the world-state reference optional upstream in F1.

## Important distinction

F2 proves only: candidate input -> universal F1 state -> universal F1 governance payload.

It does NOT prove: administration -> current main runtime -> KX108.

Current main still supports concrete registered bridges. Administration is intentionally accepted at the Universal-contract level while remaining unsupported by current main runtime until a future explicit integration stage.

## Conformance rules

A source fails closed if it attempts another decision authority, allowed_to_decide=true, allowed_to_act=true, emits_act=true, emits_verdict=true, kernel_mutation=true, x108_mutation=true, or memory/Graphiti/Neo4j write authority.

Domain-specific fields are ignored by the universal adapter rather than promoted.

## F2 exit criterion

F2 can close when:
1. all F1 tests still pass;
2. all F2 compatibility/conformance tests pass;
3. four current-main domain fixtures conform;
4. synthetic Administration conforms at contract level only;
5. October UDIP compatibility passes without semantic loss;
6. authority-leak tests fail closed;
7. no claim is made that Administration is wired into current main runtime.
