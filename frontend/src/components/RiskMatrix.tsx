import { Download } from 'lucide-react'
import type { RiskMatrix as RiskMatrixType } from '../types'

const NIVEL_COLOR: Record<string, string> = {
  CRITICO: 'bg-red-700/30 text-red-300 border-red-700/50',
  ALTO:    'bg-orange-700/30 text-orange-300 border-orange-700/50',
  MEDIO:   'bg-yellow-700/30 text-yellow-300 border-yellow-700/50',
  BAJO:    'bg-green-700/30 text-green-300 border-green-700/50',
}

const NIVEL_BADGE: Record<string, string> = {
  CRITICO: 'bg-red-600 text-white',
  ALTO:    'bg-orange-600 text-white',
  MEDIO:   'bg-yellow-600 text-white',
  BAJO:    'bg-green-700 text-white',
}

interface Props {
  matrix: RiskMatrixType
  onDownloadPdf: () => void
}

export default function RiskMatrix({ matrix, onDownloadPdf }: Props) {
  const res = matrix.resumen_ejecutivo

  return (
    <div className="flex flex-col gap-6">
      {/* Resumen ejecutivo */}
      <div className="rounded-2xl border border-slate-700 bg-slate-800/40 px-6 py-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-white">Matriz de Riesgos ISO/IEC 25010</h3>
          <button
            onClick={onDownloadPdf}
            className="cursor-pointer inline-flex items-center gap-2 rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-500 transition-colors"
          >
            <Download className="h-4 w-4" />
            Descargar acta PDF
          </button>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: 'Crítico', count: res.criticos, color: 'bg-red-700/30 border-red-700/50 text-red-300' },
            { label: 'Alto',    count: res.altos,    color: 'bg-orange-700/30 border-orange-700/50 text-orange-300' },
            { label: 'Medio',   count: res.medios,   color: 'bg-yellow-700/30 border-yellow-700/50 text-yellow-300' },
            { label: 'Bajo',    count: res.bajos,    color: 'bg-green-700/30 border-green-700/50 text-green-300' },
          ].map(item => (
            <div key={item.label} className={`rounded-xl border p-4 text-center ${item.color}`}>
              <p className="text-xl font-semibold tabular-nums">{item.count}</p>
              <p className="text-xs mt-1">{item.label}</p>
            </div>
          ))}
        </div>

        {res.qc_sin_cobertura.length > 0 && (
          <p className="mt-3 text-xs text-red-400">
            Sin cobertura: {res.qc_sin_cobertura.join(', ')}
          </p>
        )}
        <p className="mt-2 text-xs text-slate-500">
          {matrix.enriquecido_llm
            ? 'Recomendaciones enriquecidas con LLM (Groq)'
            : 'Recomendaciones de capa determinista'}
        </p>
      </div>

      {/* Tabla de riesgos */}
      <div className="flex flex-col gap-3">
        {matrix.riesgos.map(r => (
          <div
            key={r.qc}
            className={`rounded-xl border p-4 ${NIVEL_COLOR[r.nivel] ?? 'border-slate-700 bg-slate-800/40 text-slate-300'}`}
          >
            <div className="flex items-start gap-3">
              <span className={`shrink-0 mt-0.5 inline-block px-2 py-0.5 rounded text-xs font-bold ${NIVEL_BADGE[r.nivel] ?? 'bg-slate-600 text-white'}`}>
                {r.nivel}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-sm">{r.qc.replace(/_/g, ' ')}</span>
                  <span className="text-xs opacity-70">
                    {r.n_escenarios} esc. ({r.pct_total}%)
                  </span>
                </div>
                <p className="text-xs opacity-80 mb-2">{r.descripcion_riesgo}</p>
                {r.recomendacion_llm ? (
                  <p className="text-xs opacity-70">
                    <span className="font-semibold">Recomendación: </span>
                    {r.recomendacion_llm}
                  </p>
                ) : (
                  <p className="text-xs opacity-70">
                    <span className="font-semibold">Recomendación: </span>
                    {r.recomendacion_base}
                  </p>
                )}
                {r.analisis_impacto && (
                  <p className="text-xs opacity-60 mt-1">
                    <span className="font-semibold">Impacto: </span>
                    {r.analisis_impacto}
                  </p>
                )}
                {r.criterios_exito && (
                  <p className="text-xs opacity-60 mt-1">
                    <span className="font-semibold">Criterios de éxito: </span>
                    {r.criterios_exito}
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
