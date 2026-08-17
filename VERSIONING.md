# Versionnage des modèles JSON

Chaque modèle possède sa propre version sémantique au format `MAJEUR.MINEUR.CORRECTIF`.

## Règles

- `MAJEUR` : changement incompatible pour les consommateurs existants.
- `MINEUR` : ajout rétrocompatible, par exemple un champ optionnel.
- `CORRECTIF` : correction rétrocompatible qui ne change pas l'intention du contrat.

Une version publiée est immuable. Toute modification de son contenu crée une nouvelle version.

## Chemin canonique

```text
templates/<famille>/<nom-du-modele>/v<MAJEUR>.<MINEUR>.<CORRECTIF>/<template.json|schema.json>
```

Exemple indicatif de chemin, sans publier de contrat réel :

```text
templates/schemas/item/v0.1.0/schema.json
```

## Cycle de maturité

Un modèle peut être documenté avec l'un des statuts suivants :

- `draft` : contrat en réflexion, non destiné à l'intégration ;
- `experimental` : essais autorisés, changements incompatibles possibles ;
- `stable` : contrat validé pour les consommateurs explicitement listés ;
- `deprecated` : encore lisible mais remplacé par une version ou un modèle indiqué.

Un statut `stable` exige une validation séparée pour chaque client ou serveur annoncé. Il ne doit jamais être déduit de la seule présence du fichier dans ce dépôt.

## Métadonnées attendues

Le fichier `README.md` placé à côté de chaque `template.json` ou `schema.json` devra préciser au minimum :

- le propriétaire du contrat ;
- son statut ;
- les consommateurs connus ;
- les versions compatibles explicitement vérifiées ;
- les changements par rapport à la version précédente ;
- les contraintes de sécurité et les champs interdits ;
- la date de validation.

## Changements interdits

Une version existante ne doit pas être réécrite pour modifier silencieusement un contrat. Les secrets, données de production, adresses internes et paramètres commerciaux restent hors périmètre, quelle que soit la version.
