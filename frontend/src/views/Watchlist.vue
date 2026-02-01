<template>
  <div class="max-w-4xl mx-auto space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-3xl font-bold">📋 觀察清單</h1>
      <span class="text-gray-400 text-sm">追蹤感興趣的股票</span>
    </div>

    <!-- 載入中 -->
    <div v-if="loading" class="glass rounded-xl p-8 text-center">
      <span class="animate-spin text-3xl">⟳</span>
      <p class="mt-4 text-gray-400">載入中...</p>
    </div>

    <div v-else class="space-y-6">
      <!-- 新增股票 -->
      <div class="glass rounded-xl p-4">
        <div class="flex gap-3">
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
      </div>

      <!-- Tab 切換 -->
      <div class="flex gap-2">
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
      <div class="glass rounded-xl p-4">
        <!-- 美股 -->
        <div v-show="activeTab === 'US'">
          <div v-if="watchlist.US.length === 0" class="text-gray-500 text-center py-12">
            <span class="text-5xl mb-4 block">📊</span>
            <p class="text-lg">尚無美股觀察清單</p>
            <p class="text-sm mt-2">使用上方輸入框新增股票</p>
          </div>
          <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            <div
              v-for="symbol in watchlist.US"
              :key="symbol"
              class="flex items-center justify-between bg-dark-700 rounded-lg px-4 py-3 group hover:bg-dark-600 transition-colors"
            >
              <div>
                <span class="font-mono font-semibold">{{ symbol }}</span>
              </div>
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
          <div v-if="watchlist.TW.length === 0" class="text-gray-500 text-center py-12">
            <span class="text-5xl mb-4 block">📊</span>
            <p class="text-lg">尚無台股觀察清單</p>
            <p class="text-sm mt-2">使用上方輸入框新增股票</p>
          </div>
          <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            <div
              v-for="symbol in watchlist.TW"
              :key="symbol"
              class="flex items-center justify-between bg-dark-700 rounded-lg px-4 py-3 group hover:bg-dark-600 transition-colors"
            >
              <div>
                <span class="font-mono font-semibold">{{ symbol.replace('.TW', '') }}</span>
              </div>
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

    <!-- 刪除確認彈窗 -->
    <Transition name="fade">
      <div v-if="showDeleteConfirm" class="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
        <div class="glass rounded-2xl p-6 max-w-sm mx-4">
          <h3 class="text-xl font-bold mb-4">確認移除</h3>
          <p class="text-gray-300 mb-6">
            確定要從觀察清單移除 
            <span class="text-cyan-400 font-semibold">{{ pendingDeleteStock?.symbol?.replace('.TW', '') }}</span> 嗎？
          </p>
          <div class="flex gap-3">
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
    </Transition>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'
import { useToast } from '../composables/useToast'

const toast = useToast()

const loading = ref(true)
const addingStock = ref(false)

// 股票觀察清單
const watchlist = ref({ TW: [], US: [] })
const newStockSymbol = ref('')
const newStockMarket = ref('US')
const activeTab = ref('US')

// 刪除確認
const showDeleteConfirm = ref(false)
const pendingDeleteStock = ref(null)

// 載入資料
async function loadData() {
  loading.value = true
  try {
    const response = await api.get('/watchlist/')
    watchlist.value = response.data
  } catch (err) {
    console.error('載入觀察清單失敗', err)
    toast.error('載入失敗')
  } finally {
    loading.value = false
  }
}

// 驗證股票代號
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

// 新增股票
async function addStock() {
  if (!newStockSymbol.value.trim()) {
    toast.error('請輸入股票代號')
    return
  }
  
  const validationError = validateStockSymbol(newStockSymbol.value, newStockMarket.value)
  if (validationError) {
    toast.error(validationError)
    return
  }
  
  addingStock.value = true
  
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

onMounted(() => {
  loadData()
})
</script>
