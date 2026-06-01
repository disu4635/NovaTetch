import { Code2, Loader2 } from 'lucide-react'

interface Props {
  onStart: () => void
  loading: boolean
  progressMsg?: string
}

export default function CodeGenPanel({ onStart, loading, progressMsg }: Props) {
  return (
    <section className="rounded-2xl border border-emerald-500/30 bg-emerald-500/5 p-6">
      <div className="flex items-start gap-4">
        <div className="h-10 w-10 rounded-lg bg-emerald-600/20 flex items-center justify-center shrink-0">
          <Code2 className="h-5 w-5 text-emerald-400" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-white mb-1">Generación de código</h3>
          <p className="text-sm text-slate-400 mb-4">
            Genera implementaciones Python y tests Pytest a partir de los escenarios aprobados.
            Incluye análisis estático (complejidad ciclomática, cognitiva e índice de mantenibilidad),
            cobertura de ramas y trazabilidad CMMI L3.
          </p>

          {loading ? (
            <div className="flex items-center gap-3">
              <Loader2 className="h-5 w-5 text-emerald-400 animate-spin shrink-0" />
              <div>
                <p className="text-sm font-medium text-emerald-300">Generando código y tests...</p>
                {progressMsg && (
                  <p className="text-xs text-slate-500 mt-0.5">{progressMsg}</p>
                )}
              </div>
            </div>
          ) : (
            <button
              onClick={onStart}
              className="cursor-pointer inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 transition-colors"
            >
              <Code2 className="h-4 w-4" />
              Generar código
            </button>
          )}
        </div>
      </div>
    </section>
  )
}
