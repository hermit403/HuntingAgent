import client from './client'

export interface Tool {
  id: number
  tool_id: string
  name: string
  description: string
  category: string
  status: string
  created_at: string
}

export const toolsApi = {
  list: (params?: { skip?: number; limit?: number }) => client.get('/tools', { params }),
  get: (tool_id: string) => client.get(`/tools/${tool_id}`)
}
