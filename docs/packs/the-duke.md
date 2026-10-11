# The Duke — pack Action Hero v1.0.0

Pack original de commando rétro pour Ultimate Odycer : **DPS / Bruiser**, avec
**Grit** et **Munitions**, dégâts massifs, contrôle de zone, gadgets et insultes
de combat. Le nom du pack reste **The Duke**. Le kit reprend la proposition du
propriétaire et ses trois provocations.

Propriétaire : Ultimate Odycer / zedarvates. Statut : **experimental**.
Première publication : 2026-10-11. Licence Apache-2.0 pour le contenu original.
Les noms demandés servent à identifier les concepts du kit. Aucun personnage,
modèle, logo, enregistrement, texture ou fichier de jeu tiers n'est distribué;
les répliques ci-dessous sont originales, sans dialogue repris d'un jeu.

**[Scaffolding / Proxy — intégration runtime non vérifiée].** Les templates sont
des contrats déclaratifs. Ils ne constituent ni une classe jouable, ni une
attribution d'inventaire, ni des effets exécutables. `compatibility` reste vide.

## Entrée du pack

- [Œuf de classe](../../templates/items/the-duke-class-egg/v1.0.0/template.json) :
  `items:the-duke-class-egg@1.0.0`, classé `class-pack-egg`, rareté `epic`.
- [Classe The Duke](../../templates/classes/the-duke/v1.0.0/template.json) :
  `classes:the-duke@1.0.0`, rôles `dps` et `bruiser`, ressources `grit` et `ammunition`.
- Le bundle ferme ses références vers **15 compétences actives, 4 passifs et
  36 talents**, soit **57 templates** avec la classe et l'œuf.

L'ouverture vise l'accès à la classe et à sa progression. Les dépendances ne
donnent pas implicitement tous les sorts dès l'ouverture et ne constituent pas
un droit d'acquisition. Obtention, échange, consommation et économie restent à
décider côté serveur. Aucun prix ou paramètre commercial n'est publié.

## Kit de compétences

T1 contient cinq bases et Trash Talk Overdrive. T2 contient les quatre techniques
avancées et Royal Insult Protocol. T3 contient les trois ultimes du kit initial
et Ego Meltdown. Ces catégories indiquent l'intention de progression.
Les niveaux, bonus, mètres, secondes, coûts, recharges et pourcentages proposés
par le propriétaire sont conservés dans un brouillon local d'équilibrage,
hors de ce registre et sans activation runtime. Leur équilibrage reste ouvert.

