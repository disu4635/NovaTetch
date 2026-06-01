import { useState } from 'react'
import { Check, RefreshCw, MessageSquare, ChevronDown, ChevronRight, CheckCheck } from 'lucide-react'
import type { ContractB, GherkinScenario, QualityCharacteristic, ScenarioDecision } from '../types'

const QC_OPTIONS: { value: QualityCharacteristic; label: string }[] = [
  { value: 'functional_suitability', label: 'Functional Suitability' },
  { value: 'performance_efficiency', label: 'Performance Efficiency' },
  { value: 'security',               label: 'Security' },
  { value: 'usability',              label: 'Usability' },
  { value: 'reliability',            label: 'Reliability' },
  { value: 'compatibility',          label: 'Compatibility' },
  { value: 'maintainability',        label: 'Maintainability' },
  { value: 'portability',            label: 'Portability' },
]

const QC_COLOR: Record<string, string> = {
  functional_suitability: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  performance_efficiency: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  security:               'bg-red-500/20 text-red-300 border-red-500/30',
  usability:              'bg-green-500/20 text-green-300 border-green-500/30',
  reliability:            'bg-purple-500/20 text-purple-300 border-purple-500/30',
  compatibility:          'bg-orange-500/20 text-orange-300 border-orange-500/30',
  maintainability:        'bg-slate-500/20 text-slate-300 border-slate-500/30',
  portability:            'bg-teal-500/20 text-teal-300 border-teal-500/30',
}

type ActionType = 'accepted' | 'reclassified' | 'comment' | null

interface ScenarioState {
  action: ActionType
  newQc?: QualityCharacteristic
  reason?: string
}

interface Props {
  contractB: ContractB
  onSubmit: (
    decisions: ScenarioDecision[],
    reviewer: string,
    feedback: string,
    reviewStatus: string,
    useLlmRisk: boolean,
  ) => void
  submitting: boolean
}

