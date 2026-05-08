interface Props {
  onAnalyze: (prompt: string) => void
  loading: boolean
}

export default function PromptForm({ onAnalyze, loading }: Props) {
  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const fd = new FormData(e.currentTarget)
    const prompt = (fd.get('prompt') as string).trim()
    if (prompt) onAnalyze(prompt)
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <textarea
        name="prompt"
        rows={5}
        placeholder="Ej: Necesito un sistema de login seguro para usuarios que gestione permisos de forma eficiente..."
        className="w-full rounded-xl border border-slate-700 bg-slate-800/60 p-4 text-slate-100 placeholder-slate-500 resize-none focus:outline-none focus:ring-2 focus:ring-violet-500 text-base leading-relaxed"
        disabled={loading}
      />
      <button
        type="submit"
        disabled={loading}
        className="self-end flex items-center gap-2 rounded-xl bg-violet-600 px-6 py-3 font-semibold text-white hover:bg-violet-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
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
    </form>
  )
}
