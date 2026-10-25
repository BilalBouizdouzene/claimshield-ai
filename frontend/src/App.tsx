import { useEffect, useState } from 'react'
import { ShieldAlert } from 'lucide-react'
import { analyze, getClaims, getHealth, getModels, uploadAudio } from './api'
import { Sidebar, Toast, Topbar } from './components'
import { AboutScreen, BatchScreen, ClaimsScreen, DashboardScreen, EvidenceScreen, EvaluationLabScreen, MatchingScreen, SearchScreen, SettingsScreen, StatisticsScreen, StudioScreen, type ScreenContext } from './screens'
import type { Job, Page } from './types'

type ClaimsSnapshot = Awaited<ReturnType<typeof getClaims>>
const emptyMetrics = { total: 0, awaiting_identity_review: 0, matched_contracts: 0, awaiting_privacy_review: 0, ready_for_human_examination: 0 }
const pages: Page[] = ['overview', 'studio', 'claims', 'matching', 'results', 'batch', 'evaluation', 'searches', 'statistics', 'settings', 'about']

function initialPage(): Page {
  const requested = new URLSearchParams(window.location.search).get('screen') as Page | null
  return requested && pages.includes(requested) ? requested : 'overview'
}

function App() {
  const [page, setPage] = useState<Page>(initialPage)
  const captureMode = new URLSearchParams(window.location.search).get('capture') === '1'
  const requestedJob = new URLSearchParams(window.location.search).get('job')
  const [collapsed, setCollapsed] = useState(false)
  const [job, setJob] = useState<Job | null>(null)
  const [audioUrl, setAudioUrl] = useState<string>()
  const [toast, setToast] = useState<string>()
  const [error, setError] = useState<string>()
  const [health, setHealth] = useState<'checking' | 'online' | 'offline'>('checking')
  const [modelAvailable, setModelAvailable] = useState<boolean | null>(null)
  const [model, setModel] = useState(() => localStorage.getItem('claimshield.model') ?? 'whisper-base-int8')
  const [claims, setClaims] = useState<ClaimsSnapshot>({ claims: [], metrics: emptyMetrics })
  const [query, setQuery] = useState('')

  async function refreshClaims(search = query) { try { const next = await getClaims(search); setClaims(next); if (requestedJob === 'latest' && !job && next.claims[0]) setJob(next.claims[0].job) } catch { /* L’état API est déjà visible dans l’interface. */ } }
  useEffect(() => { getHealth().then(() => setHealth('online')).catch(() => setHealth('offline')); getModels().then(data => setModelAvailable(data.asr_installed)).catch(() => setModelAvailable(null)); refreshClaims('') }, [])
  useEffect(() => { localStorage.setItem('claimshield.model', model) }, [model])
  async function handleFile(file: File) { try { setError(undefined); const data = await uploadAudio(file); setJob(data.job); setAudioUrl(URL.createObjectURL(file)); setPage('studio'); setToast('Audio reçu · analyse locale en cours'); const result = await analyze(data.job.id, { language: 'auto', model }); setJob(result.job); setToast('Analyse terminée · dossier prêt pour revue'); await refreshClaims('') } catch (err) { setError(err instanceof Error ? err.message : 'Import ou analyse impossible.') } }
  async function updateJob(next: Promise<{ job: Job }>, message: string) { try { const data = await next; setJob(data.job); setToast(message); await refreshClaims('') } catch (err) { setError(err instanceof Error ? err.message : 'Action impossible.') } }
  const context: ScreenContext = { job, setJob, setPage, audioUrl, setAudioUrl, handleFile, updateJob, setError, health, modelAvailable, model, setModel, claims, query, setQuery }
  return <div className={`app-shell${captureMode ? ' capture-mode' : ''}`}><Sidebar page={page} setPage={setPage} collapsed={collapsed} setCollapsed={setCollapsed} /><main className="main"><Topbar page={page} setPage={setPage} /><div className="page-content">{error && <div className="error-banner"><ShieldAlert size={17} /><span>{error}</span><button onClick={() => setError(undefined)}>×</button></div>}{page === 'overview' && <DashboardScreen {...context} />}{page === 'studio' && <StudioScreen {...context} />}{page === 'claims' && <ClaimsScreen {...context} />}{page === 'matching' && <MatchingScreen {...context} />}{page === 'results' && <EvidenceScreen {...context} />}{page === 'batch' && <BatchScreen {...context} />}{page === 'evaluation' && <EvaluationLabScreen {...context} />}{page === 'searches' && <SearchScreen {...context} />}{page === 'statistics' && <StatisticsScreen {...context} />}{page === 'settings' && <SettingsScreen model={model} setModel={setModel} />}{page === 'about' && <AboutScreen />}</div>{toast && <Toast message={toast} onClose={() => setToast(undefined)} />}</main></div>
}

export default App
