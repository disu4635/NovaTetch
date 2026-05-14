import { useState, useEffect, useRef } from 'react'
import { Cpu, Plus } from 'lucide-react'
import { api } from './api/client'
import type {
  Ambiguity,
  Resolution,
  RunDetail,
  RunSummary,
  ContractB,
  RiskMatrix,
  ScenarioDecision,
  QualityForRunResponse,
} from './types'
import PromptForm from './components/PromptForm'
import AmbiguityResolver from './components/AmbiguityResolver'
import StoryCard from './components/StoryCard'
import RunHistory from './components/RunHistory'
import QualityPanel from './components/QualityPanel'
import ScenarioReviewer from './components/ScenarioReviewer'
import RiskMatrixComponent from './components/RiskMatrix'

type Phase =
  | 'idle'
  | 'analyzing'
  | 'resolving'
  | 'generating'
  | 'done'
  | 'error'
  | 'quality-running'
  | 'quality-review'
  | 'quality-submitting'
  | 'quality-done'

export default function App() {
  const [phase, setPhase] = useState<Phase>('idle')
  const [currentPrompt, setCurrentPrompt] = useState('')
  const [ambiguities, setAmbiguities] = useState<Ambiguity[]>([])
  const [run, setRun] = useState<RunDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [runs, setRuns] = useState<RunSummary[]>([])

  // Quality state
  const [qualityRunId, setQualityRunId] = useState<string | null>(null)
  const [qualityProgressMsg, setQualityProgressMsg] = useState<string>('')
  const [contractB, setContractB] = useState<ContractB | null>(null)
  const [riskMatrix, setRiskMatrix] = useState<RiskMatrix | null>(null)

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    api.getRuns().then(setRuns).catch(() => {})
  }, [])

  // Stop polling when unmounted
  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [])

  const handleAnalyze = async (prompt: string) => {
    setCurrentPrompt(prompt)
    setError(null)
    setPhase('analyzing')
    try {
      const { ambiguities: detected } = await api.analyze(prompt)
      setAmbiguities(detected)
      if (detected.length === 0) {
        await doGenerate(prompt, [])
      } else {
        setPhase('resolving')
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error desconocido')
      setPhase('error')
    }
  }

  const doGenerate = async (prompt: string, resolutions: Resolution[]) => {
    setPhase('generating')
    setError(null)
    try {
      const result = await api.generate(prompt, resolutions)
      setRun(result)
      setPhase('done')
      api.getRuns().then(setRuns).catch(() => {})
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error desconocido')
      setPhase('error')
    }
  }

  const handleGenerate = (resolutions: Resolution[]) => doGenerate(currentPrompt, resolutions)

  const handleSelectRun = async (runId: string) => {
    setError(null)
    // Limpiar estado de calidad previo antes de restaurar
    setQualityRunId(null)
    setContractB(null)
    setRiskMatrix(null)
    setQualityProgressMsg('')

    try {
      const detail = await api.getRun(runId)
      setRun(detail)
      setCurrentPrompt(detail.prompt)
      setAmbiguities([])

      // Intentar restaurar el estado de calidad si existe
      const qf: QualityForRunResponse = await api.getQualityForRun(runId)
      if (qf.found && qf.quality_run_id) {
        setQualityRunId(qf.quality_run_id)
        if (qf.has_review && qf.risk_matrix) {
          setRiskMatrix(qf.risk_matrix)
          setPhase('quality-done')
        } else if (qf.contract_b) {
          setContractB(qf.contract_b)
          setPhase('quality-review')
        } else {
          setPhase('done')
        }
      } else {
        setPhase('done')
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error al cargar el run')
    }
  }

  const handleReset = () => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null }
    setPhase('idle')
    setCurrentPrompt('')
    setAmbiguities([])
    setRun(null)
    setError(null)
    setQualityRunId(null)
    setQualityProgressMsg('')
    setContractB(null)
    setRiskMatrix(null)
  }

  const handleDelete = async (runId: string) => {
    try {
      await api.deleteRun(runId)
      setRuns(prev => prev.filter(r => r.run_id !== runId))
    } catch {
      // silencioso
    }
  }

  // ── Quality flow ──────────────────────────────────────────────────────────

  const handleStartQuality = async () => {
    if (!run?.run_id) return
    setError(null)
    setPhase('quality-running')
    setQualityProgressMsg('Iniciando análisis de calidad...')

    try {
      const { quality_run_id } = await api.startQuality(run.run_id)
      setQualityRunId(quality_run_id)

      pollRef.current = setInterval(async () => {
        try {
          const status = await api.getQualityStatus(quality_run_id)
          if (status.progress_msg) setQualityProgressMsg(status.progress_msg)

          if (status.status === 'completed' && status.contract_b) {
            if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null }
            setContractB(status.contract_b)
            setPhase('quality-review')
          } else if (status.status === 'failed') {
            if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null }
            setError(status.error ?? 'Error en el análisis de calidad')
            setPhase('error')
          }
        } catch {
          // ignorar errores transitorios de red
        }
      }, 3000)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error al iniciar el análisis')
      setPhase('error')
    }
  }

  const handleSubmitReview = async (
    decisions: ScenarioDecision[],
    reviewer: string,
    feedback: string,
    reviewStatus: string,
    useLlmRisk: boolean,
  ) => {
    if (!qualityRunId) return
    setPhase('quality-submitting')
    setError(null)
    try {
      const result = await api.submitReview(qualityRunId, {
        reviewer,
        decisions,
        feedback: feedback || undefined,
        review_status: reviewStatus,
        use_llm_risk: useLlmRisk,
      })
      setRiskMatrix(result.risk_matrix ?? null)
      setPhase('quality-done')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error al enviar la revisión')
      setPhase('error')
    }
  }

  const handleDownloadPdf = () => {
    if (qualityRunId) window.open(api.getPdfUrl(qualityRunId), '_blank')
  }

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex flex-col items-center">
      {/* Header */}
      <header className="w-full border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-5xl mx-auto w-full px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-violet-600 flex items-center justify-center">
              <Cpu className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-none">NovaTetch</h1>
              <p className="text-xs text-slate-400">Requirements Refiner + QualityAI</p>
            </div>
          </div>
          {phase !== 'idle' && (
            <button
              onClick={handleReset}
              className="cursor-pointer text-sm text-slate-400 hover:text-slate-200 transition-colors flex items-center gap-1"
            >
              <Plus className="h-4 w-4" />
              Nuevo análisis
            </button>
          )}
        </div>
      </header>

      <main className="flex-1 w-full max-w-5xl mx-auto px-6 py-10 flex flex-col gap-10">
        {/* Hero */}
        {phase === 'idle' && (
          <div className="text-center mb-2">
            <h2 className="text-3xl font-bold text-white mb-2">
              Transforma requerimientos en historias de usuario
            </h2>
            <p className="text-slate-400 max-w-xl mx-auto">
              Describe tu requerimiento en lenguaje natural. El agente detecta ambigüedades,
              te pide aclaraciones, genera historias de usuario validadas y luego aplica
              análisis de calidad ISO 25010 con escenarios Gherkin y matriz de riesgos.
            </p>
          </div>
        )}

        {/* Input form */}
        {(phase === 'idle' || phase === 'analyzing') && (
          <section className="rounded-2xl border border-slate-700 bg-slate-800/40 p-6">
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
              Requerimiento
            </h3>
            <PromptForm onAnalyze={handleAnalyze} loading={phase === 'analyzing'} />
          </section>
        )}

        {/* Ambiguity resolver */}
        {phase === 'resolving' && (
          <section className="rounded-2xl border border-slate-700 bg-slate-800/40 p-6">
            <AmbiguityResolver
              ambiguities={ambiguities}
              onGenerate={handleGenerate}
              loading={false}
            />
          </section>
        )}

        {/* Generating stories */}
        {phase === 'generating' && (
          <div className="flex flex-col items-center gap-4 py-16">
            <div className="h-12 w-12 animate-spin rounded-full border-4 border-violet-500 border-t-transparent" />
            <p className="text-slate-300 font-medium">Generando historias de usuario...</p>
            <p className="text-slate-500 text-sm">El LLM está procesando el requerimiento con RAG</p>
          </div>
        )}

        {/* Quality running */}
        {phase === 'quality-running' && (
          <div className="flex flex-col items-center gap-4 py-16">
            <div className="h-12 w-12 animate-spin rounded-full border-4 border-violet-500 border-t-transparent" />
            <p className="text-slate-300 font-medium">Agente V3 en ejecución...</p>
            {qualityProgressMsg && (
              <p className="text-slate-500 text-sm max-w-md text-center">{qualityProgressMsg}</p>
            )}
            <p className="text-slate-600 text-xs">Esto puede tomar varios minutos según el número de criterios</p>
          </div>
        )}

        {/* Quality submitting */}
        {phase === 'quality-submitting' && (
          <div className="flex flex-col items-center gap-4 py-16">
            <div className="h-12 w-12 animate-spin rounded-full border-4 border-violet-500 border-t-transparent" />
            <p className="text-slate-300 font-medium">Aplicando revisión y generando PDF...</p>
            <p className="text-slate-500 text-sm">El agente V4 está calculando la matriz de riesgos</p>
          </div>
        )}

        {/* Error */}
        {phase === 'error' && (
          <div className="rounded-2xl border border-red-500/40 bg-red-500/10 p-6">
            <h3 className="font-semibold text-red-300 mb-2">Error</h3>
            <p className="text-red-400 text-sm">{error}</p>
            <button
              onClick={handleReset}
              className="cursor-pointer mt-4 rounded-lg bg-red-500/20 px-4 py-2 text-sm text-red-300 hover:bg-red-500/30 transition-colors"
            >
              Intentar de nuevo
            </button>
          </div>
        )}

        {/* Stats bar — visible en todas las fases post-generación */}
        {(['done', 'quality-running', 'quality-review', 'quality-done'] as Phase[]).includes(phase) && run?.result && (
          <section className="flex flex-col gap-6">
            <div className="rounded-2xl border border-slate-700 bg-slate-800/40 px-6 py-5 flex flex-wrap gap-8">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Historias</p>
                <p className="text-2xl font-bold text-white">{run.result.user_stories.length}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Criterios</p>
                <p className="text-2xl font-bold text-white">
                  {run.result.user_stories.reduce((s, st) => s + st.acceptance_criteria.length, 0)}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Ambigüedades</p>
                <p className="text-2xl font-bold text-white">{run.result.total_ambiguities_found}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Suposiciones</p>
                <p className="text-2xl font-bold text-white">{run.result.total_assumptions_made}</p>
              </div>
              <div className="ml-auto text-right">
                <p className="text-xs text-slate-500 mb-1">ID de ejecución</p>
                <p className="font-mono text-xs text-violet-400">{run.run_id}</p>
              </div>
            </div>

            {/* Contexto del proyecto */}
            {run.result.project_context && (
              <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 px-5 py-4">
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Contexto del proyecto</p>
                <p className="text-sm text-slate-300">{run.result.project_context}</p>
              </div>
            )}

            {/* Historias de usuario — siempre visibles */}
            <div className="flex flex-col gap-4">
              {run.result.user_stories.map((story, i) => (
                <StoryCard key={story.id} story={story} index={i} />
              ))}
            </div>

            {/* Quality panel trigger */}
            {phase === 'done' && (
              <QualityPanel onStart={handleStartQuality} loading={false} />
            )}
            {phase === 'quality-running' && (
              <QualityPanel onStart={handleStartQuality} loading={true} progressMsg={qualityProgressMsg} />
            )}
          </section>
        )}

        {/* Quality Review */}
        {phase === 'quality-review' && contractB && (
          <section className="flex flex-col gap-6">
            <div className="rounded-xl border border-violet-500/30 bg-violet-500/5 px-5 py-4">
              <h3 className="font-semibold text-white mb-1">
                Revisión de calidad — {contractB.total_scenarios} escenarios Gherkin
              </h3>
              <p className="text-sm text-slate-400">
                Todos los escenarios están pre-aceptados. Cambia solo los que necesites
                reclasificar o comentar, luego envía la revisión para generar el acta PDF.
              </p>
            </div>
            <ScenarioReviewer
              contractB={contractB}
              onSubmit={handleSubmitReview}
              submitting={false}
            />
          </section>
        )}

        {/* Quality Done: Risk Matrix + PDF */}
        {phase === 'quality-done' && riskMatrix && (
          <section className="flex flex-col gap-6">
            <div className="rounded-xl border border-green-500/30 bg-green-500/5 px-5 py-4">
              <h3 className="font-semibold text-white mb-1">Análisis de calidad completado</h3>
              <p className="text-sm text-slate-400">
                La revisión fue procesada. El acta PDF está disponible para descarga.
              </p>
            </div>
            <RiskMatrixComponent
              matrix={riskMatrix}
              onDownloadPdf={handleDownloadPdf}
            />
          </section>
        )}

        {/* History */}
        {phase === 'idle' && runs.length > 0 && (
          <RunHistory runs={runs} onSelect={handleSelectRun} onDelete={handleDelete} />
        )}
      </main>
    </div>
  )
}
