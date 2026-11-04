"""Generate the documentary creature gallery without changing registry templates."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs/creature-editor'


def generate():
    data = json.loads((DOC / 'gallery-index.json').read_text(encoding='utf8'))
    rows = data['entries']
    blocks = [
        '# Galerie des créatures originales',
        f"Recettes de l’éditeur, captures réelles et états de revue — mise à jour du {data['updated']}.",
        'Les images montrent des prototypes locaux et les variantes précisées dans chaque fiche. '
        'Les JSON conservent les paramètres et les références de dépendances ; les générateurs, '
        'pièces et modèles ne sont pas distribués dans ce dépôt. Aucun modèle présenté ici '
        'n’est déclaré prêt pour le jeu ni photoréaliste final.',
        '[Index des recettes](README.md) · [Index lisible par les outils](gallery-index.json)',
    ]
    for row in rows:
        base = f"{row['id']}/{row['version']}"
        for file in ('README.md', 'recipe.json', 'preview.png'):
            if not (DOC / base / file).is_file():
                raise ValueError(f'Missing gallery dependency: {base}/{file}')
        blocks.extend([
            f"## {row['name']}",
            f"![{row['name']} — {row['preview_kind']}]({base}/preview.png)",
            f"[Fiche {row['version'][1:]}]({base}/README.md) · [Recette JSON]({base}/recipe.json)",
            row['summary'], row['scope'],
        ])
    blocks.append('La version statique du [scorpion 0.1.0](scorpion-original/v0.1.0/README.md) '
                  'et le [génome d’araignée déjà catalogué](../../templates/xeno-editor/giant-spider-eight-legs/v0.2.0/README.md) '
                  'restent conservés. L’inventaire et la recréation des autres familles se poursuivent.')
    return '\n\n'.join(blocks) + '\n'


if __name__ == '__main__':
    target = DOC / 'GALERIE.md'
    target.write_bytes(generate().encode('utf8'))
    print(target.relative_to(ROOT).as_posix())
