from __future__ import annotations

import io
import math
import wave
from pathlib import Path

import numpy as np


def load_audio(path: Path) -> tuple[np.ndarray, int]:
    """Load audio as float32 [frames, channels]. SoundFile handles WAV/FLAC/OGG/MP3 when supported."""
    try:
        import soundfile as sf

        data, sample_rate = sf.read(path, always_2d=True, dtype="float32")
        return data, int(sample_rate)
    except Exception:
        with wave.open(str(path), "rb") as wav:
            channels = wav.getnchannels()
            width = wav.getsampwidth()
            sample_rate = wav.getframerate()
            raw = wav.readframes(wav.getnframes())
        if width != 2:
            raise ValueError("Le fallback WAV ne supporte que les échantillons PCM 16 bits.")
        values = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        return values.reshape(-1, channels), sample_rate


def write_wav(path: Path, data: np.ndarray, sample_rate: int) -> None:
    data = np.asarray(data, dtype=np.float32)
    if data.ndim == 1:
        data = data[:, None]
    clipped = np.clip(data, -1, 1)
    try:
        import soundfile as sf

        sf.write(path, clipped, sample_rate, subtype="PCM_16", format="WAV")
        return
    except Exception:
        pcm = (clipped * 32767).astype(np.int16).tobytes()
        with wave.open(str(path), "wb") as wav:
            wav.setnchannels(data.shape[1])
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(pcm)


def resample_mono(data: np.ndarray, sample_rate: int, target_rate: int = 16000) -> tuple[np.ndarray, int]:
    mono = data.mean(axis=1) if data.ndim == 2 else data
    if sample_rate == target_rate:
        return mono.astype(np.float32), sample_rate
    try:
        from scipy.signal import resample_poly

        gcd = math.gcd(sample_rate, target_rate)
        result = resample_poly(mono, target_rate // gcd, sample_rate // gcd)
    except Exception:
        old_x = np.linspace(0, 1, len(mono), endpoint=False)
        new_length = max(1, round(len(mono) * target_rate / sample_rate))
        new_x = np.linspace(0, 1, new_length, endpoint=False)
        result = np.interp(new_x, old_x, mono)
    return np.asarray(result, dtype=np.float32), target_rate


def inspect_audio(path: Path) -> tuple[dict, np.ndarray]:
    data, sample_rate = load_audio(path)
    frames = int(len(data))
    channels = int(data.shape[1]) if data.ndim == 2 else 1
    duration = frames / sample_rate if sample_rate else 0
    rms = float(np.sqrt(np.mean(np.square(data)))) if frames else 0.0
    clipped = int(np.sum(np.abs(data) >= 0.999))
    mono = data.mean(axis=1) if data.ndim == 2 else data
    bins = min(180, max(24, frames // max(1, sample_rate // 8)))
    chunks = np.array_split(np.abs(mono), bins)
    waveform = [float(np.max(chunk)) if len(chunk) else 0.0 for chunk in chunks]
    return {
        "duration_seconds": round(duration, 3),
        "sample_rate": sample_rate,
        "channels": channels,
        "frames": frames,
        "rms": round(rms, 6),
        "clipped_samples": clipped,
    }, data


def _fade(length: int, fade_samples: int) -> np.ndarray:
    if length <= 0:
        return np.ones(length, dtype=np.float32)
    fade = min(fade_samples, max(1, length // 2))
    envelope = np.ones(length, dtype=np.float32)
    if fade:
        envelope[:fade] = np.linspace(0, 1, fade, endpoint=False)
        envelope[-fade:] = np.linspace(1, 0, fade, endpoint=False)
    return envelope


def redact_audio(
    data: np.ndarray,
    sample_rate: int,
    regions: list[tuple[float, float]],
    mode: str = "beep",
    beep_frequency: float = 880.0,
    fade_ms: float = 12.0,
) -> np.ndarray:
    """Apply sample-accurate masking to every channel while preserving duration."""
    result = np.array(data, dtype=np.float32, copy=True)
    if result.ndim == 1:
        result = result[:, None]
    fade_samples = max(1, round(sample_rate * fade_ms / 1000))
    for raw_start, raw_end in regions:
        start = max(0, int(round(raw_start * sample_rate)))
        end = min(len(result), int(round(raw_end * sample_rate)))
        if end <= start:
            continue
        length = end - start
        t = np.arange(length, dtype=np.float32) / sample_rate
        if mode == "silence":
            mask = np.zeros(length, dtype=np.float32)
        elif mode == "noise":
            rng = np.random.default_rng(42 + start)
            mask = rng.normal(0, 0.08, size=length).astype(np.float32)
        else:
            mask = (0.2 * np.sin(2 * np.pi * beep_frequency * t)).astype(np.float32)
        mask *= _fade(length, fade_samples)
        result[start:end, :] = mask[:, None]
    return result if data.ndim == 2 else result[:, 0]

