# Lapin original — museau sculpté, paupières et oreilles épaisses

**Version 0.2.0, encore stylisée.** Le photoréalisme final et l’intégration en jeu restent ouverts.

![Lapin — recette téléchargée puis reconstruite dans Godot](preview.png)

[Recette JSON](recipe.json) · [Profil de conception](design-profile.json) · [Mesures UV](uv-measurements.json) · [Validation](validation.json) · [Provenance](provenance.json) · [Galerie](../../GALERIE.md)

La tête reste un composant original indépendant, sans torse ni pattes. Les joues et l’arête nasale sont sculptées dans le crâne ; chaque œil latéral possède maintenant un contour de paupière fermé. Les oreilles arrondies passent de 0,42 à 0,245 m avant échelle, avec une coque arrière et un bord épaissis. Le contraste de la mâchoire et de la bouche est réduit, et le nez est assombri. Les oreilles conservent leur hauteur aux trois détails. Les trois détails du composant ont des positions, normales, UV et couleurs identiques à ceux de la tête dans le corps entier.

| Tête précédente — 0.1.0 | Nouvelle tête — 0.2.0 |
| --- | --- |
| ![Avant](../v0.1.0/head.png) | ![Après](head.png) |

Le corps possède quatre pattes, avec cinq doigts à chaque pied avant et quatre à chaque pied arrière, des semelles couvertes de fourrure et une courte queue claire. Le torse, le cou et les segments des membres forment une surface fermée et connectée ; la tête, les oreilles, les pieds et la queue restent des composants séparés qui se recouvrent.

| Profil | Dessus |
| --- | --- |
| ![Silhouette de profil](side.png) | ![Silhouette vue du dessus](top.png) |

Budget mesuré : **11 252 / 6 612 / 3 768 triangles**, plafonds **12 000 / 7 000 / 4 000**, **26 os** et **quatre influences maximum**. Les trois images originales communes aux mammifères font **512 / 256 / 256 pixels** ; estimation RGBA8 avec mipmaps complètes : **2 097 148 octets**. Il ne s’agit ni de la VRAM totale du pilote ni d’une mesure de FPS.

La diffusion des poids sur le vrai maillage réduit l’expansion maximale d’arête du premier essai de **1,640** à environ **1.359** pour la reconstruction. Un triangle trop aplati a été retriangulé sans déplacer les sommets ni ajouter de polygones ; les normales trop obliques sont corrigées dans les attributs de rendu. Sur **601 poses par niveau de détail**, aire relative minimale **0.470**, alignement minimal des normales **0.283** et aucun triangle retourné selon ce contrôle.

La marche lente conserve au moins **trois appuis**, avec une dérive CPU maximale de **0.137 mm**, une hauteur absolue d’appui de **0.336 mm** et une levée minimale de **44.94 mm**. L’éditeur contrôle les trois détails, la lecture/pause/reprise, la tête seule et l’effet réel de la topologie, du squelette et du microrelief. La recette téléchargée porte le pas de 0,085 à **0,09 m** ; sa reconstruction et la sélection passent Godot Forward+ et Compatibility sur **241 poses par niveau de détail**.

L’éditeur permet aussi de comparer les deux têtes en conservant la pose et la vue prédéfinie ; une version non admise est refusée. Le contrôle des tableaux du GLB confirme que corps, pattes, squelette, animation et images sont identiques à la revue précédente. La nouvelle tête ajoute **348 / 328 / 232 triangles**.

| Phase 15 % | Phase 40 % |
| --- | --- |
| ![Pieds à 15 %](feet-15.png) | ![Pieds à 40 %](feet-40.png) |

| Phase 65 % | Phase 90 % |
| --- | --- |
| ![Pieds à 65 %](feet-65.png) | ![Pieds à 90 %](feet-90.png) |

![Tête au détail lointain, volontairement inspectée de près](head-lod2.png)

Les neuf images sont des captures natives sans retouche de la recette reconstruite. SHA-256 du modèle capturé : `e567d3c90d5348132683492a201c74ab41ae4bd419bfb25277422e4c521a63dc`. SHA-256 de la recette : `68622d0ba9f08f30af6c4f900647fd8637cc464c45cf56e8586a7f8ee8da93f8`.

Le JSON seul nécessite le générateur et les ressources originales locales ; aucun GLB, code de générateur privé, cache ou bitmap source n’est publié. L’identité historique de lapin reste une candidate non associée et ses données serveur sont conservées. Revue locale encore stylisée : tête sculptée, contours de paupière fermés et oreilles épaissies ; marche lente rectiligne sur sol plat dans l’éditeur et Godot isolés. Raccords de composants, queue, silhouette du pelage et détails du LOD2 restent ouverts. Bonds, forces/masse, terrain, collisions exhaustives, monde principal, serveur, réseau, VR et photoréalisme final non qualifiés.
