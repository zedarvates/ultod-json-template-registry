# Jonctions corps et jambes : prototypes de revue

Ces trois copies statiques du cheval, du mouton et du lama ont été remeshées par voxels de 0,025 m pour raccorder le corps et les quatre jambes ; le cou du lama et le cou et les fanons du cheval sont inclus. Les têtes, yeux et sabots restent des pièces séparées. Les originaux ne sont pas remplacés.

`weld_report.json` relève un composant et zéro arête non-manifold pour chaque corps dans Blender avant export. `glb_geometric_audit.json` retrouve le même résultat dans les positions et triangles GLB, après regroupement des positions à 1 micromètre ; il n'inclut pas les pièces de détail. Le contrôle Blender après réimport n'a pas été exécuté car les réserves mémoire étaient insuffisantes.

Les trois GLB ont été importés dans l'éditeur avec l'IK désactivée. Les captures montrent des transitions plus douces, mais des formes primitives, des textures répétitives, des têtes et sabots non soudés et un manque de fidélité aux références. Les modèles sont des prototypes de revue, sans animation validée. Les UV ont été recalculés automatiquement et leurs coutures restent à contrôler. La tâche des huit créatures et des textures réalistes reste inachevée.
