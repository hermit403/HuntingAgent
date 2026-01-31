import client from './client'

export interface Task {
  id: number
  task_id: string
  title: string
  description: string
  status: string
  priority: number
  created_at: string
  started_at: string | null
  completed_at: string | null
  error_message: string | null
  agent_id: number | null
  result_summary?: string | null
}

export interface TaskCreate {
  task_id: string
  title: string
  description: string
  priority?: number
  code_content?: string
  target_files?: string
  parameters?: string
}

export const tasksApi = {
  create: (data: TaskCreate) => client.post('/tasks', data),
  list: (params?: { skip?: number; limit?: number }) => client.get('/tasks', { params }),
  get: (task_id: string) => client.get(`/tasks/${task_id}`),
  updateStatus: (task_id: string, status: string) => client.put(`/tasks/${task_id}/status`, {}, { params: { status } }),
  delete: (task_id: string) => client.delete(`/tasks/${task_id}`),
  cleanupDb: () => client.post('/tasks/cleanup-db')
}
