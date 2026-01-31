<template>
  <div class="audit-task">
    <el-card class="task-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon><EditPen /></el-icon>
            Create Audit Task
          </span>
        </div>
      </template>
      
      <el-form :model="form" label-position="top" label-width="120px">
        <el-form-item label="Task Title" required>
          <el-input
            v-model="form.title"
            placeholder="Enter task title"
            clearable
            maxlength="20"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="Description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="Describe the audit task"
            resize="none"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item label="Priority">
          <el-radio-group v-model="form.priority" size="large">
            <el-radio :value="0">Low</el-radio>
            <el-radio :value="1">Medium</el-radio>
            <el-radio :value="2">High</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="Code" required>
          <el-input
            v-model="form.code_content"
            type="textarea"
            :rows="12"
            placeholder="Paste your code here for security audit..."
            resize="none"
            class="code-editor"
          />
        </el-form-item>
        
        <el-form-item>
          <div class="button-group">
            <el-button type="primary" size="large" @click="submitTask" :loading="loading">
              <el-icon><Check /></el-icon>
              Submit Task
            </el-button>
            <el-button size="large" @click="resetForm">
              <el-icon><RefreshLeft /></el-icon>
              Reset
            </el-button>
          </div>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { tasksApi } from '../api/tasks'
import { useRouter } from 'vue-router'
import { EditPen, Check, RefreshLeft } from '@element-plus/icons-vue'

const router = useRouter()

const form = ref({
  task_id: `task-${Date.now()}`,
  title: '',
  description: '',
  priority: 1,
  code_content: ''
})

const loading = ref(false)

async function submitTask() {
  if (!form.value.title || !form.value.code_content) {
    ElMessage.warning('Please fill in all required fields')
    return
  }
  
  if (form.value.title.length > 20) {
    ElMessage.error('Title exceeds 20 characters limit')
    return
  }

  if (form.value.description.length > 200) {
    ElMessage.error('Description exceeds 200 characters limit')
    return
  }

  if (form.value.code_content.length > 3000) {
    ElMessage.error('Code content exceeds 3000 characters limit')
    return
  }
  
  loading.value = true
  try {
    const response = await tasksApi.create(form.value)
    console.log('Task created:', response)
    ElMessage.success('Task created successfully')
    resetForm()
    router.push('/')
  } catch (error: any) {
    console.error('Failed to create task:', error)
    const errorMsg = error?.response?.data?.detail || error?.message || 'Failed to create task'
    ElMessage.error(errorMsg)
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.value = {
    task_id: `task-${Date.now()}`,
    title: '',
    description: '',
    priority: 1,
    code_content: ''
  }
}
</script>

<style scoped lang="scss">
.audit-task {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
  min-height: 100vh;
  background: #f5f5f5;
}

.task-card {
  background: #ffffff;
  border: 1px solid rgba(233, 69, 96, 0.2);
  border-radius: 12px;
  
  :deep(.el-card__header) {
    background: rgba(233, 69, 96, 0.05);
    border-bottom: 1px solid rgba(233, 69, 96, 0.2);
  }
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  
  .card-title {
    font-size: 20px;
    font-weight: 600;
    color: #333333;
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

:deep(.el-form-item__label) {
  color: #333333;
  font-weight: 500;
}

:deep(.el-input__wrapper) {
  background: #ffffff;
  border: 1px solid rgba(233, 69, 96, 0.3);
  box-shadow: none !important;
  
  &.is-focus {
    border-color: #e94560 !important;
  }
  
  .el-input__inner {
    color: #333333;
    
    &::placeholder {
      color: #999999;
    }
  }
}

:deep(.el-textarea__inner) {
  background: #ffffff;
  border: 1px solid rgba(233, 69, 96, 0.3);
  color: #333333;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
  
  &:focus {
    border-color: #e94560;
  }
  
  &::placeholder {
    color: #999999;
  }
}

.code-editor {
  :deep(.el-textarea__inner) {
    font-family: 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.5;
  }
}

:deep(.el-radio-group) {
  .el-radio {
    margin-right: 24px;
    
    .el-radio__label {
      color: #333333;
    }
    
    &.is-checked {
      .el-radio__inner {
        background: #e94560;
        border-color: #e94560;
      }
    }
  }
}

.button-group {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 16px;
  
  .el-button {
    min-width: 140px;
  }
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, #e94560 0%, #ff6b6b 100%);
  border: none;
  
  &:hover {
    background: linear-gradient(135deg, #ff6b6b 0%, #e94560 100%);
  }
}
</style>
