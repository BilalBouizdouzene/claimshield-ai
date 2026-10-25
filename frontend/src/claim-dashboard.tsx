import { useState, type ReactNode } from 'react'
import { AlertTriangle, BadgeCheck, CarFront, Check, ChevronRight, ClipboardCheck, Clock3, Download, FileCheck2, FileSearch, FileText, Link2, MapPin, Mic2, Pencil, Play, Shield, ShieldCheck, UserRound, UsersRound, Volume2 } from 'lucide-react'
import { downloadUrl } from './api'
import { EntityBadge, Pipeline, Transcript, Waveform } from './components'
import type { ClaimDossier, Job } from './types'

type DashboardProps = {
  job: Job
  audioUrl?: string
  protectedMode: boolean
  selectedRange: [number, number] | null
  onProtectedMode: (value: boolean) => void
  onSelectRange: (range: [number, number] | null) => void
  onRedact: () => void
  onApprove: () => void
  onOpenDossier: () => void
  onConfirmCustomer: (customerId: string) => void
  onConfirmPolicy: (policyId: string) => void
  onReviewFact: (factId: string) => void
  onReviewStatus: (status: string, note?: string) => void
}

function StatusPill({ children, tone = 'cyan' }: { children: ReactNode; tone?: string }) {
  return <span className={`status-pill tone-${tone}`}><span />{children}</span>
}

function CardHeader({ eyebrow, title, icon: Icon, action }: { eyebrow: string; title: string; icon?: typeof Shield; action?: ReactNode }) {
  return <div className="reference-card-header"><div><span className="eyebrow">{eyebrow}</span><h3>{title}</h3></div>{Icon && <Icon size={18} className="card-header-icon" />}{action}</div>
}

export function PremiumClaimDashboard({ job, audioUrl, protectedMode, selectedRange, onProtectedMode, onSelectRange, onRedact, onApprove, onOpenDossier, onConfirmCustomer, onConfirmPolicy, onReviewFact, onReviewStatus }: DashboardProps) {
  const claim = job.claim
  const [note, setNote] = useState('')
  const hasProtectedAudio = job.protected_audio_ready
  return <div className="reference-workspace">
    <div className="reference-pipeline panel"><Pipeline status={job.status} stage={job.stage} /></div>
    <div className="reference-top-grid">
      <section className="panel reference-card audio-card">
        <CardHeader eyebrow="01 · AUDIO DECLARATION" title="Enregistrement audio" icon={Mic2} action={<StatusPill tone="green">Auto</StatusPill>} />
        <div className="audio-meta"><strong>{job.audio.filename}</strong><span>{formatTime(job.audio.duration_seconds)} / local WAV</span></div>
        <Waveform job={job} audioUrl={audioUrl} protectedMode={protectedMode} selectedRange={selectedRange} onSeek={() => undefined} />
        <div className="audio-card-footer"><span><span className="live-dot" /> {hasProtectedAudio ? 'Version protégée prête' : 'Source originale contrôlée'}</span><button className="button compact-button" onClick={onRedact} disabled={!job.regions.length}><ShieldCheck size={14} /> Protéger</button></div>
      </section>
      <section className="panel reference-card transcript-card">
        <CardHeader eyebrow="02 · TRANSCRIPTION" title="Transcription" icon={FileText} action={<StatusPill tone="green">{job.language ? job.language.toUpperCase() : 'AUTO'}</StatusPill>} />
        <div className="confidence-line"><span>Détection automatique de langue</span><strong>{job.language ? `Français · ${job.metrics.asr_seconds != null ? 'ASR local' : 'En attente'}` : 'En attente'}</strong></div>
        <div className="reference-tabs"><button className={!protectedMode ? 'active' : ''} onClick={() => onProtectedMode(false)}>Texte</button><button className={protectedMode ? 'active' : ''} onClick={() => onProtectedMode(true)}>Vue protégée</button></div>
        <div className="reference-transcript"><Transcript job={job} protectedMode={protectedMode} onSeek={time => onSelectRange([time, time + .8])} /></div>
        <div className="transcript-foot"><span>{job.entities.length} zones sensibles repérées</span><span>{job.transcript?.replacements ?? 0} remplacements</span></div>
      </section>
      <section className="panel reference-card language-card">
        <CardHeader eyebrow="03 · LANGUAGE" title="Langue détectée" icon={Volume2} />
        <div className="language-orb"><div className="globe-ring">◎</div><strong>{job.language ? languageName(job.language) : 'En attente'}</strong><span>Traitement local · CPU INT8</span></div>
        <div className="language-list"><div className="selected"><span>🇫🇷</span><strong>Français</strong><em>{job.language === 'fr' ? 'active' : 'supporté'}</em></div><div><span>ع</span><strong>Arabe MSA</strong><em>supporté</em></div><div><span>EN</span><strong>Anglais</strong><em>supporté</em></div></div>
      </section>
    </div>
    <div className="reference-middle-grid">
      <ExtractedInfoCard job={job} onSelectRange={onSelectRange} onReviewFact={onReviewFact} />
      <ContractCard claim={claim} onConfirmCustomer={onConfirmCustomer} onConfirmPolicy={onConfirmPolicy} />
      <ProtectedViewCard job={job} protectedMode={protectedMode} onProtectedMode={onProtectedMode} />
    </div>
    <div className="reference-bottom-grid">
      <EvidenceCard job={job} onSelectRange={onSelectRange} />
      <SummaryCard claim={claim} />
      <section className="panel reference-card actions-card">
        <CardHeader eyebrow="ACTIONS" title="Revue humaine" icon={UsersRound} />
        <StatusPill tone={claim?.workflow_status === 'READY_FOR_HUMAN_EXAMINATION' ? 'green' : 'amber'}>{workflowLabel(claim?.workflow_status)}</StatusPill>
        <textarea value={note} onChange={event => setNote(event.target.value)} placeholder="Ajouter une note interne…" rows={3} />
        <button className="primary-action" onClick={() => { onReviewStatus('READY_FOR_HUMAN_EXAMINATION', note); setNote('') }}><Check size={16} /> Marquer prêt pour examen</button>
        <div className="action-row"><button onClick={onOpenDossier}><FileCheck2 size={15} /> Dossier</button><a href={downloadUrl(job.id, 'claim')}><Download size={15} /> JSON</a><button onClick={onApprove} disabled={!hasProtectedAudio}><BadgeCheck size={15} /> Approuver</button></div>
      </section>
    </div>
    {(claim?.missing_information.length || claim?.contradictions.length) ? <div className="reference-alerts">{claim.missing_information.length > 0 && <div className="reference-alert warning"><AlertTriangle size={16} /><span><strong>Informations manquantes</strong>{claim.missing_information.join(' · ')}</span></div>}{claim.contradictions.length > 0 && <div className="reference-alert danger"><AlertTriangle size={16} /><span><strong>Contradictions à vérifier</strong>{claim.contradictions.join(' · ')}</span></div>}</div> : null}
  </div>
}

