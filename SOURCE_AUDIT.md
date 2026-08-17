# Audit des sources JSON

Audit réalisé le 17 août 2026 avant la première publication de données dans le registre.

## Sources comparées

- `templates/` à la racine : 1 JSON, plus ancien que sa copie serveur.
- `zig-server-v2/templates/` : 4 071 JSON.
- `ultimate-odycer-v-rclient/DEV serveur build/templates/` : 4 020 JSON.

## Résultat de comparaison

- 3 913 fichiers communs sont identiques.
- 95 fichiers communs diffèrent et la copie serveur est plus récente dans les 95 cas.
- 63 fichiers existent uniquement côté serveur.
- 12 fichiers existent uniquement côté client ; ce sont d'anciennes captures `_versions`.

Le build client n'est donc pas la source de référence la plus récente.

## Périmètre publié

La version initiale publie uniquement les 16 fichiers du sous-ensemble `schemas/`, sous forme d'instantanés `v0.1.0` non modifiés et marqués `experimental`.

Le lot suivant ajoute `haptics/default_patterns.json`. Les copies serveur et build client VR étaient identiques lors de l'audit ; la date plus récente du fichier client correspond uniquement à une copie plus tardive. Ce modèle est publié en `v0.1.0` avec le statut `experimental` et sans preuve d'intégration runtime.

## Éléments exclus

Les autres JSON restent hors du dépôt public en attendant un audit dédié. Ils comprennent notamment :

- du contenu narratif et de jeu dont les droits ou les inspirations doivent être vérifiés ;
- des paramètres de boutique, prix, devises premium et références SKU ;
- des classes et contrôles administratifs ;
- des chemins d'assets internes ;
- des historiques techniques `_versions` non convertis en versions sémantiques.

Aucun code du serveur Zig, secret ou paramètre d'infrastructure n'est inclus.
