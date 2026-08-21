# Couverture de l'audit des templates

Ce rapport agrégé suit l'inventaire exhaustif sans publier les chemins sensibles des fichiers exclus.

- Copies analysées : 8092
- Chemins relatifs uniques : 4083
- Candidats serveur courants : 4009
- Entrées du catalogue public : 4063
- Candidats couverts par une empreinte publiée : 1174
- Candidats couverts par référence source historique : 710
- Candidats exportés comme templates sémantiques assainis : 2125
- Candidats comptabilisés au total : 4009
- Candidats restant à traiter : 0
- Candidats encore en attente d'audit : 0
- Chemins multisources divergents : 95
- JSON invalides : 0
- Gitleaks : historique propre sur les trois sources ; scan ciblé du registre actuel propre

Le détail machine-readable par famille se trouve dans `AUDIT-COVERAGE.json`. `pending-review` ne signifie ni sûr ni exclu : la famille doit encore être auditée.

Les exports du 21 août 2026 conservent les structures utiles (statistiques, propriétés, effets, loot, IA, recettes et règles déclaratives) tout en retirant les contrôles administratifs, données commerciales, chemins internes et références tierces détectées. Les noms sont sémantiques et lisibles ; aucun dossier `original-…-<hash>` n'est publié.
