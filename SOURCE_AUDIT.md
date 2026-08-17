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

Le lot `styles` publie les six fichiers audités : citadelle elfique, crypte d'ossements, forge d'obsidienne, gothique prospère, hameau forestier et oasis désertique. Les copies serveur et client sont identiques octet pour octet et ne contiennent que des identifiants logiques de pièces et accessoires. Aucun asset, droit d'utilisation d'asset, rendu ou assemblage runtime n'est inclus ou certifié.

Le lot `rifts` publie les quatre fichiers audités : chaos, dimensionnel, élémentaire et temporel. Les copies serveur et client sont identiques octet pour octet. Les niveaux, coordonnées, vagues, délais, propriétés, objectifs et récompenses sont des valeurs déclaratives non certifiées ; toute activation et attribution doit être autorisée et validée côté serveur. Aucun code serveur, protocole interne ou état de production n'est inclus.

Le lot `party` publie `adventure_party.json`, identique octet pour octet entre les sources serveur et client auditées. Les méthodes de butin, bonus, appartenances, factions et limites de composition sont déclaratifs et doivent être recalculés, autorisés et validés côté serveur. `city_layouts/havre_du_roi.json` reste exclu car les copies divergent et la source contient un layout résolu par le serveur ainsi que des chemins d'assets internes. `gathering_node/mithril_vein.json` reste exclu en raison de sa référence explicite au Mithril associé à Tolkien.

Le lot `mentorship` publie `combat_training.json`, identique octet pour octet entre les sources serveur et client auditées. Les niveaux, réputation, objectifs, durées, expérience, points de compétence et titres sont des valeurs déclaratives non certifiées. Le serveur doit vérifier l'éligibilité et la progression puis rester seul responsable de toute attribution.

Le lot `marriage` publie `romantic_marriage.json`, identique octet pour octet entre les sources serveur et client auditées. Il ne contient aucune identité réelle, SKU ou monnaie premium. Le consentement mutuel, les prérequis, le coût de cérémonie, les bonus, le logement et le stockage partagé doivent être vérifiés transactionnellement côté serveur ; `ceremony_cost` reste une unité abstraite non certifiée.

Le lot `social_event` publie `wedding_ceremony.json`, identique octet pour octet entre les sources serveur et client auditées. Les participants, horaires, frais, expérience et objets distribués sont déclaratifs et doivent être autorisés et validés côté serveur. `mount/frost_dragon_mythic.json` reste exclu car il contient un chemin d'asset interne non audité et des paramètres de combat. `treasure_maps/treasure_map_tier_5.json` reste exclu en raison de références fortement évocatrices d'Ultima Online et de valeurs économiques non adaptées.

Le lot suivant publie `dungeon/crypt_of_shadows.json` depuis la source serveur et `paragons/paragon_master_config.json`. La copie client du donjon diverge : sa compatibilité reste donc vide et aucune synchronisation client n'est revendiquée. Les difficultés, apparitions, statistiques, butins et récompenses sont déclaratifs et doivent être calculés et validés côté serveur. `bods/bod_blacksmith_platemail.json` et `champions/champion_despise_vermin.json` restent exclus pour références directes à Ultima Online. `planets/terre.json` reste exclu comme configuration runtime interne divergente, et `pvp/temporal_chronomancer_arena.json` pour ses contrôles administratifs et mécanismes internes détaillés.

Le lot `bosses` publie `custom_beast_01.json` et `gardien_crypte_01.json`, identiques octet pour octet entre les sources serveur et client auditées. Leurs statistiques, phases, capacités, invocations et références de butin sont déclaratives et doivent être résolues et validées côté serveur. Les deux fichiers `loot` restent exclus car leurs commentaires révèlent des chemins et statistiques d'implémentation Zig et les copies client divergent. Les deux tournois restent exclus pour leurs mécanismes économiques, pari ou contrôles administratifs. Les deux fichiers `virtues_factions` restent exclus pour leurs marqueurs associés à Ultima Online, notamment Britain.

Le lot `masterpiece` publie ses trois créations, identiques octet pour octet entre les sources serveur et client auditées : armure divine, élixir de vie éternelle et lame d'éternité. Les matériaux, expériences, propriétés, immunités et bonus permanents sont déclaratifs et doivent être validés puis attribués côté serveur. Les trois fichiers `ability` restent exclus dans l'attente d'une adaptation originale, car le lot contient des noms de capacités directement associés à Warcraft, notamment `Blizzard` et `Frostbolt`.

Le lot `dungeons` publie ses six layouts depuis la source serveur : antre de glace, crypte d'ossements profonde, crypte de démonstration, crypte générée par grammaire, forteresse d'obsidienne et repaire de racines. Les six copies client divergent ; aucune compatibilité client n'est revendiquée. Tuiles, murs, marqueurs, références de boss et récompenses restent déclaratifs, sans asset inclus ou certifié. Les cinq fichiers `skillclass` restent exclus car ils déclarent être importés de Sphere et reprennent la taxonomie de compétences Ultima Online.

Le lot `recipe` publie cinq fichiers identiques octet pour octet entre les sources serveur et client auditées : robe de tissu, armure de fer, épée de fer, armure de cuir et bombe fumigène. Ingrédients, stations, niveaux, qualités, durées et expériences sont déclaratifs et doivent être validés côté serveur. `healing_potion.json` reste exclu pour ses composants `peacebloom` et `silverleaf` associés à Warcraft. `minor_strength_enchant.json` reste exclu dans l'attente d'une adaptation plus originale de ses composants, notamment `arcane_dust`.

Le lot `creatures` publie 29 des 30 fichiers depuis la source serveur : animaux communs, créatures fantasy et figures mythologiques celtiques, chinoises ou nordiques, plus un drone d'entraînement lunaire. Les 29 copies présentes côté client divergent ; le drone lunaire est absent du client. Aucune compatibilité client n'est donc revendiquée. Chimies, traits, anatomies, pièces et butins sont déclaratifs, sans asset inclus ou certifié, et les entrées mythologiques ne constituent pas des références culturelles ou historiques. `xenomorph.json` reste exclu comme référence directe à la franchise Alien.

Le lot `content_pipeline` publie son manifeste et 1 000 quêtes générées, identiques octet pour octet entre les sources serveur et client auditées. Les marqueurs tels que `balance_validated` ou `ready_for_import` décrivent uniquement l'état déclaré par la source et ne constituent pas une certification. Les 168 sorts générés restent exclus car ils exposent des contrôles administratifs et appartiennent à une collection de sorts nécessitant un audit de droits et de contrat plus approfondi.

## Éléments exclus

Les autres JSON restent hors du dépôt public en attendant un audit dédié. Ils comprennent notamment :

- du contenu narratif et de jeu dont les droits ou les inspirations doivent être vérifiés ;
- des paramètres de boutique, prix, devises premium et références SKU ;
- des classes et contrôles administratifs ;
- des chemins d'assets internes ;
- des historiques techniques `_versions` non convertis en versions sémantiques.

Aucun code du serveur Zig, secret ou paramètre d'infrastructure n'est inclus.
