# Pièces de l’éditeur d’architecture — sélection initiale

Six pièces effectivement utilisées par l’éditeur, conservées séparément du [kit proxy](../base-modulaire-v1/README.md). Leur origine comme créations du projet a été confirmée par son propriétaire. Les termes de licence applicables aux fichiers 3D restent à préciser ; ne pas déduire une licence particulière de cette confirmation.

| Identifiant éditeur | Fichier | SHA-256 |
| --- | --- | --- |
| mur_pierre | [GLB](mur_pierre.glb) | `ef57d49f9f6d1a63576eb5dde959fd38ad91d459b39ba84e45790edf1ec5df3e` |
| porte_bois | [GLB](porte_bois.glb) | `390cf55673d41c9dcfbc3d08b86414ef099147d5a9ae2192b547c8520cd0d3b3` |
| fenetre_simple | [GLB](fenetre_simple.glb) | `3dd2be8877d581ca3269cf35e2dc87e2a6abf0899f9b6e0239750224aa6adb2e` |
| sol_dalle_pierre | [GLB](sol_dalle_pierre.glb) | `b5dc7ffd55886566aeddf0de088a2b028908df56bbe1c58274f09ddfda6f882e` |
| porte_renforcee | [GLB](porte_renforcee.glb) | `804f75b3b4d733112e6f3260621309449cf7cdccb520d1244564cc96e3c57509` |
| colonne_pierre | [GLB](colonne_pierre.glb) | `6f9f1ffddfff08e9f7212f66b18b57ae19f9f3f728ad1ab30b66b3cd9e45abac` |

Les textures sont incorporées dans les GLB ; aucune URI externe n’a été détectée dans leurs descriptions glTF. Le [manifeste](manifest.json) indique leurs tailles et empreintes. Les aperçus de bâtiments correspondants sont dans la [galerie d’architecture](../../../../templates/architecture-editor/GALERIE.md).

Ces fichiers sont des instantanés de l’éditeur : vérifier échelle, orientation, raccords et comportement dans chaque consommateur avant adoption. Leur présence ne démontre ni compatibilité serveur, ni collisions, ni qualité VR. Les six proxies ont été testés séparément : leurs résultats ne s’appliquent pas automatiquement à ces fichiers.

En essai local isolé, les six GLB ont été chargés avec un manifeste temporaire dans une copie de l’éditeur comportant une correction candidate des lambrequins. Un assemblage exporté en JSON puis réimporté conserve les identifiants, coordonnées, arêtes et rotations contrôlés. La capture étant vide, cet essai ne qualifie pas l’aspect ou les raccords visuels. Il ne prouve ni l’intégration permanente ni le fonctionnement serveur.
