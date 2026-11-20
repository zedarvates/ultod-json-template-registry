# Essai PBR des huit créatures — prototypes rejetés

Suivi de la PR #86. Cette revue documente des résultats non conformes ; ne pas utiliser comme modèles finaux.

Huit GLB animés ont reçu des UV automatiques et des textures procédurales de couleur et de rugosité, avec une normale neutre. Les matériaux sont provisoires et les régions de couleur ne sont pas préservées. `manifest.json` identifie les sources et leurs empreintes ; `structural_results.json` compare les nombres de triangles, joints et pistes, sans valider leurs valeurs ni la déformation.

Les huit GLB ont été importés dans l'éditeur local avec l'IK désactivée et les matériaux source affichés. `browser_results.json` contient les résultats techniques ; les captures `*_editor.png` montrent le rendu réel. Le chargement technique a réussi, mais la revue visuelle échoue : le cheval, le mouton et le lama présentent des parties disjointes et des détails manquants ; le crabe ne montre que les pattes ; le rat est incomplet ; le serpent et le taureau ne ressemblent pas suffisamment aux références ; la gelée a perdu ses couleurs de noyaux. Les cartes normales sont plates et les textures ne sont pas réalistes. La marche et les appuis restent invalidés.

Une tentative de réassemblage depuis les pièces séparées existe localement, mais n'est pas retenue ici : l'export perd les couleurs de sommets. Refaire les assemblages, préserver leurs couleurs et matériaux, améliorer les UV et vérifier les rendus sous plusieurs éclairages avant toute promotion.
