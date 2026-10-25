import json

from backend.app.main import _protected_report
from backend.app.models import AlignmentEvidence, AudioMetadata, ClaimDossier, DetectedEntity, ProtectedTranscript, RedactionJob, JobStatus
from backend.app.services_evaluation import cer, entity_metrics, score_corpus, wer


def test_asr_metrics_are_reproducible():
    assert wer("bonjour le monde", "bonjour le monde") == 0.0
    assert wer("bonjour le monde", "bonjour monde") == 1 / 3
    assert cer("abc", "abx") == 1 / 3


def test_pii_metrics_use_exact_category_and_value_matching():
    result = entity_metrics(
        [{"category": "PHONE_NUMBER", "text": "0612345678"}, {"category": "PERSON", "text": "Alice"}],
        [{"category": "PHONE_NUMBER", "text": "0612345678"}, {"category": "EMAIL", "text": "a@example.test"}],
    )
    assert result["true_positive"] == 1
    assert result["precision"] == 0.5
    assert result["recall"] == 0.5
    assert score_corpus([{"reference": "bonjour", "hypothesis": "bonjour"}])["examples"] == 1


def test_protected_export_does_not_contain_raw_entity_text():
    entity = DetectedEntity(
        id="ent_1", category="PERSON", text="Alice Martin", text_start=0, text_end=12,
        source="test", alignment=AlignmentEvidence(method="test", quality="high"),
    )
    job = RedactionJob(
        id="job_test", status=JobStatus.ready, model="faster-whisper/base-int8",
        audio=AudioMetadata(filename="alice-call.wav", duration_seconds=1, sample_rate=16_000, channels=1, frames=16_000),
        transcript=ProtectedTranscript(original="Bonjour Alice Martin", protected="Bonjour [PERSON]", replacements=1),
        entities=[entity], claim=ClaimDossier(incident_summary="Alice Martin a déclaré un accident."),
    )
    serialized = json.dumps(_protected_report(job), ensure_ascii=False)
    assert "Alice Martin" not in serialized
    assert "alice-call.wav" not in serialized
    assert "[PERSON]" in serialized
