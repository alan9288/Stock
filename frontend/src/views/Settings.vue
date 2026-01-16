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

        <!-- 股票列表 -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- 美股 -->
          <div class="bg-dark-800/50 rounded-xl p-4">
            <h3 class="font-semibold text-lg mb-4 flex items-center gap-2">
              🇺🇸 美股觀察
              <span class="text-sm text-gray-400">({{ watchlist.US.length }} 支)</span>
            </h3>
            <div v-if="watchlist.US.length === 0" class="text-gray-500 text-center py-4">
              尚無觀察股票
            </div>
            <div v-else class="space-y-2">
              <div
                v-for="symbol in watchlist.US"
                :key="symbol"
                class="flex items-center justify-between bg-dark-700 rounded-lg px-4 py-2"
              >
                <span class="font-mono font-semibold">{{ symbol }}</span>
                <button
                  @click="removeStock(symbol, 'US')"
                  class="text-rose-400 hover:text-rose-300 transition-colors"
                  title="移除"
                >
                  ✕
                </button>
              </div>
            </div>
          </div>

          <!-- 台股 -->
          <div class="bg-dark-800/50 rounded-xl p-4">
            <h3 class="font-semibold text-lg mb-4 flex items-center gap-2">
              🇹🇼 台股觀察
              <span class="text-sm text-gray-400">({{ watchlist.TW.length }} 支)</span>
            </h3>
            <div v-if="watchlist.TW.length === 0" class="text-gray-500 text-center py-4">
              尚無觀察股票
            </div>
            <div v-else class="space-y-2">
              <div
                v-for="symbol in watchlist.TW"
                :key="symbol"
                class="flex items-center justify-between bg-dark-700 rounded-lg px-4 py-2"
              >
                <span class="font-mono font-semibold">{{ symbol.replace('.TW', '') }}</span>
                <button
                  @click="removeStock(symbol, 'TW')"
                  class="text-rose-400 hover:text-rose-300 transition-colors"
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
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

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

const saveResult = ref(null)
const testEmailResult = ref(null)

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
async function addStock() {
  if (!newStockSymbol.value.trim()) return
  
  addingStock.value = true
  stockMessage.value = null
  
  try {
    const response = await api.post('/watchlist/add', {
      symbol: newStockSymbol.value.trim(),
      market: newStockMarket.value
    })
    stockMessage.value = { success: true, text: response.data.message }
    newStockSymbol.value = ''
    
    // 重新載入觀察清單
    const watchlistRes = await api.get('/watchlist/')
    watchlist.value = watchlistRes.data
  } catch (err) {
    stockMessage.value = { success: false, text: err.response?.data?.detail || '新增失敗' }
  } finally {
    addingStock.value = false
    setTimeout(() => { stockMessage.value = null }, 3000)
  }
}

async function removeStock(symbol, market) {
  try {
    await api.post('/watchlist/remove', { symbol, market })
    
    // 重新載入觀察清單
    const watchlistRes = await api.get('/watchlist/')
    watchlist.value = watchlistRes.data
    
    stockMessage.value = { success: true, text: `已移除 ${symbol}` }
    setTimeout(() => { stockMessage.value = null }, 2000)
  } catch (err) {
    stockMessage.value = { success: false, text: err.response?.data?.detail || '移除失敗' }
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
    saveResult.value = { success: true, message: '✅ 設定已儲存' }
  } catch (err) {
    saveResult.value = { success: false, message: '❌ 儲存失敗: ' + (err.response?.data?.detail || err.message) }
  } finally {
    saving.value = false
    setTimeout(() => { saveResult.value = null }, 3000)
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
