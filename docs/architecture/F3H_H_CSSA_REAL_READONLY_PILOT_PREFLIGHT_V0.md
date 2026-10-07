# F3H-H — Préflight du pilote CSSA réel en lecture seule (V0)

Date : 2026-10-08

Branche : `feat/f3h-h-cssa-real-readonly-pilot-preflight-v0`

Base : `feat/f3h-g-real-source-onboarding-pilot-v0` (PR #14 DRAFT)

## Objet

Ne pas reconstruire F3H-E/F/G. Ces briques font déjà respectivement :
classification READONLY, registre opérationnel et onboarding à deux clés.

Ce préflight fournit **un état de préparation**, pas une autorisation,
ni une connexion, ni l'exécution du pilote.

## Inventaire constaté des accès et des preuves

| Source | Observée | Autorité interne CSSA | Classification possible | Exploitation interne réelle |
|---|---|---|---|---|
| Gmail personnel déjà connecté | Oui | NON | Oui, en mode shadow personnel | NON |
| Communications publiques CSSA | Oui (exemples antérieurs) | NON | Oui, source publique | NON |
| Confirmations billetterie personnelles | Oui | NON | Transaction personnelle | NON |
| Boîte opérationnelle du club | NON | NON | Pas encore | NON |
| Dossier documentaire interne actuel du club | NON, arbre historique insuffisant | NON | Pas encore | NON |
| Calendrier / formulaire / API interne | NON | NON | Pas encore | NON |

Les 8 exemples réels précédemment calibrés dans F3H-E se répartissent en
4 informations match, 1 marketing, 2 confirmations transactionnelles
et 1 document comptable personnel. **0 promotion CRM/TASK**.

Aucun destinataire, mail personnel, identifiant fournisseur, corps, pièce
jointe, secret ou donnée interne CSSA n'est reproduit dans ce dépôt public.

## Prochaine preuve réelle nécessaire

La **première source opérationnelle** doit être fournie par le club lui-même :

1. soit UNE boîte fonctionnelle du CSSA, en READONLY limité ;
2. soit UN dépôt de documents internes CSSA explicitement autorisé en READONLY.

Ne pas utiliser la boîte personnelle d'un supporter ou un dossier historique
pour simuler cette autorisation.

Les engagements humains nécessaires sont :
- identification d'un responsable du club habilité à autoriser l'accès ;
- périmètre exact : compte/dossier, finalité, durée, types de documents ;
- confirmation d'un accès READONLY, sans envoi ni modification ;
- exclusions des données de mineurs, santé, discipline, paie, finances sensibles ;
- modalités d'arrêt et révocation, conservation et suppression des données ;
- revue des documents avant utilisation et validation humaine des cas sensibles.

Les noms, mails, preuves d'identité et autorisations signées restent
**hors du dépôt Git public** (stockage local/privé adapté).

## Contrat d'entrée existant, réutilisé

```text
Source CSSA vraiment observée (F3H-G)
  + SHA-256 identité / capacité vérifiés
          ↓
Autorisation humaine exacte (F3H-G)
  + sous-ensemble READONLY
          ↓
Registration F3H-F immuable et ACTIVE
          ↓
Preflight F3H-H (inspection uniquement)
          ↓
Vérification humaine et technique de séance
          ↓
Lecture bornée depuis la vraie source
          ↓
F3H-E routeur / shadow / HOLD
          ↓
CRM/TASK candidate seulement si cas opérationnel prouvé
          ↓
KX108 ONLY pour toute action gouvernée
```

**Le préflight F3H-H ne déclenche jamais la lecture.**
Même `PRECHECK_READONLY_SOURCE_REGISTERED_NOT_INGESTING` n'autorise
aucune collecte sans autorisation et exécution séparées.

## Cas à refuser

- compte personnel -> jamais source opérationnelle CSSA ;
- identité source non observée, hash modifié ou dérive de capacités ;
- autorisation absente, machine, hash non lié au candidat ;
- capacité `SEND` / `WRITE` / `DELETE` dans la demande approuvée ;
- inscription F3H-F absente, différente, corrompue ou révoquée ;
- toute tentative de qualifier du marketing comme tâche interne réelle ;
- toute écriture dans Gmail, Footclubs/FMI ou logiciel du club.

## Premier essai terrain : métriques

Une seule source, une période courte et approuvée, une revue par un responsable.
Journaliser uniquement agrégats et receipts sans données personnelles :

- nombre de sources observées / autorisées ;
- informations vs transactions vs demandes d'action réelles ;
- HOLD et raisons ;
- échéances extraites et confirmées manuellement ;
- doublons évités ;
- cas proposés, validés et refusés par humain ;
- traçabilité effective des cas, temps de recherche.

**Aucune écriture externe. Aucun envoi. Aucun secret dans Git.**

## Limites et état réel

```text
REAL_CSSA_INTERNAL_MAILBOX_CONNECTED = FALSE
REAL_CSSA_INTERNAL_DOCUMENT_REPOSITORY_CONNECTED = FALSE
REAL_CSSA_OPERATIONAL_SOURCE_ACTIVATED = FALSE
PILOT_STARTED = FALSE
PILOT_MODE = PREPARATION_ONLY
DECISION_AUTHORITY = KX108_ONLY
```

Le code F3H-H évalue les preuves que le système pourra recevoir :
il ne prétend pas vérifier l'habilitation réelle d'un approbateur
par la seule présence d'un champ `approved_by`.

## Étape suivante après cette Forge

**Décision humaine côté CSSA** : quelle source le club accepte-t-il
de fournir en lecture seule, sous quelle responsabilité et avec quelle
documentation d'autorisation ?

Tant qu'il n'y en a pas, le pilote reste BLOQUÉ sans fabriquer de
vérité opérationnelle.
