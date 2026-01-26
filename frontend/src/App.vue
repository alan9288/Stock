<template>
  <div class="min-h-screen bg-dark-900">
    <!-- Toast 通知 -->
    <ToastProvider />
    
    <!-- 導航列 -->
    <nav v-if="isAuthenticated" class="glass sticky top-0 z-50 px-4 md:px-6 py-4">
      <div class="max-w-7xl mx-auto flex items-center justify-between">
        <div class="flex items-center gap-3">
          <span class="text-2xl">📊</span>
          <h1 class="text-lg md:text-xl font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
            股票監控儀表板
          </h1>
        </div>
        
        <!-- 漢堡選單按鈕 (手機版) -->
        <button 
          @click="menuOpen = !menuOpen"
          class="md:hidden p-2 rounded-lg hover:bg-white/10 transition-all"
        >
          <span class="text-xl">{{ menuOpen ? '✕' : '☰' }}</span>
        </button>
        
        <!-- 桌面版導航 -->
        <div class="hidden md:flex items-center gap-2">
          <router-link 
            to="/" 
            class="nav-link"
            :class="{ 'nav-link-active': $route.path === '/' }"
          >
            🏠 儀表板
          </router-link>
          <router-link 
            to="/holdings" 
            class="nav-link"
            :class="{ 'nav-link-active': $route.path === '/holdings' }"
          >
            💼 持股
          </router-link>
          <router-link 
            to="/settings" 
            class="nav-link"
            :class="{ 'nav-link-active': $route.path === '/settings' }"
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
      
      <!-- 手機版選單 -->
      <Transition name="slide-down">
        <div v-if="menuOpen" class="md:hidden mt-4 pt-4 border-t border-white/10 space-y-2">
          <router-link 
            to="/" 
            class="mobile-nav-link"
            :class="{ 'mobile-nav-link-active': $route.path === '/' }"
            @click="menuOpen = false"
          >
            🏠 儀表板
          </router-link>
          <router-link 
            to="/holdings" 
            class="mobile-nav-link"
            :class="{ 'mobile-nav-link-active': $route.path === '/holdings' }"
            @click="menuOpen = false"
          >
            💼 持股
          </router-link>
          <router-link 
            to="/settings" 
            class="mobile-nav-link"
            :class="{ 'mobile-nav-link-active': $route.path === '/settings' }"
            @click="menuOpen = false"
          >
            ⚙️ 設定
          </router-link>
          
          <!-- 使用者區域 -->
          <div class="flex items-center justify-between pt-4 mt-4 border-t border-white/10">
            <span class="text-gray-400">👤 {{ user?.name || user?.email }}</span>
            <button 
              @click="handleLogout"
              class="px-3 py-1 text-sm bg-rose-500/20 text-rose-400 rounded-lg hover:bg-rose-500/30 transition-all"
            >
              登出
            </button>
          </div>
        </div>
      </Transition>
    </nav>

    <!-- 主內容 -->
    <main :class="isAuthenticated ? 'max-w-7xl mx-auto px-4 md:px-6 py-8' : ''">
      <Transition name="fade" mode="out-in">
        <router-view :key="$route.path" />
      </Transition>
    </main>

    <!-- 頁尾 -->
    <footer v-if="isAuthenticated" class="text-center text-gray-500 text-sm py-8">
      <p>Stock Monitor v2.0 | 多用戶版 | Powered by FastAPI + Vue 3</p>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from './stores/auth'
import ToastProvider from './components/ToastProvider.vue'

const router = useRouter()
const { user, isAuthenticated, logout } = useAuth()

const menuOpen = ref(false)

function handleLogout() {
  logout()
  menuOpen.value = false
  router.push('/login')
}
</script>

<style scoped>
/* 桌面版導航連結 */
.nav-link {
  @apply px-4 py-2 rounded-lg transition-all hover:bg-white/10 relative;
}

.nav-link-active {
  @apply bg-gradient-to-r from-purple-500/30 to-cyan-500/30 text-white font-semibold;
  box-shadow: 0 2px 0 0 theme('colors.cyan.400');
}

/* 手機版導航連結 */
.mobile-nav-link {
  @apply block w-full px-4 py-3 rounded-xl transition-all hover:bg-white/10;
}

.mobile-nav-link-active {
  @apply bg-gradient-to-r from-purple-500/30 to-cyan-500/30 text-white font-semibold;
}

/* 頁面過場動畫 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 手機選單展開動畫 */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
