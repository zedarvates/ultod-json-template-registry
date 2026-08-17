# UltOd JSON Template Registry

Registre central destiné aux modèles JSON versionnés de l'écosystème Ultimate Odycer.

## Statut

**Documentation initiale.** Aucun modèle JSON applicatif n'est encore publié ni déclaré compatible avec un client ou un serveur.

Les contrats seront ajoutés progressivement après validation de leur rôle, de leur propriétaire et de leur compatibilité.

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
  <famille>/
    <nom-du-modele>/
      v<MAJEUR>.<MINEUR>.<CORRECTIF>/
        template.json
        README.md
```

Les familles et premiers modèles seront créés seulement lorsque leurs contrats seront suffisamment définis.

## Versionnage

Le registre suit un versionnage sémantique par modèle. Les règles détaillées se trouvent dans [VERSIONING.md](VERSIONING.md).

## Licence

Aucune licence open source n'est sélectionnée à ce stade. L'ajout d'une licence fera l'objet d'une décision explicite avant publication de modèles réutilisables.
