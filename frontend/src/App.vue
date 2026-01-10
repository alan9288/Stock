<template>
  <div class="min-h-screen bg-dark-900">
    <!-- 導航列 -->
    <nav class="glass sticky top-0 z-50 px-6 py-4">
      <div class="max-w-7xl mx-auto flex items-center justify-between">
        <div class="flex items-center gap-3">
          <span class="text-2xl">📊</span>
          <h1 class="text-xl font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
            股票監控儀表板
          </h1>
        </div>
        <div class="flex gap-4">
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
        </div>
      </div>
    </nav>

    <!-- 主內容 -->
    <main class="max-w-7xl mx-auto px-6 py-8">
      <router-view />
    </main>

    <!-- 頁尾 -->
    <footer class="text-center text-gray-500 text-sm py-8">
      <p>Stock Monitor v1.0 | Powered by FastAPI + Vue 3</p>
    </footer>
  </div>
</template>

<script setup>
// App 組件
</script>
