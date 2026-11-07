# Revue des raccords : cheval, mouton et lama

Trois prototypes statiques ont été importés dans l'éditeur en mode matériaux source, IK désactivée. Les captures `*_editor.png` documentent le résultat et `browser_results.json` le chargement technique. Ces images ne prouvent ni raccord soudé, ni animation, ni fidélité réaliste.

Les quatre jambes de chaque créature sont réorientées verticalement. Pour le cheval, les boîtes englobantes des jambes et fanons n'ont plus l'écart vertical initial de 0,175 m ; ce test approximatif ne prouve pas que les surfaces se rejoignent. Une tête provisoire composée de primitives a été ajoutée.

Revue visuelle : les parties se chevauchent, mais les transitions restent dures ; les visages, crinière et fanons sont insuffisants et les matériaux ont une répétition visible. Les trois modèles ne satisfont pas les références et ne doivent pas être promus comme assets finis. Les autres créatures ne sont pas améliorées par cette étape.

`manifest.json` identifie les fichiers d'entrée et de sortie ; `horse_bounds.json` conserve les mesures de boîtes englobantes. Le script source est `repair_quadrupeds_v2.py`.
