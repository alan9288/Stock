<template>
  <div class="max-w-4xl mx-auto space-y-8">
    <h1 class="text-3xl font-bold">⚙️ 設定</h1>

    <!-- 載入中 -->
    <div v-if="loading" class="glass rounded-xl p-8 text-center">
      <span class="animate-spin text-3xl">⟳</span>
      <p class="mt-4 text-gray-400">載入設定中...</p>
    </div>

    <div v-else class="space-y-8">
      <!-- ========== 股票管理區塊 ========== -->
      <div class="glass rounded-2xl p-6">
        <h2 class="text-2xl font-bold mb-6">📈 股票觀察清單</h2>
        
        <!-- 新增股票 -->
        <div class="flex gap-4 mb-6">
          <select v-model="newStockMarket" class="bg-dark-800 border border-white/10 rounded-xl px-4 py-3 text-white">
            <option value="US">🇺🇸 美股</option>
            <option value="TW">🇹🇼 台股</option>
          </select>
          <input
            v-model="newStockSymbol"
            type="text"
            :placeholder="newStockMarket === 'TW' ? '輸入股票代號 (如: 2330)' : '輸入股票代號 (如: AAPL)'"
            class="flex-1 bg-dark-800 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500"
            @keyup.enter="addStock"
          />
          <button
            @click="addStock"
            :disabled="addingStock || !newStockSymbol.trim()"
            class="px-6 py-3 btn-gradient rounded-xl font-semibold disabled:opacity-50"
          >
            {{ addingStock ? '新增中...' : '➕ 新增' }}
          </button>
        </div>

        <!-- 新增結果訊息 -->
        <p v-if="stockMessage" :class="stockMessage.success ? 'text-emerald-400' : 'text-rose-400'" class="mb-4 text-sm">
          {{ stockMessage.text }}
        </p>

        <!-- Tab 切換 -->
        <div class="flex gap-2 mb-6">
          <button 
            @click="activeTab = 'US'" 
            class="px-6 py-3 rounded-xl font-semibold transition-all"
            :class="activeTab === 'US' ? 'btn-gradient' : 'bg-white/10 hover:bg-white/20'"
          >
            🇺🇸 美股 ({{ watchlist.US.length }})
          </button>
          <button 
            @click="activeTab = 'TW'" 
            class="px-6 py-3 rounded-xl font-semibold transition-all"
            :class="activeTab === 'TW' ? 'btn-gradient' : 'bg-white/10 hover:bg-white/20'"
          >
            🇹🇼 台股 ({{ watchlist.TW.length }})
          </button>
        </div>

        <!-- 股票列表 -->
        <div class="bg-dark-800/50 rounded-xl p-4">
          <!-- 美股 -->
          <div v-show="activeTab === 'US'">
            <div v-if="watchlist.US.length === 0" class="text-gray-500 text-center py-8">
              <span class="text-4xl mb-3 block">📊</span>
              尚無觀察股票，使用上方輸入框新增
            </div>
            <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              <div
                v-for="symbol in watchlist.US"
                :key="symbol"
                class="flex items-center justify-between bg-dark-700 rounded-lg px-4 py-3 group hover:bg-dark-600 transition-colors"
              >
                <span class="font-mono font-semibold">{{ symbol }}</span>
                <button
                  @click="confirmRemoveStock(symbol, 'US')"
                  class="text-rose-400 hover:text-rose-300 transition-colors opacity-50 group-hover:opacity-100"
                  title="移除"
                >
                  ✕
                </button>
              </div>
            </div>
          </div>

          <!-- 台股 -->
          <div v-show="activeTab === 'TW'">
            <div v-if="watchlist.TW.length === 0" class="text-gray-500 text-center py-8">
              <span class="text-4xl mb-3 block">📊</span>
              尚無觀察股票，使用上方輸入框新增
            </div>
            <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              <div
                v-for="symbol in watchlist.TW"
                :key="symbol"
                class="flex items-center justify-between bg-dark-700 rounded-lg px-4 py-3 group hover:bg-dark-600 transition-colors"
              >
                <span class="font-mono font-semibold">{{ symbol.replace('.TW', '') }}</span>
                <button
                  @click="confirmRemoveStock(symbol, 'TW')"
                  class="text-rose-400 hover:text-rose-300 transition-colors opacity-50 group-hover:opacity-100"
                  title="移除"
                >
                  ✕
                </button>
              </div>
            </div>
          </div>
        </div>
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

    <!-- 刪除確認彈窗 -->
    <div v-if="showDeleteConfirm" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showDeleteConfirm = false">
      <div class="glass rounded-2xl p-8 w-full max-w-sm mx-4 text-center">
        <span class="text-5xl mb-4 block">⚠️</span>
        <h3 class="text-xl font-bold mb-3">確認移除</h3>
        <p class="text-gray-400 mb-6">
          確定要從觀察清單中移除<br>
          <span class="font-semibold text-white">{{ pendingDeleteStock?.symbol }}</span> 嗎？
        </p>
        <div class="flex gap-4">
          <button 
            @click="showDeleteConfirm = false" 
            class="flex-1 px-6 py-3 rounded-xl bg-white/10 hover:bg-white/20 transition-colors"
          >
            取消
          </button>
          <button 
            @click="executeRemoveStock" 
            class="flex-1 px-6 py-3 rounded-xl bg-rose-500 hover:bg-rose-600 transition-colors font-semibold"
          >
            確認移除
          </button>
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
const addingStock = ref(false)

