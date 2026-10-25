from __future__ import annotations

import json
import os
import shutil
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from .models import (
    AnalysisOptions, AudioRedactionRegion, ClaimFactPatch, DetectedEntity, EntityPatch, JobStatus,
    MatchStatus, RedactRequest, RedactionSettings, RedactionJob, RegionCreate, ReviewStatus,
    ReviewUpdate, WorkflowStatus,
    ASRSegment, AudioMetadata, ProcessingMetrics, ProcessingStage, ProtectedTranscript,
)
from .services_asr import transcribe
from .services_audio import inspect_audio, load_audio, redact_audio, write_wav
from .services_claim import extract_claim
from .services_pii import detect_entities, protected_transcript
from .services_matching import match_claim
from .services_evaluation import score_corpus
from .storage import delete as delete_stored_job, initialize as initialize_storage, list_jobs, load as load_stored_job, save as save_stored_job, search_customers, search_policies


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "data" / "runtime"
RUNTIME.mkdir(parents=True, exist_ok=True)
DB_PATH = RUNTIME / "claimshield.sqlite3"
initialize_storage(DB_PATH)
jobs: dict[str, RedactionJob] = {}

MAX_UPLOAD_BYTES = int(os.getenv("CLAIMSHIELD_MAX_UPLOAD_MB", "50")) * 1024 * 1024
MAX_AUDIO_SECONDS = int(os.getenv("CLAIMSHIELD_MAX_AUDIO_MINUTES", "15")) * 60
RETENTION_DAYS = int(os.getenv("CLAIMSHIELD_RETENTION_DAYS", "30"))
ALLOWED_EXTENSIONS = {".wav", ".flac", ".ogg", ".mp3", ".m4a"}
ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv(
    "CLAIMSHIELD_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174",
).split(",") if origin.strip()]

app = FastAPI(title="ClaimShield AI API", version="0.2.0", description="Local-first automotive claim evidence intelligence API")
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["Content-Type"], allow_credentials=False)


class EvaluationExample(BaseModel):
    reference: str = ""
    hypothesis: str = ""
    reference_entities: list[dict | str] = Field(default_factory=list)
    predicted_entities: list[dict | str] = Field(default_factory=list)


class EvaluationRequest(BaseModel):
    examples: list[EvaluationExample] = Field(min_length=1, max_length=10_000)


def _job_dir(job_id: str) -> Path:
    directory = RUNTIME / job_id
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _get(job_id: str) -> RedactionJob:
    if job_id not in jobs:
        stored = load_stored_job(DB_PATH, job_id)
        if stored:
            jobs[job_id] = stored
    if job_id not in jobs:
        raise HTTPException(404, "Session introuvable ou supprimée.")
    return jobs[job_id]


def _serialize(job: RedactionJob) -> dict:
    return job.model_dump(mode="json")


def _persist(job: RedactionJob) -> None:
    save_stored_job(DB_PATH, job)


def cleanup_expired_jobs() -> int:
    if RETENTION_DAYS <= 0:
        return 0
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    removed = 0
    for stored_job in list_jobs(DB_PATH):
        created_at = stored_job.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        if created_at >= cutoff:
            continue
        jobs.pop(stored_job.id, None)
        delete_stored_job(DB_PATH, stored_job.id)
        shutil.rmtree(RUNTIME / stored_job.id, ignore_errors=True)
        removed += 1
    return removed


cleanup_expired_jobs()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "claimshield-api", "local_processing": True, "version": app.version, "retention_days": RETENTION_DAYS}


@app.get("/api/models")
def models() -> dict:
    try:
        import faster_whisper  # noqa: F401
        asr_available = True
    except ImportError:
        asr_available = False
    return {"models": [
        {"id": "whisper-base-int8", "label": "Whisper base · CPU INT8", "available": asr_available, "mode": "fast", "default": True},
        {"id": "whisper-small-int8", "label": "Whisper small · CPU INT8", "available": asr_available, "mode": "quality"},
        {"id": "whisper-tiny-int8", "label": "Whisper tiny · CPU INT8", "available": asr_available, "mode": "light"},
    ], "asr_installed": asr_available, "supported_languages": ["fr", "en", "ar"], "note": "Les poids sont téléchargés uniquement par l'utilisateur via l'installation optionnelle."}