| Capacité | Catégorie | Intention et précautions | JSON |
| --- | --- | --- | --- |
| Mighty Kick | T1 | Coup de pied qui repousse; heurter un mur peut alimenter Grit après validation de collision serveur. | [mighty-kick](../../templates/spells/the-duke-mighty-kick/v1.0.0/template.json) |
| Boomstick Burst | T1 | Décharge en cône à courte portée; Grit élevé favorise les critiques selon le profil serveur. | [boomstick-burst](../../templates/spells/the-duke-boomstick-burst/v1.0.0/template.json) |
| Pipe Bomb | T1 | Bombe collante à explosion manuelle. Le saut assisté d'un allié nécessite son consentement et une trajectoire validée; il ne permet pas le déplacement forcé d'un joueur. | [pipe-bomb](../../templates/spells/the-duke-pipe-bomb/v1.0.0/template.json) |
| Ego Boost | T1 | Une réplique originale accompagne un bonus offensif et une protection contre peur et charme, liés à un profil serveur. | [ego-boost](../../templates/spells/the-duke-ego-boost/v1.0.0/template.json) |
| Steroids | T1 | Renforce vitesse, récupération de Grit et force. Le flou proposé est cosmétique, désactivable, et désactivé par défaut en VR. | [steroids](../../templates/spells/the-duke-steroids/v1.0.0/template.json) |
| Chaingun Cyclone | T2 | Canalisation balistique circulaire avec protection. La rotation concerne l'avatar ou l'effet; aucun mouvement de caméra ou du casque VR n'est imposé. | [chaingun-cyclone](../../templates/spells/the-duke-chaingun-cyclone/v1.0.0/template.json) |
| Holo-Duke | T2 | Un hologramme détourne l'attention puis explose légèrement à expiration. Il ne duplique ni le joueur ni son inventaire. | [holo-duke](../../templates/spells/the-duke-holo-duke/v1.0.0/template.json) |
| Freezethrower | T2 | Immobilisation cryogénique selon immunités et résistances; la bombe sur une cible gelée peut bénéficier d'une synergie critique serveur. | [freezethrower](../../templates/spells/the-duke-freezethrower/v1.0.0/template.json) |
| Kick'n Reload | T2 | Recharge et frappe rapprochée liées en une technique; récupération de Boomstick selon le profil serveur. Le coup exige une cible valide à portée. | [kick-n-reload](../../templates/spells/the-duke-kick-n-reload/v1.0.0/template.json) |
| Hail to the King | T3 | Fenêtre de carnage : dégâts, récupération de Grit et critiques renforcés. Une réplique originale accompagne l'activation; aucun enregistrement vocal du joueur n'est requis. | [hail-to-the-king](../../templates/spells/the-duke-hail-to-the-king/v1.0.0/template.json) |
| Nuke Strike | T3 | Frappe tactique annoncée, suivie d'une brûlure résiduelle et d'un ralentissement du lanceur. Respecte protections de zone, collision et cibles autorisées. | [nuke-strike](../../templates/spells/the-duke-nuke-strike/v1.0.0/template.json) |
| Balls of Steel | T3 | Protection défensive majeure et renvoi partiel. Aucun renvoi récursif : dégâts réfléchis ne déclenchent pas une nouvelle réflexion. | [balls-of-steel](../../templates/spells/the-duke-balls-of-steel/v1.0.0/template.json) |
| Trash Talk Overdrive | T1 | Provocation insultante en cône avec baisse de précision et gain de Grit. Face à un boss, vulnérabilité et armure du lanceur restent soumises aux immunités. En PvP, aucune prise de contrôle de la caméra ou de la cible du joueur. | [trash-talk-overdrive](../../templates/spells/the-duke-trash-talk-overdrive/v1.0.0/template.json) |
| Royal Insult Protocol | T2 | Provocation élite, dissipation de buffs admissibles, baisse de cadence et bonus du lanceur contre sa cible. Ne dissipe pas une protection indissipable. | [royal-insult-protocol](../../templates/spells/the-duke-royal-insult-protocol/v1.0.0/template.json) |
| Ego Meltdown | T3 | Tirade de provocation en zone qui fragilise le moral et l'offensive ennemie et stimule Grit. Ne contourne pas les immunités ni les protections contre le contrôle mental. | [ego-meltdown](../../templates/spells/the-duke-ego-meltdown/v1.0.0/template.json) |
| One-Liner Mastery | Passif | Une réplique de combat éligible peut déclencher un buff choisi côté serveur. Une fenêtre d'éligibilité empêche le spam; le chat libre n'est pas un déclencheur. Les choix aléatoires doivent être traçables dans la simulation. | [one-liner-mastery](../../templates/spells/the-duke-one-liner-mastery/v1.0.0/template.json) |
| Action Reload | Passif | Une recharge validée prépare un bonus pour le prochain tir admissible; le profil serveur règle consommation et cumul. | [action-reload](../../templates/spells/the-duke-action-reload/v1.0.0/template.json) |
| Heroic Momentum | Passif | Une élimination attribuée par le serveur déclenche un élan de vitesse temporaire. Aucun événement de mort fourni par le client ne suffit. | [heroic-momentum](../../templates/spells/the-duke-heroic-momentum/v1.0.0/template.json) |
| Old-School Badass | Passif | Protection contre les contrôles psychiques définis par le serveur. Le cumul avec Ego Boost suit une règle explicite et ne confère pas une immunité universelle. | [old-school-badass](../../templates/spells/the-duke-old-school-badass/v1.0.0/template.json) |

## Trois branches de spécialisation

Chaque branche a douze nœuds déclaratifs liés en chaîne. Chaque nœud référence
la capacité qu’il modifie et, après le premier, le précédent nœud. Les rangs,
points, niveaux et règles d’exclusivité restent côté serveur.

