import { Download, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'
import type { ContractC } from '../types'

const STATUS_BADGE: Record<string, string> = {
  approved:      'bg-green-600/20 text-green-300 border-green-600/40',
  rejected:      'bg-red-600/20 text-red-300 border-red-600/40',
  needs_changes: 'bg-yellow-600/20 text-yellow-300 border-yellow-600/40',
  pending_review:'bg-slate-600/20 text-slate-300 border-slate-600/40',
}

const STATUS_LABEL: Record<string, string> = {
  approved:       'Aprobado',
  rejected:       'Rechazado',
  needs_changes:  'Cambios solicitados',
  pending_review: 'Pendiente revisión',
}

interface Props {
  contractC: ContractC
  onDownloadCode: () => void
}

export default function CodeGenResults({ contractC, onDownloadCode }: Props) {
  const qr = contractC.quality_report
  const tm = contractC.traceability_matrix
  const cr = contractC.coverage_report
  const review = contractC.review

  return (
    <div className="flex flex-col gap-6">
      {/* Encabezado con estado de revisión */}
      <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/5 px-6 py-5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-white mb-1">Generación de Código Completada</h3>
            <div className="flex items-center gap-3">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${STATUS_BADGE[review.review_status] ?? ''}`}>
                {STATUS_LABEL[review.review_status] ?? review.review_status}
              </span>
              {review.approved_by && (
                <span className="text-xs text-slate-400">Revisado por: {review.approved_by}</span>
              )}
            </div>
          </div>
          <button
            onClick={onDownloadCode}
            className="cursor-pointer inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 transition-colors"
          >
            <Download className="h-4 w-4" />
            Descargar código (.zip)
          </button>
        </div>
      </div>

      {/* Stats rápidas */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="rounded-xl border border-slate-700 bg-slate-800/40 p-4 text-center">
          <p className="text-2xl font-bold text-white">{contractC.total_modules}</p>
          <p className="text-xs text-slate-400 mt-1">Módulos</p>
        </div>
        <div className="rounded-xl border border-slate-700 bg-slate-800/40 p-4 text-center">
          <p className="text-2xl font-bold text-white">{contractC.total_tests}</p>
          <p className="text-xs text-slate-400 mt-1">Tests</p>
        </div>
        {cr && (
          <div className={`rounded-xl border p-4 text-center ${cr.meets_threshold ? 'border-green-500/30 bg-green-500/5' : 'border-red-500/30 bg-red-500/5'}`}>
            <p className={`text-2xl font-bold ${cr.meets_threshold ? 'text-green-400' : 'text-red-400'}`}>
              {cr.branch_coverage_pct.toFixed(1)}%
            </p>
            <p className="text-xs text-slate-400 mt-1">Branch Coverage</p>
          </div>
        )}
        {tm && (
          <div className={`rounded-xl border p-4 text-center ${tm.cmmi_l3_compliant ? 'border-green-500/30 bg-green-500/5' : 'border-red-500/30 bg-red-500/5'}`}>
            <p className={`text-2xl font-bold ${tm.cmmi_l3_compliant ? 'text-green-400' : 'text-red-400'}`}>
              {tm.cmmi_l3_compliant ? '✓' : '✗'}
            </p>
            <p className="text-xs text-slate-400 mt-1">CMMI L3</p>
          </div>
        )}
      </div>

      {/* Quality Report */}
      {qr && (
        <div className="rounded-2xl border border-slate-700 bg-slate-800/40 p-5">
          <h4 className="font-semibold text-white mb-3">Quality Report ISO 25010</h4>

          {/* ISO 25010 cobertura */}
          <div className="flex flex-col gap-2 mb-4">
            {qr.iso_25010_coverage.map(item => {
              const icon =
                item.status === 'measured'
                  ? <CheckCircle className="h-3.5 w-3.5 text-green-400 shrink-0" />
                  : item.status === 'requires_human_judgment'
                  ? <AlertTriangle className="h-3.5 w-3.5 text-yellow-400 shrink-0" />
                  : <XCircle className="h-3.5 w-3.5 text-slate-500 shrink-0" />
              return (
                <div key={item.characteristic} className="flex items-start gap-2 text-xs">
                  {icon}
                  <span className="text-slate-300 w-44 shrink-0">{item.characteristic.replace(/_/g, ' ')}</span>
                  <span className="text-slate-500">{item.verdict ?? item.status}</span>
                </div>
              )
            })}
          </div>

          {/* Funciones sobre umbral */}
          {qr.function_metrics.length > 0 && (
            <>
              <p className="text-xs font-medium text-slate-400 mb-2">
                Métricas por función — {qr.functions_exceeding_threshold} sobre umbral
              </p>
              <div className="flex flex-col gap-1 max-h-40 overflow-y-auto">
                {qr.function_metrics.map((fm, i) => (
                  <div key={i} className={`flex items-center gap-3 text-xs px-2 py-1 rounded ${fm.exceeds_threshold ? 'bg-red-500/10 border border-red-500/20' : ''}`}>
                    <span className="font-mono text-slate-400 w-36 truncate">{fm.function_name}</span>
                    <span className="text-slate-400">{fm.module}</span>
                    <span className="ml-auto">CC:{fm.cyclomatic_complexity} CogC:{fm.cognitive_complexity}</span>
                    {fm.exceeds_threshold && <span className="text-red-400">⚠</span>}
                  </div>
                ))}
              </div>
            </>
          )}

          {/* Hallazgos de seguridad */}
          {qr.security_findings.length > 0 && (
            <div className="mt-4">
              <p className="text-xs font-medium text-slate-400 mb-2">
                Hallazgos de seguridad — {qr.security_findings.length} encontrados
              </p>
              <div className="flex flex-col gap-1">
                {qr.security_findings.map((sf, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs">
                    <span className={`px-1.5 py-0.5 rounded font-bold uppercase ${
                      sf.severity === 'high' ? 'bg-red-600/30 text-red-300' :
                      sf.severity === 'medium' ? 'bg-orange-600/30 text-orange-300' :
                      'bg-yellow-600/30 text-yellow-300'
                    }`}>{sf.severity}</span>
                    <span className="font-mono text-slate-400">{sf.test_id}</span>
                    <span className="text-slate-400">{sf.module}:L{sf.line_number}</span>
                    <span className="text-slate-300 truncate">{sf.description}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Trazabilidad CMMI L3 */}
      {tm && (
        <div className="rounded-2xl border border-slate-700 bg-slate-800/40 p-5">
          <h4 className="font-semibold text-white mb-3">Matriz de Trazabilidad CMMI L3</h4>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div>
              <p className="text-xs text-slate-400">Cobertura de requisitos</p>
              <p className={`text-xl font-bold ${tm.requirements_coverage_pct >= 100 ? 'text-green-400' : 'text-yellow-400'}`}>
                {tm.requirements_coverage_pct.toFixed(1)}%
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-400">Tests justificados</p>
              <p className={`text-xl font-bold ${tm.tests_justified_pct >= 100 ? 'text-green-400' : 'text-yellow-400'}`}>
                {tm.tests_justified_pct.toFixed(1)}%
              </p>
            </div>
          </div>

          {tm.orphan_scenarios.length > 0 && (
            <div className="mb-2">
              <p className="text-xs text-red-400 mb-1">Escenarios sin test (huérfanos forward):</p>
              <div className="flex flex-wrap gap-1">
                {tm.orphan_scenarios.map(id => (
                  <span key={id} className="px-2 py-0.5 text-xs bg-red-500/20 text-red-300 border border-red-500/30 rounded-full">{id}</span>
                ))}
              </div>
            </div>
          )}
          {tm.orphan_tests.length > 0 && (
            <div>
              <p className="text-xs text-orange-400 mb-1">Tests sin escenario (huérfanos backward):</p>
              <div className="flex flex-wrap gap-1">
                {tm.orphan_tests.map(t => (
                  <span key={t} className="px-2 py-0.5 text-xs bg-orange-500/20 text-orange-300 border border-orange-500/30 rounded-full">{t}</span>
                ))}
              </div>
            </div>
          )}
          {tm.cmmi_l3_compliant && (
            <p className="text-xs text-green-400 flex items-center gap-1 mt-2">
              <CheckCircle className="h-3.5 w-3.5" /> Sin huérfanos — cumple CMMI L3
            </p>
          )}
        </div>
      )}

      {/* Feedback del revisor */}
      {review.reviewer_feedback && (
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/30 px-5 py-4">
          <p className="text-xs font-medium text-slate-500 mb-1">Feedback del revisor senior</p>
          <p className="text-sm text-slate-300">{review.reviewer_feedback}</p>
        </div>
      )}
    </div>
  )
}
