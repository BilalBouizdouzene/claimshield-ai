# Sécurité et confidentialité

- Le backend se lie à `127.0.0.1` par défaut et ne prend aucun chemin utilisateur arbitraire.
- Les IDs de session sont opaques et les fichiers sont stockés sous `data/runtime/<job_id>`.
- Les extensions, la taille et la durée maximale sont configurables par variables d’environnement ; les noms de fichiers sont normalisés avant stockage.
- Les exports `report` et `claim` remplacent les textes sensibles par des catégories (`[PERSON]`, `[PHONE_NUMBER]`, etc.) et ne sont pas des copies brutes de la session.
- Le transcript protégé est séparé de la source originale ; l’audio protégé est produit par réécriture WAV réelle.
- Les logs et noms d’export par défaut ne contiennent pas le transcript brut.
- La suppression d’un job supprime ses artefacts locaux ; la rétention automatique au démarrage est configurable avec `CLAIMSHIELD_RETENTION_DAYS`.
- CORS est limité aux origines configurées avec `CLAIMSHIELD_ALLOWED_ORIGINS` et les credentials navigateur sont désactivés par défaut.
- Le batch est séquentiel et limité à 20 fichiers par lancement pour éviter une charge locale non bornée.
- Aucun audio n’est envoyé à un service externe.

Risques résiduels : le processus local et les permissions du poste Windows restent dans le périmètre de confiance ; les règles peuvent manquer des entités ; l’audio original reste présent dans le runtime tant que la session n’est pas supprimée ; le speaker embedding, le contexte et les effets de bord ne sont pas neutralisés. Ne pas utiliser ce prototype comme preuve de conformité réglementaire.