function ExtractedInfoCard({ job, onSelectRange, onReviewFact }: { job: Job; onSelectRange: (range: [number, number] | null) => void; onReviewFact: (id: string) => void }) {
  const facts = job.claim?.facts ?? []
  return <section className="panel reference-card extracted-card"><CardHeader eyebrow="04 · CLAIM UNDERSTANDING" title="Informations extraites (IA)" icon={ClipboardCheck} action={<button className="card-action"><Pencil size={13} /> Modifier</button>} /><div className="fact-grid">{facts.length ? facts.map(fact => <button className={`extracted-fact ${fact.verification_state === 'reviewed' ? 'verified' : ''}`} key={fact.id} onClick={() => { if (fact.evidence.audio_start != null && fact.evidence.audio_end != null) onSelectRange([fact.evidence.audio_start, fact.evidence.audio_end]); onReviewFact(fact.id) }}><span className="fact-icon"><FactIcon field={fact.field} /></span><span><small>{fact.label}</small><strong>{fact.value ?? 'Non renseigné'}</strong></span><em>{fact.verification_state === 'reviewed' ? '✓' : 'IA'}</em></button>) : <div className="empty-inline">Les faits apparaîtront après transcription.</div>}</div></section>
}

function ContractCard({ claim, onConfirmCustomer, onConfirmPolicy }: { claim: ClaimDossier | null; onConfirmCustomer: (id: string) => void; onConfirmPolicy: (id: string) => void }) {
  const customer = claim?.customer_candidates?.[0]
  const policy = claim?.policy_candidates?.[0]
  return <section className="panel reference-card contract-card"><CardHeader eyebrow="05 · ASSOCIATION" title="Client & contrat" icon={Link2} action={<StatusPill tone={policy ? 'green' : 'amber'}>{policy ? 'Contrat trouvé' : 'À vérifier'}</StatusPill>} />{customer ? <div className="candidate-block"><div className="candidate-heading"><div className="round-icon"><UserRound size={17} /></div><div><strong>{customer.full_name}</strong><span>{customer.customer_id} · {customer.match_status}</span></div></div><div className="match-reasons">{customer.match_reasons.map(reason => <span key={reason}>✓ {reason}</span>)}</div><button className="outline-action" onClick={() => onConfirmCustomer(customer.customer_id)} disabled={customer.match_status === 'MATCH_CONFIRMED_BY_REVIEWER'}>{customer.match_status === 'MATCH_CONFIRMED_BY_REVIEWER' ? 'Client confirmé' : 'Confirmer le client'}</button></div> : <div className="empty-inline">Aucun candidat client confirmé. Un nom seul ne suffit pas.</div>}{policy && <><div className="policy-block"><div className="policy-icon"><Shield size={18} /></div><div><strong>{policy.policy_number}</strong><span>{policy.insurance_product} · {policy.policy_status}</span><small>{policy.vehicle_label ?? 'Véhicule non associé'} · {policy.registration_number ?? 'Plaque inconnue'}</small></div><button onClick={() => onConfirmPolicy(policy.policy_id)} disabled={policy.match_status === 'MATCH_CONFIRMED_BY_REVIEWER'}>{policy.match_status === 'MATCH_CONFIRMED_BY_REVIEWER' ? '✓' : 'Associer'}</button></div><div className="vehicle-card"><div className="vehicle-visual"><span className="vehicle-scan" /><CarFront size={43} strokeWidth={1.25} /></div><div><small>VÉHICULE ASSURÉ</small><strong>{policy.vehicle_label ?? 'Véhicule automobile'}</strong><span>Immatriculation : {policy.registration_number ?? 'à vérifier'}</span></div></div></>}{claim && claim.customer_candidates.length > 1 && <div className="candidate-count"><UsersRound size={13} /> {claim.customer_candidates.length} candidats — la revue humaine est obligatoire</div>}</section>
}

