# CSSA V0.1 — Entreprise universelle / Domaine Obsidia

Status: **PRE-FORGE**
Runtime implementation: **NO**
Kernel mutation: **NO**
Decision authority: **KX108_ONLY**

## Purpose

Ce dépôt est le chantier de pré-forge puis de construction du cas réel **CSSA** comme terrain de validation de la V0.1 Entreprise d'Obsidia.

Le dépôt sépare strictement trois niveaux :

```text
UNIVERSAL / UDIP
        ↓
ADMINISTRATION
        ↓
CSSA
```

- **Universal / UDIP** : contrats de raccord d'un domaine à Obsidia sans absorber le métier dans le Core.
- **Administration** : primitives administratives réutilisables uniquement lorsqu'elles sont effectivement démontrées génériques.
- **CSSA** : objets, règles, workflows, sources et contraintes propres au Club Sportif Sedan Ardennes.

Le projet local **Mémoire & Identité CSSA** reste séparé de l'administration et pourra vivre comme un autre projet/pack de la même organisation.

## Doctrine

- Le domaine traduit ; KX108 tranche.
- DOMAIN != AUTHORITY.
- PROPOSAL != DECISION != ACTION.
- SOURCE != TRUST.
- OBSERVATION != TRUTH.
- DATA != EXPERIENCE != LEARNING != KNOWLEDGE != MEMORY.
- Aucun élément spécifique CSSA ne remonte vers Administration ou Universal sans preuve de généralité.
- Aucun ancien contrat/branche n'est considéré obsolète ou canonique uniquement selon son avance/retard Git.

## Existing sources to audit

Source principale actuelle :
- `Eaubin08/obsidia-x108-proofs@main`

Branches historiques à confronter sémantiquement :
- `codex/udip-domain-packs-v0`
- `docs/obsidia-ontology-layer-contracts-v0`
- branches V0.1 / monde / domaines pertinentes si elles contiennent des contrats non promus sur main.

Artefacts déjà identifiés :
- `docs/UNIVERSAL_DOMAIN_INTEGRATION_PROTOCOL_V0.md` sur `codex/udip-domain-packs-v0`
- `domains/administration/` sur `codex/udip-domain-packs-v0`
- `docs/architecture/OBSIDIA_ONTOLOGY_AND_LAYER_CONTRACTS_V0.md` sur `docs/obsidia-ontology-layer-contracts-v0`
- sections V0.1 / Domain Integration du `README.md` actuel de `obsidia-x108-proofs@main`

## Current rule

**Plan / audit / sources / boundaries first. Build only after PRE-FORGE FREEZE.**
