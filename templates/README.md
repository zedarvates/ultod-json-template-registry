# Modèles JSON

Ce dossier accueille les modèles et schémas JSON versionnés du registre.

## État actuel

La première collection contient 16 schémas issus de la source serveur la plus récente et un modèle de motifs haptiques identique côté serveur et build client VR. Ils sont publiés en `v0.1.0` avec le statut `experimental` et sans certification de compatibilité.

Le fichier `catalog.json` fournit leur chemin, leur version et leur empreinte SHA-256.

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
