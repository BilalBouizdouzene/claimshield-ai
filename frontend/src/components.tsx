import { useRef, useState, type MouseEvent, type ReactNode } from 'react'
import { Activity, AudioLines, BarChart3, Bell, BookOpen, Boxes, BrainCircuit, CarFront, Check, CheckCircle2, ChevronLeft, ChevronRight, CircleHelp, ClipboardCheck, FileAudio, FileSearch, FileText, FlaskConical, FolderOpen, Gauge, Link2, LockKeyhole, Mic, MoreHorizontal, Play, Search, Settings, Shield, ShieldCheck, Upload, UserRound, UsersRound, X } from 'lucide-react'
import type { Entity, Job, Page, Region } from './types'

const nav: { id: Page; label: string; icon: typeof Activity }[] = [
  { id: 'studio', label: 'Nouveau sinistre', icon: AudioLines },
  { id: 'overview', label: 'Tableau de bord', icon: Activity },
  { id: 'claims', label: 'Sinistres', icon: FileSearch },
  { id: 'matching', label: 'Clients & contrats', icon: UsersRound },
  { id: 'searches', label: 'Recherches', icon: Search },
  { id: 'results', label: 'Preuves du dossier', icon: ClipboardCheck },
  { id: 'batch', label: 'Traitement batch', icon: Boxes },
  { id: 'statistics', label: 'Statistiques', icon: BarChart3 },
  { id: 'evaluation', label: 'Laboratoire IA', icon: FlaskConical },
]

export function Sidebar({ page, setPage, collapsed, setCollapsed }: { page: Page; setPage: (page: Page) => void; collapsed: boolean; setCollapsed: (value: boolean) => void }) {
  return <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
    <div className="brand"><div className="brand-mark"><ShieldCheck size={20} /></div>{!collapsed && <div><strong>ClaimShield <em>AI</em></strong><span>SMART · SECURE · FASTER CLAIMS</span></div>}</div>
    <div className="sidebar-section-label">ESPACE DE TRAVAIL</div>
    <nav>{nav.map(item => { const Icon = item.icon; return <button key={item.id} className={page === item.id ? 'nav-item active' : 'nav-item'} onClick={() => setPage(item.id)} title={item.label}><Icon size={18} />{!collapsed && <span>{item.label}</span>}{item.id === 'studio' && !collapsed && <span className="nav-dot" />}</button> })}</nav>
    <SidebarSecurityVisual collapsed={collapsed} />
    <div className="sidebar-spacer" />
    <div className="sidebar-section-label">SYSTÈME</div>
    <button className={page === 'settings' ? 'nav-item active' : 'nav-item'} onClick={() => setPage('settings')}><Settings size={18} />{!collapsed && <span>Paramètres</span>}</button>
    <button className={page === 'about' ? 'nav-item active' : 'nav-item'} onClick={() => setPage('about')}><BookOpen size={18} />{!collapsed && <span>À propos / Recherche</span>}</button>
    <div className="sidebar-footer">{!collapsed && <><div className="local-badge"><span className="status-pulse" />LOCAL ONLY<small>v0.1 · CPU-ready</small></div></>}<button className="collapse-btn" onClick={() => setCollapsed(!collapsed)}>{collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}</button></div>
  </aside>
}

function SidebarSecurityVisual({ collapsed }: { collapsed: boolean }) {
  if (collapsed) return null
  return <div className="sidebar-security-visual" aria-hidden="true"><div className="security-orbit orbit-a" /><div className="security-orbit orbit-b" /><div className="security-orbit orbit-c" /><div className="security-shield"><ShieldCheck size={138} strokeWidth={1.05} /><CarFront className="security-car" size={43} strokeWidth={1.35} /></div><div className="security-floor" /><span>DONNÉES<br /><b>PROTÉGÉES</b></span></div>
}

