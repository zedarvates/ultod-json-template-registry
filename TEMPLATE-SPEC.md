# UltOd JSON Template Specification

Version de la spécification : `1.0.0`

Cette référence définit comment créer un nouveau modèle JSON compatible avec le registre UltOd. Elle s'adresse aux contributeurs humains, aux outils de génération et aux LLM.

Les termes **DOIT**, **NE DOIT PAS**, **DEVRAIT** et **PEUT** sont normatifs.

## 1. Conventions

### 1.1 Organisation des fichiers

Un nouveau modèle DOIT utiliser cette structure :

```text
templates/<famille>/<nom-du-modele>/v<MAJEUR>.<MINEUR>.<CORRECTIF>/
  template.json
  README.md
```

Un schéma JSON remplace `template.json` par `schema.json`.

- `<famille>` et `<nom-du-modele>` DOIVENT être en `kebab-case` ASCII.
- La version du dossier DOIT commencer par `v` et suivre SemVer.
- Une version publiée NE DOIT PAS être modifiée. Toute modification crée une nouvelle version.
- `templates/catalog.json` DOIT référencer chaque version publiée.

### 1.2 Format JSON

- Le fichier DOIT être du JSON UTF-8 valide.
- Les clés DOIVENT être en `snake_case` ASCII.
- Les identifiants DOIVENT être stables, uniques dans leur famille et en `snake_case`.
- Les nombres DOIVENT être des nombres JSON, jamais des chaînes.
- Les booléens DOIVENT utiliser `true` ou `false`, jamais `0`, `1`, `yes` ou `no`.
- Une valeur absente DEVRAIT être omise. Utiliser `null` seulement si le contrat distingue explicitement `null` d'une absence.
- Les durées et unités DOIVENT être explicites dans la clé : `duration_ms`, `cooldown_seconds`, `distance_m`.
- Les références vers d'autres modèles DOIVENT utiliser des identifiants logiques, jamais un chemin absolu.

### 1.3 Statuts

Chaque entrée de catalogue DOIT utiliser l'un des statuts suivants :

- `draft` : travail en cours, non destiné à l'intégration ;
- `experimental` : testable, mais susceptible de changer ;
- `stable` : contrat validé pour les consommateurs listés ;
- `deprecated` : encore lisible, mais remplacé par une version indiquée.

La présence d'un fichier dans le registre ne prouve jamais son intégration runtime.

## 2. Champs obligatoires

### 2.1 Nouveau modèle

Tout nouveau `template.json` créé après cette spécification DOIT contenir :

| Champ | Type | Règle |
| --- | --- | --- |
| `id` | chaîne | Identifiant stable en `snake_case`. |
| `template_type` | chaîne | Type logique stable en `snake_case`. |
| `version` | chaîne | Version SemVer identique au dossier, sans préfixe `v`. |

Un modèle historique publié comme instantané PEUT ne pas posséder ces trois champs. Cette exception DOIT être signalée dans le `README.md` de sa version et ne s'applique pas aux nouveaux modèles.

### 2.2 Entrée de catalogue

Chaque version DOIT avoir une entrée dans `templates/catalog.json` contenant :

| Champ | Type | Règle |
| --- | --- | --- |
| `name` | chaîne | Nom du modèle en `kebab-case`. |
| `kind` | chaîne | Nature du contrat, par exemple `biome-template`. |
| `version` | chaîne | Version SemVer sans préfixe `v`. |
| `status` | chaîne | `draft`, `experimental`, `stable` ou `deprecated`. |
| `file` | chaîne | Chemin relatif canonique du JSON. |
| `source_file` | chaîne | Nom de la source auditée, si le modèle est un instantané. |
| `sha256` | chaîne | Empreinte SHA-256 hexadécimale en minuscules. |
| `compatibility` | tableau | Consommateurs dont la compatibilité a réellement été vérifiée. |

Le tableau `compatibility` DOIT rester vide tant qu'aucune preuve de compatibilité n'existe.

Lorsqu'une compatibilité est vérifiée, chaque élément du tableau DOIT être un objet contenant :

| Champ | Type | Règle |
| --- | --- | --- |
| `consumer` | chaîne | Identifiant stable du client, serveur ou outil. |
| `version` | chaîne | Version exacte testée. |
| `verified_at` | chaîne | Date ISO 8601 de la validation. |
| `evidence` | chaîne | Référence vers un test, rapport ou commit vérifiable. |

### 2.3 Documentation de version

Le `README.md` placé à côté du JSON DOIT préciser :

- le statut ;
- la source ou l'auteur ;
- la compatibilité vérifiée ;
- les dépendances et références logiques ;
- les limites connues ;
- l'empreinte SHA-256 ;
- les changements depuis la version précédente, sauf pour `v0.1.0`.

## 3. Champs optionnels

Un modèle PEUT utiliser les champs communs suivants lorsqu'ils ont un sens :

