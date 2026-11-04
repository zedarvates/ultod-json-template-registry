# Import des recettes de l’éditeur d’architecture

La collection [Old School 90s MMORPG Like](../templates/architecture-editor/README.md)
sépare le fichier natif importable, la capture et l’entrée de catalogue.

Préparer localement un manifeste JSON (ne pas le committer) :

```json
[
  {
    "slug": "uo-0156",
    "version": "1.2.0",
    "blueprint": "/local/house.blueprint.json",
    "preview": "/local/viewport.jpg",
    "reviewed_model_sha256": "<empreinte du GLB correspondant à la capture>"
  }
]
```

Utiliser un plan d’auteur et une capture JPEG cadrée sur le résultat, sans
interface d’administration, données de joueur ni chemins locaux. Vérifier
que la capture correspond au plan et au GLB déclaré avant l’import.

```sh
python scripts/import_architecture_templates.py manifest.json --validator /local/native_blueprint_validator
python scripts/import_architecture_templates.py manifest.json --validator /local/native_blueprint_validator --apply
python -m unittest discover -s tests -v
python scripts/validate_registry.py
```

Le script vérifie le plan avec le validateur Zig local et met à jour
le catalogue, l’index et la [galerie en images](../templates/architecture-editor/GALERIE.md)
en lot. La galerie montre la dernière version de chaque architecture. Il est idempotent si les octets sont identiques.
Si le plan ou la capture change, choisir une version supérieure. L’import ne
fait ni commit ni envoi Git : publier les fichiers validés via le flux Git du
dépôt. Les aperçus de revue ne certifient pas le serveur de jeu ni la VR.

Après l’ajout de captures complémentaires ou pour actualiser la galerie sans
importer de recette :

```sh
python scripts/generate_architecture_gallery.py
python scripts/generate_architecture_gallery.py --check
```

Les tests vérifient que la galerie reste à jour et que ses liens locaux existent.
