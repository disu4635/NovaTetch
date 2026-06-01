import { useState, useEffect, useRef } from 'react'
import { Cpu, RotateCcw, ChevronsUpDown, ChevronsDownUp, Copy, CheckCheck } from 'lucide-react'
import { api } from './api/client'
import type {
  Ambiguity,
  Resolution,
  RunDetail,
  RunSummary,
  ContractB,
  ContractC,
  RiskMatrix,
  ScenarioDecision,
  ModuleAction,
  QualityForRunResponse,
  UserStory,
} from './types'
import PromptForm from './components/PromptForm'
import AmbiguityResolver from './components/AmbiguityResolver'
import StoryCard from './components/StoryCard'
import RunHistory from './components/RunHistory'
import QualityPanel from './components/QualityPanel'
import ScenarioReviewer from './components/ScenarioReviewer'
import RiskMatrixComponent from './components/RiskMatrix'
import CodeGenPanel from './components/CodeGenPanel'
import CodeReviewer from './components/CodeReviewer'
import CodeGenResults from './components/CodeGenResults'

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
  | 'codegen-running'
  | 'codegen-review'
  | 'codegen-submitting'
  | 'codegen-done'

// Phase to return to when recovering from an error mid-pipeline
const ERROR_RECOVERY: Partial<Record<Phase, Phase>> = {
  'quality-running':    'done',
  'quality-submitting': 'quality-review',
  'codegen-running':    'quality-done',
  'codegen-submitting': 'codegen-review',
}

