# VoiceShield → ClaimShield migration plan

## Existing functionality preserved

- FastAPI upload, local audio validation and waveform inspection.
- Optional faster-whisper CPU ASR path with word timestamps.
- Rule-based sensitive entity detection and explicit missing-alignment state.
- Sample-accurate WAV redaction with silence, beep and noise modes.
- React microphone capture converted to WAV locally.

## ClaimShield additions in this migration

- Claim domain schemas: facts, evidence links, event timeline and dossier.
- Automatic analysis after upload or microphone stop.
- Supported-language guardrail for French, English and Modern Standard Arabic.
- Conservative rule-based extraction for incident type, date/time, location, damages, estimates, vehicles, injuries, witnesses and police references.
- Neutral missing-information and contradiction flags.
- Policy metadata (`INTERNAL_CLAIM_REVIEW` by default) carried into redaction provenance.
- Claim dossier endpoint and JSON export.
- Evidence Explorer and Event Timeline cards on the results page.

## Intentionally not claimed yet

- Presidio/spaCy multilingual coverage is not installed by default.
- Arabic extraction patterns require a dedicated annotated validation set.
- Automatic number-word normalization and insurance identifier coverage remain experimental.
- SQLite persistence, batch ZIP processing and benchmark scores require their own validation pass.

This document prevents the automotive layer from masking the known limitations of the inherited VoiceShield pipeline.