function ProtectedViewCard({ job, protectedMode, onProtectedMode }: { job: Job; protectedMode: boolean; onProtectedMode: (value: boolean) => void }) {
  const rows = job.entities.slice(0, 7)
  return <section className="panel reference-card protected-card"><CardHeader eyebrow="06 · PRIVACY" title="Vue protégée" icon={ShieldCheck} action={<div className="segmented"><button className={!protectedMode ? 'active' : ''} onClick={() => onProtectedMode(false)}>Original</button><button className={protectedMode ? 'active' : ''} onClick={() => onProtectedMode(true)}>Masquée</button></div>} /><div className="protected-list">{rows.length ? rows.map(entity => <div key={entity.id}><span className="protected-entity-icon"><EntityBadge category={entity.category} /></span><strong>{protectedMode ? mask(entity.category) : entity.text}</strong><span>{entity.audio_start != null ? `${entity.audio_start.toFixed(2)}s` : 'à vérifier'}</span></div>) : <div className="empty-inline">Aucune donnée sensible détectée.</div>}</div><div className="privacy-note"><ShieldCheck size={14} /> La vue protégée est dérivée ; l’original reste réservé à la revue locale.</div></section>
}

function EvidenceCard({ job, onSelectRange }: { job: Job; onSelectRange: (range: [number, number] | null) => void }) {
  const facts = job.claim?.facts ?? []
  return <section className="panel reference-card evidence-card"><CardHeader eyebrow="07 · EVIDENCE" title="Preuves et segments audio" icon={Volume2} />{facts.slice(0, 5).map((fact, index) => <button className="evidence-row" key={fact.id} onClick={() => fact.evidence.audio_start != null && fact.evidence.audio_end != null && onSelectRange([fact.evidence.audio_start, fact.evidence.audio_end])}><span className="evidence-play"><Play size={11} /></span><span className="evidence-wave">▁▃▅▂▇▅▃▁</span><span className="evidence-time">{fact.evidence.audio_start != null ? `${fact.evidence.audio_start.toFixed(2)}–${fact.evidence.audio_end?.toFixed(2)}` : '—'}</span><strong>{fact.evidence_text ?? fact.value ?? 'Évidence non alignée'}</strong><em>{index % 2 ? 'Fait' : 'Client'}</em></button>)}{!facts.length && <div className="empty-inline">Les preuves apparaîtront avec le dossier.</div>}</section>
}

