import type { RunSummary } from '../types'

interface Props {
  runs: RunSummary[]
  onSelect: (runId: string) => void
}

const statusConfig = {
  completed: 'text-emerald-400',
  pending: 'text-amber-400',
  failed: 'text-red-400',
}

export default function RunHistory({ runs, onSelect }: Props) {
  if (!runs.length) return null

  return (
    <div>
      <h3 className="text-sm font-semibold text-slate-400 mb-3 uppercase tracking-wider">
        Historial reciente
      </h3>
      <div className="flex flex-col gap-2">
        {runs.map(run => (
          <button
            key={run.run_id}
            onClick={() => onSelect(run.run_id)}
            className="flex items-center justify-between rounded-xl border border-slate-700/60 bg-slate-800/40 px-4 py-3 text-left hover:bg-slate-700/40 transition-colors group"
          >
            <div className="min-w-0">
              <p className="text-sm text-slate-200 truncate group-hover:text-white transition-colors">
                {run.prompt}
              </p>
              <p className="text-xs text-slate-500 mt-0.5">
                {new Date(run.created_at).toLocaleString('es-AR')}
              </p>
            </div>
            <div className="shrink-0 ml-4 flex items-center gap-2">
              {run.story_count !== undefined && run.story_count !== null && (
                <span className="text-xs text-slate-500">{run.story_count} historias</span>
              )}
              <span className={`text-xs font-medium ${statusConfig[run.status]}`}>
                {run.status}
              </span>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
