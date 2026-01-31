import client from './client'

export interface AuditResult {
  id: number
  result_id: string
  task_id: string
  severity: string
  category: string
  description: string
  file_path: string
  line_number: number
  code_snippet: string
  created_at: string
}

export interface AuditResultCreate {
  result_id: string
  task_id: string
  severity: string
  category: string
  description: string
  file_path: string
  line_number: number
  code_snippet: string
}

export const resultsApi = {
  list: (params?: { skip?: number; limit?: number; task_id?: string; severity?: string }) => 
    client.get('/results', { params }),
  get: (result_id: string) => 
    client.get(`/results/${result_id}`),
  create: (data: AuditResultCreate) => 
    client.post('/results', data)
}
