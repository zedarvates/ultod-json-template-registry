# Réutiliser les bases des éditeurs

Les galeries servent à choisir une silhouette et une catégorie proches du besoin, puis à partir de leurs recettes et pièces pour construire une variante. Une image de galerie est un aperçu de revue ; elle ne garantit ni la qualité finale ni l’intégration au jeu.

## Architecture

1. Parcourir la [galerie classique](../templates/architecture-editor/GALERIE.md) ou la [galerie moderne](../assets/architecture-editor/architecture-moderne-contemporaine/README.md).
2. Pour une maison classique, télécharger le `blueprint.json` lié et l’importer dans l’éditeur sur grille. Pour un bâtiment moderne, télécharger `recette.json` et l’ouvrir dans l’atelier « Bâtiment depuis une référence ». Ces deux formats sont distincts ; aucune conversion n’est démontrée ici.
3. Le [kit de pièces de base](../assets/architecture-editor/parts/base-modulaire-v1/README.md) fournit six GLB simples indépendants, avec dimensions et empreintes. Un chargement et un export/réimport isolés ont été observés avec les six pièces, un manifeste temporaire et une correction candidate de l’éditeur ; voir la fiche pour les limites. Le mapping permanent et le raccordement serveur restent à réaliser et vérifier.

## Créatures

Choisir une base dans la [galerie des créatures](creature-editor/GALERIE.md), suivre sa fiche et télécharger la recette indiquée. Les pièces Xeno déjà publiées sous [assets/xeno-editor](../assets/xeno-editor/) ne couvrent que certaines créatures et versions : utiliser leurs fiches et conserver les références propres à chaque recette. Vérifier attaches, rig, déformations et animation après toute modification.

## Dessin, Codex et serveur

Un dessin, une capture ou une description peut servir de référence humaine pour sélectionner une base, relever les différences et préparer une nouvelle recette versionnée. Décrire les changements, conserver la recette source et ses références, puis revoir la géométrie et les animations. La sélection automatique par image et la reconstruction complète depuis un dessin ne sont pas établies par ce dépôt.

Avant toute utilisation effective, vérifier le format et les dépendances dans le consommateur concerné, les droits de chaque ajout, les dimensions, les raccords, les collisions et les performances. Une recette ou un GLB présent ici ne prouve pas sa compatibilité avec le serveur, un client, Godot ou la VR. Les contrôles de chaque fiche gardent leur portée propre.

[Pistes pour le graphe de contenu, la découverte et les styles](registry-content-graph-roadmap.md).