### Action Hero

DPS pur, critique, burst et munitions; ultime recommandé : Hail to the King.

| Nœud | Intention | JSON |
| --- | --- | --- |
| Visée d'acier | Précision du tir à courte portée. | [steady-aim](../../templates/skills/the-duke-action-hero-steady-aim/v1.0.0/template.json) |
| Réserve d'ego | Réserve de Grit pour les séquences offensives. | [grit-reserves](../../templates/skills/the-duke-action-hero-grit-reserves/v1.0.0/template.json) |
| Ceinture chargée | Gestion améliorée des munitions. | [loaded-belt](../../templates/skills/the-duke-action-hero-loaded-belt/v1.0.0/template.json) |
| Recharge de héros | Renforce le prochain tir après recharge. | [action-reload](../../templates/skills/the-duke-action-hero-action-reload/v1.0.0/template.json) |
| Double décharge | Variante à double tir du Boomstick. | [double-boomstick](../../templates/skills/the-duke-action-hero-double-boomstick/v1.0.0/template.json) |
| Fragmentation | Variante de bombe à fragmentation. | [fragmentation](../../templates/skills/the-duke-action-hero-fragmentation/v1.0.0/template.json) |
| Ego critique | Accentue la synergie critique avec Grit. | [critical-ego](../../templates/skills/the-duke-action-hero-critical-ego/v1.0.0/template.json) |
| Cyclone concentré | Renforce la pression du cyclone. | [cyclone-focus](../../templates/skills/the-duke-action-hero-cyclone-focus/v1.0.0/template.json) |
| Tempo héroïque | Enchaîne l'élan après une élimination valide. | [heroic-tempo](../../templates/skills/the-duke-action-hero-heroic-tempo/v1.0.0/template.json) |
| Réplique percutante | Oriente la réplique vers le burst. | [one-liner-impact](../../templates/skills/the-duke-action-hero-one-liner-impact/v1.0.0/template.json) |
| Assaut royal | Renforce la fenêtre offensive de l'ultime. | [royal-burst](../../templates/skills/the-duke-action-hero-royal-burst/v1.0.0/template.json) |
| Héros d'action | Talent final de burst et de gestion des munitions. | [action-hero-capstone](../../templates/skills/the-duke-action-hero-action-hero-capstone/v1.0.0/template.json) |

### Explosives Expert

Zone et contrôle; ultime recommandé : Nuke Strike.

| Nœud | Intention | JSON |
| --- | --- | --- |
| Formation explosive | Améliore la maîtrise des zones explosives. | [blast-training](../../templates/skills/the-duke-explosives-expert-blast-training/v1.0.0/template.json) |
| Pose contrôlée | Facilite le placement admissible des charges. | [sticky-handling](../../templates/skills/the-duke-explosives-expert-sticky-handling/v1.0.0/template.json) |
| Préparation cryogénique | Prépare le combo sur cible gelée. | [cryo-preparation](../../templates/skills/the-duke-explosives-expert-cryo-preparation/v1.0.0/template.json) |
| Tactique de diversion | Renforce la diversion de l'hologramme. | [decoy-tactics](../../templates/skills/the-duke-explosives-expert-decoy-tactics/v1.0.0/template.json) |
| Gel en chaîne | Variante de gel propagé entre cibles admissibles. | [chain-freeze](../../templates/skills/the-duke-explosives-expert-chain-freeze/v1.0.0/template.json) |
| Double hologramme | Variante à deux leurres dans les limites serveur. | [double-hologram](../../templates/skills/the-duke-explosives-expert-double-hologram/v1.0.0/template.json) |
| Souffle élargi | Étend la zone selon le profil serveur. | [wider-blast](../../templates/skills/the-duke-explosives-expert-wider-blast/v1.0.0/template.json) |
| Détonation cryogénique | Renforce la synergie bombe et gel. | [frozen-detonation](../../templates/skills/the-duke-explosives-expert-frozen-detonation/v1.0.0/template.json) |
| Braises persistantes | Renforce la brûlure résiduelle. | [residual-fire](../../templates/skills/the-duke-explosives-expert-residual-fire/v1.0.0/template.json) |
| Recul maîtrisé | Module la contrepartie de ralentissement. | [controlled-recoil](../../templates/skills/the-duke-explosives-expert-controlled-recoil/v1.0.0/template.json) |
| Ogive tactique | Renforce l'ultime de contrôle de zone. | [tactical-warhead](../../templates/skills/the-duke-explosives-expert-tactical-warhead/v1.0.0/template.json) |
| Expert en explosifs | Talent final d'explosifs et de contrôle de zone. | [explosives-expert-capstone](../../templates/skills/the-duke-explosives-expert-explosives-expert-capstone/v1.0.0/template.json) |

