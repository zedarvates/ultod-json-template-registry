# Variante de revue : yeux et sabots

Copies statiques du cheval, du mouton et du lama : remesh des corps, membres, têtes et sabots, avec yeux séparés et matériaux distincts pour yeux et sabots. Les matériaux ont été transférés par proximité ; les UV ont été recalculés.

Dans Blender avant export, chaque maillage principal compte un composant et zéro arête non-manifold ; les yeux sont exclus de cette mesure. L'audit Blender après réimport avec fusion des sommets retrouve ces résultats ; voir `reimport_audit.json`. Les trois GLB ont été chargés dans l'éditeur avec IK désactivée ; les captures montrent des yeux et sabots plus visibles, mais des silhouettes primitives et des textures répétitives. Ces modèles sont des prototypes non conformes aux références, sans animation validée.

`weld_report.json` conserve les sources, empreintes et mesures avant export ; `browser_results.json` et les captures documentent l'import et le rendu. Les coutures UV, la fidélité des couleurs et la locomotion restent à vérifier.
