# Modèles JSON

Ce dossier accueillera les modèles JSON versionnés lorsqu'ils auront été définis et validés.

## État actuel

Aucun modèle applicatif n'est publié. Ce dossier documente uniquement la structure prévue.

## Ajout futur d'un modèle

Chaque ajout devra disposer d'un répertoire de famille, d'un nom stable et d'une version explicite :

```text
<famille>/<nom-du-modele>/v<MAJEUR>.<MINEUR>.<CORRECTIF>/
  template.json
  README.md
```

Le `README.md` de la version devra identifier son statut et ses consommateurs réels. Un modèle commun à plusieurs clients ne sera placé dans une famille partagée qu'après confirmation que le contrat est réellement commun.

## Frontière serveur

Aucun code du serveur Zig ne doit être copié ici. Un modèle lié à une interface serveur pourra décrire un contrat public validé, mais il ne devra contenir ni implémentation propriétaire, ni configuration de déploiement, ni secret.