### Ego Titan

Bruiser et survie; ultime recommandé : Balls of Steel.

| Nœud | Intention | JSON |
| --- | --- | --- |
| Flux de Grit | Améliore la récupération de Grit. | [grit-flow](../../templates/skills/the-duke-ego-titan-grit-flow/v1.0.0/template.json) |
| Bottes lourdes | Renforce le coup et son contrôle admissible. | [heavy-boots](../../templates/skills/the-duke-ego-titan-heavy-boots/v1.0.0/template.json) |
| Peau dure | Renforce la résistance du bruiser. | [thick-skin](../../templates/skills/the-duke-ego-titan-thick-skin/v1.0.0/template.json) |
| Armure de provocation | Améliore la protection obtenue face au danger. | [taunt-armour](../../templates/skills/the-duke-ego-titan-taunt-armour/v1.0.0/template.json) |
| Coup étourdissant | Variante de coup qui peut étourdir selon immunités. | [stunning-kick](../../templates/skills/the-duke-ego-titan-stunning-kick/v1.0.0/template.json) |
| Survoltage prolongé | Variante de renforcement plus durable. | [lasting-steroids](../../templates/skills/the-duke-ego-titan-lasting-steroids/v1.0.0/template.json) |
| Pression royale | Renforce la pression sur la cible provoquée. | [royal-pressure](../../templates/skills/the-duke-ego-titan-royal-pressure/v1.0.0/template.json) |
| Ego inébranlable | Renforce la protection psychique admissible. | [unshaken-ego](../../templates/skills/the-duke-ego-titan-unshaken-ego/v1.0.0/template.json) |
| Renvoi maîtrisé | Améliore le renvoi sans boucle récursive. | [controlled-reflection](../../templates/skills/the-duke-ego-titan-controlled-reflection/v1.0.0/template.json) |
| Endurance de tirade | Soutient la récupération de Grit pendant la provocation. | [meltdown-endurance](../../templates/skills/the-duke-ego-titan-meltdown-endurance/v1.0.0/template.json) |
| Posture d'acier | Renforce l'ultime défensif. | [steel-stance](../../templates/skills/the-duke-ego-titan-steel-stance/v1.0.0/template.json) |
| Titan de l'ego | Talent final de survie et de provocation. | [ego-titan-capstone](../../templates/skills/the-duke-ego-titan-ego-titan-capstone/v1.0.0/template.json) |

## Vingt répliques originales et mapping proposé

Ces exemples de dialogue sont de la documentation, pas des champs de template.
Le mapping associe chaque ligne à une activation. One-Liner Mastery peut choisir
un buff serveur éligible; parler ou écrire dans le chat ne déclenche rien.
Une ligne obligatoire signifie une présentation à l'activation, jamais une
obligation d'utiliser le micro. Voix, sous-titres, volume et options d'accessibilité
restent indépendants de l'effet serveur. Aucune voix ni icône n'est livrée.

