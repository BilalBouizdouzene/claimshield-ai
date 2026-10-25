import numpy as np

from backend.app.services_audio import redact_audio


def test_redaction_changes_only_requested_region():
    sample_rate = 1000
    source = np.linspace(-0.8, 0.8, sample_rate, dtype=np.float32)
    redacted = redact_audio(source, sample_rate, [(0.2, 0.4)], mode="silence", fade_ms=0)
    assert np.allclose(redacted[:200], source[:200])
    assert np.allclose(redacted[400:], source[400:])
    assert np.allclose(redacted[210:390], 0)


def test_redaction_preserves_shape_and_duration():
    source = np.zeros((2000, 2), dtype=np.float32)
    output = redact_audio(source, 1000, [(0.1, 0.5)], mode="beep")
    assert output.shape == source.shape

