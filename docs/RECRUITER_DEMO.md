# ClaimShield AI — parcours recruteur réel, environ 2 minutes

## Avant le rendez-vous

```powershell
.\scripts\start_backend.ps1
.\scripts\start_frontend.ps1
```

Ouvrir `http://127.0.0.1:5173`. Le parcours présenté utilise un audio réel enregistré au microphone ou importé localement et une transcription `faster-whisper` CPU.

## Parcours de test

1. **Tableau de bord (15 s)** — Montrer le pipeline, le statut du traitement local et l’avertissement sur les limites d’anonymisation.
2. **Nouveau sinistre (35 s)** — Cliquer `Nouveau sinistre`, puis `Enregistrer au micro`. Prononcer une déclaration courte avec des données fictives et cliquer `Arrêter et analyser`.
3. **Détection (25 s)** — Montrer `PERSON` et `PHONE_NUMBER`, l’origine `hybrid_rules`, les secondes audio et le statut de revue. Cliquer une entité pour voir sa région.
4. **Revue humaine (20 s)** — Désactiver une redaction, ajouter une région manuelle et expliquer la différence entre une décision automatique et une validation humaine.
5. **Redaction réelle (15 s)** — Choisir `Beep`, cliquer `Générer l’audio protégé`, puis télécharger le WAV. Le backend remplace réellement les samples, ce n’est pas un mute du player.
6. **Batch et évaluation (15 s)** — Ouvrir `Traitement batch` pour importer plusieurs audios réels, puis `Laboratoire IA` pour importer data/evaluation/sample_corpus.json et afficher WER/CER/précision-rappel PII. Ce fichier est un smoke corpus fictif : il valide le pipeline, mais ne sert pas à revendiquer une performance générale.

Le menu **Clients & contrats** présente la correspondance explicable et la confirmation humaine. **Preuves du dossier** permet de relire les segments et d’exporter l’audio/transcript protégé. **Paramètres** permet de choisir le modèle CPU, les limites de conservation et les options d’export.

Le navigateur encode l’audio en WAV localement ; aucune donnée microphone n’est envoyée ailleurs que vers le backend `127.0.0.1`.

## Message à retenir

ClaimShield illustre l’ingénierie de bout en bout : audio signal processing, ASR local `faster-whisper`, détection sensible, extraction de faits, preuves horodatées, revue humaine, export et limites mesurables. Il ne prend aucune décision de fraude, de responsabilité ou d’indemnisation.