| Champ | Type | Usage |
| --- | --- | --- |
| `name` | chaîne | Nom affichable. |
| `description` | chaîne | Description destinée aux humains. |
| `enabled` | booléen | Activation déclarative ; ne constitue pas une autorisation. |
| `tags` | tableau de chaînes | Recherche et classification. |
| `dependencies` | tableau de chaînes | Identifiants logiques requis. |
| `metadata` | objet | Informations non fonctionnelles et extensibles. |

Les champs spécifiques à une famille DOIVENT être documentés par un JSON Schema versionné lorsque cette famille devient `stable`.

Un consommateur DEVRAIT ignorer les champs optionnels inconnus, sauf si le schéma de la version définit explicitement `additionalProperties: false`.

## 4. Règles de compatibilité

### 4.1 Compatibilité des lecteurs

- Un lecteur DOIT sélectionner une version prise en charge ; il ne doit pas supposer que la dernière version est compatible.
- Un lecteur DOIT échouer proprement si un champ obligatoire manque ou possède un type invalide.
- Un lecteur NE DOIT PAS donner de privilège, monnaie, objet, rang ou accès à partir d'une valeur cliente non validée.
- Une référence inconnue DOIT être signalée ou ignorée selon le contrat de la famille, jamais remplacée silencieusement par une ressource privilégiée.
- Les champs inconnus NE DOIVENT PAS modifier le comportement de sécurité par défaut.

### 4.2 Changements incompatibles

Les changements suivants exigent une nouvelle version majeure :

- supprimer ou renommer un champ ;
- changer le type, l'unité ou la signification d'un champ ;
- rendre obligatoire un champ auparavant optionnel ;
- réduire une plage numérique acceptée ;
- supprimer une valeur d'énumération ;
- changer une valeur par défaut d'une manière qui modifie le comportement ;
- déplacer le modèle vers une autre famille ou changer son `id`.

Ajouter une valeur d'énumération n'est rétrocompatible que si le contrat demande déjà aux lecteurs d'accepter les valeurs inconnues. Sinon, le changement est majeur.

### 4.3 Sécurité et périmètre public

Un modèle public NE DOIT PAS contenir :

- secret, mot de passe, token, clé ou chaîne de connexion ;
- URL ou adresse interne de production ;
- chemin absolu local ;
- donnée personnelle ou donnée de production ;
- paramètre de facturation, quota commercial ou infrastructure hébergée ;
- commande administrative, contournement d'autorisation ou réglage de performance serveur ;
- ressource tierce dont les droits ne sont pas vérifiés.

Les permissions déclaratives PEUVENT être décrites, mais l'autorité DOIT rester côté serveur.

## 5. Versioning

Chaque modèle suit SemVer indépendamment : `MAJEUR.MINEUR.CORRECTIF`.

- `MAJEUR` : changement incompatible.
- `MINEUR` : ajout rétrocompatible, comme un champ optionnel.
- `CORRECTIF` : correction sans changement de contrat ni de comportement attendu.

Une correction de faute dans une description PEUT être un correctif. Une modification de récompense, de valeur par défaut, de permission ou de règle de gameplay n'est pas automatiquement un correctif : elle DOIT être classée selon son impact sur les consommateurs.

Le détail des règles de publication se trouve dans [VERSIONING.md](VERSIONING.md).

## 6. Exemples

### 6.1 Modèle minimal valide

Chemin : `templates/events/community-festival/v1.0.0/template.json`

```json
{
  "id": "community_festival",
  "template_type": "event",
  "version": "1.0.0",
  "name": "Community Festival",
  "description": "A small recurring social event.",
  "enabled": true,
  "tags": ["social", "seasonal"],
  "duration_ms": 3600000,
  "dependencies": ["location_town_square"]
}
```

### 6.2 Entrée de catalogue correspondante

```json
{
  "name": "community-festival",
  "kind": "event-template",
  "version": "1.0.0",
  "status": "experimental",
  "file": "templates/events/community-festival/v1.0.0/template.json",
  "sha256": "<64-caracteres-hexadecimaux-minuscules>",
  "compatibility": []
}
```

L'empreinte factice DOIT être remplacée par la véritable empreinte avant publication.

### 6.3 Exemple incompatible

```json
{
  "id": "community-festival",
  "template_type": "event",
  "version": 1,
  "duration": "one hour",
  "admin_override": true,
  "server_url": "http://internal-host:8080"
}
```

Cet exemple est invalide : `version` n'est pas une chaîne SemVer, l'unité de `duration` est ambiguë et les champs administratifs ou internes sont interdits.

## 7. Checklist pour humains et LLM

Avant de proposer un modèle :

- produire du JSON strict, sans commentaire ;
- vérifier `id`, `template_type` et `version` ;
- utiliser des unités explicites ;
- conserver uniquement des références logiques ;
- ne jamais inventer une compatibilité ;
- laisser `compatibility` vide sans preuve ;
- calculer l'empreinte SHA-256 ;
- documenter les limites et dépendances ;
- rechercher les secrets et données internes ;
- créer une nouvelle version au lieu de modifier une version publiée.
