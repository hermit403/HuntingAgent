<template>
  <ErrorBoundary>
    <el-container class="app-container">
      <el-header class="app-header">
        <div class="header-content">
          <div class="logo">
            <el-icon :size="32"><Lock /></el-icon>
            <span>HuntingAgent</span>
          </div>
          <el-menu
            :default-active="activeMenu"
            mode="horizontal"
            router
            class="header-menu"
          >
            <el-menu-item index="/">Dashboard</el-menu-item>
            <el-menu-item index="/audit">Audit Task</el-menu-item>
            <el-menu-item index="/results">Results</el-menu-item>
          </el-menu>
        </div>
      </el-header>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </ErrorBoundary>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Lock } from '@element-plus/icons-vue'
import ErrorBoundary from './components/ErrorBoundary.vue'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>

<style scoped lang="scss">
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.app-header {
  background: rgba(255, 255, 255, 0.95);
  border-bottom: 1px solid rgba(233, 69, 96, 0.2);
  padding: 0;
  backdrop-filter: blur(10px);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  padding: 0 32px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #e94560;
  font-size: 26px;
  font-weight: 700;
  text-shadow: 0 2px 8px rgba(233, 69, 96, 0.3);
  
  .el-icon {
    filter: drop-shadow(0 2px 4px rgba(233, 69, 96, 0.4));
  }
}

.header-menu {
  background: transparent;
  border: none;
  
  :deep(.el-menu-item) {
    color: #a0a0a0;
    font-weight: 500;
    font-size: 15px;
    padding: 0 20px;
    height: 60px;
    line-height: 60px;
    border-radius: 8px;
    transition: all 0.3s ease;
    
    &:hover {
      color: #e94560;
      background: rgba(233, 69, 96, 0.1);
    }
    
    &.is-active {
      color: #e94560;
      background: rgba(233, 69, 96, 0.2);
      border-bottom: 2px solid #e94560;
    }
  }
}

.app-main {
  background: transparent;
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}
</style>
