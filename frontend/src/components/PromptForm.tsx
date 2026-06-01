import { useState } from 'react'

const MIN_CHARS = 50

interface Props {
  onAnalyze: (prompt: string) => void
  loading: boolean
}

export default function PromptForm({ onAnalyze, loading }: Props) {
  const [value, setValue] = useState('')
  const charCount = value.trim().length
  const isReady = charCount >= MIN_CHARS && !loading

  const submit = () => {
    const prompt = value.trim()
    if (prompt.length >= MIN_CHARS) onAnalyze(prompt)
  }

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    submit()
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey) && isReady) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      <div className="relative">
        <textarea
          name="prompt"
          rows={5}
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ej: Necesito un sistema de login seguro para usuarios que gestione permisos de forma eficiente..."
          className="w-full rounded-xl border border-slate-700 bg-slate-800/60 p-4 text-slate-100 placeholder-slate-500 resize-none focus:outline-none focus:ring-2 focus:ring-violet-500 text-base leading-relaxed"
          disabled={loading}
        />
        <span className={`absolute bottom-3 right-3 text-xs tabular-nums ${charCount < MIN_CHARS && charCount > 0 ? 'text-slate-500' : 'text-slate-600'}`}>
          {charCount}
        </span>
      </div>
      {charCount > 0 && charCount < MIN_CHARS && (
        <p className="text-xs text-slate-500 -mt-1">
          Añade más detalle para mejores resultados — {MIN_CHARS - charCount} caracteres más
        </p>
      )}
      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-600 select-none">Ctrl + Enter para enviar</p>
        <button
          type="submit"
          disabled={!isReady}
          className="cursor-pointer flex items-center gap-2 rounded-xl bg-violet-600 px-6 py-3 font-semibold text-white hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              Analizando...
            </>
          ) : (
            'Analizar requerimiento'
          )}
        </button>
      </div>
    </form>
  )
}
