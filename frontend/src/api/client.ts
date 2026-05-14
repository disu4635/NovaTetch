import type {
  Ambiguity,
  Resolution,
  RunDetail,
  RunSummary,
  QualityStatusResponse,
  QualityForRunResponse,
  ReviewResult,
  ScenarioDecision,
} from '../types'

const BASE_STORIES = '/api/stories'
const BASE_QUALITY = '/api/quality'

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(body.detail ?? `HTTP ${res.status}`)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  // Stories
  analyze: (prompt: string): Promise<{ ambiguities: Ambiguity[] }> =>
    request<{ ambiguities: Ambiguity[] }>(
      `${BASE_STORIES}/analyze`,
      { method: 'POST', body: JSON.stringify({ prompt }) },
    ),

  generate: (prompt: string, resolutions: Resolution[]): Promise<RunDetail> =>
    request<RunDetail>(
      `${BASE_STORIES}/generate`,
      { method: 'POST', body: JSON.stringify({ prompt, resolutions }) },
    ),

  getRuns: (): Promise<RunSummary[]> =>
    request<RunSummary[]>(`${BASE_STORIES}/runs`),

  getRun: (runId: string): Promise<RunDetail> =>
    request<RunDetail>(`${BASE_STORIES}/runs/${runId}`),

  deleteRun: (runId: string): Promise<void> =>
    request<void>(`${BASE_STORIES}/runs/${runId}`, { method: 'DELETE' }),

  // Quality
  startQuality: (runId: string): Promise<{ quality_run_id: string }> =>
    request<{ quality_run_id: string }>(
      `${BASE_QUALITY}/start/${runId}`,
      { method: 'POST' },
    ),

  getQualityStatus: (qualityRunId: string): Promise<QualityStatusResponse> =>
    request<QualityStatusResponse>(`${BASE_QUALITY}/status/${qualityRunId}`),

  getQualityForRun: (runId: string): Promise<QualityForRunResponse> =>
    request<QualityForRunResponse>(`${BASE_QUALITY}/for-run/${runId}`),

  submitReview: (
    qualityRunId: string,
    payload: {
      reviewer: string
      decisions: ScenarioDecision[]
      feedback?: string
      review_status: string
      use_llm_risk: boolean
    },
  ): Promise<ReviewResult> =>
    request<ReviewResult>(
      `${BASE_QUALITY}/review/${qualityRunId}`,
      { method: 'POST', body: JSON.stringify(payload) },
    ),

  getPdfUrl: (qualityRunId: string): string =>
    `${BASE_QUALITY}/download/${qualityRunId}`,
}
