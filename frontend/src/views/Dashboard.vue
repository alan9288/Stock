<template>
  <div class="space-y-8">
    <!-- 標題區 -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-3xl font-bold">即時監控</h2>
        <p class="text-gray-400 mt-1">{{ serverTime }}</p>
      </div>
      <button 
        @click="fetchData" 
        :disabled="loading"
        class="btn-gradient px-6 py-3 rounded-xl font-semibold flex items-center gap-2"
      >
        <span v-if="loading" class="animate-spin">⟳</span>
        <span v-else>🔄</span>
        刷新數據
      </button>
    </div>

    <!-- 市場狀態卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- 台股 -->
      <div class="glass rounded-2xl p-6">
        <div class="flex items-center gap-3 mb-4">
          <span class="text-3xl">🇹🇼</span>
          <div>
            <h3 class="font-semibold text-lg">台股市場</h3>
            <p class="text-gray-400 text-sm">{{ marketStatus.TW?.local_time || '--:--' }}</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <span 
            class="w-3 h-3 rounded-full animate-pulse"
            :class="marketStatus.TW?.is_open ? 'bg-emerald-400' : 'bg-rose-400'"
          ></span>
          <span :class="marketStatus.TW?.is_open ? 'text-emerald-400' : 'text-rose-400'">
            {{ marketStatus.TW?.status || '載入中...' }}
          </span>
        </div>
      </div>

      <!-- 美股 -->
      <div class="glass rounded-2xl p-6">
        <div class="flex items-center gap-3 mb-4">
          <span class="text-3xl">🇺🇸</span>
          <div>
            <h3 class="font-semibold text-lg">美股市場</h3>
            <p class="text-gray-400 text-sm">{{ marketStatus.US?.local_time || '--:--' }}</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <span 
            class="w-3 h-3 rounded-full animate-pulse"
            :class="marketStatus.US?.is_open ? 'bg-emerald-400' : 'bg-rose-400'"
          ></span>
          <span :class="marketStatus.US?.is_open ? 'text-emerald-400' : 'text-rose-400'">
            {{ marketStatus.US?.status || '載入中...' }}
          </span>
        </div>
      </div>

      <!-- 監控統計 -->
      <div class="glass rounded-2xl p-6">
        <div class="flex items-center gap-3 mb-4">
          <span class="text-3xl">📈</span>
          <div>
            <h3 class="font-semibold text-lg">監控統計</h3>
            <p class="text-gray-400 text-sm">即時追蹤</p>
          </div>
        </div>
        <div class="flex gap-4 text-center">
          <div>
            <p class="text-2xl font-bold text-cyan-400">{{ stocks.TW?.length || 0 }}</p>
            <p class="text-gray-400 text-sm">台股</p>
          </div>
          <div>
            <p class="text-2xl font-bold text-purple-400">{{ stocks.US?.length || 0 }}</p>
            <p class="text-gray-400 text-sm">美股</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 美股表格 -->
    <div v-if="stocks.US?.length" class="glass rounded-2xl overflow-hidden">
      <div class="px-6 py-4 border-b border-white/10">
        <h3 class="font-semibold text-lg flex items-center gap-2">
          🇺🇸 美股即時報價
        </h3>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="text-gray-400 text-sm border-b border-white/10">
              <th class="px-6 py-4 text-left">代號</th>
              <th class="px-6 py-4 text-left">群組</th>
              <th class="px-6 py-4 text-right">現價</th>
              <th class="px-6 py-4 text-right">昨收</th>
              <th class="px-6 py-4 text-right">漲跌幅</th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="stock in stocks.US" 
              :key="stock.symbol"
              class="border-b border-white/5 hover:bg-white/5 transition-colors"
            >
              <td class="px-6 py-4 font-semibold">{{ stock.symbol }}</td>
              <td class="px-6 py-4 text-gray-400">{{ stock.group }}</td>
              <td class="px-6 py-4 text-right font-mono">
                {{ stock.price ? `$${stock.price.toFixed(2)}` : '--' }}
              </td>
              <td class="px-6 py-4 text-right font-mono text-gray-400">
                {{ stock.prev_close ? `$${stock.prev_close.toFixed(2)}` : '--' }}
              </td>
              <td class="px-6 py-4 text-right font-semibold">
                <span :class="getChangeClass(stock.change_pct)">
                  {{ formatChange(stock.change_pct) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 台股表格 -->
    <div v-if="stocks.TW?.length" class="glass rounded-2xl overflow-hidden">
      <div class="px-6 py-4 border-b border-white/10">
        <h3 class="font-semibold text-lg flex items-center gap-2">
          🇹🇼 台股即時報價
        </h3>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="text-gray-400 text-sm border-b border-white/10">
              <th class="px-6 py-4 text-left">代號</th>
              <th class="px-6 py-4 text-left">群組</th>
              <th class="px-6 py-4 text-right">現價</th>
              <th class="px-6 py-4 text-right">昨收</th>
              <th class="px-6 py-4 text-right">漲跌幅</th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="stock in stocks.TW" 
              :key="stock.symbol"
              class="border-b border-white/5 hover:bg-white/5 transition-colors"
            >
              <td class="px-6 py-4 font-semibold">{{ stock.symbol.replace('.TW', '') }}</td>
              <td class="px-6 py-4 text-gray-400">{{ stock.group }}</td>
              <td class="px-6 py-4 text-right font-mono">
                {{ stock.price ? `$${stock.price.toFixed(2)}` : '--' }}
              </td>
              <td class="px-6 py-4 text-right font-mono text-gray-400">
                {{ stock.prev_close ? `$${stock.prev_close.toFixed(2)}` : '--' }}
              </td>
              <td class="px-6 py-4 text-right font-semibold">
                <!-- 台股紅漲綠跌 -->
                <span :class="getChangeClassTW(stock.change_pct)">
                  {{ formatChange(stock.change_pct) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 空狀態 -->
    <div v-if="!stocks.TW?.length && !stocks.US?.length && !loading" class="glass rounded-2xl p-12 text-center">
      <span class="text-6xl mb-4 block">📭</span>
      <h3 class="text-xl font-semibold mb-2">尚無監控股票</h3>
      <p class="text-gray-400 mb-6">請前往設定頁面新增投資組合</p>
      <router-link to="/settings" class="btn-gradient px-6 py-3 rounded-xl inline-block">
        前往設定
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { getMarketStatus, getStocks } from '../api'

const loading = ref(false)
const serverTime = ref('')
const marketStatus = ref({})
const stocks = ref({ TW: [], US: [] })

let refreshTimer = null

async function fetchData() {
  loading.value = true
  try {
    const [status, stockData] = await Promise.all([
      getMarketStatus(),
      getStocks()
    ])
    marketStatus.value = status
    serverTime.value = status.server_time
    stocks.value = stockData
  } catch (error) {
    console.error('載入失敗:', error)
  } finally {
    loading.value = false
  }
}

function formatChange(pct) {
  if (pct === null || pct === undefined) return '--'
  const sign = pct >= 0 ? '+' : ''
  return `${sign}${pct.toFixed(2)}%`
}

// 美股：綠漲紅跌
function getChangeClass(pct) {
  if (pct === null || pct === undefined) return 'text-gray-400'
  return pct >= 0 ? 'text-emerald-400' : 'text-rose-400'
}

// 台股：紅漲綠跌
function getChangeClassTW(pct) {
  if (pct === null || pct === undefined) return 'text-gray-400'
  return pct >= 0 ? 'text-rose-400' : 'text-emerald-400'
}

onMounted(() => {
  fetchData()
  // 每 30 秒自動刷新
  refreshTimer = setInterval(fetchData, 30000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>
