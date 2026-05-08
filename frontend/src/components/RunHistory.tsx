import { Trash2 } from 'lucide-react'
import type { RunSummary } from '../types'

interface Props {
  runs: RunSummary[]
  onSelect: (runId: string) => void
  onDelete: (runId: string) => void
}

const statusConfig = {
  completed: { color: 'text-emerald-400', label: 'Completado' },
  pending:   { color: 'text-amber-400',   label: 'Pendiente' },
  failed:    { color: 'text-red-400',     label: 'Fallido' },
}

export default function RunHistory({ runs, onSelect, onDelete }: Props) {
  if (!runs.length) return null

  const handleDelete = (e: React.MouseEvent, runId: string) => {
    e.stopPropagation()
    onDelete(runId)
  }

  return (
    <div>
      <h3 className="text-sm font-semibold text-slate-400 mb-3 uppercase tracking-wider">
        Historial reciente
      </h3>
      <div className="flex flex-col gap-2">
        {runs.map(run => (
          <div
            key={run.run_id}
            className="flex items-center gap-2 rounded-xl border border-slate-700/60 bg-slate-800/40 hover:bg-slate-700/40 transition-colors group"
          >
            <button
              onClick={() => onSelect(run.run_id)}
              className="flex-1 flex items-center justify-between px-4 py-3 text-left cursor-pointer min-w-0"
            >
              <div className="min-w-0">
                <p className="text-sm text-slate-200 truncate group-hover:text-white transition-colors">
                  {run.prompt}
                </p>
                <p className="text-xs text-slate-500 mt-0.5">
                  {new Date(run.created_at).toLocaleString('es-CO')}
                </p>
              </div>
              <div className="shrink-0 ml-4 flex items-center gap-2">
                {run.story_count !== undefined && run.story_count !== null && (
                  <span className="text-xs text-slate-500">{run.story_count} historias</span>
                )}
                <span className={`text-xs font-medium ${statusConfig[run.status].color}`}>
                  {statusConfig[run.status].label}
                </span>
              </div>
            </button>

            <button
              onClick={e => handleDelete(e, run.run_id)}
              title="Eliminar"
              className="shrink-0 mr-3 p-1.5 rounded-lg text-slate-600 hover:text-red-400 hover:bg-red-500/10 transition-colors cursor-pointer opacity-0 group-hover:opacity-100"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
