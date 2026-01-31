import client from './client'

export interface Agent {
  id: number
  agent_id: string
  name: string
  role: string
  status: string
  created_at: string
}

export const agentsApi = {
  list: (params?: { skip?: number; limit?: number }) => client.get('/agents', { params }),
  get: (agent_id: string) => client.get(`/agents/${agent_id}`),
  updateStatus: (agent_id: string, status: string) => client.put(`/agents/${agent_id}/status`, {}, { params: { status } })
}
