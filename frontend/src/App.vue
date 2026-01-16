<template>
  <div class="min-h-screen bg-dark-900">
    <!-- 導航列 -->
    <nav v-if="isAuthenticated" class="glass sticky top-0 z-50 px-6 py-4">
      <div class="max-w-7xl mx-auto flex items-center justify-between">
        <div class="flex items-center gap-3">
          <span class="text-2xl">📊</span>
          <h1 class="text-xl font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
            股票監控儀表板
          </h1>
        </div>
        <div class="flex items-center gap-4">
          <router-link 
            to="/" 
            class="px-4 py-2 rounded-lg transition-all hover:bg-white/10"
            :class="{ 'bg-white/10': $route.path === '/' }"
          >
            🏠 儀表板
          </router-link>
          <router-link 
            to="/settings" 
            class="px-4 py-2 rounded-lg transition-all hover:bg-white/10"
            :class="{ 'bg-white/10': $route.path === '/settings' }"
          >
            ⚙️ 設定
          </router-link>
          
          <!-- 使用者區域 -->
          <div class="flex items-center gap-3 ml-4 pl-4 border-l border-white/10">
            <span class="text-gray-400">👤 {{ user?.name || user?.email }}</span>
            <button 
              @click="handleLogout"
              class="px-3 py-1 text-sm bg-rose-500/20 text-rose-400 rounded-lg hover:bg-rose-500/30 transition-all"
            >
              登出
            </button>
          </div>
        </div>
      </div>
    </nav>

    <!-- 主內容 -->
    <main :class="isAuthenticated ? 'max-w-7xl mx-auto px-6 py-8' : ''">
      <router-view />
    </main>

    <!-- 頁尾 -->
    <footer v-if="isAuthenticated" class="text-center text-gray-500 text-sm py-8">
      <p>Stock Monitor v2.0 | 多用戶版 | Powered by FastAPI + Vue 3</p>
    </footer>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuth } from './stores/auth'

const router = useRouter()
const { user, isAuthenticated, logout } = useAuth()

function handleLogout() {
  logout()
  router.push('/login')
}
</script>

