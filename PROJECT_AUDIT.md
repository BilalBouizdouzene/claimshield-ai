# Project audit — ClaimShield AI

Date : 2026-10-24  
Environnement ciblé : Windows 10/11, Python 3.11+, Node.js LTS, CPU.

## Statut

| Domaine | Statut | Preuve |
|---|---|---|
| App shell React + FastAPI | IMPLEMENTED_AND_TESTED | build frontend, import FastAPI et smoke API validés |
| Microphone → WAV local | IMPLEMENTED_AND_TESTED | capture navigateur, encodage WAV local et upload validés |
| Claim facts / evidence links | IMPLEMENTED_AND_TESTED | `backend/app/services_claim.py` + smoke dossier |
| Event timeline / missing fields | IMPLEMENTED_AND_TESTED | dossier ClaimShield conservateur + démo |
| SQLite job metadata | IMPLEMENTED_AND_TESTED | reload de session validé via smoke API |
| Catalogue clients / véhicules / contrats fictifs | IMPLEMENTED_AND_TESTED | SQLite seed idempotent + matching candidat |
| Matching expliqué et confirmation humaine | IMPLEMENTED_AND_TESTED | candidats multiples, confirmation client/contrat, workflow |
| Claims workspace / dashboard de revue | IMPLEMENTED_AND_TESTED | navigation interactive validée dans le navigateur local |
| Supported-language guardrail | IMPLEMENTED_AND_TESTED | fr / en / ar only |
| Health / models / upload API | IMPLEMENTED_AND_TESTED | endpoints dans `backend/app/main.py` |
| Détection règles FR/EN | IMPLEMENTED_AND_TESTED | `backend/tests/test_pii.py` |
| Alignement word timestamps | IMPLEMENTED_AND_TESTED | statut missing explicite + tests |
| Redaction WAV silence/beep/noise | IMPLEMENTED_AND_TESTED | `backend/tests/test_audio.py` |
| Démo synthétique | NOT_USED_IN_UI | le parcours produit utilise uniquement un audio importé ou enregistré ; le catalogue reste fictif |
| faster-whisper | IMPLEMENTED_AND_TESTED | dépendance installée dans `.venv-claimshield`, CPU INT8 validé |
| Presidio/spaCy | NOT_IMPLEMENTED | extension prévue, non revendiquée |
| Batch audio réel | IMPLEMENTED_AND_TESTED | endpoint séquentiel `/api/audio/batch`, erreurs par fichier |
| Corpus / benchmarks | PARTIAL_AND_EXPLICIT | WER/CER/PII disponibles sur corpus fourni ; aucun score inventé sans annotations |
| Arabic / Darija | GUARDRAIL_ONLY | arabe accepté comme langue, couverture de règles limitée ; Darija non supporté |

## Commandes de validation

```powershell
.\.venv-claimshield\Scripts\python.exe -m pytest backend/tests -q
cd frontend; npm install; npm run build
```

Résultats observés dans cet environnement :

- `npm install` : PASS, 69 packages installés avec versions compatibles.
- `npm run build` : PASS, TypeScript compilé et bundle Vite ClaimShield produit.
- `Invoke-WebRequest http://127.0.0.1:5173/` : PASS, HTTP 200.
- `python -m pytest backend/tests -q` : PASS, 14 tests ; un avertissement de dépréciation Starlette/httpx reste à traiter.
- Smoke test FastAPI / redaction WAV / reload SQLite / claim extraction / matching : PASS.
- Parcours navigateur local : PASS, enregistrement/import réel, confirmation client, association contrat, batch, laboratoire et paramètres.

## Go / no-go

**Go pour une démonstration portfolio de l’interface, du traitement audio local, du dossier de sinistre, de la redaction WAV, du batch et de l’évaluation sur corpus fourni. No-go pour un usage de production, une revendication d’anonymisation, un score généralisé sans corpus représentatif ou une certification de conformité.**

