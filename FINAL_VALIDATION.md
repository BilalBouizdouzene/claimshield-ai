# Final validation — ClaimShield AI

Ce fichier est la checklist de sortie et doit être mis à jour après chaque installation locale.

## À valider

- [x] API démarre sur `127.0.0.1:8000`.
- [x] Frontend démarre sur `127.0.0.1:5173`.
- [x] `GET /api/health` retourne `status=ok`.
- [x] Le parcours réel ouvre une session à partir d’un audio importé et affiche des timestamps explicites.
- [x] Le moteur exporte un WAV dont les samples des régions changent.
- [x] Les samples hors régions restent égaux dans la tolérance du codec.
- [x] Le transcript protégé ne contient pas les valeurs sensibles.
- [x] Le téléchargement JSON ne contient pas de chemin absolu externe.
- [x] La suite pytest passe (14 tests).
- [x] Le build TypeScript passe.
- [x] Un test réel avec faster-whisper/base-int8 est exécuté après installation volontaire du modèle.
- [x] Le même audio réel est comparé avec faster-whisper/small-int8.
- [x] L’endpoint d’évaluation refuse un corpus vide et calcule WER/CER/PII sur un corpus fourni.
- [x] Une déclaration audio réelle produit un dossier avec faits, candidats client/contrat et preuves audio.
- [x] Les langues détectées hors `fr`, `en`, `ar` sont bloquées en revue humaine.

## Résultats connus

Validé dans cette session : build frontend TypeScript/Vite, compilation Python, 14 tests backend, smoke FastAPI, redaction WAV, exports protégés, limites d’upload, rétention locale, reload SQLite, matching client/contrat, batch réel et parcours navigateur local du dossier ClaimShield. Un seul fichier public permet déjà d’observer WER/CER, mais il ne constitue pas un benchmark représentatif et ne contient pas d’annotations PII. Les scores de précision, rappel, F1, leakage rate, extraction de faits et alignement restent donc non revendiqués pour le produit tant qu’un corpus représentatif annoté n’est pas fourni. L’endpoint de laboratoire permet de calculer ces métriques sur un corpus explicitement importé.

## Test audio public exécuté

- Source : petit fichier français public téléchargé dans `data/runtime/external_corpus`, conservé hors Git.
- Entrée : MP3, 34,429 secondes, mono, 44 100 Hz.
- Modèle : `faster-whisper/base-int8`, langue détectée `fr`.
- ASR : 19,2165 secondes, facteur temps réel `0,5581`, session `READY_FOR_REVIEW`.
- Comparaison avec le texte de référence fourni par le corpus : WER `0,292683`, CER `0,198261`.
- Comparaison `small-int8` sur le même fichier : 45,467 secondes, facteur temps réel `1,3206`, WER `0,304878`, CER `0,201739`.
- Décision locale : conserver `base-int8` par défaut pour ce prototype ; `small-int8` est disponible comme option qualité, mais ce test ne montre aucun gain et double environ le temps de traitement.
- Batch réel : 1 fichier terminé, 0 erreur.
- Redaction réelle : région manuelle 1,0–2,0 s, WAV protégé généré et téléchargé avec HTTP 200.
- PII : non évaluée sur ce corpus, car il ne contient pas d’annotations PII ; aucun score PII n’est revendiqué.

