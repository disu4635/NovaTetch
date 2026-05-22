import { useState } from 'react'
import { Check, AlertTriangle, ChevronDown, ChevronRight, Shield, BarChart2 } from 'lucide-react'
import type { ContractC, GeneratedCodeModule, ModuleAction, FunctionMetrics, SecurityFinding } from '../types'

const CC_BAND_COLOR: Record<string, string> = {
  A: 'text-green-400', B: 'text-yellow-400', C: 'text-orange-400',
  D: 'text-red-400',   E: 'text-red-600',
}

const SEV_COLOR: Record<string, string> = {
  low: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30',
  medium: 'text-orange-400 bg-orange-400/10 border-orange-400/30',
  high: 'text-red-400 bg-red-400/10 border-red-400/30',
}

type ModuleActionType = 'accepted' | 'smell_flagged' | 'skipped' | null

interface ModuleState {
  action: ModuleActionType
  notes?: string
}

function FunctionMetricRow({ fm }: { fm: FunctionMetrics }) {
  return (
    <div className={`flex items-center gap-3 text-xs px-3 py-1.5 rounded-lg ${fm.exceeds_threshold ? 'bg-red-500/10 border border-red-500/20' : 'bg-slate-800/40'}`}>
      <span className="text-slate-400 font-mono w-40 truncate">{fm.function_name}</span>
      <span className={`font-bold ${CC_BAND_COLOR[fm.cc_band] ?? 'text-slate-400'}`}>CC:{fm.cyclomatic_complexity}({fm.cc_band})</span>
      <span className={fm.cognitive_complexity >= 15 ? 'text-red-400 font-bold' : 'text-slate-400'}>CogC:{fm.cognitive_complexity}</span>
      {fm.exceeds_threshold && <span className="text-red-400 text-xs">⚠ Sobre umbral</span>}
    </div>
  )
}

function SecurityFindingRow({ sf }: { sf: SecurityFinding }) {
  return (
    <div className={`flex items-start gap-2 text-xs px-3 py-1.5 rounded-lg border ${SEV_COLOR[sf.severity] ?? ''}`}>
      <Shield className="h-3 w-3 mt-0.5 shrink-0" />
      <span className="font-bold uppercase">{sf.severity}</span>
      <span className="font-mono text-slate-400">{sf.test_id}</span>
      <span className="text-slate-300">{sf.description}</span>
      <span className="ml-auto text-slate-500 shrink-0">L{sf.line_number}</span>
    </div>
  )
}

