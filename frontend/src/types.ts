export type Page = 'overview' | 'studio' | 'claims' | 'matching' | 'results' | 'batch' | 'evaluation' | 'searches' | 'statistics' | 'settings' | 'about'

export type Entity = {
  id: string
  category: string
  text: string
  text_start: number
  text_end: number
  audio_start: number | null
  audio_end: number | null
  source: string
  confidence: number | null
  review_status: 'unreviewed' | 'needs_attention' | 'reviewed' | 'approved'
  redaction_enabled: boolean
  human_override: boolean
  alignment: { method: string; quality: string; word_ids: string[]; note?: string }
}

export type Region = {
  id: string
  start: number
  end: number
  category: string
  source: string
  enabled: boolean
  review_status: string
}

export type ClaimFact = {
  id: string
  field: string
  label: string
  value: string | number | null
  extraction_method: string
  evidence_text: string | null
  evidence: { text_start: number; text_end: number; audio_start: number | null; audio_end: number | null; quality: string; note?: string | null }
  verification_state: string
  status: string
}

export type ClaimEvent = {
  id: string
  label: string
  description: string
  relative_time: string | null
  absolute_time: string | null
  evidence_text: string | null
  evidence: { text_start: number; text_end: number; audio_start: number | null; audio_end: number | null; quality: string; note?: string | null }
  uncertainty: string
  conflicts_with: string[]
}

export type ClaimDossier = {
  claim_id: string | null
  incident_summary: string | null
  facts: ClaimFact[]
  timeline: ClaimEvent[]
  missing_information: string[]
  contradictions: string[]
  privacy_policy: string
  review_status: string
  workflow_status: string
  customer_status: string
  policy_status: string
  customer_candidates: CustomerCandidate[]
  policy_candidates: PolicyCandidate[]
  selected_customer_id: string | null
  selected_policy_id: string | null
  selected_vehicle_id: string | null
  reviewer_notes: string[]
  audit_history: { event: string; timestamp: number; [key: string]: unknown }[]
}

export type CustomerCandidate = {
  customer_id: string
  full_name: string
  customer_status: string
  match_status: string
  match_reasons: string[]
  matched_identifiers: string[]
  phone_masked?: string | null
  email_masked?: string | null
  policy_ids: string[]
}

export type PolicyCandidate = {
  policy_id: string
  policy_number: string
  insurance_product: string
  policy_status: string
  effective_start: string
  effective_end: string
  customer_id: string
  customer_name: string
  vehicle_id?: string | null
  vehicle_label?: string | null
  registration_number?: string | null
  match_status: string
  match_reasons: string[]
}

export type Job = {
  id: string
  status: string
  stage: string
  source: string
  language: string | null
  model: string
  audio: { filename: string; duration_seconds: number; sample_rate: number; channels: number; frames: number; source: string; rms?: number }
  segments: { id: string; text: string; start: number | null; end: number | null; words: { id: string; text: string; start: number | null; end: number | null }[] }[]
  transcript: { original: string; protected: string; replacements: number } | null
  entities: Entity[]
  regions: Region[]
  metrics: { asr_seconds?: number; detection_seconds?: number; redaction_seconds?: number; total_seconds?: number; real_time_factor?: number }
  waveform: number[]
  redaction_settings: { mode: string; beep_frequency: number; fade_ms: number; padding_ms: number }
  protected_audio_ready: boolean
  error?: string | null
  claim: ClaimDossier | null
}

