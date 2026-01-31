<template>
  <div v-if="error" class="error-boundary">
    <el-result
      icon="error"
      title="Something went wrong"
      :sub-title="errorMessage"
    >
      <template #extra>
        <el-button type="primary" @click="resetError">Try again</el-button>
        <el-button @click="goHome">Go to Dashboard</el-button>
      </template>
    </el-result>
  </div>
  <slot v-else />
</template>

<script setup lang="ts">
import { ref, onErrorCaptured } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const error = ref<Error | null>(null)
const errorMessage = ref('')

onErrorCaptured((err: Error) => {
  error.value = err
  errorMessage.value = err.message || 'An unexpected error occurred'
  console.error('ErrorBoundary caught an error:', err)
  return false
})

function resetError() {
  error.value = null
  errorMessage.value = ''
}

function goHome() {
  router.push('/')
  resetError()
}
</script>

<style scoped>
.error-boundary {
  padding: 40px;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
