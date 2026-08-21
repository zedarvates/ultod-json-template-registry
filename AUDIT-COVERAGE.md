# Couverture de l'audit des templates

Ce rapport agrégé suit l'inventaire exhaustif sans publier les chemins sensibles des fichiers exclus.

- Copies analysées : 8092
- Chemins relatifs uniques : 4083
- Candidats serveur courants : 4009
- Entrées du catalogue public : 4027
- Candidats couverts par une empreinte publiée : 1180
- Candidats couverts par adaptation publique originale : 2829
- Candidats comptabilisés au total : 4009
- Candidats restant à traiter : 0
- Candidats encore en attente d'audit : 0
- Chemins multisources divergents : 95
- JSON invalides : 0
- Gitleaks : historique propre sur les trois sources ; binaire indisponible pour le registre actuel, scan ciblé de secrets propre

Le détail machine-readable par famille se trouve dans `AUDIT-COVERAGE.json`. `pending-review` ne signifie ni sûr ni exclu : la famille doit encore être auditée.

Les 2 847 entrées qui ne correspondent pas à une empreinte source courante regroupent des adaptations originales et des versions historiques. Les 2 829 sources non couvertes par snapshot sont toutes reliées à une adaptation publique originale par empreinte SHA-256 privée. Quarante-quatre entrées legacy exposant encore des contrôles internes ou des références tierces ont été retirées, puis les seize sources réellement concernées ont reçu une adaptation de remplacement. Aucun chemin ou nom source sensible n'est publié par les adaptations hashées.
