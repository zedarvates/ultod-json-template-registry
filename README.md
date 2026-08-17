# UltOd JSON Template Registry

Registre central destiné aux modèles JSON versionnés de l'écosystème Ultimate Odycer.

## Statut

**Registre expérimental.** Une première collection de 16 schémas JSON et un modèle de motifs haptiques sont publiés en version `0.1.0`.

Ces schémas sont des instantanés non certifiés. Aucun n'est encore déclaré compatible avec une version précise d'un client ou du serveur.

## Objectif

Ce dépôt doit fournir un emplacement public et traçable pour les modèles JSON partagés ou spécialisés, notamment pour :

- le client Godot VR MMORPG ;
- le client Godot Classic 3D MMORPG ;
- de futurs clients 2.5D web, dont la technologie reste à confirmer ;
- les outils de contenu et de configuration qui consomment ces modèles.

## Limites

Ce dépôt ne doit pas contenir :

- le code du serveur Zig ;
- du code exécutable des clients ;
- des secrets, identifiants ou données de production ;
- des paramètres d'infrastructure ou de facturation ;
- des exports ou ressources dont les droits n'ont pas été vérifiés.

La présence d'un modèle dans ce registre ne prouve pas son intégration de bout en bout. Toute compatibilité doit être documentée et validée séparément.

## Organisation prévue

```text
templates/
  catalog.json
  schemas/
    <nom-du-schema>/
      v<MAJEUR>.<MINEUR>.<CORRECTIF>/
        schema.json
        README.md
  haptics/
    <nom-du-modele>/
      v<MAJEUR>.<MINEUR>.<CORRECTIF>/
        template.json
        README.md
```

Le détail de la sélection initiale et des exclusions se trouve dans [SOURCE_AUDIT.md](SOURCE_AUDIT.md).

## Versionnage

Le registre suit un versionnage sémantique par modèle. Les règles détaillées se trouvent dans [VERSIONING.md](VERSIONING.md).

## Licence

Les schémas, modèles et documents originaux de ce registre sont distribués sous
licence Apache-2.0. Cette licence ne couvre pas le serveur Zig propriétaire, les
services hébergés, les données de production, les ressources tierces ni les
composants commerciaux d'Ultimate Odycer.