function copyAllStories(stories: UserStory[]): string {
  const sep = '\n\n' + '─'.repeat(60) + '\n\n'
  return stories.map(story => {
    const criteria = story.acceptance_criteria.map((ac, i) =>
      `  ${i + 1}. ${ac.description}\n     Given ${ac.given}\n     When ${ac.when}\n     Then ${ac.then}`
    ).join('\n\n')
    return `[${story.id}] ${story.title}\n\nComo ${story.as_a}\nQuiero ${story.i_want}\nPara que ${story.so_that}\n\nCriterios de aceptación:\n${criteria}`
  }).join(sep)
}

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

  // Codegen state
  const [codegenRunId, setCodegenRunId] = useState<string | null>(null)
  const [codegenProgressMsg, setCodegenProgressMsg] = useState<string>('')
  const [contractC, setContractC] = useState<ContractC | null>(null)

  // Story expansion: true=expanded, false=collapsed; missing key → first-card default
  const [expandedMap, setExpandedMap] = useState<Record<string, boolean>>({})
  const [copiedAll, setCopiedAll] = useState(false)

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  // Tracks which phase we were in before an error, for contextual recovery
  const prevPhaseRef = useRef<Phase>('idle')

  useEffect(() => {
    api.getRuns().then(setRuns).catch(() => {})
  }, [])

  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [])

  // ── Story expansion helpers ───────────────────────────────────────────────

  const collapseAllStories = (stories: UserStory[]) =>
    setExpandedMap(Object.fromEntries(stories.map(s => [s.id, false])))

  const expandAllStories = (stories: UserStory[]) =>
    setExpandedMap(Object.fromEntries(stories.map(s => [s.id, true])))

  const handleCopyAll = async () => {
    if (!run?.result) return
    await navigator.clipboard.writeText(copyAllStories(run.result.user_stories))
    setCopiedAll(true)
    setTimeout(() => setCopiedAll(false), 2000)
  }

  // ── Analysis flow ─────────────────────────────────────────────────────────

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
      prevPhaseRef.current = 'idle'
      setError(e instanceof Error ? e.message : 'No se pudo detectar ambigüedades. Intenta de nuevo.')
      setPhase('error')
    }
  }

  const doGenerate = async (prompt: string, resolutions: Resolution[]) => {
    setPhase('generating')
    setError(null)
    try {
      const result = await api.generate(prompt, resolutions)
      setRun(result)
      setExpandedMap({}) // reset to default (first card open via fallback)
      setPhase('done')
      api.getRuns().then(setRuns).catch(() => {})
    } catch (e: unknown) {
      prevPhaseRef.current = 'generating'
      setError(e instanceof Error ? e.message : 'No se pudieron generar las historias. Intenta de nuevo.')
      setPhase('error')
    }
  }

  const handleGenerate = (resolutions: Resolution[]) => doGenerate(currentPrompt, resolutions)

  const handleSelectRun = async (runId: string) => {
    setError(null)
    setQualityRunId(null)
    setContractB(null)
    setRiskMatrix(null)
    setQualityProgressMsg('')
    setExpandedMap({})

    try {
      const detail = await api.getRun(runId)
      setRun(detail)
      setCurrentPrompt(detail.prompt)
      setAmbiguities([])

      const qf: QualityForRunResponse = await api.getQualityForRun(runId)
      if (qf.found && qf.quality_run_id) {
        setQualityRunId(qf.quality_run_id)
        if (qf.has_review && qf.risk_matrix) {
          setRiskMatrix(qf.risk_matrix)

          const cgf = await api.getCodegenForQualityRun(qf.quality_run_id)
          if (cgf.found && cgf.codegen_run_id && cgf.contract_c) {
            setCodegenRunId(cgf.codegen_run_id)
            setContractC(cgf.contract_c)
            if (cgf.has_review) {
              setPhase('codegen-done')
            } else {
              // Restore to codegen-review: collapse stories so reviewer is visible
              if (detail.result?.user_stories) collapseAllStories(detail.result.user_stories)
              setPhase('codegen-review')
            }
          } else {
            setPhase('quality-done')
          }
        } else if (qf.contract_b) {
          setContractB(qf.contract_b)
          // Restore to quality-review: collapse stories so reviewer is visible
          if (detail.result?.user_stories) collapseAllStories(detail.result.user_stories)
          setPhase('quality-review')
        } else {
          setPhase('done')
        }
      } else {
        setPhase('done')
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'No se pudo cargar el análisis. Intenta de nuevo.')
    }
  }

  const handleReset = () => {
    if (run !== null) {
      if (!window.confirm('¿Iniciar un análisis nuevo? El progreso actual no se guardará.')) return
    }
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
    setCodegenRunId(null)
    setCodegenProgressMsg('')
    setContractC(null)
    setExpandedMap({})
  }

  const handleErrorRecover = () => {
    const target = ERROR_RECOVERY[prevPhaseRef.current]
    if (target) {
      setError(null)
      setPhase(target)
    } else {
      handleReset()
    }
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
    prevPhaseRef.current = 'quality-running'
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
            // Collapse stories so ScenarioReviewer is immediately visible on scroll
            if (run?.result?.user_stories) collapseAllStories(run.result.user_stories)
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
      setError(e instanceof Error ? e.message : 'No se pudo iniciar el análisis de calidad. Intenta de nuevo.')
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
    prevPhaseRef.current = 'quality-submitting'
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
      setError(e instanceof Error ? e.message : 'No se pudo procesar la revisión de escenarios. Intenta de nuevo.')
      setPhase('error')
    }
  }

  const handleDownloadPdf = () => {
    if (qualityRunId) window.open(api.getPdfUrl(qualityRunId), '_blank')
  }

  // ── Codegen flow ──────────────────────────────────────────────────────────

  const handleStartCodegen = async () => {
    if (!qualityRunId) return
    setError(null)
    prevPhaseRef.current = 'codegen-running'
    setPhase('codegen-running')
    setCodegenProgressMsg('Iniciando generación de código...')

    try {
      const { codegen_run_id } = await api.startCodegen(qualityRunId)
      setCodegenRunId(codegen_run_id)

      pollRef.current = setInterval(async () => {
        try {
          const status = await api.getCodegenStatus(codegen_run_id)
          if (status.progress_msg) setCodegenProgressMsg(status.progress_msg)

          if (status.status === 'completed' && status.contract_c) {
            if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null }
            setContractC(status.contract_c)
            // Collapse stories so CodeReviewer is immediately visible
            if (run?.result?.user_stories) collapseAllStories(run.result.user_stories)
            setPhase('codegen-review')
          } else if (status.status === 'failed') {
            if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null }
            setError(status.error ?? 'Error en la generación de código')
            setPhase('error')
          }
        } catch {
          // ignorar errores transitorios
        }
      }, 3000)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'No se pudo iniciar la generación de código. Intenta de nuevo.')
      setPhase('error')
    }
  }

  const handleSubmitCodeReview = async (
    actions: ModuleAction[],
    reviewer: string,
    verdict: string,
    feedback: string,
  ) => {
    if (!codegenRunId) return
    prevPhaseRef.current = 'codegen-submitting'
    setPhase('codegen-submitting')
    setError(null)
    try {
      const result = await api.submitCodeReview(codegenRunId, {
        reviewer,
        module_actions: actions,
        verdict,
        feedback: feedback || undefined,
      }) as { codegen_run_id: string; reviewed_contract_c: ContractC }
      setContractC(result.reviewed_contract_c)
      setPhase('codegen-done')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'No se pudo procesar la revisión del código. Intenta de nuevo.')
      setPhase('error')
    }
  }

  const handleDownloadCode = () => {
    if (codegenRunId) window.open(api.getCodeDownloadUrl(codegenRunId), '_blank')
  }

  // ── Render ────────────────────────────────────────────────────────────────

  const postGenPhases: Phase[] = ['done', 'quality-running', 'quality-review', 'quality-done', 'codegen-running', 'codegen-review', 'codegen-done']
  const hasRecovery = ERROR_RECOVERY[prevPhaseRef.current] !== undefined

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center">
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
              type="button"
              onClick={handleReset}
              className="cursor-pointer text-sm text-slate-400 hover:text-slate-200 transition-colors flex items-center gap-1.5"
            >
              <RotateCcw className="h-4 w-4" aria-hidden />
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
            <p className="text-slate-300 font-medium">Analizando calidad ISO 25010...</p>
            {qualityProgressMsg && (
              <p className="text-slate-500 text-sm max-w-md text-center">{qualityProgressMsg}</p>
            )}
            <p className="text-slate-600 text-xs">Puede tomar varios minutos según el número de criterios de aceptación</p>
          </div>
        )}

        {/* Quality submitting */}
        {phase === 'quality-submitting' && (
          <div className="flex flex-col items-center gap-4 py-16">
            <div className="h-12 w-12 animate-spin rounded-full border-4 border-violet-500 border-t-transparent" />
            <p className="text-slate-300 font-medium">Aplicando revisión y generando acta PDF...</p>
            <p className="text-slate-500 text-sm">Calculando la matriz de riesgos con las decisiones del revisor</p>
          </div>
        )}

        {/* Error */}
        {phase === 'error' && (
          <div className="rounded-2xl border border-red-500/40 bg-red-500/10 p-6">
            <h3 className="font-semibold text-red-300 mb-2">Error</h3>
            <p className="text-red-400 text-sm">{error}</p>
            <div className="flex gap-3 mt-4">
              {hasRecovery && (
                <button
                  type="button"
                  onClick={handleErrorRecover}
                  className="cursor-pointer rounded-lg bg-slate-700/60 px-4 py-2 text-sm text-slate-300 hover:bg-slate-700 transition-colors"
                >
                  Volver al paso anterior
                </button>
              )}
              <button
                type="button"
                onClick={() => { prevPhaseRef.current = 'idle'; handleReset() }}
                className="cursor-pointer rounded-lg bg-red-500/20 px-4 py-2 text-sm text-red-300 hover:bg-red-500/30 transition-colors"
              >
                {hasRecovery ? 'Empezar de nuevo' : 'Intentar de nuevo'}
              </button>
            </div>
          </div>
        )}

        {/* Stats bar + stories — visible en todas las fases post-generación */}
        {postGenPhases.includes(phase) && run?.result && (
          <section className="flex flex-col gap-6">
            {/* Run metadata — compact inline row */}
            <div className="flex flex-wrap items-center gap-x-5 gap-y-1.5 text-sm pb-2 border-b border-slate-800/80">
              <span>
                <span className="font-semibold tabular-nums text-slate-200">{run.result.user_stories.length}</span>
                <span className="text-slate-500 ml-1.5">historias</span>
              </span>
              <span className="text-slate-700" aria-hidden>·</span>
              <span>
                <span className="font-semibold tabular-nums text-slate-200">
                  {run.result.user_stories.reduce((s, st) => s + st.acceptance_criteria.length, 0)}
                </span>
                <span className="text-slate-500 ml-1.5">criterios</span>
              </span>
              <span className="text-slate-700" aria-hidden>·</span>
              <span>
                <span className="font-semibold tabular-nums text-slate-200">{run.result.total_ambiguities_found}</span>
                <span className="text-slate-500 ml-1.5">ambigüedades detectadas</span>
              </span>
              <span className="text-slate-700" aria-hidden>·</span>
              <span>
                <span className="font-semibold tabular-nums text-slate-200">{run.result.total_assumptions_made}</span>
                <span className="text-slate-500 ml-1.5">suposiciones</span>
              </span>
              <span className="ml-auto font-mono text-xs text-slate-600">{run.run_id}</span>
            </div>

            {/* Contexto del proyecto */}
            {run.result.project_context && (
              <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 px-5 py-4">
                <p className="text-xs font-medium text-slate-500 mb-1">Contexto del proyecto</p>
                <p className="text-sm text-slate-300">{run.result.project_context}</p>
              </div>
            )}

            {/* Stories toolbar */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-400">
                {run.result.user_stories.length} historias de usuario
              </span>
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => expandAllStories(run.result!.user_stories)}
                  className="cursor-pointer inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 transition-colors"
                  aria-label="Expandir todas las historias"
                >
                  <ChevronsUpDown className="h-3.5 w-3.5" aria-hidden />
                  Expandir
                </button>
                <button
                  type="button"
                  onClick={() => collapseAllStories(run.result!.user_stories)}
                  className="cursor-pointer inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 transition-colors"
                  aria-label="Colapsar todas las historias"
                >
                  <ChevronsDownUp className="h-3.5 w-3.5" aria-hidden />
                  Colapsar
                </button>
                <button
                  type="button"
                  onClick={handleCopyAll}
                  className="cursor-pointer inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-700/50 transition-colors"
                  aria-label="Copiar todas las historias al portapapeles"
                >
                  {copiedAll
                    ? <><CheckCheck className="h-3.5 w-3.5 text-emerald-400" aria-hidden /><span className="text-emerald-400">Copiado</span></>
                    : <><Copy className="h-3.5 w-3.5" aria-hidden />Copiar todo</>
                  }
                </button>
              </div>
            </div>

            {/* Historias de usuario */}
            <div className="flex flex-col gap-4">
              {run.result.user_stories.map((story, i) => (
                <StoryCard
                  key={story.id}
                  story={story}
                  index={i}
                  isExpanded={expandedMap[story.id] ?? (i === 0)}
                  onToggle={() => setExpandedMap(prev => ({
                    ...prev,
                    [story.id]: !(prev[story.id] ?? (i === 0)),
                  }))}
                />
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

        {/* Quality Done + codegen phases: Risk Matrix */}
        {(['quality-done', 'codegen-running', 'codegen-review', 'codegen-done'] as Phase[]).includes(phase) && riskMatrix && (
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
            {phase === 'quality-done' && (
              <CodeGenPanel onStart={handleStartCodegen} loading={false} />
            )}
            {phase === 'codegen-running' && (
              <CodeGenPanel onStart={handleStartCodegen} loading={true} progressMsg={codegenProgressMsg} />
            )}
          </section>
        )}

        {/* Codegen submitting */}
        {phase === 'codegen-submitting' && (
          <div className="flex flex-col items-center gap-4 py-16">
            <div className="h-12 w-12 animate-spin rounded-full border-4 border-emerald-500 border-t-transparent" />
            <p className="text-slate-300 font-medium">Aplicando revisión del código...</p>
          </div>
        )}

        {/* Codegen Review */}
        {phase === 'codegen-review' && contractC && (
          <section className="flex flex-col gap-6">
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/5 px-5 py-4">
              <h3 className="font-semibold text-white mb-1">
                Revisión de código — {contractC.total_modules} módulos generados
              </h3>
              <p className="text-sm text-slate-400">
                Se generó el código, los tests y el análisis estático.
                Revisa cada módulo como desarrollador senior y emite tu veredicto.
              </p>
            </div>
            <CodeReviewer
              contractC={contractC}
              onSubmit={handleSubmitCodeReview}
              submitting={false}
            />
          </section>
        )}

        {/* Codegen Done */}
        {phase === 'codegen-done' && contractC && (
          <section className="flex flex-col gap-6">
            <CodeGenResults
              contractC={contractC}
              onDownloadCode={handleDownloadCode}
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
