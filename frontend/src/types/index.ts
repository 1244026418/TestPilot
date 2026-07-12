export interface User {
  id: number
  username: string
  role: 'admin' | 'user'
  created_at: string
}

export interface Project {
  id: number
  name: string
  description: string
  created_at: string
}

export interface ApiEndpoint {
  id: number
  project_id: number
  name: string
  method: string
  url: string
  headers: Record<string, unknown>
  body: Record<string, unknown>
  expected_status: number
  created_at: string
}

export interface TestEnvironment {
  id: number
  project_id: number
  name: string
  base_url: string
  variables: Record<string, unknown>
  is_active: boolean
  created_at: string
}

export interface AssertionRule {
  type: string
  operator?: string
  target?: string
  expected?: unknown
  schema?: Record<string, unknown>
}

export interface ExtractorRule {
  name: string
  expression: string
}

export interface TestCase {
  id: number
  endpoint_id: number
  title: string
  category: string
  request_headers: Record<string, unknown>
  request_body: Record<string, unknown>
  expected_status: number | null
  expected_contains: string | null
  assertions: AssertionRule[]
  extractors: ExtractorRule[]
  reason: string
  created_by_ai: boolean
  created_at: string
}

export interface TestResult {
  id: number
  testcase_id: number
  status: string
  status_code: number | null
  elapsed_ms: number | null
  request_url: string | null
  error: string | null
  response_snippet: string | null
  assertion_results: Array<{
    type: string
    target: string
    passed: boolean
    expected: unknown
    actual: unknown
    message: string
  }>
  extracted_variables: string[]
}

export interface TestRun {
  id: number
  project_id: number
  environment_id: number | null
  environment_name: string | null
  status: string
  total: number
  passed: number
  failed: number
  report_path: string | null
  started_at: string
  finished_at: string | null
  results: TestResult[]
}

export interface DashboardStats {
  projects: number
  endpoints: number
  cases: number
  runs: number
  passed_runs: number
  failed_runs: number
  latest_run: TestRun | null
}
