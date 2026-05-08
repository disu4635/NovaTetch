import { useState } from 'react'
import type { Ambiguity, Resolution } from '../types'

interface Props {
  ambiguities: Ambiguity[]
  onGenerate: (resolutions: Resolution[]) => void
  loading: boolean
}

const severityConfig = {
  alta: { color: 'text-red-400 border-red-500/40 bg-red-500/10', dot: 'bg-red-400', label: 'Alta' },
  media: { color: 'text-amber-400 border-amber-500/40 bg-amber-500/10', dot: 'bg-amber-400', label: 'Media' },
  baja: { color: 'text-emerald-400 border-emerald-500/40 bg-emerald-500/10', dot: 'bg-emerald-400', label: 'Baja' },
}

type Choice = 'accept' | 'custom' | 'dismiss'

interface CardState {
  choice: Choice
  custom: string
}

export default function AmbiguityResolver({ ambiguities, onGenerate, loading }: Props) {
  const initial: CardState[] = ambiguities.map(() => ({ choice: 'accept', custom: '' }))
  const [states, setStates] = useState<CardState[]>(initial)

  const update = (i: number, patch: Partial<CardState>) =>
    setStates(prev => prev.map((s, idx) => (idx === i ? { ...s, ...patch } : s)))

  const handleGenerate = () => {
    const resolutions: Resolution[] = ambiguities.map((amb, i) => {
      const s = states[i]
      if (s.choice === 'dismiss') {
        return { word: amb.word, category: amb.category, analyst_resolution: '', status: 'dismissed' }
      }
      const text = s.choice === 'custom' ? s.custom.trim() : amb.suggestion
      return { word: amb.word, category: amb.category, analyst_resolution: text, status: 'resolved' }
    })
    onGenerate(resolutions)
  }

  const allReady = states.every(s => {
    if (s.choice === 'dismiss') return true
    if (s.choice === 'accept') return true
    return s.custom.trim().length > 0
  })

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-200">
          Ambigüedades detectadas
          <span className="ml-2 rounded-full bg-violet-500/20 px-2 py-0.5 text-sm text-violet-300">
            {ambiguities.length}
          </span>
        </h2>
        <div className="flex gap-3 text-xs text-slate-400">
          {(['alta', 'media', 'baja'] as const).map(sev => {
            const count = ambiguities.filter(a => a.severity === sev).length
            if (!count) return null
            const cfg = severityConfig[sev]
            return (
              <span key={sev} className="flex items-center gap-1">
                <span className={`h-2 w-2 rounded-full ${cfg.dot}`} />
                {cfg.label}: {count}
              </span>
            )
          })}
        </div>
      </div>

      {ambiguities.map((amb, i) => {
        const cfg = severityConfig[amb.severity]
        const s = states[i]
        return (
          <div key={i} className={`rounded-xl border p-5 ${cfg.color}`}>
            <div className="flex items-start justify-between gap-4 mb-3">
              <div>
                <span className="font-semibold text-base">"{amb.word}"</span>
                <span className="ml-2 text-xs opacity-70">{amb.category.replace(/_/g, ' ')}</span>
              </div>
              <span className={`shrink-0 text-xs font-medium px-2 py-0.5 rounded-full border ${cfg.color}`}>
                {cfg.label}
              </span>
            </div>

            <p className="text-sm opacity-80 italic mb-1">Contexto: {amb.context}</p>
            <p className="text-sm mb-4">
              <span className="font-medium">Sugerencia:</span> {amb.suggestion}
            </p>

            <div className="flex flex-col gap-2">
              {(
                [
                  { value: 'accept', label: 'Aceptar sugerencia' },
                  { value: 'custom', label: 'Escribir mi resolución' },
                  { value: 'dismiss', label: 'No es ambiguo' },
                ] as { value: Choice; label: string }[]
              ).map(opt => (
                <label key={opt.value} className="flex items-center gap-2 cursor-pointer text-sm">
                  <input
                    type="radio"
                    name={`choice-${i}`}
                    value={opt.value}
                    checked={s.choice === opt.value}
                    onChange={() => update(i, { choice: opt.value })}
                    className="accent-violet-500"
                  />
                  {opt.label}
                </label>
              ))}

              {s.choice === 'custom' && (
                <input
                  type="text"
                  value={s.custom}
                  onChange={e => update(i, { custom: e.target.value })}
                  placeholder="Ej: Tiempo de respuesta menor a 2 segundos"
                  className="mt-1 w-full rounded-lg border border-slate-600 bg-slate-900/60 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
              )}
            </div>
          </div>
        )
      })}

      <button
        onClick={handleGenerate}
        disabled={!allReady || loading}
        className="cursor-pointer self-end flex items-center gap-2 rounded-xl bg-violet-600 px-6 py-3 font-semibold text-white hover:bg-violet-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? (
          <>
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            Generando historias...
          </>
        ) : (
          'Generar historias de usuario'
        )}
      </button>
    </div>
  )
}
