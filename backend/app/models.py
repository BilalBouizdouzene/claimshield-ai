from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    uploaded = "uploaded"
    processing = "processing"
    ready = "ready"
    failed = "failed"
    approved = "approved"


class ProcessingStage(str, Enum):
    idle = "IDLE"
    recording = "RECORDING"
    audio_received = "AUDIO_RECEIVED"
    preprocessing = "PREPROCESSING"
    detecting_language = "DETECTING_LANGUAGE"
    transcribing = "TRANSCRIBING"
    detecting_sensitive_information = "DETECTING_SENSITIVE_INFORMATION"
    aligning_audio = "ALIGNING_AUDIO"
    applying_privacy_policy = "APPLYING_PRIVACY_POLICY"
    generating_protected_audio = "GENERATING_PROTECTED_AUDIO"
    extracting_claim_facts = "EXTRACTING_CLAIM_FACTS"
    building_event_timeline = "BUILDING_EVENT_TIMELINE"
    preparing_claim_dossier = "PREPARING_CLAIM_DOSSIER"
    ready_for_review = "READY_FOR_REVIEW"
    approved_for_export = "APPROVED_FOR_EXPORT"
    error = "ERROR"


class ReviewStatus(str, Enum):
    unreviewed = "unreviewed"
    needs_attention = "needs_attention"
    reviewed = "reviewed"
    approved = "approved"


class WorkflowStatus(str, Enum):
    draft = "DRAFT"
    awaiting_identity_review = "AWAITING_IDENTITY_REVIEW"
    awaiting_contract_review = "AWAITING_CONTRACT_REVIEW"
    awaiting_privacy_review = "AWAITING_PRIVACY_REVIEW"
    awaiting_evidence_review = "AWAITING_EVIDENCE_REVIEW"
    ready_for_human_examination = "READY_FOR_HUMAN_EXAMINATION"
    needs_more_information = "NEEDS_MORE_INFORMATION"
    review_blocked = "REVIEW_BLOCKED"
    archived = "ARCHIVED"


class MatchStatus(str, Enum):
    match_candidate = "MATCH_CANDIDATE"
    multiple_candidates = "MULTIPLE_CANDIDATES"
    no_match = "NO_MATCH"
    insufficient_information = "INSUFFICIENT_INFORMATION"
    conflicting_identifiers = "CONFLICTING_IDENTIFIERS"
    confirmed_by_reviewer = "MATCH_CONFIRMED_BY_REVIEWER"


class AudioMetadata(BaseModel):
    filename: str
    duration_seconds: float
    sample_rate: int
    channels: int
    frames: int
    format: str = "WAV"
    rms: float | None = None
    clipped_samples: int | None = None
    source: str = "upload"


class ASRWord(BaseModel):
    id: str
    text: str
    start: float | None = None
    end: float | None = None
    confidence: float | None = None


class ASRSegment(BaseModel):
    id: str
    text: str
    start: float | None = None
    end: float | None = None
    words: list[ASRWord] = Field(default_factory=list)


class AlignmentEvidence(BaseModel):
    method: str
    quality: str
    word_ids: list[str] = Field(default_factory=list)
    note: str | None = None


class DetectedEntity(BaseModel):
    id: str
    category: str
    text: str
    text_start: int
    text_end: int
    audio_start: float | None = None
    audio_end: float | None = None
    source: str
    confidence: float | None = None
    review_status: ReviewStatus = ReviewStatus.unreviewed
    redaction_enabled: bool = True
    alignment: AlignmentEvidence
    human_override: bool = False


class AudioRedactionRegion(BaseModel):
    id: str
    start: float
    end: float
    category: str = "CUSTOM_ENTITY"
    source: str = "automatic"
    enabled: bool = True
    review_status: ReviewStatus = ReviewStatus.unreviewed


class ProcessingMetrics(BaseModel):
    asr_seconds: float | None = None
    detection_seconds: float | None = None
    alignment_seconds: float | None = None
    redaction_seconds: float | None = None
    total_seconds: float | None = None
    real_time_factor: float | None = None


class EvidenceLink(BaseModel):
    text_start: int
    text_end: int
    audio_start: float | None = None
    audio_end: float | None = None
    quality: str = "missing"
    note: str | None = None