function ModuleCard({
  mod, state, metrics, findings, onChange,
}: {
  mod: GeneratedCodeModule
  state: ModuleState
  metrics: FunctionMetrics[]
  findings: SecurityFinding[]
  onChange: (s: ModuleState) => void
}) {
  const [showCode, setShowCode] = useState(false)
  const [showMetrics, setShowMetrics] = useState(false)

  const actionBg =
    state.action === 'accepted'     ? 'border-green-500/40 bg-green-500/5' :
    state.action === 'smell_flagged'? 'border-orange-500/40 bg-orange-500/5' :
    'border-slate-700 bg-slate-800/40'

  return (
    <div className={`rounded-xl border p-4 transition-colors ${actionBg}`}>
      {/* Header */}
      <div className="flex items-start gap-3 mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <span className="font-mono text-sm font-semibold text-white">{mod.filename}</span>
            <span className="text-xs text-slate-500">US: {mod.user_story_id}</span>
          </div>
          <p className="text-xs text-slate-400">{mod.description}</p>
        </div>

        {/* Badges de métricas rápidas */}
        <div className="flex gap-2 shrink-0">
          {metrics.length > 0 && (
            <button
              onClick={() => setShowMetrics(v => !v)}
              className="cursor-pointer inline-flex items-center gap-1 px-2 py-1 rounded text-xs bg-slate-700/50 text-slate-300 hover:bg-slate-600/50"
            >
              <BarChart2 className="h-3 w-3" />
              {metrics.length} fn
            </button>
          )}
          {findings.length > 0 && (
            <span className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs bg-red-500/20 text-red-300 border border-red-500/30">
              <Shield className="h-3 w-3" />
              {findings.length}
            </span>
          )}
        </div>
      </div>

      {/* Métricas expandibles */}
      {showMetrics && metrics.length > 0 && (
        <div className="mb-3 flex flex-col gap-1">
          {metrics.map((fm, i) => <FunctionMetricRow key={i} fm={fm} />)}
        </div>
      )}

      {/* Hallazgos de seguridad */}
      {findings.length > 0 && (
        <div className="mb-3 flex flex-col gap-1">
          {findings.map((sf, i) => <SecurityFindingRow key={i} sf={sf} />)}
        </div>
      )}

      {/* Código expandible */}
      <div className="mb-3">
        <button
          onClick={() => setShowCode(v => !v)}
          className="cursor-pointer flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200"
        >
          {showCode ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
          {showCode ? 'Ocultar código' : 'Ver código'}
        </button>
        {showCode && (
          <pre className="mt-2 text-xs text-slate-300 bg-slate-900 rounded-lg p-3 overflow-x-auto max-h-64 overflow-y-auto font-mono leading-relaxed border border-slate-700">
            {mod.source_code}
          </pre>
        )}
      </div>

      {/* Acciones */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => onChange({ action: 'accepted' })}
          className={`cursor-pointer inline-flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
            state.action === 'accepted'
              ? 'bg-green-600 text-white'
              : 'bg-slate-700/50 text-slate-300 hover:bg-green-600/30'
          }`}
        >
          <Check className="h-3 w-3" /> Aceptar
        </button>
        <button
          onClick={() => onChange({ action: 'smell_flagged', notes: state.notes })}
          className={`cursor-pointer inline-flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
            state.action === 'smell_flagged'
              ? 'bg-orange-600 text-white'
              : 'bg-slate-700/50 text-slate-300 hover:bg-orange-600/30'
          }`}
        >
          <AlertTriangle className="h-3 w-3" /> Marcar smell
        </button>
        <button
          onClick={() => onChange({ action: 'skipped' })}
          className={`cursor-pointer inline-flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
            state.action === 'skipped'
              ? 'bg-slate-600 text-white'
              : 'bg-slate-700/50 text-slate-300 hover:bg-slate-600/30'
          }`}
        >
          Saltar
        </button>
      </div>

      {/* Nota para smell */}
      {state.action === 'smell_flagged' && (
        <div className="mt-2">
          <input
            type="text"
            placeholder="Describe el code smell o problema (naming, design intent, acoplamiento...)"
            value={state.notes ?? ''}
            onChange={e => onChange({ ...state, notes: e.target.value })}
            className="w-full bg-slate-700 text-white text-xs rounded-lg px-3 py-2 border border-slate-600 placeholder-slate-500 focus:outline-none focus:border-orange-500"
          />
        </div>
      )}
    </div>
  )
}

interface Props {
  contractC: ContractC
  onSubmit: (actions: ModuleAction[], reviewer: string, verdict: string, feedback: string) => void
  submitting: boolean
}

export default function CodeReviewer({ contractC, onSubmit, submitting }: Props) {
  const [states, setStates] = useState<Record<string, ModuleState>>(() =>
    Object.fromEntries(contractC.generated_code.map(m => [m.filename, { action: 'accepted' as ModuleActionType }]))
  )
  const [reviewer, setReviewer] = useState('')
  const [verdict, setVerdict] = useState('approved')
  const [feedback, setFeedback] = useState('')

  const qr = contractC.quality_report
  const tm = contractC.traceability_matrix
  const cr = contractC.coverage_report

  const handleChange = (filename: string, s: ModuleState) =>
    setStates(prev => ({ ...prev, [filename]: s }))

  const handleSubmit = () => {
    const actions: ModuleAction[] = contractC.generated_code
      .map(m => {
        const s = states[m.filename]
        return {
          module_name: m.filename,
          action: (s?.action ?? 'skipped') as ModuleAction['action'],
          notes: s?.notes,
        }
      })
    onSubmit(actions, reviewer, verdict, feedback)
  }

  const n_activos = Object.values(states).filter(s => s.action !== null && s.action !== 'skipped').length

  return (
    <div className="flex flex-col gap-6">
      {/* Resumen de métricas */}
      <div className="rounded-2xl border border-slate-700 bg-slate-800/40 px-6 py-5 flex flex-wrap gap-6">
        <div>
          <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Módulos</p>
          <p className="text-2xl font-bold text-white">{contractC.total_modules}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Tests</p>
          <p className="text-2xl font-bold text-white">{contractC.total_tests}</p>
        </div>
        {qr && (
          <>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Fn sobre umbral</p>
              <p className={`text-2xl font-bold ${qr.functions_exceeding_threshold > 0 ? 'text-red-400' : 'text-green-400'}`}>
                {qr.functions_exceeding_threshold}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Seguridad</p>
              <p className={`text-2xl font-bold ${qr.security_findings.length > 0 ? 'text-orange-400' : 'text-green-400'}`}>
                {qr.security_findings.length}
              </p>
            </div>
          </>
        )}
        {cr && (
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Branch cov.</p>
            <p className={`text-2xl font-bold ${cr.meets_threshold ? 'text-green-400' : 'text-red-400'}`}>
              {cr.branch_coverage_pct.toFixed(1)}%
            </p>
          </div>
        )}
        {tm && (
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">CMMI L3</p>
            <p className={`text-2xl font-bold ${tm.cmmi_l3_compliant ? 'text-green-400' : 'text-red-400'}`}>
              {tm.cmmi_l3_compliant ? '✓' : '✗'}
            </p>
          </div>
        )}
        <div className="ml-auto text-right">
          <p className="text-xs text-slate-500 mb-1">Revisados</p>
          <p className="text-2xl font-bold text-emerald-400">{n_activos}/{contractC.total_modules}</p>
        </div>
      </div>

      {/* Módulos para revisar */}
      <div className="flex flex-col gap-3">
        {contractC.generated_code.map(mod => {
          const metrics = qr?.function_metrics.filter(fm => fm.module === mod.filename) ?? []
          const findings = qr?.security_findings.filter(sf => sf.module === mod.filename) ?? []
          return (
            <ModuleCard
              key={mod.filename}
              mod={mod}
              state={states[mod.filename] ?? { action: null }}
              metrics={metrics}
              findings={findings}
              onChange={s => handleChange(mod.filename, s)}
            />
          )
        })}
      </div>

      {/* Formulario veredicto */}
      <div className="rounded-2xl border border-slate-700 bg-slate-800/40 p-6 flex flex-col gap-4">
        <h4 className="font-semibold text-white">Veredicto del desarrollador senior</h4>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs text-slate-400 uppercase tracking-wider">Identificador del revisor *</label>
          <input
            type="text"
            placeholder="Ej: carlos.mendoza.senior"
            value={reviewer}
            onChange={e => setReviewer(e.target.value)}
            className="bg-slate-700 text-white text-sm rounded-lg px-4 py-2.5 border border-slate-600 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs text-slate-400 uppercase tracking-wider">Observaciones generales</label>
          <textarea
            rows={2}
            placeholder="Notas sobre naming, design intent, cohesión, oportunidades de refactor..."
            value={feedback}
            onChange={e => setFeedback(e.target.value)}
            className="bg-slate-700 text-white text-sm rounded-lg px-4 py-2.5 border border-slate-600 placeholder-slate-500 focus:outline-none focus:border-emerald-500 resize-none"
          />
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-xs text-slate-400 uppercase tracking-wider">Veredicto final</label>
          <div className="flex flex-wrap gap-3">
            {[
              { value: 'approved',      label: 'Aprobar' },
              { value: 'needs_changes', label: 'Pedir cambios' },
              { value: 'rejected',      label: 'Rechazar' },
            ].map(opt => (
              <label key={opt.value} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="verdict"
                  value={opt.value}
                  checked={verdict === opt.value}
                  onChange={() => setVerdict(opt.value)}
                  className="accent-emerald-500"
                />
                <span className="text-sm text-slate-300">{opt.label}</span>
              </label>
            ))}
          </div>
        </div>

        <button
          onClick={handleSubmit}
          disabled={!reviewer.trim() || submitting}
          className="cursor-pointer rounded-lg bg-emerald-600 px-6 py-3 text-sm font-semibold text-white hover:bg-emerald-500 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {submitting ? 'Enviando revisión...' : 'Enviar revisión y finalizar'}
        </button>
      </div>
    </div>
  )
}