| Ligne | Réplique originale | Activation |
| --- | --- | --- |
| 01 | « Vous avez des grandes gueules. Moi, j’ai les gros calibres. » | `trash-talk-overdrive` |
| 02 | « Viens, sac de boulons, je vais te desserrer l’ego. » | `trash-talk-overdrive` |
| 03 | « Vous appelez ça une menace ? J’ai vu des portes plus coriaces. » | `trash-talk-overdrive` |
| 04 | « Bande de tas de ferraille, la casse est par ici ! » | `trash-talk-overdrive` |
| 05 | « Rapprochez-vous, les tocards : la leçon commence. » | `trash-talk-overdrive` |
| 06 | « Tes beaux effets de lumière vont pas sauver ta sale tronche. » | `royal-insult-protocol` |
| 07 | « Remballe ta couronne en carton, champion. » | `royal-insult-protocol` |
| 08 | « T’as empilé les buffs pour cacher quoi ? Le vide ? » | `royal-insult-protocol` |
| 09 | « Le spectacle est fini. Maintenant, on démonte le décor. » | `royal-insult-protocol` |
| 10 | « Tu bombes le torse ? Parfait, ça fait une plus grosse cible. » | `royal-insult-protocol` |
| 11 | « Votre ego prend toute la place. Je vais faire du ménage. » | `ego-meltdown` |
| 12 | « J’ai compté vos chances. Ça m’a pas pris longtemps. » | `ego-meltdown` |
| 13 | « Tout ce bruit pour finir en pièces détachées ! » | `ego-meltdown` |
| 14 | « Les grandes gueules devant, les excuses derrière ! » | `ego-meltdown` |
| 15 | « On va baisser le volume : je commence par vous. » | `ego-meltdown` |
| 16 | « Le héros est arrivé. Le reste, c’est de la poussière. » | `ego-boost` |
| 17 | « J’ai pas une armée. J’ai une bonne raison d’avancer. » | `ego-boost` |
| 18 | « Aujourd’hui, même mon ombre cogne plus fort que toi. » | `ego-boost` |
| 19 | « Assez bavardé. Place au très gros problème. » | `hail-to-the-king` |
| 20 | « La couronne ? Je l’ai gagnée à coups de bottes. » | `hail-to-the-king` |

## Contrat public et intégration à réaliser

Le schéma `spells/1.1.0` ajoute les labels facultatifs `capability_tags`.
Le schéma `classes/1.1.0` ajoute `resource_kinds`, `role_tags` et
`specialization_tags`. Ce sont des classifications bornées, pas des instructions
exécutables. Les schémas 1.0.0 et tous les templates déjà publiés sont immuables.

Un futur adaptateur sélectionne les versions exactes, vérifie les checksums et
résout le bundle. Référence absente, label inconnu ou profil non lié : échec
explicite. Tous les chiffres d'équilibrage restent définis par le serveur.

L'ouverture de l'œuf vérifie possession et éligibilité et traite consommation
et déblocage de façon atomique et idempotente. Répétition et déconnexion ne
doivent ni perdre l'œuf ni dupliquer un droit. Le cas d'une classe déjà connue
doit être décidé avant toute intégration.

Le serveur lie portée, collision, immunités, boss, factions, règles PvP,
protections de zone, buffs dissipables, contrôle psychique, limites de gadgets,
grit et munitions. Une provocation PvE agit sur l'aggro; elle ne force jamais
la caméra ou la cible d'un autre joueur en PvP. Les debuffs PvP demandent un
profil distinct. Une bombe de saut sur allié nécessite son consentement.
La réflexion ne peut pas se réfléchir récursivement.

En VR, Chaingun Cyclone ne fait pas tourner le casque, et le flou de Steroids
est optionnel et désactivé par défaut. Punchlines et effets visuels demandent
des assets originaux ou des droits vérifiés. Les labels ne prouvent pas leur
disponibilité. Neutre/mercenaire décrit un profil de faction envisagé et ne
contourne aucune permission serveur.

La compatibilité demande des preuves séparées : parsing typé, liens, chargement
isolé, ouverture de l'œuf, acquisitions de talents et capacités dans le runtime.
La validation du registre ne prouve aucun de ces comportements de jeu.

## Vérification de publication

Les tests contrôlent la fermeture des 57 templates, les trois chaînes de douze
talents, les capacités de provocation, les checksums, l'absence de valeurs
autoritaires et les bornes des deux nouveaux schémas facultatifs.

```text
python -m unittest discover -s tests -v
python scripts/migrate_catalog_v2.py --check
python scripts/validate_registry.py
```

La CI de la pull request fournit la preuve publique de validation des données.
