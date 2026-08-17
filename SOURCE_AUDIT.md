# Audit des sources JSON

Audit réalisé le 17 août 2026 avant la première publication de données dans le registre.

## Sources comparées

- `templates/` à la racine : 1 JSON, plus ancien que sa copie serveur.
- `zig-server-v2/templates/` : 4 071 JSON.
- `ultimate-odycer-v-rclient/DEV serveur build/templates/` : 4 020 JSON.

## Résultat de comparaison

- 3 913 fichiers communs sont identiques.
- 95 fichiers communs diffèrent et la copie serveur est plus récente dans les 95 cas.
- 63 fichiers existent uniquement côté serveur.
- 12 fichiers existent uniquement côté client ; ce sont d'anciennes captures `_versions`.

Le build client n'est donc pas la source de référence la plus récente.

## Périmètre publié

La version initiale publie uniquement les 16 fichiers du sous-ensemble `schemas/`, sous forme d'instantanés `v0.1.0` non modifiés et marqués `experimental`.

Le lot suivant ajoute `haptics/default_patterns.json`. Les copies serveur et build client VR étaient identiques lors de l'audit ; la date plus récente du fichier client correspond uniquement à une copie plus tardive. Ce modèle est publié en `v0.1.0` avec le statut `experimental` et sans preuve d'intégration runtime.

Le lot `avatars` ajoute trois presets. `preset_defaut.json` était identique côté serveur et build client VR ; `human_athletic_f.json` et `human_balanced_m.json` étaient uniquement présents côté serveur. Les valeurs sont conservées sans modification, mais les marqueurs source tels que `mvp_ready` ne constituent pas une validation des assets, du rendu ou de l'intégration runtime.

Le lot `biomes` ajoute huit modèles identiques côté serveur et build client VR. Les noms de textures, sons, créatures, NPC, donjons et événements sont conservés comme identifiants logiques. Les fichiers correspondants, leurs droits et leur disponibilité runtime ne sont ni inclus ni certifiés.

Le lot `achievements` ajoute trois collections identiques côté serveur et build client VR. Les déclencheurs, récompenses, points et identifiants d'objets sont conservés sans modification, mais leur disponibilité runtime et leur équilibrage ne sont pas certifiés.

Le lot `events` publie uniquement `festival_template.json`, identique côté serveur et build client VR. `temporal_crisis.json` reste exclu car il contient des multiplicateurs de charge CPU, mémoire et trafic réseau ainsi que des contrôles administratifs. Les activités et récompenses du festival restent des identifiants et valeurs non certifiés.

Le lot `guilds` ajoute trois configurations identiques côté serveur et build client VR : onglets de banque, rangs et factions. Les permissions restent des valeurs déclaratives non fiables côté client ; toute invitation, promotion, diplomatie, opération bancaire ou utilisation de ressources doit être autorisée et validée côté serveur.

Le lot `locations` publie uniquement `city_template.json`, identique côté serveur et build client VR. `temporal_nexus_complex.json` reste exclu car il contient des contrôles administratifs et des mécanismes internes complexes. Les coordonnées et références du modèle de ville restent des valeurs logiques non certifiées.

Le lot `houses` publie uniquement `exemple_maisonnette_meublee.json`, identique octet pour octet entre les sources serveur et client auditées. `uo_villa_marbre.json` reste exclu car sa référence explicite au style Ultima Online exige une clarification des droits ou une adaptation visuelle originale. Les pièces et accessoires publiés sont des identifiants logiques ; les ressources visuelles, le rendu et l'assemblage runtime ne sont pas certifiés.

Le lot `names` publie uniquement `viking.json`, identique octet pour octet entre les sources serveur et client auditées. Ce modèle emploie des noms historiques et des termes issus de la mythologie nordique pour générer des noms de fiction ; il ne constitue pas une référence linguistique, historique ou culturelle. `elfe.json` et `nain.json` sont exclus en raison de noms directement associés à Tolkien, `lovecraftien.json` en raison de références directes au mythe de Cthulhu, `fantasy.json` en raison de marqueurs associés notamment à Warcraft et D&D, et `gaulois.json` dans l'attente d'une adaptation plus nettement originale de ses noms humoristiques.

## Éléments exclus

Les autres JSON restent hors du dépôt public en attendant un audit dédié. Ils comprennent notamment :

- du contenu narratif et de jeu dont les droits ou les inspirations doivent être vérifiés ;
- des paramètres de boutique, prix, devises premium et références SKU ;
- des classes et contrôles administratifs ;
- des chemins d'assets internes ;
- des historiques techniques `_versions` non convertis en versions sémantiques.

Aucun code du serveur Zig, secret ou paramètre d'infrastructure n'est inclus.
