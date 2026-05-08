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