export function Topbar({ page, setPage }: { page: Page; setPage: (page: Page) => void }) {
  const label = nav.find(item => item.id === page)?.label ?? (page === 'settings' ? 'Settings' : 'About / Research')
  return <header className="topbar"><div className="breadcrumbs"><span>ClaimShield AI</span><ChevronRight size={14} /><strong>{label}</strong></div><div className="global-search"><Search size={15} /><input aria-label="Rechercher" placeholder="Rechercher un sinistre, un client, un contrat…" onKeyDown={event => { if (event.key === 'Enter') setPage('claims') }} /><kbd>⌘ K</kbd></div><div className="topbar-actions"><div className="processing-indicator"><span className="status-pulse" />Local processing</div><button className="icon-button" title="Notifications"><Bell size={18} /><span className="notification-dot" /></button><button className="icon-button" title="Help"><CircleHelp size={18} /></button><div className="profile-chip"><div className="avatar"><UserRound size={15} /></div><span><strong>Gestionnaire</strong><small>Revue locale</small></span></div></div></header>
}

export function SectionTitle({ eyebrow, title, description, action }: { eyebrow?: string; title: string; description?: string; action?: ReactNode }) {
  return <div className="section-title"><div>{eyebrow && <div className="eyebrow">{eyebrow}</div>}<h1>{title}</h1>{description && <p>{description}</p>}</div>{action}</div>
}

export function MetricCard({ label, value, detail, icon: Icon, accent = 'cyan' }: { label: string; value: string; detail: string; icon: typeof Gauge; accent?: string }) {
  return <div className={`metric-card accent-${accent}`}><div className="metric-icon"><Icon size={17} /></div><div className="metric-label">{label}</div><div className="metric-value">{value}</div><div className="metric-detail">{detail}</div></div>
}

export function Waveform({ job, audioUrl, protectedMode, onSeek, selectedRange }: { job: Job | null; audioUrl?: string; protectedMode: boolean; onSeek?: (time: number) => void; selectedRange?: [number, number] | null }) {
  const audioRef = useRef<HTMLAudioElement>(null)
  const values = job?.waveform?.length ? job.waveform : Array.from({ length: 120 }, (_, i) => 0.22 + Math.abs(Math.sin(i * 0.37)) * 0.42 + (i % 7 === 0 ? 0.16 : 0))
  const duration = job?.audio.duration_seconds ?? 8
  function seek(event: MouseEvent<HTMLDivElement>) { const rect = event.currentTarget.getBoundingClientRect(); const time = ((event.clientX - rect.left) / rect.width) * duration; if (audioRef.current && audioUrl) audioRef.current.currentTime = time; onSeek?.(time) }
  return <div className="waveform-wrap"><div className="waveform-toolbar"><div className="waveform-legend"><span className="legend-dot safe" /> safe <span className="legend-dot pii" /> sensitive <span className="legend-dot manual" /> manual</div><div className="waveform-tools"><button className="tiny-btn"><span>−</span></button><span>100%</span><button className="tiny-btn">+</button><button className="tiny-btn"><MoreHorizontal size={15} /></button></div></div><div className="waveform" onClick={seek}>{values.map((value, i) => { const time = i / values.length * duration; const isPii = job?.regions.some(region => time >= region.start && time <= region.end); const selected = selectedRange && time >= selectedRange[0] && time <= selectedRange[1]; return <span key={i} className={`wave-bar ${isPii ? 'pii' : ''} ${selected ? 'selected' : ''}`} style={{ height: `${Math.max(10, value * 100)}%` }} /> })}<div className="playhead" style={{ left: '18%' }} /></div><div className="timeline"><span>00:00</span><span>{formatDuration(duration / 2)}</span><span>{formatDuration(duration)}</span></div>{audioUrl && <audio ref={audioRef} className="native-audio" controls src={audioUrl} />}</div>
}

function formatDuration(seconds: number) { const mins = Math.floor(seconds / 60).toString().padStart(2, '0'); const secs = Math.floor(seconds % 60).toString().padStart(2, '0'); return `${mins}:${secs}` }

