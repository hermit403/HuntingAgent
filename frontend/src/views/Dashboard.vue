<template>
  <div class="dashboard">
    <div class="stats-grid">
      <div class="stat-card pending">
        <div class="stat-icon">
          <el-icon :size="48"><Document /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ pendingTasks }}</div>
          <div class="stat-label">Pending Tasks</div>
        </div>
      </div>
      <div class="stat-card running">
        <div class="stat-icon">
          <el-icon :size="48"><Loading /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ runningTasks }}</div>
          <div class="stat-label">Running Tasks</div>
        </div>
      </div>
      <div class="stat-card completed">
        <div class="stat-icon">
          <el-icon :size="48"><CircleCheck /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ completedTasks }}</div>
          <div class="stat-label">Completed Tasks</div>
        </div>
      </div>
      <div class="stat-card agents">
        <div class="stat-icon">
          <el-icon :size="48"><Monitor /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ agents.length }}</div>
          <div class="stat-label">Active Agents</div>
        </div>
      </div>
    </div>

    <div class="content-grid">
      <el-card class="task-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">Recent Tasks</span>
            <div style="flex: 1"></div>
            <el-button type="primary" size="default" @click="$router.push('/audit')">
              <el-icon><Plus /></el-icon>
              New Task
            </el-button>
            <el-button type="danger" size="default" @click="cleanupDatabase">
              Clear DB
            </el-button>
          </div>
        </template>
        <el-table :data="tasks.slice(0, 10)" stripe style="width: 100%" :header-cell-style="{background: '#1a1a2e', color: '#e94560'}">
          <el-table-column prop="title" label="Title" min-width="150" />
          <el-table-column prop="status" label="Progress" width="300">
            <template #default="{ row }">
              <div style="display: flex; flex-direction: column; gap: 5px">
                <div style="display: flex; align-items: center; gap: 10px; justify-content: space-between">
                  <el-tag :type="getStatusType(row.status)" effect="dark" size="small">
                    {{ row.status }}
                  </el-tag>
                  <span v-if="row.status === 'running' || (row.progress && row.progress > 0)" style="font-size: 12px; color: #666">
                    {{ Math.round(row.progress || 0) }}%
                  </span>
                </div>
                <el-progress 
                  v-if="row.status === 'running' || (row.progress && row.progress > 0)" 
                  :percentage="row.progress || 0" 
                  :stroke-width="4"
                  :show-text="false"
                />
                <div v-if="row.message" style="font-size: 11px; color: #606266; font-style: italic; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" :title="row.message">
                  {{ row.message }}
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="Created" width="180">
            <template #default="{ row }">
               {{ new Date(row.created_at).toLocaleString() }}
            </template>
          </el-table-column>
        </el-table>
      </el-card>
      
      <el-card class="agent-card">
        <template #header>
          <span class="card-title">Agent Status</span>
        </template>
        <el-table :data="agents" stripe style="width: 100%" :header-cell-style="{background: '#1a1a2e', color: '#e94560'}">
          <el-table-column prop="name" label="Agent" min-width="150" />
          <el-table-column prop="role" label="Role" min-width="150" />
          <el-table-column prop="status" label="Status" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'info'" effect="dark">
                {{ row.status }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- Summary Board -->
    <div class="summary-section" v-if="latestSummaryTask">
      <el-card class="summary-card">
        <template #header>
          <div class="card-header">
            <span class="card-title">Latest Audit Summary: {{ latestSummaryTask.title }}</span>
            <el-tag type="success" effect="dark" size="small">Completed</el-tag>
          </div>
        </template>
        <div class="summary-content">
          <pre>{{ latestSummaryTask.result_summary }}</pre>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { tasksApi } from '../api/tasks'
import { agentsApi } from '../api/agents'
import { WebSocketClient } from '../utils/websocket'
import { Document, Loading, CircleCheck, Monitor, Plus } from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import type { Task } from '../api/tasks'
import type { Agent } from '../api/agents'

const tasks = ref<(Task & { progress?: number; message?: string })[]>([])
const agents = ref<Agent[]>([])
const wsClient = ref<WebSocketClient | null>(null)

const pendingTasks = computed(() => tasks.value.filter(t => t.status === 'pending').length)
const runningTasks = computed(() => tasks.value.filter(t => t.status === 'running').length)
const completedTasks = computed(() => tasks.value.filter(t => t.status === 'completed').length)
const latestSummaryTask = computed(() => tasks.value.find(t => t.status === 'completed' && t.result_summary))

async function loadTasks() {
  const tasksRes = await tasksApi.list({ limit: 100 })
  tasks.value = Array.isArray(tasksRes) ? tasksRes : (Array.isArray(tasksRes?.data) ? tasksRes.data : [])

  tasks.value.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

  tasks.value.forEach(t => {
    if (t.status === 'completed') {
      t.progress = 100
      t.message = 'Task completed'
    } else if (t.status === 'failed') {
      t.progress = 100
      t.message = t.error_message || 'Task failed'
    }
  })
}

async function loadAgents() {
  try {
    const agentsRes = await agentsApi.list()
    agents.value = Array.isArray(agentsRes) ? agentsRes : (Array.isArray(agentsRes?.data) ? agentsRes.data : [])
  } catch (e) {
    console.warn('Failed to load agents', e)
    agents.value = []
  }
}

async function cleanupDatabase() {
  try {
    await ElMessageBox.confirm(
      'This will clear database. Continue?',
      'Confirmation',
      { type: 'warning', confirmButtonText: 'Clear', cancelButtonText: 'Cancel' }
    )
    await tasksApi.cleanupDb()
    await loadTasks()
    ElMessage.success('Database cleared')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('Database cleanup failed')
    }
  }
}

