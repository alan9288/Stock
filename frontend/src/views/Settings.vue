<template>
  <div class="max-w-4xl mx-auto space-y-8">
    <h1 class="text-3xl font-bold">⚙️ 設定</h1>

    <!-- 載入中 -->
    <div v-if="loading" class="glass rounded-xl p-8 text-center">
      <span class="animate-spin text-3xl">⟳</span>
      <p class="mt-4 text-gray-400">載入設定中...</p>
    </div>

    <div v-else class="space-y-8">
      <!-- 觀察清單已移至獨立頁面 -->
      <div class="glass rounded-xl p-4 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <span class="text-2xl">📋</span>
          <div>
            <p class="font-semibold">股票觀察清單</p>
            <p class="text-gray-400 text-sm">管理您追蹤的股票</p>
          </div>
        </div>
        <router-link to="/watchlist" class="px-4 py-2 btn-gradient rounded-xl font-semibold">
          前往管理 →
        </router-link>
      </div>

      <!-- ========== 通知設定區塊 ========== -->
      <div class="glass rounded-2xl p-6">
        <h2 class="text-2xl font-bold mb-6">🔔 通知設定</h2>
        
        <div class="space-y-6">
          <!-- 通知信箱 -->
          <div>
            <label class="block text-sm text-gray-400 mb-2">📧 通知信箱</label>
            <div class="flex gap-4">
              <input
                v-model="settings.notification_email"
                type="email"
                placeholder="your@email.com"
                class="flex-1 bg-dark-800 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500"
              />
              <button
                @click="sendTestEmail"
                :disabled="testingEmail"
                class="px-4 py-2 bg-emerald-500/20 text-emerald-400 rounded-xl hover:bg-emerald-500/30 transition-all disabled:opacity-50"
              >
                {{ testingEmail ? '發送中...' : '測試' }}
              </button>
            </div>
            <p v-if="testEmailResult" :class="testEmailResult.success ? 'text-emerald-400' : 'text-rose-400'" class="mt-2 text-sm">
              {{ testEmailResult.message }}
            </p>
          </div>

          <!-- 啟用通知 -->
          <div class="flex items-center justify-between">
            <div>
              <p class="font-semibold">啟用通知</p>
              <p class="text-gray-400 text-sm">當股票價格變動超過門檻時發送 Email</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input v-model="settings.enabled" type="checkbox" class="sr-only peer">
              <div class="w-14 h-7 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-[4px] after:bg-white after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-cyan-500"></div>
            </label>
          </div>

          <!-- 門檻設定 -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm text-gray-400 mb-2">🇹🇼 台股警報門檻</label>
              <input
                v-model="settings.thresholds_tw"
                type="text"
                placeholder="+3 +5 -5 -10"
                class="w-full bg-dark-800 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500"
              />
            </div>
            <div>
              <label class="block text-sm text-gray-400 mb-2">🇺🇸 美股警報門檻</label>
              <input
                v-model="settings.thresholds_us"
                type="text"
                placeholder="+5 +10 -5 -10"
                class="w-full bg-dark-800 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500"
              />
            </div>
          </div>

          <!-- 儲存按鈕 -->
          <div class="flex justify-end gap-4 pt-4">
            <button
              @click="saveSettings"
              :disabled="saving"
              class="px-6 py-3 btn-gradient rounded-xl font-semibold"
            >
              {{ saving ? '儲存中...' : '💾 儲存通知設定' }}
            </button>
          </div>

          <!-- 儲存結果 -->
          <div v-if="saveResult" :class="saveResult.success ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'" class="rounded-xl p-4 text-center">
            {{ saveResult.message }}
          </div>
        </div>
      </div>

      <!-- ========== 帳號安全區塊 ========== -->
      <div class="glass rounded-2xl p-6">
        <h2 class="text-2xl font-bold mb-6">🔐 帳號安全</h2>
        
        <div class="space-y-4">
          <!-- 現有密碼 -->
          <div>
            <label class="block text-sm text-gray-400 mb-2">現有密碼</label>
            <input
              v-model="passwordForm.currentPassword"
              type="password"
              placeholder="輸入現有密碼"
              class="w-full bg-dark-800 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500"
            />
          </div>
          
          <!-- 新密碼 -->
          <div>
            <label class="block text-sm text-gray-400 mb-2">新密碼</label>
            <input
              v-model="passwordForm.newPassword"
              type="password"
              placeholder="輸入新密碼（至少 6 個字元）"
              class="w-full bg-dark-800 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500"
            />
          </div>
          
          <!-- 確認新密碼 -->
          <div>
            <label class="block text-sm text-gray-400 mb-2">確認新密碼</label>
            <input
              v-model="passwordForm.confirmPassword"
              type="password"
              placeholder="再次輸入新密碼"
              class="w-full bg-dark-800 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500"
            />
          </div>
          
          <!-- 修改密碼按鈕 -->
          <div class="flex justify-end pt-2">
            <button
              @click="changePassword"
              :disabled="changingPassword"
              class="px-6 py-3 btn-gradient rounded-xl font-semibold disabled:opacity-50"
            >
              {{ changingPassword ? '修改中...' : '🔑 修改密碼' }}
            </button>
          </div>
          
          <!-- 結果訊息 -->
          <div v-if="passwordResult" :class="passwordResult.success ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'" class="rounded-xl p-4 text-center">
            {{ passwordResult.message }}
          </div>
        </div>
      </div>
    </div>


  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
