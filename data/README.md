# Local data

Les fichiers d’exécution, audios et exports générés sont ignorés par Git. Utilisez uniquement des enregistrements consentis ou des fixtures fictives locales, jamais des données personnelles dans un commit. Le parcours de l’interface n’utilise pas d’audio synthétique : il attend un enregistrement microphone ou un fichier importé. Le catalogue client/contrat de test reste fictif et sert uniquement à vérifier le matching explicable.

Pour vérifier le Laboratoire IA, importez data/evaluation/sample_corpus.json. Il contient deux exemples textuels fictifs et doit uniquement valider le fonctionnement de l’écran et de l’endpoint d’évaluation ; ses scores ne sont pas un benchmark ASR ou PII.