// 通知設定
const settings = ref({
  notification_email: '',
  thresholds_tw: '+3 +5 -5 -10',
  thresholds_us: '+5 +10 -5 -10',
  enabled: true
})

// 股票觀察清單
const watchlist = ref({ TW: [], US: [] })
const newStockSymbol = ref('')
const newStockMarket = ref('US')
const stockMessage = ref(null)
const activeTab = ref('US')

// 刪除確認
const showDeleteConfirm = ref(false)
const pendingDeleteStock = ref(null)

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
    const [settingsRes, watchlistRes] = await Promise.all([
      api.get('/notifications/settings'),
      api.get('/watchlist/')
    ])
    settings.value = settingsRes.data
    watchlist.value = watchlistRes.data
  } catch (err) {
    console.error('載入設定失敗', err)
  } finally {
    loading.value = false
  }
}

// ========== 股票管理 ==========
function validateStockSymbol(symbol, market) {
  symbol = symbol.toUpperCase().trim()
  if (market === 'US') {
    if (!/^[A-Z]{1,5}$/.test(symbol)) {
      return '美股代號必須是 1-5 個英文字母'
    }
  } else {
    const clean = symbol.replace('.TW', '')
    if (!/^\d{4,6}$/.test(clean)) {
      return '台股代號必須是 4-6 位數字'
    }
  }
  return null
}

async function addStock() {
  if (!newStockSymbol.value.trim()) {
    toast.error('請輸入股票代號')
    return
  }
  
  // 驗證格式
  const validationError = validateStockSymbol(newStockSymbol.value, newStockMarket.value)
  if (validationError) {
    toast.error(validationError)
    return
  }
  
  addingStock.value = true
  stockMessage.value = null
  
  try {
    const response = await api.post('/watchlist/add', {
      symbol: newStockSymbol.value.trim(),
      market: newStockMarket.value
    })
    toast.success(response.data.message)
    newStockSymbol.value = ''
    
    // 重新載入觀察清單
    const watchlistRes = await api.get('/watchlist/')
    watchlist.value = watchlistRes.data
  } catch (err) {
    toast.error(err.response?.data?.detail || '新增失敗')
  } finally {
    addingStock.value = false
  }
}

// 確認刪除
function confirmRemoveStock(symbol, market) {
  pendingDeleteStock.value = { symbol, market }
  showDeleteConfirm.value = true
}

// 執行刪除
async function executeRemoveStock() {
  if (!pendingDeleteStock.value) return
  
  const { symbol, market } = pendingDeleteStock.value
  showDeleteConfirm.value = false
  try {
    await api.post('/watchlist/remove', { symbol, market })
    
    // 重新載入觀察清單
    const watchlistRes = await api.get('/watchlist/')
    watchlist.value = watchlistRes.data
    
    toast.success(`已移除 ${symbol.replace('.TW', '')}`)
  } catch (err) {
    toast.error(err.response?.data?.detail || '移除失敗')
  } finally {
    pendingDeleteStock.value = null
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
