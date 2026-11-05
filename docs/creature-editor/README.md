# Créatures originales — recettes de revue

**[Voir la galerie en images](GALERIE.md)** · [Index JSON](gallery-index.json)

Ces instantanés proviennent des ateliers de l’éditeur de créatures. Les recettes sont des documents de revue versionnés ; leurs générateurs, pièces et modèles source ne sont pas inclus. Les formats varient : projets paramétriques, génomes natifs de l’éditeur pour les arthropodes, ou recette de prototype. Ces fiches documentaires ne sont pas des entrées strict-v1 du catalogue. Chaque fiche précise la variante effectivement capturée et les contrôles réalisés ; le crocodilien 0.2.0 montre désormais le corps et la tête de la recette reconstruite. Les modèles ne sont pas qualifiés pour une intégration en jeu sur cette seule base.

| Créature | Version | Recette et capture |
| --- | --- | --- |
| Chauve-souris géante | 0.1.0 | [Fiche](bat-original/v0.1.0/README.md) |
| Araignée géante — huit pattes | 0.1.0 | [Génome et marche](spider-original/v0.1.0/README.md) |
| Crocodilien — museau affiné et paupières sculptées | 0.6.0 | [Recette, tête et marche Godot](crocodile-original/v0.6.0/README.md) · [Version 0.5.0 conservée](crocodile-original/v0.5.0/README.md) |
| Sanglier géant | 0.1.0 | [Fiche](boar-original/v0.1.0/README.md) |
| Gazer | 0.1.0 | [Fiche](gazer-original/v0.1.0/README.md) |
| Golem | 0.1.0 | [Fiche](golem-original/v0.1.0/README.md) |
| Ours brun — plantigradie et marche | 0.1.0 | [Recette et captures Godot](bear-original/v0.1.0/README.md) |
| Rapace — peau et écailles | 0.2.0 | [Recette et captures Godot](raptor-original/v0.2.0/README.md) |
| Lapin — museau, paupières et oreilles | 0.2.0 | [Recette et captures Godot — tête affinée](rabbit-original/v0.2.0/README.md) |
| Grenouille géante — peau et doigts palmés | 0.1.0 | [Recette et captures Godot — première revue](frog-original/v0.1.0/README.md) |
| Dragon — crâne et narines connectés | 0.2.0 | [Composant et comparaisons Godot — revue partielle](dragon-cranium-original/v0.2.0/README.md) |
| Dragon — corps et marche, ailes à construire | 0.1.0 | [Recette et captures Godot — corps de revue](dragon-body-original/v0.1.0/README.md) |
| Dragon — ailes articulées et déploiement au sol | 0.1.0 | [Recette et captures Godot — ailes de revue](dragon-wings-original/v0.1.0/README.md) |
| Biche — silhouette et marche | 0.1.0 | [Recette et captures Godot](deer-doe-original/v0.1.0/README.md) |
| Cerf à bois — silhouette et marche | 0.1.0 | [Recette et captures Godot](deer-stag-original/v0.1.0/README.md) |
| Cheval brun — silhouette et marche | 0.1.0 | [Recette et captures Godot](horse-original/v0.1.0/README.md) |
| Vache brune — crâne, oreilles et fanon | 0.2.0 | [Recette et captures Godot](bovine-original/v0.2.0/README.md) · [Première revue conservée](bovine-original/v0.1.0/README.md) |
| Puma — tête continue et pelage nuancé | 0.2.0 | [Recette et captures Godot](cougar-original/v0.2.0/README.md) · [Première base conservée](cougar-original/v0.1.0/README.md) |
| Loup — oreilles et marche | 0.1.0 | [Recette reconstruite](wolf-original/v0.1.0/README.md) |
| Rat géant | 0.1.0 | [Fiche](rat-original/v0.1.0/README.md) |
| Scarabée géant — six pattes | 0.1.0 | [Génome et marche](beetle-original/v0.1.0/README.md) |
| Scorpion — marche articulée | 0.2.0 | [Recette animée](scorpion-original/v0.2.0/README.md) · [Ancienne fiche statique](scorpion-original/v0.1.0/README.md) |
| Serpent | 0.1.0 | [Fiche](serpent-original/v0.1.0/README.md) |

La galerie est régénérable avec `python scripts/generate_creature_gallery.py` depuis la racine du dépôt. Ajouter une version documentaire dans `gallery-index.json` conserve les anciennes recettes et images. Les nouvelles fiches associent les SHA-256 de la recette, de l’image et du modèle capturé dans `provenance.json`.

Les versions documentaires sont propres à ces fiches ; elles ne remplacent pas les versions du catalogue Xeno. Le [génome d’araignée déjà catalogué en 0.2.0](../../templates/xeno-editor/giant-spider-eight-legs/v0.2.0/README.md) reste inchangé.

L’inventaire des autres créatures et leur qualification restent en cours.