function SummaryCard({ claim }: { claim: ClaimDossier | null }) {
  return <section className="panel reference-card summary-card"><CardHeader eyebrow="08 · DOSSIER" title="Résumé du sinistre" icon={FileText} action={<StatusPill tone="violet">IA · révisable</StatusPill>} /><p>{claim?.incident_summary ?? 'Le résumé sera généré après l’analyse de la déclaration.'}</p><div className="summary-progress"><span>État du workflow</span><strong>{workflowLabel(claim?.workflow_status)}</strong></div><div className="progress-line"><span style={{ width: `${workflowProgress(claim?.workflow_status)}%` }} /></div></section>
}

export function ClaimsWorkspace({ claims, query, onQuery, onOpen }: { claims: { job: Job; claim: NonNullable<Job['claim']> }[]; query: string; onQuery: (value: string) => void; onOpen: (job: Job) => void }) {
  const [status, setStatus] = useState('all')
  const visible = claims.filter(item => (status === 'all' || item.claim.workflow_status === status) && `${item.claim.claim_id} ${item.job.audio.filename}`.toLowerCase().includes(query.toLowerCase()))
  return <div className="claims-workspace"><div className="workspace-toolbar"><div><span className="eyebrow">CLAIMS WORKSPACE</span><h2>Dossiers locaux</h2></div><div className="workspace-filters"><label><span>⌕</span><input value={query} onChange={event => onQuery(event.target.value)} placeholder="Rechercher un sinistre…" /></label><select value={status} onChange={event => setStatus(event.target.value)}><option value="all">Tous les statuts</option><option value="AWAITING_IDENTITY_REVIEW">Identité à revoir</option><option value="AWAITING_CONTRACT_REVIEW">Contrat à revoir</option><option value="READY_FOR_HUMAN_EXAMINATION">Prêt pour examen</option></select></div></div><div className="claims-table panel"><div className="claims-table-head"><span>Référence</span><span>Déclaration</span><span>Client / contrat</span><span>Workflow</span><span>Action</span></div>{visible.length ? visible.map(item => <button className="claim-table-row" key={item.job.id} onClick={() => onOpen(item.job)}><strong>{item.claim.claim_id}</strong><span>{item.job.audio.filename}<small>{item.job.language?.toUpperCase() ?? '—'} · {formatTime(item.job.audio.duration_seconds)}</small></span><span>{item.claim.selected_customer_id ?? 'Candidat à confirmer'}<small>{item.claim.selected_policy_id ?? 'Contrat non associé'}</small></span><span><StatusPill tone={item.claim.workflow_status.includes('READY') ? 'green' : 'amber'}>{workflowLabel(item.claim.workflow_status)}</StatusPill></span><span><ChevronRight size={16} /></span></button>) : <div className="empty-table"><FileSearchIcon /><strong>Aucun dossier trouvé</strong><span>Lancez une déclaration réelle depuis le studio.</span></div>}</div></div>
}

export function MatchingWorkspace({ job, onConfirmCustomer, onConfirmPolicy }: { job: Job | null; onConfirmCustomer: (id: string) => void; onConfirmPolicy: (id: string) => void }) {
  const claim = job?.claim
  return <div className="matching-workspace"><div className="workspace-toolbar"><div><span className="eyebrow">CUSTOMER & CONTRACT MATCHING</span><h2>Association vérifiable</h2></div><StatusPill tone="amber">Aucune confirmation automatique</StatusPill></div>{!claim ? <div className="panel empty-workspace"><UsersRound size={28} /><strong>Ouvrez un dossier pour voir les candidats.</strong></div> : <div className="matching-grid"><section className="panel matching-panel"><CardHeader eyebrow="CUSTOMER CANDIDATES" title="Identité extraite" icon={UserRound} />{claim.customer_candidates.length ? claim.customer_candidates.map(candidate => <div className="match-row" key={candidate.customer_id}><div><strong>{candidate.full_name}</strong><span>{candidate.customer_id} · {candidate.phone_masked}</span><small>{candidate.match_reasons.join(' · ')}</small></div><button className="outline-action" onClick={() => onConfirmCustomer(candidate.customer_id)}>{candidate.match_status === 'MATCH_CONFIRMED_BY_REVIEWER' ? 'Confirmé' : 'Confirmer'}</button></div>) : <div className="empty-inline">Aucun candidat : le nom seul ne permet pas une confirmation.</div>}</section><section className="panel matching-panel"><CardHeader eyebrow="POLICY CANDIDATES" title="Contrats locaux" icon={Link2} />{claim.policy_candidates.length ? claim.policy_candidates.map(policy => <div className="match-row" key={policy.policy_id}><div><strong>{policy.policy_number}</strong><span>{policy.customer_name} · {policy.policy_status}</span><small>{policy.vehicle_label} · {policy.registration_number}</small></div><button className="outline-action" onClick={() => onConfirmPolicy(policy.policy_id)}>{policy.match_status === 'MATCH_CONFIRMED_BY_REVIEWER' ? 'Associé' : 'Associer'}</button></div>) : <div className="empty-inline">Aucun contrat correspondant.</div>}</section></div>}</div>
}

