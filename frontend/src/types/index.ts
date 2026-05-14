export interface Ambiguity {
  word: string
  category: string
  ieee_830_violation: string
  iso_25010_category: string
  suggestion: string
  context: string
  severity: 'alta' | 'media' | 'baja'
}

export interface Resolution {
  word: string
  category: string
  analyst_resolution: string
  status: 'resolved' | 'dismissed'
}

export interface AcceptanceCriterion {
  id: string
  description: string
  given: string
  when: string
  then: string
  test_data_examples: Record<string, string>[]
  is_negative_case: boolean
  boundary_values: string[]
}

export interface AmbiguityResolution {
  original_text: string
  issue: string
  resolution: string
  assumption_made: boolean
}

export interface UserStory {
  id: string
  title: string
  story_type: 'functional' | 'non_functional' | 'technical'
  priority: 'critical' | 'high' | 'medium' | 'low'
  as_a: string
  i_want: string
  so_that: string
  acceptance_criteria: AcceptanceCriterion[]
  business_rules: string[]
  dependencies: string[]
  ui_elements: string[]
  api_endpoints: string[]
  ambiguities_resolved: AmbiguityResolution[]
}

export interface RunResult {
  pipeline_run_id: string
  agent_version: string
  original_requirements_text: string
  project_context: string
  user_stories: UserStory[]
  total_ambiguities_found: number
  total_assumptions_made: number
  coverage_notes?: string
  created_at: string
}

export interface RunDetail {
  run_id: string
  prompt: string
  status: 'pending' | 'completed' | 'failed'
  created_at: string
  story_count?: number
  result?: RunResult
  error?: string
}

export interface RunSummary {
  run_id: string
  prompt: string
  status: 'pending' | 'completed' | 'failed'
  created_at: string
  story_count?: number
}

// ── Quality / V3 / V4 types ──────────────────────────────────────────────────

export type QualityCharacteristic =
  | 'functional_suitability'
  | 'performance_efficiency'
  | 'security'
  | 'usability'
  | 'reliability'
  | 'compatibility'
  | 'maintainability'
  | 'portability'

export type ScenarioType =
  | 'positive'
  | 'negative'
  | 'boundary'
  | 'edge_case'
  | 'error_handling'

export interface GherkinStep {
  keyword: string
  text: string
}

export interface GherkinScenario {
  name: string
  scenario_type: ScenarioType
  quality_characteristic: QualityCharacteristic
  tags: string[]
  steps: GherkinStep[]
  acceptance_criterion_id: string
  user_story_id: string
}

export interface GherkinFeature {
  name: string
  description: string
  user_story_id: string
  scenarios: GherkinScenario[]
}

export interface CoverageByCharacteristic {
  [key: string]: number
}

export interface ContractB {
  pipeline_run_id: string
  agent_version: string
  features: GherkinFeature[]
  total_scenarios: number
  total_positive: number
  total_negative: number
  total_boundary: number
  coverage_by_characteristic: CoverageByCharacteristic
}

export interface RiskItem {
  qc: string
  n_escenarios: number
  pct_total: number
  nivel: 'CRITICO' | 'ALTO' | 'MEDIO' | 'BAJO'
  descripcion_riesgo: string
  contexto_impacto: string
  recomendacion_base: string
  recomendacion_llm: string
  analisis_impacto?: string
  criterios_exito?: string
  referencias_tecnicas?: string
  enriquecido_llm: boolean
}

export interface RiskMatrix {
  pipeline_run_id: string
  total_escenarios: number
  enriquecido_llm: boolean
  riesgos: RiskItem[]
  resumen_ejecutivo: {
    total_qc: number
    criticos: number
    altos: number
    medios: number
    bajos: number
    qc_sin_cobertura: string[]
  }
}

export interface ScenarioDecision {
  scenario_name: string
  action: 'accepted' | 'reclassified' | 'comment'
  new_quality_characteristic?: QualityCharacteristic
  reason?: string
}

export interface QualityStatusResponse {
  quality_run_id: string
  run_id: string
  status: 'running' | 'completed' | 'failed'
  progress_msg?: string
  contract_b?: ContractB
  error?: string
}

export interface ReviewResult {
  quality_run_id: string
  pdf_available: boolean
  pdf_url?: string
  risk_matrix?: RiskMatrix
  reviewed_contract_b?: ContractB
}

export interface QualityForRunResponse {
  found: boolean
  quality_run_id?: string
  status?: string
  has_review: boolean
  contract_b?: ContractB
  risk_matrix?: RiskMatrix
  pdf_url?: string
}