function ScenarioCard({
  scenario,
  state,
  onChange,
}: {
  scenario: GherkinScenario
  state: ScenarioState
  onChange: (s: ScenarioState) => void
}) {
  const [expanded, setExpanded] = useState(false)

  const qcColor = QC_COLOR[scenario.quality_characteristic] ?? 'bg-slate-500/20 text-slate-300 border-slate-500/30'
  const actionBg =
    state.action === 'accepted'     ? 'border-green-500/40 bg-green-500/5' :
    state.action === 'reclassified' ? 'border-yellow-500/40 bg-yellow-500/5' :
    state.action === 'comment'      ? 'border-blue-500/40 bg-blue-500/5' :
    'border-slate-700 bg-slate-800/40'

  return (
    <div className={`rounded-xl border p-4 transition-colors ${actionBg}`}>
      {/* Header */}
      <div className="flex items-start gap-3">
        <button
          type="button"
          onClick={() => setExpanded(v => !v)}
          aria-expanded={expanded}
          aria-label={expanded ? 'Colapsar pasos' : 'Expandir pasos'}
          className="cursor-pointer mt-0.5 text-slate-400 hover:text-slate-200"
        >
          {expanded
            ? <ChevronDown className="h-4 w-4" aria-hidden />
            : <ChevronRight className="h-4 w-4" aria-hidden />}
        </button>

        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <span className="text-sm font-medium text-white truncate">{scenario.name}</span>
            <span className="text-xs text-slate-500 shrink-0">{scenario.scenario_type}</span>
          </div>
          <div className="flex flex-wrap gap-1.5 mb-3">
            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs border ${qcColor}`}>
              {state.action === 'reclassified' && state.newQc
                ? state.newQc.replace(/_/g, ' ')
                : scenario.quality_characteristic.replace(/_/g, ' ')}
            </span>
            <span className="text-xs text-slate-600">AC: {scenario.acceptance_criterion_id}</span>
          </div>

          {/* Steps (collapsed by default) */}
          {expanded && (
            <div className="mb-3 space-y-1">
              {scenario.steps.map((step, i) => (
                <p key={i} className="text-xs text-slate-400">
                  <span className="font-semibold text-slate-300">{step.keyword} </span>
                  {step.text}
                </p>
              ))}
            </div>
          )}

          {/* Action buttons */}
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => onChange({ action: 'accepted' })}
              className={`cursor-pointer inline-flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                state.action === 'accepted'
                  ? 'bg-green-600 text-white'
                  : 'bg-slate-700/50 text-slate-300 hover:bg-green-600/30'
              }`}
            >
              <Check className="h-3 w-3" aria-hidden /> Aceptar
            </button>
            <button
              type="button"
              onClick={() =>
                onChange({ action: 'reclassified', newQc: scenario.quality_characteristic })
              }
              className={`cursor-pointer inline-flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                state.action === 'reclassified'
                  ? 'bg-yellow-600 text-white'
                  : 'bg-slate-700/50 text-slate-300 hover:bg-yellow-600/30'
              }`}
            >
              <RefreshCw className="h-3 w-3" aria-hidden /> Reclasificar
            </button>
            <button
              type="button"
              onClick={() => onChange({ action: 'comment' })}
              className={`cursor-pointer inline-flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                state.action === 'comment'
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700/50 text-slate-300 hover:bg-blue-600/30'
              }`}
            >
              <MessageSquare className="h-3 w-3" aria-hidden /> Comentar
            </button>
          </div>

          {/* Reclassify controls */}
          {state.action === 'reclassified' && (
            <div className="mt-3 flex flex-col gap-2">
              <select
                value={state.newQc ?? scenario.quality_characteristic}
                onChange={e =>
                  onChange({ ...state, newQc: e.target.value as QualityCharacteristic })
                }
                className="bg-slate-700 text-white text-xs rounded-lg px-3 py-2 border border-slate-600 focus:outline-none focus:border-violet-500"
              >
                {QC_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
              <input
                type="text"
                placeholder="Razón del cambio (requerida para auditoría CMMI L3)"
                value={state.reason ?? ''}
                onChange={e => onChange({ ...state, reason: e.target.value })}
                className="bg-slate-700 text-white text-xs rounded-lg px-3 py-2 border border-slate-600 placeholder-slate-500 focus:outline-none focus:border-violet-500"
              />
            </div>
          )}

          {/* Comment control */}
          {state.action === 'comment' && (
            <div className="mt-3">
              <input
                type="text"
                placeholder="Comentario para el escenario"
                value={state.reason ?? ''}
                onChange={e => onChange({ ...state, reason: e.target.value })}
                className="w-full bg-slate-700 text-white text-xs rounded-lg px-3 py-2 border border-slate-600 placeholder-slate-500 focus:outline-none focus:border-violet-500"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function ScenarioReviewer({ contractB, onSubmit, submitting }: Props) {
  const allScenarios = contractB.features.flatMap(f => f.scenarios)

  const [states, setStates] = useState<Record<string, ScenarioState>>(() =>
    Object.fromEntries(allScenarios.map(s => [s.acceptance_criterion_id, { action: 'accepted' as ActionType }]))
  )
  const [reviewStarted, setReviewStarted] = useState(false)
  const [reviewer, setReviewer] = useState('')
  const [feedback, setFeedback] = useState('')
  const [reviewStatus, setReviewStatus] = useState('approved')
  const [useLlmRisk, setUseLlmRisk] = useState(true)

  const handleChange = (id: string, s: ScenarioState) => {
    setReviewStarted(true)
    setStates(prev => ({ ...prev, [id]: s }))
  }

  const acceptAll = () => {
    setReviewStarted(true)
    setStates(Object.fromEntries(
      allScenarios.map(s => [s.acceptance_criterion_id, { action: 'accepted' as ActionType }])
    ))
  }

  const handleSubmit = () => {
    const decisions: ScenarioDecision[] = allScenarios
      .filter(s => states[s.acceptance_criterion_id]?.action !== null)
      .map(s => {
        const st = states[s.acceptance_criterion_id]
        return {
          scenario_name: s.name,
          action: st.action!,
          new_quality_characteristic: st.action === 'reclassified' ? st.newQc : undefined,
          reason: st.reason,
        }
      })
    onSubmit(decisions, reviewer, feedback, reviewStatus, useLlmRisk)
  }

  const n_reviewed = allScenarios.filter(s => states[s.acceptance_criterion_id]?.action !== null).length
  const canSubmit = reviewer.trim().length > 0 && !submitting && reviewStarted

  return (
    <div className="flex flex-col gap-6">
      {/* Header stats — compact inline row */}
      <div className="flex flex-wrap items-center gap-x-5 gap-y-1.5 text-sm pb-4 border-b border-slate-800/80">
        <span>
          <span className="font-semibold tabular-nums text-slate-200">{allScenarios.length}</span>
          <span className="text-slate-500 ml-1.5">escenarios</span>
        </span>
        <span className="text-slate-700" aria-hidden>·</span>
        <span>
          <span className="font-semibold tabular-nums text-slate-200">{contractB.features.length}</span>
          <span className="text-slate-500 ml-1.5">features</span>
        </span>
        <span className="text-slate-700" aria-hidden>·</span>
        <span>
          <span className="font-semibold tabular-nums text-green-400">{contractB.total_positive}</span>
          <span className="text-slate-500 ml-1.5">positivos</span>
        </span>
        <span className="text-slate-700" aria-hidden>·</span>
        <span>
          <span className="font-semibold tabular-nums text-red-400">{contractB.total_negative}</span>
          <span className="text-slate-500 ml-1.5">negativos</span>
        </span>
        <span className="text-slate-700" aria-hidden>·</span>
        <span>
          <span className="font-semibold tabular-nums text-violet-400">{n_reviewed}</span>
          <span className="text-slate-500 ml-1.5">revisados</span>
        </span>
        <button
          type="button"
          onClick={acceptAll}
          className="cursor-pointer ml-auto inline-flex items-center gap-2 rounded-lg bg-green-600/15 border border-green-500/25 px-3 py-1.5 text-sm font-medium text-green-400 hover:bg-green-600/25 transition-colors"
        >
          <CheckCheck className="h-3.5 w-3.5" />
          Aceptar todos
        </button>
      </div>

      {/* Escenarios agrupados por feature */}
      {contractB.features.map(feature => (
        <section key={feature.user_story_id} className="flex flex-col gap-3">
          <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 px-4 py-3">
            <h4 className="font-semibold text-white text-sm">{feature.name}</h4>
            <p className="text-xs text-slate-500 mt-0.5">{feature.description}</p>
          </div>
          <div className="flex flex-col gap-2 pl-2">
            {feature.scenarios.map(sc => (
              <ScenarioCard
                key={sc.acceptance_criterion_id}
                scenario={sc}
                state={states[sc.acceptance_criterion_id] ?? { action: null }}
                onChange={s => handleChange(sc.acceptance_criterion_id, s)}
              />
            ))}
          </div>
        </section>
      ))}

      {/* Formulario de decisión global */}
      <div className="rounded-2xl border border-slate-700 bg-slate-800/40 p-6 flex flex-col gap-4">
        <h4 className="font-semibold text-white">Decisión global del analista</h4>

        {!reviewStarted && (
          <p className="text-sm text-amber-400/80 bg-amber-500/10 border border-amber-500/20 rounded-lg px-4 py-3">
            Revisa al menos un escenario o usa "Aceptar todos" para habilitar el envío.
          </p>
        )}

        <div className="flex flex-col gap-1.5">
          <label className="text-sm text-slate-400">
            Identificador del revisor <span className="text-slate-600">*</span>
          </label>
          <input
            type="text"
            placeholder="Ej: ana.garcia.qa"
            value={reviewer}
            onChange={e => setReviewer(e.target.value)}
            className="bg-slate-700 text-white text-sm rounded-lg px-4 py-2.5 border border-slate-600 placeholder-slate-500 focus:outline-none focus:border-violet-500"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-sm text-slate-400">
            Comentario global <span className="text-slate-600">(opcional)</span>
          </label>
          <textarea
            rows={2}
            placeholder="Observaciones generales sobre el suite..."
            value={feedback}
            onChange={e => setFeedback(e.target.value)}
            className="bg-slate-700 text-white text-sm rounded-lg px-4 py-2.5 border border-slate-600 placeholder-slate-500 focus:outline-none focus:border-violet-500 resize-none"
          />
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-sm text-slate-400">Decisión final</label>
          <div className="flex flex-wrap gap-3">
            {[
              { value: 'approved',      label: 'Aprobar',       color: 'green' },
              { value: 'needs_changes', label: 'Pedir cambios', color: 'yellow' },
              { value: 'rejected',      label: 'Rechazar',      color: 'red' },
            ].map(opt => (
              <label key={opt.value} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="review_status"
                  value={opt.value}
                  checked={reviewStatus === opt.value}
                  onChange={() => setReviewStatus(opt.value)}
                  className="accent-violet-500"
                />
                <span className="text-sm text-slate-300">{opt.label}</span>
              </label>
            ))}
          </div>
        </div>

        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={useLlmRisk}
            onChange={e => setUseLlmRisk(e.target.checked)}
            className="accent-violet-500"
          />
          <span className="text-sm text-slate-300">
            Enriquecer recomendaciones de riesgo con LLM (Groq)
          </span>
        </label>

        <button
          onClick={handleSubmit}
          disabled={!canSubmit}
          className="cursor-pointer rounded-lg bg-violet-600 px-6 py-3 text-sm font-semibold text-white hover:bg-violet-500 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {submitting ? 'Generando acta PDF...' : 'Enviar revisión y generar PDF'}
        </button>
      </div>
    </div>
  )
}