export function DossierView({ job, onBack, onReviewStatus }: { job: Job; onBack: () => void; onReviewStatus: (status: string, note?: string) => void }) {
  const claim = job.claim
  return <div className="dossier-view"><div className="dossier-heading"><button className="back-link" onClick={onBack}>← Retour aux preuves</button><div><span className="eyebrow">CLAIM DOSSIER · HUMAN REVIEW</span><h1>{claim?.claim_id ?? 'Dossier en préparation'}</h1><p>Document de travail local · aucune décision de couverture, fraude ou responsabilité.</p></div><div className="dossier-actions"><a className="button secondary" href={downloadUrl(job.id, 'claim')}><Download size={15} /> JSON structuré</a><button className="button primary" onClick={() => onReviewStatus('READY_FOR_HUMAN_EXAMINATION')}><Check size={15} /> Prêt pour examen</button></div></div><div className="dossier-grid"><section className="panel dossier-main"><CardHeader eyebrow="INCIDENT OVERVIEW" title="Résumé de la déclaration" icon={CarFront} /><p className="dossier-summary">{claim?.incident_summary ?? 'Résumé indisponible.'}</p><div className="dossier-facts">{claim?.facts.map(fact => <div key={fact.id}><small>{fact.label}</small><strong>{fact.value ?? 'Non renseigné'}</strong><span>{fact.evidence.audio_start != null ? `${fact.evidence.audio_start.toFixed(2)}–${fact.evidence.audio_end?.toFixed(2)}s` : 'Evidence unverified'}</span></div>)}</div></section><aside className="panel dossier-side"><CardHeader eyebrow="REVIEW STATUS" title="État du dossier" icon={ClipboardCheck} /><StatusPill tone={claim?.workflow_status === 'READY_FOR_HUMAN_EXAMINATION' ? 'green' : 'amber'}>{workflowLabel(claim?.workflow_status)}</StatusPill><div className="dossier-status-list"><div><span>Client</span><strong>{claim?.selected_customer_id ?? 'À confirmer'}</strong></div><div><span>Contrat</span><strong>{claim?.selected_policy_id ?? 'À associer'}</strong></div><div><span>Protection</span><strong>{job.protected_audio_ready ? 'Audio prêt' : 'À vérifier'}</strong></div><div><span>Preuves</span><strong>{claim?.facts.length ?? 0} faits</strong></div></div></aside></div></div>
}

function FactIcon({ field }: { field: string }) { if (field.includes('location')) return <MapPin size={15} />; if (field.includes('vehicle') || field.includes('damage')) return <CarFront size={15} />; if (field.includes('date') || field.includes('time')) return <Clock3 size={15} />; return <FileText size={15} /> }
function FileSearchIcon() { return <FileSearch size={24} /> }
function mask(category: string) { return `[${category.replaceAll('_', ' ')}]` }
function formatTime(value: number) { return `${Math.floor(value / 60).toString().padStart(2, '0')}:${Math.floor(value % 60).toString().padStart(2, '0')}` }
function languageName(language: string) { return language === 'fr' ? 'Français' : language === 'en' ? 'Anglais' : language === 'ar' ? 'Arabe MSA' : language.toUpperCase() }
function workflowLabel(value?: string | null) { return value === 'READY_FOR_HUMAN_EXAMINATION' ? 'Prêt pour examen' : value === 'AWAITING_IDENTITY_REVIEW' ? 'Identité à revoir' : value === 'AWAITING_CONTRACT_REVIEW' ? 'Contrat à revoir' : value === 'AWAITING_PRIVACY_REVIEW' ? 'Protection à revoir' : value === 'NEEDS_MORE_INFORMATION' ? 'Informations manquantes' : 'Brouillon à revoir' }
function workflowProgress(value?: string | null) { return value === 'READY_FOR_HUMAN_EXAMINATION' ? 100 : value === 'AWAITING_EVIDENCE_REVIEW' ? 82 : value === 'AWAITING_PRIVACY_REVIEW' ? 68 : value === 'AWAITING_CONTRACT_REVIEW' ? 50 : value === 'AWAITING_IDENTITY_REVIEW' ? 32 : 15 }