class ClaimFact(BaseModel):
    id: str
    field: str
    label: str
    value: str | int | float | None = None
    extraction_method: str = "rules"
    evidence_text: str | None = None
    evidence: EvidenceLink = Field(default_factory=lambda: EvidenceLink(text_start=0, text_end=0))
    verification_state: ReviewStatus = ReviewStatus.unreviewed
    status: str = "extracted"


class ClaimEvent(BaseModel):
    id: str
    label: str
    description: str
    relative_time: str | None = None
    absolute_time: str | None = None
    evidence_text: str | None = None
    evidence: EvidenceLink = Field(default_factory=lambda: EvidenceLink(text_start=0, text_end=0))
    uncertainty: str = "stated"
    conflicts_with: list[str] = Field(default_factory=list)


class CustomerCandidate(BaseModel):
    customer_id: str
    full_name: str
    customer_status: str
    match_status: MatchStatus = MatchStatus.match_candidate
    match_reasons: list[str] = Field(default_factory=list)
    matched_identifiers: list[str] = Field(default_factory=list)
    phone_masked: str | None = None
    email_masked: str | None = None
    policy_ids: list[str] = Field(default_factory=list)


class PolicyCandidate(BaseModel):
    policy_id: str
    policy_number: str
    insurance_product: str
    policy_status: str
    effective_start: str
    effective_end: str
    customer_id: str
    customer_name: str
    vehicle_id: str | None = None
    vehicle_label: str | None = None
    registration_number: str | None = None
    match_status: MatchStatus = MatchStatus.match_candidate
    match_reasons: list[str] = Field(default_factory=list)


class ReviewUpdate(BaseModel):
    workflow_status: WorkflowStatus | None = None
    note: str | None = None


class ClaimDossier(BaseModel):
    claim_id: str | None = None
    incident_summary: str | None = None
    facts: list[ClaimFact] = Field(default_factory=list)
    timeline: list[ClaimEvent] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    privacy_policy: str = "INTERNAL_CLAIM_REVIEW"
    review_status: ReviewStatus = ReviewStatus.unreviewed
    workflow_status: WorkflowStatus = WorkflowStatus.draft
    customer_status: MatchStatus = MatchStatus.insufficient_information
    policy_status: MatchStatus = MatchStatus.insufficient_information
    customer_candidates: list[CustomerCandidate] = Field(default_factory=list)
    policy_candidates: list[PolicyCandidate] = Field(default_factory=list)
    selected_customer_id: str | None = None
    selected_policy_id: str | None = None
    selected_vehicle_id: str | None = None
    reviewer_notes: list[str] = Field(default_factory=list)
    audit_history: list[dict[str, Any]] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProtectedTranscript(BaseModel):
    original: str
    protected: str
    replacements: int


class RedactionSettings(BaseModel):
    mode: str = "beep"
    beep_frequency: float = 880.0
    fade_ms: float = 12.0
    padding_ms: float = 80.0
    privacy_policy: str = "INTERNAL_CLAIM_REVIEW"


class RedactionJob(BaseModel):
    id: str
    status: JobStatus
    stage: ProcessingStage = ProcessingStage.idle
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "upload"
    language: str | None = None
    model: str
    audio: AudioMetadata
    segments: list[ASRSegment] = Field(default_factory=list)
    transcript: ProtectedTranscript | None = None
    entities: list[DetectedEntity] = Field(default_factory=list)
    regions: list[AudioRedactionRegion] = Field(default_factory=list)
    metrics: ProcessingMetrics = Field(default_factory=ProcessingMetrics)
    waveform: list[float] = Field(default_factory=list)
    redaction_settings: RedactionSettings = Field(default_factory=RedactionSettings)
    protected_audio_ready: bool = False
    error: str | None = None
    provenance: list[dict[str, Any]] = Field(default_factory=list)
    claim: ClaimDossier | None = None


class EntityPatch(BaseModel):
    category: str | None = None
    audio_start: float | None = None
    audio_end: float | None = None
    redaction_enabled: bool | None = None
    review_status: ReviewStatus | None = None


class ClaimFactPatch(BaseModel):
    value: str | int | float | None = None
    verification_state: ReviewStatus | None = None


class RegionCreate(BaseModel):
    start: float
    end: float
    category: str = "CUSTOM_ENTITY"


class RedactRequest(BaseModel):
    settings: RedactionSettings = Field(default_factory=RedactionSettings)


class AnalysisOptions(BaseModel):
    language: str = "auto"
    model: str = "whisper-base-int8"
    transcript_hint: str | None = None

