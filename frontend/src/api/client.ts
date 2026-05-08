import type { Ambiguity, Resolution, RunDetail, RunSummary } from '../types'

const BASE = '/api/stories'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(body.detail ?? `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  analyze: (prompt: string): Promise<{ ambiguities: Ambiguity[] }> =>
    request('/analyze', { method: 'POST', body: JSON.stringify({ prompt }) }),

  generate: (prompt: string, resolutions: Resolution[]): Promise<RunDetail> =>
    request('/generate', { method: 'POST', body: JSON.stringify({ prompt, resolutions }) }),

  getRuns: (): Promise<RunSummary[]> => request('/runs'),

  getRun: (runId: string): Promise<RunDetail> => request(`/runs/${runId}`),
}
