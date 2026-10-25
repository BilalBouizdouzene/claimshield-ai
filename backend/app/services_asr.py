from __future__ import annotations

import time
import uuid
from functools import lru_cache
from pathlib import Path

from .models import ASRSegment, ASRWord


@lru_cache(maxsize=3)
def _load_model(size: str):
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "faster-whisper n'est pas installé. Installez backend[asr] après validation du téléchargement du modèle, "
            "puis relancez l'analyse audio réelle."
        ) from exc
    return WhisperModel(size, device="cpu", compute_type="int8")


def transcribe(path: Path, model_name: str, language: str) -> tuple[list[ASRSegment], str, float, str]:
    """Run local faster-whisper when installed. No cloud fallback is used."""
    started = time.perf_counter()
    size = "tiny" if "tiny" in model_name else "base" if "base" in model_name else "small"
    model = _load_model(size)
    segments, info = model.transcribe(
        str(path), language=None if language == "auto" else language, word_timestamps=True
    )
    parsed: list[ASRSegment] = []
    for segment in segments:
        words = [
            ASRWord(
                id=f"w_{uuid.uuid4().hex[:10]}",
                text=w.word,
                start=w.start,
                end=w.end,
                confidence=getattr(w, "probability", None),
            )
            for w in (segment.words or [])
        ]
        parsed.append(
            ASRSegment(
                id=f"seg_{uuid.uuid4().hex[:10]}",
                text=segment.text.strip(),
                start=segment.start,
                end=segment.end,
                words=words,
            )
        )
    return parsed, getattr(info, "language", language), time.perf_counter() - started, f"faster-whisper/{size}-int8"

