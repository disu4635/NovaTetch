import { useState } from 'react'
import { ChevronDown, Copy, CheckCheck } from 'lucide-react'
import type { UserStory } from '../types'

interface Props {
  story: UserStory
  index: number
  isExpanded?: boolean
  onToggle?: () => void
}

const priorityConfig = {
  critical: { color: 'bg-red-500/20 text-red-300 border-red-500/30', label: 'Crítica' },
  high:     { color: 'bg-orange-500/20 text-orange-300 border-orange-500/30', label: 'Alta' },
  medium:   { color: 'bg-amber-500/20 text-amber-300 border-amber-500/30', label: 'Media' },
  low:      { color: 'bg-slate-500/20 text-slate-300 border-slate-500/30', label: 'Baja' },
}

const typeConfig = {
  functional:     { color: 'bg-blue-500/20 text-blue-300 border-blue-500/30', label: 'Funcional' },
  non_functional: { color: 'bg-purple-500/20 text-purple-300 border-purple-500/30', label: 'No funcional' },
  technical:      { color: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30', label: 'Técnica' },
}

function copyStoryText(story: UserStory): string {
  const criteria = story.acceptance_criteria.map((ac, i) =>
    `${i + 1}. ${ac.description}\n   Given ${ac.given}\n   When ${ac.when}\n   Then ${ac.then}`
  ).join('\n\n')

  return [
    `[${story.id}] ${story.title}`,
    ``,
    `Como ${story.as_a}`,
    `Quiero ${story.i_want}`,
    `Para que ${story.so_that}`,
    ``,
    `Criterios de aceptación:`,
    criteria,
  ].join('\n')
}

export default function StoryCard({ story, index, isExpanded, onToggle }: Props) {
  const [internalOpen, setInternalOpen] = useState(index === 0)
  const [copied, setCopied] = useState(false)

  const controlled = isExpanded !== undefined
  const open = controlled ? isExpanded : internalOpen

  const toggle = () => {
    if (controlled) onToggle?.()
    else setInternalOpen(o => !o)
  }

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation()
    await navigator.clipboard.writeText(copyStoryText(story))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="rounded-2xl border border-slate-700 bg-slate-800/50 overflow-hidden">
      {/* Header */}
      <button
        type="button"
        className="cursor-pointer w-full flex items-center justify-between p-5 text-left hover:bg-slate-700/30 transition-colors"
        onClick={toggle}
        aria-expanded={open}
      >
        <div className="flex items-center gap-3 min-w-0">
          <span className="shrink-0 rounded-lg bg-violet-500/20 px-2.5 py-1 text-xs font-mono font-bold text-violet-300 border border-violet-500/30">
            {story.id}
          </span>
          <span className="font-semibold text-slate-100 truncate">{story.title}</span>
        </div>
        <div className="flex items-center gap-2 ml-4 shrink-0">
          <span className={`rounded-full px-2 py-0.5 text-xs font-medium border ${priorityConfig[story.priority].color}`}>
            {priorityConfig[story.priority].label}
          </span>
          <span className={`rounded-full px-2 py-0.5 text-xs font-medium border ${typeConfig[story.story_type].color}`}>
            {typeConfig[story.story_type].label}
          </span>
          <button
            type="button"
            onClick={handleCopy}
            className="cursor-pointer rounded-lg p-1.5 text-slate-500 hover:text-slate-300 hover:bg-slate-700/50 transition-colors"
            aria-label={copied ? 'Historia copiada' : 'Copiar historia al portapapeles'}
          >
            {copied
              ? <CheckCheck className="h-3.5 w-3.5 text-emerald-400" aria-hidden />
              : <Copy className="h-3.5 w-3.5" aria-hidden />
            }
          </button>
          <ChevronDown
            className={`h-4 w-4 text-slate-400 transition-transform ${open ? 'rotate-180' : ''}`}
            aria-hidden
          />
        </div>
      </button>

      {open && (
        <div className="px-6 pt-2 pb-6 flex flex-col gap-6">
          {/* Story narrative */}
          <div className="rounded-xl bg-slate-900/50 p-4 border border-slate-700/50">
            <div className="grid gap-2 text-sm">
              <p><span className="text-slate-400">Como</span> <span className="text-slate-100">{story.as_a}</span></p>
              <p><span className="text-slate-400">Quiero</span> <span className="text-slate-100">{story.i_want}</span></p>
              <p><span className="text-slate-400">Para que</span> <span className="text-slate-100">{story.so_that}</span></p>
            </div>
          </div>

          {/* Acceptance criteria */}
          <div>
            <h4 className="text-sm font-semibold text-slate-300 mb-3">
              Criterios de aceptación
              <span className="ml-2 text-xs font-normal text-slate-500">
                ({story.acceptance_criteria.length} criterios)
              </span>
            </h4>
            <div className="flex flex-col gap-3">
              {story.acceptance_criteria.map(ac => (
                <div
                  key={ac.id}
                  className={`rounded-xl border p-4 text-sm ${
                    ac.is_negative_case
                      ? 'border-red-500/30 bg-red-500/5'
                      : 'border-slate-700/50 bg-slate-900/40'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-mono text-xs font-bold text-violet-400">{ac.id}</span>
                    {ac.is_negative_case && (
                      <span className="rounded-full bg-red-500/20 px-2 py-0.5 text-xs text-red-300 border border-red-500/30">
                        caso negativo
                      </span>
                    )}
                    <span className="text-slate-300">{ac.description}</span>
                  </div>
                  <div className="grid gap-1 text-slate-400 text-xs">
                    <p><span className="text-slate-500 font-medium">Given</span> {ac.given}</p>
                    <p><span className="text-slate-500 font-medium">When</span> {ac.when}</p>
                    <p><span className="text-slate-500 font-medium">Then</span> {ac.then}</p>
                  </div>
                  {ac.test_data_examples.length > 0 && (
                    <div className="mt-2">
                      <span className="text-xs text-slate-500">Datos de prueba: </span>
                      {ac.test_data_examples.map((ex, i) => (
                        <span key={i} className="ml-1 rounded bg-slate-800 px-1.5 py-0.5 text-xs font-mono text-slate-300">
                          {JSON.stringify(ex)}
                        </span>
                      ))}
                    </div>
                  )}
                  {ac.boundary_values.length > 0 && (
                    <div className="mt-1 flex gap-1 flex-wrap">
                      <span className="text-xs text-slate-500">Límites:</span>
                      {ac.boundary_values.map((v, i) => (
                        <span key={i} className="rounded bg-slate-800 px-1.5 py-0.5 text-xs font-mono text-slate-300">{v}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Business rules */}
          {story.business_rules.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-slate-300 mb-2">Reglas de negocio</h4>
              <ul className="list-disc list-inside text-sm text-slate-400 space-y-1">
                {story.business_rules.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>
          )}

          {/* Resolved ambiguities */}
          {story.ambiguities_resolved.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-slate-300 mb-2">Ambigüedades resueltas</h4>
              <div className="flex flex-col gap-2">
                {story.ambiguities_resolved.map((a, i) => (
                  <div key={i} className="flex gap-3 text-sm rounded-lg bg-slate-900/40 border border-slate-700/40 p-3">
                    <span className="shrink-0 text-slate-500 italic">"{a.original_text}"</span>
                    <span className="text-slate-500">→</span>
                    <span className="text-slate-300">{a.resolution}</span>
                    {a.assumption_made && (
                      <span className="shrink-0 rounded-full bg-amber-500/20 px-2 text-xs text-amber-300 border border-amber-500/30 self-center">
                        suposición
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
