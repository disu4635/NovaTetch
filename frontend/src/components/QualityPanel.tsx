import { FlaskConical, Loader2 } from 'lucide-react'

interface Props {
  onStart: () => void
  loading: boolean
  progressMsg?: string
}

export default function QualityPanel({ onStart, loading, progressMsg }: Props) {
  return (
    <section className="rounded-2xl border border-violet-500/30 bg-violet-500/5 p-6">
      <div className="flex items-start gap-4">
        <div className="h-10 w-10 rounded-lg bg-violet-600/20 flex items-center justify-center shrink-0">
          <FlaskConical className="h-5 w-5 text-violet-400" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-white mb-1">Análisis de calidad ISO 25010</h3>
          <p className="text-sm text-slate-400 mb-4">
            Genera escenarios Gherkin para cada criterio de aceptación, clasificados según ISO 25010.
            Al aprobar la revisión, produce la matriz de riesgos con recomendaciones de mitigación.
          </p>

          {loading ? (
            <div className="flex items-center gap-3">
              <Loader2 className="h-5 w-5 text-violet-400 animate-spin shrink-0" />
              <div>
                <p className="text-sm font-medium text-violet-300">Generando escenarios Gherkin...</p>
                {progressMsg && (
                  <p className="text-xs text-slate-500 mt-0.5">{progressMsg}</p>
                )}
              </div>
            </div>
          ) : (
            <button
              onClick={onStart}
              className="cursor-pointer inline-flex items-center gap-2 rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-500 transition-colors"
            >
              <FlaskConical className="h-4 w-4" />
              Iniciar análisis de calidad
            </button>
          )}
        </div>
      </div>
    </section>
  )
}
