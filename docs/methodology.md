# Méthodologie

ClaimShield conserve quatre niveaux de preuve :

1. le transcript et la langue retournés par l’ASR local ;
2. les spans texte et leur source de détection ;
3. les word timestamps associés, ou l’état `missing` quand aucune frontière fiable n’est disponible ;
4. la liste finale des régions approuvées avant export.

Les règles FR/EN sont un socle léger : elles privilégient le contexte explicite pour les noms et des formats structurés pour les emails, téléphones, IBAN, cartes et adresses. Elles ne remplacent pas un NER entraîné ni une validation humaine.

## Évaluation prévue

Le corpus doit comporter transcript, type d’entité, offsets texte, offsets audio vérifiés, langue, speaker ID et split. Les métriques prévues sont précision, rappel, F1, couverture temporelle, fuite résiduelle, durée de sur-masquage, erreur de frontière, WER/CER, préservation audio et real-time factor. Sans ces annotations, l’UI affiche `Not evaluated`.

