# Registre de contenu : relations, découverte et styles

Cette note évalue des pistes d’évolution. Elle ne modifie aucun contrat publié et ne déclare aucune intégration cliente ou serveur.

## État actuel

Le [contrat strict](../TEMPLATE-SPEC.md) définit déjà une identité `famille:slug`, une version et des dépendances exactes `famille:slug@version`. Le [catalogue et son validateur](../scripts/registry_catalog.py) indexent ces références et contrôlent notamment les dépendances manquantes et certains liens de remplacement. Les données historiques `legacy-unvalidated` ne bénéficient pas des mêmes garanties. Ce graphe n’établit pas que tout contenu historique est relié ou utilisable par un consommateur.

Les champs `intended_consumers` sont des intentions ; `compatibility` reste vide tant que chaque combinaison consommateur/version n’a pas ses preuves. Les versions publiées restent immuables. Le serveur conserve l’autorité sur les règles de jeu.

## Pistes à instruire

1. **Découverte machine** : construire une vue dérivée et régénérable à partir du catalogue et des contrats, conservant profils, références exactes, catégories et tags réellement déclarés. Signaler les champs absents ; ne pas inventer d’identité pour les éléments historiques ou hors catalogue.
2. **Graphe** : exposer les liens déjà validés et leurs versions ; distinguer dépendance obligatoire, remplacement et association de découverte. Mesurer les références non résolues et étudier séparément la politique des cycles de dépendances, qui n’est pas garantie par le seul contrôle des alias.
3. **Styles** : le [schéma styles v1](../templates/schemas/styles/v1.0.0/schema.json) accepte uniquement `display_name` et `applies_to_tag` dans `spec`. Matériaux, couleurs, toits, symboles et étiquettes audio ou PNJ demandent un nouveau schéma versionné et des références vérifiables ; ne pas les ajouter aux versions existantes. Les noms de styles proposés sont des idées à documenter avec leurs auteurs, pas des identités déjà officielles.
4. **Provenance et qualité** : conserver source et droits vérifiés par élément. Un modèle d’IA d’origine n’est pertinent que s’il est connu et utile ; un score de qualité chiffré exige une méthode, des critères et des preuves. L’absence de preuve ne doit jamais devenir une note ou une compatibilité inventée.
5. **Référence dessin** : utiliser les aperçus pour proposer des candidats, puis laisser l’auteur confirmer et versionner sa recette. Toute recherche automatique par image et toute reconstruction restent à implémenter et qualifier séparément.

Les modèles modernes de l’atelier ont actuellement le même `id` interne et ne font pas partie du catalogue strict. Les distinguer par chemin ne les transforme pas en deux identités canoniques ; une migration explicite est nécessaire avant leur indexation comme contrats.