export function Pipeline({ status, stage }: { status: string; stage?: string }) {
  const stages: { label: string; icon: typeof Activity }[] = [
    { label: 'ENREGISTREMENT', icon: Mic },
    { label: 'TRANSCRIPTION', icon: AudioLines },
    { label: 'COMPRÉHENSION', icon: FileText },
    { label: 'IDENTIFICATION', icon: UserRound },
    { label: 'CONTRAT', icon: Link2 },
    { label: 'PROTECTION', icon: Shield },
    { label: 'VÉRIFICATION', icon: CheckCircle2 },
    { label: 'DOSSIER', icon: FolderOpen },
  ]
  const stageMap: Record<string, number> = { IDLE: 0, RECORDING: 0, AUDIO_RECEIVED: 0, PREPROCESSING: 1, DETECTING_LANGUAGE: 1, TRANSCRIBING: 1, EXTRACTING_CLAIM_FACTS: 2, BUILDING_EVENT_TIMELINE: 2, DETECTING_SENSITIVE_INFORMATION: 5, ALIGNING_AUDIO: 5, APPLYING_PRIVACY_POLICY: 5, GENERATING_PROTECTED_AUDIO: 5, PREPARING_CLAIM_DOSSIER: 7, READY_FOR_REVIEW: 7, APPROVED_FOR_EXPORT: 7, ERROR: 0 }
  const current = stage ? (stageMap[stage] ?? 0) : status === 'processing' ? 1 : status === 'ready' || status === 'approved' ? 4 : 0
  return <div className="pipeline">{stages.map(({ label, icon: Icon }, index) => <div className={`pipeline-step ${index < current ? 'done' : ''} ${index === current && status === 'processing' ? 'running' : ''}`} key={label}><div className="pipeline-icon">{index === current && status === 'processing' ? <span className="spinner" /> : <Icon size={15} />}</div><span className="pipeline-number">{index + 1}</span><strong>{label}</strong>{index < stages.length - 1 && <div className="pipeline-line" />}</div>)}</div>
}

export function EmptyState({ onStart }: { onStart: () => void }) { return <div className="empty-state"><div className="empty-orbit"><Mic size={28} /></div><h3>Prêt pour un test audio réel</h3><p>Enregistrez une déclaration avec le microphone ou importez un fichier audio local. La transcription est exécutée par faster-whisper.</p><div className="empty-actions"><button className="button secondary" onClick={onStart}><Mic size={16} /> Commencer un test réel</button><span>Traitement local · WAV, FLAC, OGG ou MP3</span></div></div> }

function encodeWav(chunks: Float32Array[], sampleRate: number): Blob {
  const length = chunks.reduce((total, chunk) => total + chunk.length, 0)
  const buffer = new ArrayBuffer(44 + length * 2)
  const view = new DataView(buffer)
  const writeString = (offset: number, value: string) => [...value].forEach((character, index) => view.setUint8(offset + index, character.charCodeAt(0)))
  writeString(0, 'RIFF'); view.setUint32(4, 36 + length * 2, true); writeString(8, 'WAVE'); writeString(12, 'fmt ')
  view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true); view.setUint32(24, sampleRate, true)
  view.setUint32(28, sampleRate * 2, true); view.setUint16(32, 2, true); view.setUint16(34, 16, true); writeString(36, 'data'); view.setUint32(40, length * 2, true)
  let offset = 44
  for (const chunk of chunks) for (const sample of chunk) { const value = Math.max(-1, Math.min(1, sample)); view.setInt16(offset, value < 0 ? value * 0x8000 : value * 0x7fff, true); offset += 2 }
  return new Blob([buffer], { type: 'audio/wav' })
}