onMounted(async () => {
  try {
    await loadTasks()
    await loadAgents()

    // Connect WebSocket
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = (import.meta as any).env?.MODE === 'development' ? 'localhost:8000' : location.host
    
    const clientId = `dashboard_${Date.now()}`
    const finalUrl = (import.meta as any).env?.MODE === 'development' 
       ? `ws://${host}/ws`
       : `${protocol}//${host}/ws`
    
    wsClient.value = new WebSocketClient(finalUrl, clientId)
    wsClient.value.connect()
    
    wsClient.value.on('task_update', async (data: any) => {
      const task = tasks.value.find(t => t.task_id === data.task_id)
      if (task) {
        task.status = data.status
        if (data.progress !== undefined) {
          task.progress = data.progress
        }
        if (data.message) {
          task.message = data.message
        }
      } else {
        try {
          const newTask = (await tasksApi.get(data.task_id)) as unknown as Task
          if (newTask && !tasks.value.find(t => t.task_id === newTask.task_id)) {
            tasks.value.unshift(newTask)
            tasks.value.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
            if (tasks.value.length > 100) {
              tasks.value = tasks.value.slice(0, 100)
            }
          }
        } catch (e) {
          // ignore error for non-existent or inaccessible tasks
        }
      }
    })

    wsClient.value.on('task_summary', (data: any) => {
      const task = tasks.value.find(t => t.task_id === data.task_id)
      if (task) {
        task.result_summary = data.summary
      }
    })

    wsClient.value.on('agent_status', (data: any) => {
      const agent = agents.value.find(a => a.agent_id === data.agent_id)
      if (agent) {
        agent.status = data.status
      }
    })
    
  } catch (error) {
    console.error('Failed to load data:', error)
    tasks.value = []
  }
})

onUnmounted(() => {
  if (wsClient.value) {
    wsClient.value.disconnect()
  }
})

function getStatusType(status: string) {
  const types: Record<string, any> = {
    pending: 'warning',
    running: 'primary',
    completed: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}
</script>

<style scoped lang="scss">
.dashboard {
  padding: 24px;
  min-height: 100vh;
  background: #f5f5f5;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  background: #ffffff;
  border: 1px solid rgba(233, 69, 96, 0.2);
  border-radius: 12px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  transition: all 0.3s ease;
  cursor: pointer;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(233, 69, 96, 0.3);
  }
  
  &.pending {
    border-color: rgba(233, 69, 96, 0.4);
    
    .stat-icon {
      color: #e94560;
      background: rgba(233, 69, 96, 0.1);
    }
  }
  
  &.running {
    border-color: rgba(15, 52, 96, 0.4);
    
    .stat-icon {
      color: #0f3460;
      background: rgba(15, 52, 96, 0.1);
    }
  }
  
  &.completed {
    border-color: rgba(22, 199, 132, 0.4);
    
    .stat-icon {
      color: #16c784;
      background: rgba(22, 199, 132, 0.1);
    }
  }
  
  &.agents {
    border-color: rgba(247, 183, 49, 0.4);
    
    .stat-icon {
      color: #f7b731;
      background: rgba(247, 183, 49, 0.1);
    }
  }
  
  .stat-icon {
    width: 64px;
    height: 64px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .stat-content {
    flex: 1;
  }
  
  .stat-value {
    font-size: 36px;
    font-weight: 700;
    color: #333333;
    margin-bottom: 4px;
  }
  
  .stat-label {
    font-size: 14px;
    color: #666666;
    font-weight: 500;
  }
}

.content-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 20px;
}

.task-card, .agent-card {
  background: #ffffff;
  border: 1px solid rgba(233, 69, 96, 0.2);
  border-radius: 12px;
  
  :deep(.el-card__header) {
    background: rgba(233, 69, 96, 0.05);
    border-bottom: 1px solid rgba(233, 69, 96, 0.2);
  }
  
  :deep(.el-table) {
    background: transparent;
    
    th {
      background: rgba(233, 69, 96, 0.05) !important;
      color: #e94560;
    }
    
    tr {
      background: transparent;
      
      &:hover td {
        background: rgba(233, 69, 96, 0.05) !important;
      }
    }
    
    td {
      border-bottom: 1px solid rgba(233, 69, 96, 0.2);
      color: #333333;
    }
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  .card-title {
    font-size: 18px;
    font-weight: 600;
    color: #333333;
  }
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, #e94560 0%, #ff6b6b 100%);
  border: none;
  
  &:hover {
    background: linear-gradient(135deg, #ff6b6b 0%, #e94560 100%);
  }
}

.summary-section {
  margin-top: 24px;
}

.summary-card {
  background: #ffffff;
  border: 1px solid rgba(233, 69, 96, 0.2);
  border-radius: 12px;
  
   :deep(.el-card__header) {
    background: rgba(233, 69, 96, 0.05);
    border-bottom: 1px solid rgba(233, 69, 96, 0.2);
  }
}

.summary-content {
  padding: 10px;
  
  pre {
    white-space: pre-wrap;
    font-family: inherit;
    color: #333;
    font-size: 14px;
    line-height: 1.6;
    margin: 0;
  }
}
</style>
