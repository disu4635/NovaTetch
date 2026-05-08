import { useState, useEffect } from 'react'
import { api } from './api/client'
import type { Ambiguity, Resolution, RunDetail, RunSummary } from './types'
import PromptForm from './components/PromptForm'
import AmbiguityResolver from './components/AmbiguityResolver'
import StoryCard from './components/StoryCard'
import RunHistory from './components/RunHistory'

type Phase = 'idle' | 'analyzing' | 'resolving' | 'generating' | 'done' | 'error'

export default function App() {
  const [phase, setPhase] = useState<Phase>('idle')
  const [currentPrompt, setCurrentPrompt] = useState('')
  const [ambiguities, setAmbiguities] = useState<Ambiguity[]>([])
  const [run, setRun] = useState<RunDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [runs, setRuns] = useState<RunSummary[]>([])

  useEffect(() => {
    api.getRuns().then(setRuns).catch(() => {})
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
    try {
      const detail = await api.getRun(runId)
      setRun(detail)
      setCurrentPrompt(detail.prompt)
      setAmbiguities([])
      setPhase('done')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error al cargar el run')
    }
  }

  const handleReset = () => {
    setPhase('idle')
    setCurrentPrompt('')
    setAmbiguities([])
    setRun(null)
    setError(null)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-violet-600 flex items-center justify-center">
              <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-none">QualityAI</h1>
              <p className="text-xs text-slate-400">Requirements Refiner</p>
            </div>
          </div>
          {phase !== 'idle' && (
            <button
              onClick={handleReset}
              className="text-sm text-slate-400 hover:text-slate-200 transition-colors flex items-center gap-1"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Nuevo análisis
            </button>
          )}
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-10 flex flex-col gap-10">
        {/* Hero */}
        {phase === 'idle' && (
          <div className="text-center mb-2">
            <h2 className="text-3xl font-bold text-white mb-2">
              Transforma requerimientos en historias de usuario
            </h2>
            <p className="text-slate-400 max-w-xl mx-auto">
              Describe tu requerimiento en lenguaje natural. El agente detecta ambigüedades,
              te pide aclaraciones y genera historias de usuario validadas con criterios de aceptación.
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

        {/* Generating */}
        {phase === 'generating' && (
          <div className="flex flex-col items-center gap-4 py-16">
            <div className="h-12 w-12 animate-spin rounded-full border-4 border-violet-500 border-t-transparent" />
            <p className="text-slate-300 font-medium">Generando historias de usuario...</p>
            <p className="text-slate-500 text-sm">El LLM está procesando el requerimiento con RAG</p>
          </div>
        )}

        {/* Error */}
        {phase === 'error' && (
          <div className="rounded-2xl border border-red-500/40 bg-red-500/10 p-6">
            <h3 className="font-semibold text-red-300 mb-2">Error</h3>
            <p className="text-red-400 text-sm">{error}</p>
            <button
              onClick={handleReset}
              className="mt-4 rounded-lg bg-red-500/20 px-4 py-2 text-sm text-red-300 hover:bg-red-500/30 transition-colors"
            >
              Intentar de nuevo
            </button>
          </div>
        )}

        {/* Results */}
        {phase === 'done' && run?.result && (
          <section className="flex flex-col gap-6">
            {/* Stats bar */}
            <div className="rounded-2xl border border-slate-700 bg-slate-800/40 p-5 flex flex-wrap gap-6">
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
                <p className="text-xs text-slate-500 mb-1">Run ID</p>
                <p className="font-mono text-xs text-violet-400">{run.run_id}</p>
              </div>
            </div>

            {/* Context */}
            {run.result.project_context && (
              <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 px-5 py-4">
                <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Contexto del proyecto</p>
                <p className="text-sm text-slate-300">{run.result.project_context}</p>
              </div>
            )}

            {/* Stories */}
            <div className="flex flex-col gap-4">
              {run.result.user_stories.map((story, i) => (
                <StoryCard key={story.id} story={story} index={i} />
              ))}
            </div>
          </section>
        )}

        {/* History */}
        {phase === 'idle' && runs.length > 0 && (
          <RunHistory runs={runs} onSelect={handleSelectRun} />
        )}
      </main>
    </div>
  )
}