@app.post("/api/audio/upload")
async def upload_audio(file: UploadFile = File(...)) -> dict:
    filename = Path(file.filename or "audio.wav").name
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(415, "Format non supporté. Utilisez WAV, FLAC, OGG, MP3 ou M4A.")
    content = await file.read()
    if not content:
        raise HTTPException(422, "Le fichier audio est vide.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"Fichier trop volumineux (limite: {MAX_UPLOAD_BYTES // 1024 // 1024} Mo).")
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    directory = _job_dir(job_id)
    source_path = directory / f"source{suffix}"
    source_path.write_bytes(content)
    try:
        meta, _ = inspect_audio(source_path)
    except Exception as exc:
        shutil.rmtree(directory, ignore_errors=True)
        raise HTTPException(422, f"Audio illisible: {exc}") from exc
    if meta["duration_seconds"] > MAX_AUDIO_SECONDS:
        shutil.rmtree(directory, ignore_errors=True)
        raise HTTPException(413, f"Durée maximale dépassée ({MAX_AUDIO_SECONDS // 60} minutes).")
    audio = AudioMetadata(filename=filename, format=suffix[1:].upper(), source="upload", **meta)
    job = RedactionJob(id=job_id, status=JobStatus.uploaded, stage=ProcessingStage.audio_received, model="whisper-base-int8", audio=audio)
    jobs[job_id] = job
    _persist(job)
    return {"job": _serialize(job)}


@app.post("/api/audio/batch")
async def batch_audio(files: list[UploadFile] = File(...), model: str = "whisper-base-int8") -> dict:
    """Process a bounded list of local audio files sequentially."""
    if not files:
        raise HTTPException(422, "Ajoutez au moins un fichier audio.")
    if len(files) > 20:
        raise HTTPException(413, "La file batch est limitée à 20 fichiers par lancement.")
    results: list[dict] = []
    for file in files:
        try:
            uploaded = await upload_audio(file)
            job_id = uploaded["job"]["id"]
            analyzed = analyze_audio(job_id, AnalysisOptions(language="auto", model=model))
            results.append({"job": analyzed["job"], "status": "completed"})
        except HTTPException as exc:
            results.append({"filename": Path(file.filename or "audio").name, "status": "failed", "error": str(exc.detail)})
    return {"results": results, "completed": sum(item["status"] == "completed" for item in results), "failed": sum(item["status"] == "failed" for item in results)}


def _build_job_from_segments(job: RedactionJob, segments: list[ASRSegment], language: str, model: str, asr_seconds: float, source: str, privacy_policy: str = "INTERNAL_CLAIM_REVIEW") -> None:
    text = " ".join(segment.text for segment in segments).strip()
    words = [word for segment in segments for word in segment.words]
    job.stage = ProcessingStage.detecting_sensitive_information
    detection_start = time.perf_counter()
    entities = detect_entities(text, words, source="hybrid_rules")
    detection_seconds = time.perf_counter() - detection_start
    protected, replacements = protected_transcript(text, entities)
    regions: list[AudioRedactionRegion] = []
    job.stage = ProcessingStage.aligning_audio
    for entity in entities:
        if entity.audio_start is not None and entity.audio_end is not None:
            regions.append(AudioRedactionRegion(id=f"reg_{uuid.uuid4().hex[:10]}", start=entity.audio_start, end=entity.audio_end, category=entity.category))
    job.status = JobStatus.ready
    job.stage = ProcessingStage.preparing_claim_dossier
    job.source = source
    job.language = language
    job.model = model
    job.segments = segments
    job.entities = entities
    job.regions = regions
    job.transcript = ProtectedTranscript(original=text, protected=protected, replacements=replacements)
    job.claim = extract_claim(text, words, language, privacy_policy)
    job.claim.claim_id = f"CLM-{uuid.uuid4().hex[:8].upper()}"
    customer_candidates, policy_candidates = match_claim(text, entities, DB_PATH)
    job.claim.customer_candidates = customer_candidates
    job.claim.policy_candidates = policy_candidates
    job.claim.customer_status = customer_candidates[0].match_status if customer_candidates else MatchStatus.insufficient_information
    job.claim.policy_status = policy_candidates[0].match_status if policy_candidates else MatchStatus.insufficient_information
    job.claim.workflow_status = WorkflowStatus.awaiting_identity_review if customer_candidates else WorkflowStatus.needs_more_information
    job.claim.audit_history.append({"event": "claim_draft_created", "claim_id": job.claim.claim_id, "timestamp": time.time()})
    if customer_candidates:
        job.claim.reviewer_notes.append("Identité proposée par correspondance explicable ; confirmation humaine requise.")
    job.stage = ProcessingStage.ready_for_review
    job.metrics = ProcessingMetrics(asr_seconds=round(asr_seconds, 4), detection_seconds=round(detection_seconds, 4), total_seconds=round(asr_seconds + detection_seconds, 4), real_time_factor=round(asr_seconds / max(job.audio.duration_seconds, 0.001), 4))
    job.provenance.append({"event": "analysis_completed", "source": source, "model": model, "privacy_policy": privacy_policy, "timestamp": time.time()})
    _persist(job)


@app.post("/api/audio/analyze/{job_id}")
def analyze_audio(job_id: str, options: AnalysisOptions) -> dict:
    job = _get(job_id)
    if options.model not in {"whisper-base-int8", "whisper-small-int8", "whisper-tiny-int8"}:
        raise HTTPException(422, "Modèle Whisper non supporté.")
    directory = _job_dir(job_id)
    source_path = next(directory.glob("source.*"), None)
    if source_path is None:
        raise HTTPException(404, "Source audio introuvable.")
    job.status = JobStatus.processing
    job.stage = ProcessingStage.preprocessing
    try:
        job.stage = ProcessingStage.detecting_language
        segments, language, asr_seconds, model = transcribe(source_path, options.model, options.language)
        if language not in {"fr", "en", "ar"}:
            job.status = JobStatus.failed
            job.stage = ProcessingStage.error
            job.error = f"Langue détectée non supportée: {language}. Les langues supportées sont fr, en et ar."
            _persist(job)
            raise HTTPException(422, job.error)
        _build_job_from_segments(job, segments, language, model, asr_seconds, "asr")
    except HTTPException:
        raise
    except Exception as exc:
        job.status = JobStatus.failed
        job.stage = ProcessingStage.error
        job.error = str(exc)
        _persist(job)
        raise HTTPException(503, str(exc)) from exc
    return {"job": _serialize(job)}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    return {"job": _serialize(_get(job_id))}


@app.get("/api/jobs/{job_id}/claim")
def get_claim(job_id: str) -> dict:
    job = _get(job_id)
    return {"claim": job.claim.model_dump(mode="json") if job.claim else None}


@app.get("/api/claims")
def list_claims(query: str = "", workflow_status: str | None = None) -> dict:
    """Return persisted local claim drafts for the Claims Workspace."""
    jobs_found = []
    for stored_job in list_jobs(DB_PATH):
        # Ignore legacy records created before the real-audio workflow.
        # They may remain in the local database for backward compatibility, but
        # never presented as real claims in the user interface.
        if stored_job.source == "synthetic_demo":
            continue
        if not stored_job.claim:
            continue
        claim = stored_job.claim
        haystack = f"{claim.claim_id} {stored_job.audio.filename} {claim.incident_summary or ''}".lower()
        if query.strip().lower() not in haystack:
            continue
        if workflow_status and claim.workflow_status.value != workflow_status:
            continue
        jobs_found.append({"job": _serialize(stored_job), "claim": claim.model_dump(mode="json")})
    counts = {
        "total": len(jobs_found),
        "awaiting_identity_review": sum(item["claim"]["workflow_status"] == WorkflowStatus.awaiting_identity_review.value for item in jobs_found),
        "matched_contracts": sum(item["claim"]["selected_policy_id"] is not None for item in jobs_found),
        "awaiting_privacy_review": sum(item["claim"]["workflow_status"] == WorkflowStatus.awaiting_privacy_review.value for item in jobs_found),
        "ready_for_human_examination": sum(item["claim"]["workflow_status"] == WorkflowStatus.ready_for_human_examination.value for item in jobs_found),
    }
    return {"claims": jobs_found, "metrics": counts}


@app.get("/api/claims/metrics")
def claim_metrics() -> dict:
    return list_claims()["metrics"]


@app.get("/api/claims/{claim_id}")
def get_claim_by_reference(claim_id: str) -> dict:
    stored_job = next((item for item in list_jobs(DB_PATH) if item.claim and item.claim.claim_id == claim_id), None)
    if not stored_job:
        raise HTTPException(404, "Dossier de sinistre introuvable.")
    return {"job": _serialize(stored_job)}


@app.get("/api/customers/search")
def customers_search(q: str = "") -> dict:
    return {"customers": search_customers(DB_PATH, q)}


@app.get("/api/policies/search")
def policies_search(q: str = "") -> dict:
    return {"policies": search_policies(DB_PATH, q)}


@app.patch("/api/jobs/{job_id}/claim/facts/{fact_id}")
def patch_claim_fact(job_id: str, fact_id: str, patch: ClaimFactPatch) -> dict:
    job = _get(job_id)
    if not job.claim:
        raise HTTPException(409, "Le dossier de sinistre n'est pas encore disponible.")
    fact = next((item for item in job.claim.facts if item.id == fact_id), None)
    if not fact:
        raise HTTPException(404, "Fait de sinistre introuvable.")
    updates = patch.model_dump(exclude_none=True)
    for key, value in updates.items():
        setattr(fact, key, value)
    fact.status = "reviewed"
    job.claim.review_status = ReviewStatus.reviewed
    _persist(job)
    return {"job": _serialize(job)}


@app.post("/api/jobs/{job_id}/matching/customer/{customer_id}/confirm")
def confirm_customer(job_id: str, customer_id: str) -> dict:
    job = _get(job_id)
    if not job.claim:
        raise HTTPException(409, "Le dossier de sinistre n'est pas encore disponible.")
    candidate = next((item for item in job.claim.customer_candidates if item.customer_id == customer_id), None)
    if not candidate:
        raise HTTPException(404, "Candidat client introuvable dans ce dossier.")
    candidate.match_status = MatchStatus.confirmed_by_reviewer
    job.claim.selected_customer_id = customer_id
    job.claim.customer_status = MatchStatus.confirmed_by_reviewer
    job.claim.workflow_status = WorkflowStatus.awaiting_contract_review
    job.claim.audit_history.append({"event": "customer_confirmed", "customer_id": customer_id, "timestamp": time.time()})
    _persist(job)
    return {"job": _serialize(job)}


@app.post("/api/jobs/{job_id}/matching/policy/{policy_id}/confirm")
def confirm_policy(job_id: str, policy_id: str) -> dict:
    job = _get(job_id)
    if not job.claim:
        raise HTTPException(409, "Le dossier de sinistre n'est pas encore disponible.")
    candidate = next((item for item in job.claim.policy_candidates if item.policy_id == policy_id), None)
    if not candidate:
        raise HTTPException(404, "Candidat contrat introuvable dans ce dossier.")
    candidate.match_status = MatchStatus.confirmed_by_reviewer
    job.claim.selected_policy_id = policy_id
    job.claim.selected_vehicle_id = candidate.vehicle_id
    job.claim.policy_status = MatchStatus.confirmed_by_reviewer
    job.claim.workflow_status = WorkflowStatus.awaiting_privacy_review
    job.claim.audit_history.append({"event": "policy_confirmed", "policy_id": policy_id, "timestamp": time.time()})
    _persist(job)
    return {"job": _serialize(job)}


@app.patch("/api/jobs/{job_id}/review")
def update_review(job_id: str, update: ReviewUpdate) -> dict:
    job = _get(job_id)
    if not job.claim:
        raise HTTPException(409, "Le dossier de sinistre n'est pas encore disponible.")
    if update.workflow_status is not None:
        job.claim.workflow_status = update.workflow_status
    if update.note and update.note.strip():
        job.claim.reviewer_notes.append(update.note.strip())
    job.claim.audit_history.append({"event": "review_updated", "workflow_status": job.claim.workflow_status.value, "timestamp": time.time()})
    _persist(job)
    return {"job": _serialize(job)}


@app.get("/api/jobs/{job_id}/events")
def job_events(job_id: str) -> StreamingResponse:
    job = _get(job_id)
    payload = "data: " + json.dumps({"status": job.status, "stage": job.stage, "error": job.error}) + "\n\n"
    return StreamingResponse(iter([payload]), media_type="text/event-stream")


@app.patch("/api/jobs/{job_id}/entities/{entity_id}")
def patch_entity(job_id: str, entity_id: str, patch: EntityPatch) -> dict:
    job = _get(job_id)
    entity = next((item for item in job.entities if item.id == entity_id), None)
    if entity is None:
        raise HTTPException(404, "Entité introuvable.")
    updates = patch.model_dump(exclude_none=True)
    for key, value in updates.items():
        setattr(entity, key, value)
    entity.human_override = True
    job.status = JobStatus.ready
    job.provenance.append({"event": "entity_updated", "entity_id": entity_id, "changes": updates, "timestamp": time.time()})
    _persist(job)
    return {"job": _serialize(job)}


@app.post("/api/jobs/{job_id}/regions")
def add_region(job_id: str, payload: RegionCreate) -> dict:
    job = _get(job_id)
    if payload.start < 0 or payload.end <= payload.start or payload.end > job.audio.duration_seconds + 0.01:
        raise HTTPException(422, "Intervalle audio invalide.")
    region = AudioRedactionRegion(id=f"reg_{uuid.uuid4().hex[:10]}", start=payload.start, end=payload.end, category=payload.category, source="manual", review_status=ReviewStatus.needs_attention)
    job.regions.append(region)
    job.provenance.append({"event": "manual_region_added", "region_id": region.id, "timestamp": time.time()})
    _persist(job)
    return {"job": _serialize(job)}


@app.delete("/api/jobs/{job_id}/regions/{region_id}")
def delete_region(job_id: str, region_id: str) -> dict:
    job = _get(job_id)
    before = len(job.regions)
    job.regions = [region for region in job.regions if region.id != region_id]
    if len(job.regions) == before:
        raise HTTPException(404, "Région introuvable.")
    _persist(job)
    return {"job": _serialize(job)}


@app.post("/api/jobs/{job_id}/redact")
def redact(job_id: str, payload: RedactRequest) -> dict:
    job = _get(job_id)
    source_path = next(_job_dir(job_id).glob("source.*"), None)
    if source_path is None:
        raise HTTPException(404, "Source audio introuvable.")
    enabled = [(region.start - payload.settings.padding_ms / 1000, region.end + payload.settings.padding_ms / 1000) for region in job.regions if region.enabled]
    job.stage = ProcessingStage.generating_protected_audio
    started = time.perf_counter()
    data, sample_rate = load_audio(source_path)
    redacted = redact_audio(data, sample_rate, enabled, payload.settings.mode, payload.settings.beep_frequency, payload.settings.fade_ms)
    output = _job_dir(job_id) / "protected.wav"
    write_wav(output, redacted, sample_rate)
    job.redaction_settings = payload.settings
    if job.claim:
        job.claim.privacy_policy = payload.settings.privacy_policy
    job.protected_audio_ready = True
    job.metrics.redaction_seconds = round(time.perf_counter() - started, 4)
    job.status = JobStatus.ready
    job.stage = ProcessingStage.ready_for_review
    job.provenance.append({"event": "redaction_exported", "mode": payload.settings.mode, "region_count": len(enabled), "timestamp": time.time()})
    _persist(job)
    return {"job": _serialize(job)}


@app.post("/api/jobs/{job_id}/approve")
def approve(job_id: str) -> dict:
    job = _get(job_id)
    if not job.protected_audio_ready:
        raise HTTPException(409, "Générez d'abord l'audio protégé.")
    for entity in job.entities:
        entity.review_status = ReviewStatus.approved
    for region in job.regions:
        region.review_status = ReviewStatus.approved
    job.status = JobStatus.approved
    job.stage = ProcessingStage.approved_for_export
    _persist(job)
    return {"job": _serialize(job)}


def _download(job_id: str, filename: str, media_type: str) -> FileResponse:
    _get(job_id)
    path = _job_dir(job_id) / filename
    if not path.exists():
        raise HTTPException(404, "Export indisponible.")
    return FileResponse(path, media_type=media_type, filename=filename)


def _protected_string(value: str, replacements: list[tuple[str, str]]) -> str:
    result = value
    for raw, placeholder in sorted(replacements, key=lambda item: len(item[0]), reverse=True):
        if raw:
            result = result.replace(raw, placeholder)
    return result


def _protected_value(value: object, replacements: list[tuple[str, str]]) -> object:
    if isinstance(value, str):
        return _protected_string(value, replacements)
    if isinstance(value, list):
        return [_protected_value(item, replacements) for item in value]
    if isinstance(value, dict):
        return {key: _protected_value(item, replacements) for key, item in value.items()}
    return value


def _protected_report(job: RedactionJob) -> dict:
    report = _serialize(job)
    replacements = [
        (entity["text"], f"[{entity['category'].replace('_', ' ')}]")
        for entity in report.get("entities", [])
        if entity.get("text")
    ]
    report = _protected_value(report, replacements)
    report["export_policy"] = "protected_review_export"
    report["audio"]["filename"] = "protected-audio.wav"
    report["transcript"] = {
        "protected": job.transcript.protected if job.transcript else "",
        "replacements": job.transcript.replacements if job.transcript else 0,
    }
    for entity in report.get("entities", []):
        entity["text"] = f"[{entity['category'].replace('_', ' ')}]"
    return report


@app.get("/api/jobs/{job_id}/download/audio")
def download_audio(job_id: str) -> FileResponse:
    return _download(job_id, "protected.wav", "audio/wav")


@app.get("/api/jobs/{job_id}/download/transcript")
def download_transcript(job_id: str) -> FileResponse:
    job = _get(job_id)
    path = _job_dir(job_id) / "protected-transcript.txt"
    path.write_text((job.transcript.protected if job.transcript else ""), encoding="utf-8")
    return FileResponse(path, media_type="text/plain", filename="protected-transcript.txt")


@app.get("/api/jobs/{job_id}/download/report")
def download_report(job_id: str) -> FileResponse:
    path = _job_dir(job_id) / "audit-report.json"
    report = _protected_report(_get(job_id))
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return FileResponse(path, media_type="application/json", filename="audit-report.json")


@app.get("/api/jobs/{job_id}/download/claim")
def download_claim(job_id: str) -> FileResponse:
    job = _get(job_id)
    if not job.claim:
        raise HTTPException(404, "Dossier de sinistre indisponible.")
    path = _job_dir(job_id) / "claim-dossier.json"
    protected_claim = _protected_report(job).get("claim")
    path.write_text(json.dumps(protected_claim, ensure_ascii=False, indent=2), encoding="utf-8")
    return FileResponse(path, media_type="application/json", filename="claim-dossier.json")


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str) -> dict:
    _get(job_id)
    jobs.pop(job_id, None)
    delete_stored_job(DB_PATH, job_id)
    shutil.rmtree(_job_dir(job_id), ignore_errors=True)
    return {"deleted": True}


@app.get("/api/evaluation/results")
def evaluation_results() -> dict:
    return {"status": "not_evaluated", "message": "Aucun corpus annoté n'est configuré. Les métriques ne sont pas inventées.", "metrics": []}


@app.post("/api/evaluation/score")
def evaluation_score(payload: EvaluationRequest) -> dict:
    try:
        result = score_corpus([item.model_dump() for item in payload.examples])
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {"status": "evaluated", "metrics": result}

