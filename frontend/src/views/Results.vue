<template>
  <div class="results">
    <el-card class="results-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon><Document /></el-icon>
            Audit Results
          </span>
          <el-input
            v-model="searchText"
            placeholder="Search results..."
            style="width: 300px"
            clearable
            size="default"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </template>
      
      <el-table
        :data="filteredResults"
        style="width: 100%"
        stripe
        :header-cell-style="{background: '#1a1a2e', color: '#e94560'}"
        v-loading="loading"
      >
        <el-table-column prop="task_title" label="Task Title" width="200" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.task_title || row.task_id }}
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="Severity" width="100">
          <template #default="{ row }">
            <el-tag :type="getSeverityType(row.severity)" effect="dark">
              {{ row.severity }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="Category" width="120">
          <template #default="{ row }">
             <el-tag effect="light">{{ row.category || 'unknown' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="Result Description" min-width="300" />
        <el-table-column prop="code_snippet" label="Code Context" min-width="200">
          <template #default="{ row }">
             <code style="background: #e0e0e0; padding: 2px 4px; border-radius: 4px; color: #d63384;" v-if="row.code_snippet">{{ row.code_snippet }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="Created" width="180">
          <template #default="{ row }">
             {{ new Date(row.created_at).toLocaleString() }}
          </template>
        </el-table-column>
      </el-table>
      
      <div v-if="!loading && results.length === 0" class="empty-state">
        <el-empty description="No audit results found" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Search, Document } from '@element-plus/icons-vue'
import { resultsApi } from '../api/results'

const searchText = ref('')
const results = ref([])
const loading = ref(false)

const filteredResults = computed(() => {
  if (!searchText.value) return results.value
  const search = searchText.value.toLowerCase()
  return results.value.filter((r: any) =>
    r.description?.toLowerCase().includes(search) ||
    r.task_id?.toLowerCase().includes(search)
  )
})

onMounted(async () => {
  loading.value = true
  try {
    const response = await resultsApi.list()
    // The interceptor returns the data directly
    results.value = Array.isArray(response) ? response : (response?.data || [])
  } catch (error) {
    console.error('Failed to load results:', error)
  } finally {
    loading.value = false
  }
})

function getSeverityType(severity: string) {
  const types: Record<string, any> = {
    critical: 'danger',
    high: 'warning',
    medium: 'primary',
    low: 'info',
    info: 'success'
  }
  return types[severity] || 'info'
}
</script>

<style scoped lang="scss">
.results {
  padding: 24px;
  min-height: 100vh;
  background: #f5f5f5;
}

.results-card {
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
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.empty-state {
  padding: 40px 0;
  text-align: center;
}

:deep(.el-empty) {
  --el-empty-description-color: #666666;
}
</style>