export function UploadCard({ onFile, onError }: { onFile: (file: File) => void; onError?: (message?: string) => void }) {
  const input = useRef<HTMLInputElement>(null)
  const processor = useRef<ScriptProcessorNode | null>(null)
  const stream = useRef<MediaStream | null>(null)
  const context = useRef<AudioContext | null>(null)
  const chunks = useRef<Float32Array[]>([])
  const [recording, setRecording] = useState(false)
  async function startRecording() {
    try {
      if (!navigator.mediaDevices?.getUserMedia) throw new Error('Ce navigateur ne permet pas l’accès au microphone.')
      const mediaStream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } })
      const audioContext = new AudioContext()
      const source = audioContext.createMediaStreamSource(mediaStream)
      const recorder = audioContext.createScriptProcessor(4096, 1, 1)
      chunks.current = []
      recorder.onaudioprocess = event => chunks.current.push(new Float32Array(event.inputBuffer.getChannelData(0)))
      const silentGain = audioContext.createGain(); silentGain.gain.value = 0
      source.connect(recorder); recorder.connect(silentGain); silentGain.connect(audioContext.destination)
      stream.current = mediaStream; context.current = audioContext; processor.current = recorder; setRecording(true); onError?.(undefined)
    } catch (error) { onError?.(error instanceof Error ? error.message : 'Accès au microphone refusé.') }
  }
  async function stopRecording() {
    const audioContext = context.current; const recorder = processor.current
    recorder?.disconnect(); stream.current?.getTracks().forEach(track => track.stop()); context.current = null; processor.current = null; stream.current = null; setRecording(false)
    if (!audioContext) return
    const blob = encodeWav(chunks.current, audioContext.sampleRate); await audioContext.close(); onFile(new File([blob], `microphone-${new Date().toISOString().replace(/[:.]/g, '-')}.wav`, { type: 'audio/wav' })); chunks.current = []
  }
  return <div className="upload-card"><div className={`upload-icon ${recording ? 'recording-icon' : ''}`}><Mic size={21} /></div><h3>{recording ? 'Enregistrement en cours…' : 'Enregistrez une déclaration réelle'}</h3><p>Importez un fichier audio ou utilisez le microphone · 50 Mo maximum · traitement local</p><div className="upload-actions"><button className="button primary" onClick={() => input.current?.click()} disabled={recording}><Upload size={16} /> Importer un audio</button><button className={`button ${recording ? 'recording-button' : 'secondary'}`} onClick={() => recording ? stopRecording() : startRecording()}><Mic size={16} /> {recording ? 'Arrêter et analyser' : 'Enregistrer au micro'}</button><input ref={input} type="file" accept="audio/*" hidden onChange={event => { const file = event.target.files?.[0]; if (file) onFile(file) }} /></div><div className="upload-hint"><LockKeyhole size={13} /> L’audio du microphone est converti en WAV puis analysé localement par faster-whisper</div></div>
}

export function EntityBadge({ category }: { category: string }) { return <span className={`entity-badge ${category.toLowerCase().replace('_', '-')}`}><span />{category.replace('_', ' ')}</span> }

export function EntityRow({ entity, onSelect, onToggle }: { entity: Entity; onSelect: () => void; onToggle: () => void }) { return <div className={`entity-row ${entity.alignment.quality === 'missing' ? 'attention' : ''}`} onClick={onSelect}><div className="entity-main"><EntityBadge category={entity.category} /><strong>{entity.text}</strong><span className="entity-source">{entity.source}</span></div><div className="entity-meta"><span>{entity.audio_start != null ? `${entity.audio_start.toFixed(2)}s → ${entity.audio_end?.toFixed(2)}s` : 'Alignement requis'}</span><span className={`review-chip ${entity.review_status}`}>{entity.review_status === 'needs_attention' ? 'À vérifier' : entity.review_status === 'approved' ? 'Approuvé' : 'Non revu'}</span><button className={`switch ${entity.redaction_enabled ? 'on' : ''}`} onClick={event => { event.stopPropagation(); onToggle() }}><span /></button></div></div> }

export function Transcript({ job, protectedMode, onSeek }: { job: Job; protectedMode: boolean; onSeek: (time: number) => void }) { const words = job.segments.flatMap(segment => segment.words); return <div className="transcript-text">{protectedMode ? job.transcript?.protected : <>{words.length ? words.map(word => <button key={word.id} className="transcript-word" onClick={() => word.start != null && onSeek(word.start)}>{word.text}</button>) : job.transcript?.original}</>}</div> }

export function Toast({ message, onClose }: { message: string; onClose: () => void }) { return <div className="toast"><Check size={16} /><span>{message}</span><button onClick={onClose}><X size={15} /></button></div> }

