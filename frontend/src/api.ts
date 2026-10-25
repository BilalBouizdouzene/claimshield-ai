import type { Job } from './types'

const API = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, init)
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.detail ?? 'Une erreur est survenue.')
  return data as T
}

export async function getHealth() { return request<{ status: string; local_processing: boolean }>('/health') }
export async function getModels() { return request<{ models: { id: string; label: string; available: boolean; mode: string }[]; asr_installed: boolean }>('/models') }
export async function getClaims(query = '') { return request<{ claims: { job: Job; claim: NonNullable<Job['claim']> }[]; metrics: { total: number; awaiting_identity_review: number; matched_contracts: number; awaiting_privacy_review: number; ready_for_human_examination: number } }>(`/claims?query=${encodeURIComponent(query)}`) }
export async function searchCustomers(query = '') { return request<{ customers: { customer_id: string; full_name: string; phone: string; email: string; postal_address: string; customer_status: string }[] }>(`/customers/search?q=${encodeURIComponent(query)}`) }
export async function searchPolicies(query = '') { return request<{ policies: Record<string, string | null>[] }>(`/policies/search?q=${encodeURIComponent(query)}`) }
export async function uploadAudio(file: File) {
  const form = new FormData(); form.append('file', file)
  return request<{ job: Job }>('/audio/upload', { method: 'POST', body: form })
}
export async function analyze(jobId: string, options: { language: string; model: string }) {
  return request<{ job: Job }>(`/audio/analyze/${jobId}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(options) })
}
export async function processBatch(files: File[], model: string) {
  const form = new FormData(); files.forEach(file => form.append('files', file))
  return request<{ results: { job?: Job; filename?: string; status: string; error?: string }[]; completed: number; failed: number }>(`/audio/batch?model=${encodeURIComponent(model)}`, { method: 'POST', body: form })
}
export async function scoreEvaluation(examples: { reference: string; hypothesis: string; reference_entities?: (string | { category?: string; text?: string })[]; predicted_entities?: (string | { category?: string; text?: string })[] }[]) {
  return request<{ status: string; metrics: { examples: number; wer: number; cer: number; pii: { precision: number; recall: number; f1: number }; method: string; warning: string } }>('/evaluation/score', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ examples }) })
}
export async function patchClaimFact(jobId: string, factId: string, patch: Record<string, unknown>) {
  return request<{ job: Job }>(`/jobs/${jobId}/claim/facts/${factId}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(patch) })
}
export async function patchEntity(jobId: string, entityId: string, patch: Record<string, unknown>) {
  return request<{ job: Job }>(`/jobs/${jobId}/entities/${entityId}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(patch) })
}
export async function addRegion(jobId: string, start: number, end: number) {
  return request<{ job: Job }>(`/jobs/${jobId}/regions`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ start, end }) })
}
export async function redact(jobId: string, mode: string, privacyPolicy = 'INTERNAL_CLAIM_REVIEW') {
  return request<{ job: Job }>(`/jobs/${jobId}/redact`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ settings: { mode, privacy_policy: privacyPolicy, padding_ms: 80, fade_ms: 12, beep_frequency: 880 } }) })
}
export async function approve(jobId: string) { return request<{ job: Job }>(`/jobs/${jobId}/approve`, { method: 'POST' }) }
export async function confirmCustomer(jobId: string, customerId: string) { return request<{ job: Job }>(`/jobs/${jobId}/matching/customer/${customerId}/confirm`, { method: 'POST' }) }
export async function confirmPolicy(jobId: string, policyId: string) { return request<{ job: Job }>(`/jobs/${jobId}/matching/policy/${policyId}/confirm`, { method: 'POST' }) }
export async function updateReview(jobId: string, patch: { workflow_status?: string; note?: string }) { return request<{ job: Job }>(`/jobs/${jobId}/review`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(patch) }) }
export function downloadUrl(jobId: string, kind: 'audio' | 'transcript' | 'report' | 'claim') { return `${API}/jobs/${jobId}/download/${kind}` }

