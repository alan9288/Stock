<template>
  <div class="min-h-screen flex items-center justify-center px-4">
    <div class="glass rounded-2xl p-8 w-full max-w-md">
      <!-- Logo -->
      <div class="text-center mb-8">
        <span class="text-5xl">📈</span>
        <h1 class="text-2xl font-bold mt-4">股票監控系統</h1>
        <p class="text-gray-400 mt-2">登入您的帳戶</p>
      </div>

      <!-- 錯誤訊息 -->
      <div v-if="error" class="bg-rose-500/20 border border-rose-500 text-rose-300 px-4 py-3 rounded-xl mb-6">
        {{ error }}
      </div>

      <!-- 登入表單 -->
      <form @submit.prevent="handleLogin" class="space-y-6">
        <!-- Email -->
        <div>
          <label class="block text-sm text-gray-400 mb-2">Email</label>
          <input
            v-model="email"
            type="email"
            required
            placeholder="your@email.com"
            class="w-full bg-dark-800 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500"
          />
        </div>

        <!-- 密碼 -->
        <div>
          <label class="block text-sm text-gray-400 mb-2">密碼</label>
          <input
            v-model="password"
            type="password"
            required
            placeholder="••••••••"
            class="w-full bg-dark-800 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500"
          />
        </div>

        <!-- 登入按鈕 -->
        <button
          type="submit"
          :disabled="loading"
          class="w-full btn-gradient py-3 rounded-xl font-semibold flex items-center justify-center gap-2"
        >
          <span v-if="loading" class="animate-spin">⟳</span>
          {{ loading ? '登入中...' : '登入' }}
        </button>
      </form>

      <!-- 分隔線 -->
      <div class="flex items-center my-6">
        <div class="flex-1 border-t border-white/10"></div>
        <span class="px-4 text-gray-500 text-sm">或</span>
        <div class="flex-1 border-t border-white/10"></div>
      </div>

      <!-- 註冊連結 -->
      <p class="text-center text-gray-400">
        還沒有帳戶？
        <router-link to="/register" class="text-cyan-400 hover:underline">
          立即註冊
        </router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../stores/auth'

const router = useRouter()
const { login, loading, error } = useAuth()

const email = ref('')
const password = ref('')

async function handleLogin() {
  const result = await login(email.value, password.value)
  if (result.success) {
    router.push('/')
  }
}
</script>
