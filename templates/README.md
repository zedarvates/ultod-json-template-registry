# Modèles JSON

Ce dossier accueille les modèles et schémas JSON versionnés du registre.

## État actuel

La collection contient actuellement 16 schémas, un modèle de motifs haptiques, trois presets d'avatar, huit biomes, trois collections d'achievements, un modèle d'événement, trois configurations de guilde, un modèle de lieu, un blueprint de maison, un modèle de noms, six styles architecturaux, quatre modèles de rift, une configuration de groupe, un parcours de mentorat, un modèle de mariage, un événement social, sept donjons, une configuration de parangons, deux modèles de boss, trois chefs-d'œuvre d'artisanat, cinq recettes et 29 modèles de créatures. Ils sont publiés en `v0.1.0` avec le statut `experimental` et sans certification de compatibilité, d'assets, de rendu, de balancing ou d'exactitude culturelle.

Les permissions, rangs et accès de banque décrits dans les modèles de guilde sont uniquement déclaratifs. Ils ne doivent jamais remplacer une autorisation et une validation côté serveur.

Les niveaux, vagues, durées, coordonnées et récompenses décrits dans les modèles de rift sont uniquement déclaratifs. Le client ne doit jamais pouvoir les imposer au serveur.

Les méthodes de butin, bonus, appartenances, factions et limites de groupe sont uniquement déclaratifs. Le serveur doit recalculer et autoriser leur application.

Les prérequis, objectifs, durées et récompenses de mentorat sont uniquement déclaratifs. Le serveur doit valider la progression et attribuer les récompenses.

Le consentement, les coûts, bonus, logements et stockages partagés d'un mariage doivent être validés transactionnellement côté serveur.

Les participants, horaires, frais et récompenses d'un événement social doivent être autorisés et validés côté serveur.

Les difficultés, apparitions, statistiques et récompenses de donjon ou de parangon doivent être calculées et validées côté serveur.

Les statistiques, phases, capacités, invocations et butins de boss doivent être calculés et validés côté serveur.

Les matériaux, expériences, bonus permanents, immunités et propriétés de chefs-d'œuvre doivent être validés et attribués côté serveur.

Les ingrédients, stations, niveaux, qualités, temps de fabrication et expériences de recettes doivent être validés côté serveur.

Les chimies, traits, anatomies, pièces et butins de créatures sont déclaratifs ; ils ne constituent pas une référence scientifique ou culturelle.

Le fichier `catalog.json` fournit leur chemin, leur version et leur empreinte SHA-256.

Tout nouveau modèle créé pour ce registre doit suivre [TEMPLATE-SPEC.md](../TEMPLATE-SPEC.md).

## Ajout futur d'un modèle

Chaque ajout devra disposer d'un répertoire de famille, d'un nom stable et d'une version explicite :

```text
<famille>/<nom-du-modele>/v<MAJEUR>.<MINEUR>.<CORRECTIF>/
  template.json ou schema.json
  README.md
```

Le `README.md` de la version devra identifier son statut et ses consommateurs réels. Un modèle commun à plusieurs clients ne sera placé dans une famille partagée qu'après confirmation que le contrat est réellement commun.

## Frontière serveur

Aucun code du serveur Zig ne doit être copié ici. Un modèle lié à une interface serveur pourra décrire un contrat public validé, mais il ne devra contenir ni implémentation propriétaire, ni configuration de déploiement, ni secret.
