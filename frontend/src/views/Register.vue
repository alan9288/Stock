<template>
  <div class="min-h-screen flex items-center justify-center px-4">
    <div class="glass rounded-2xl p-8 w-full max-w-md">
      <!-- Logo -->
      <div class="text-center mb-8">
        <span class="text-5xl">📊</span>
        <h1 class="text-2xl font-bold mt-4">建立新帳戶</h1>
        <p class="text-gray-400 mt-2">開始追蹤您的投資組合</p>
      </div>

      <!-- 錯誤訊息 -->
      <div v-if="error" class="bg-rose-500/20 border border-rose-500 text-rose-300 px-4 py-3 rounded-xl mb-6">
        {{ error }}
      </div>

      <!-- 註冊表單 -->
      <form @submit.prevent="handleRegister" class="space-y-6">
        <!-- 名稱 -->
        <div>
          <label class="block text-sm text-gray-400 mb-2">名稱</label>
          <input
            v-model="name"
            type="text"
            placeholder="您的名稱"
            class="w-full bg-dark-800 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500"
          />
        </div>

        <!-- Email -->
        <div>
          <label class="block text-sm text-gray-400 mb-2">Email <span class="text-rose-400">*</span></label>
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
          <label class="block text-sm text-gray-400 mb-2">密碼 <span class="text-rose-400">*</span></label>
          <input
            v-model="password"
            type="password"
            required
            minlength="6"
            placeholder="至少 6 個字元"
            class="w-full bg-dark-800 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500"
          />
        </div>

        <!-- 確認密碼 -->
        <div>
          <label class="block text-sm text-gray-400 mb-2">確認密碼 <span class="text-rose-400">*</span></label>
          <input
            v-model="confirmPassword"
            type="password"
            required
            placeholder="再次輸入密碼"
            class="w-full bg-dark-800 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500"
            :class="{ 'ring-2 ring-rose-500': confirmPassword && password !== confirmPassword }"
          />
          <p v-if="confirmPassword && password !== confirmPassword" class="text-rose-400 text-sm mt-1">
            密碼不一致
          </p>
        </div>

        <!-- 註冊按鈕 -->
        <button
          type="submit"
          :disabled="loading || (confirmPassword && password !== confirmPassword)"
          class="w-full btn-gradient py-3 rounded-xl font-semibold flex items-center justify-center gap-2 disabled:opacity-50"
        >
          <span v-if="loading" class="animate-spin">⟳</span>
          {{ loading ? '註冊中...' : '建立帳戶' }}
        </button>
      </form>

      <!-- 分隔線 -->
      <div class="flex items-center my-6">
        <div class="flex-1 border-t border-white/10"></div>
        <span class="px-4 text-gray-500 text-sm">或</span>
        <div class="flex-1 border-t border-white/10"></div>
      </div>

      <!-- 登入連結 -->
      <p class="text-center text-gray-400">
        已經有帳戶？
        <router-link to="/login" class="text-cyan-400 hover:underline">
          立即登入
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
const { register, loading, error } = useAuth()

const name = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')

async function handleRegister() {
  if (password.value !== confirmPassword.value) {
    return
  }
  
  const result = await register(email.value, password.value, name.value || null)
  if (result.success) {
    router.push('/')
  }
}
</script>