import { useToast } from '../composables/useToast'

const toast = useToast()

const loading = ref(true)
const saving = ref(false)
const testingEmail = ref(false)

// 通知設定
const settings = ref({
  notification_email: '',
  thresholds_tw: '+3 +5 -5 -10',
  thresholds_us: '+5 +10 -5 -10',
  enabled: true
})

const saveResult = ref(null)
const testEmailResult = ref(null)

// 密碼修改
const changingPassword = ref(false)
const passwordResult = ref(null)
const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// ========== 載入資料 ==========
async function loadData() {
  loading.value = true
  try {
    const settingsRes = await api.get('/notifications/settings')
    settings.value = settingsRes.data
  } catch (err) {
    console.error('載入設定失敗', err)
  } finally {
    loading.value = false
  }
}

// ========== 通知設定 ==========
async function saveSettings() {
  saving.value = true
  saveResult.value = null
  
  try {
    await api.put('/notifications/settings', {
      notification_email: settings.value.notification_email,
      thresholds_tw: settings.value.thresholds_tw,
      thresholds_us: settings.value.thresholds_us,
      enabled: settings.value.enabled
    })
    toast.success('設定已儲存')
  } catch (err) {
    toast.error('儲存失敗: ' + (err.response?.data?.detail || err.message))
  } finally {
    saving.value = false
  }
}

// ========== 密碼修改 ==========
async function changePassword() {
  // 前端驗證
  if (!passwordForm.value.currentPassword) {
    passwordResult.value = { success: false, message: '請輸入現有密碼' }
    return
  }
  if (!passwordForm.value.newPassword) {
    passwordResult.value = { success: false, message: '請輸入新密碼' }
    return
  }
  if (passwordForm.value.newPassword.length < 6) {
    passwordResult.value = { success: false, message: '新密碼至少需要 6 個字元' }
    return
  }
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    passwordResult.value = { success: false, message: '新密碼與確認密碼不一致' }
    return
  }
  
  changingPassword.value = true
  passwordResult.value = null
  
  try {
    await api.put('/auth/password', {
      current_password: passwordForm.value.currentPassword,
      new_password: passwordForm.value.newPassword
    })
    passwordResult.value = { success: true, message: '✅ 密碼已更新成功' }
    // 清空表單
    passwordForm.value = { currentPassword: '', newPassword: '', confirmPassword: '' }
  } catch (err) {
    passwordResult.value = { success: false, message: '❌ ' + (err.response?.data?.detail || '修改失敗') }
  } finally {
    changingPassword.value = false
    setTimeout(() => { passwordResult.value = null }, 5000)
  }
}

async function sendTestEmail() {
  testingEmail.value = true
  testEmailResult.value = null
  
  try {
    await api.put('/notifications/settings', {
      notification_email: settings.value.notification_email
    })
    const response = await api.post('/notifications/test-email')
    testEmailResult.value = { success: true, message: response.data.message }
  } catch (err) {
    testEmailResult.value = { success: false, message: err.response?.data?.detail || '發送失敗' }
  } finally {
    testingEmail.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>
