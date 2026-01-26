<template>
  <div class="space-y-8">
    <!-- 標題區 -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-3xl font-bold">即時監控</h2>
        <p class="text-gray-400 mt-1">{{ serverTime }}</p>
      </div>
      <div class="flex items-center gap-4">
        <!-- 電源模式指示器 -->
        <span class="px-3 py-1 rounded-full text-sm bg-white/10">
          {{ powerModeDisplay }}
        </span>
        
        <!-- 自動刷新倒數 -->
        <RefreshCountdown :seconds="countdown" :total="pollingInterval || 30" />
        
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
    </div>

    <!-- 搜尋列 -->
    <div class="max-w-md">
      <StockSearch :stocks="stocks" @select="openChart" />
    </div>

    <!-- 市場狀態卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- 骨架屏 -->
      <template v-if="loading && !stocks.TW?.length && !stocks.US?.length">
        <div v-for="i in 3" :key="i" class="glass rounded-2xl p-6 animate-pulse">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 bg-white/10 rounded-full"></div>
            <div class="space-y-2">
              <div class="h-4 w-20 bg-white/10 rounded"></div>
              <div class="h-3 w-16 bg-white/10 rounded"></div>
            </div>
          </div>
          <div class="h-4 w-24 bg-white/10 rounded"></div>
        </div>
      </template>

      <!-- 台股 -->
      <div v-else class="glass rounded-2xl p-6">
        <div class="flex items-center gap-3 mb-4">
          <span class="text-3xl">🇹🇼</span>
          <div>
            <h3 class="font-semibold text-lg">台股市場</h3>
            <p class="text-gray-400 text-sm">{{ marketStatus.TW?.local_time || '--:--' }}</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <span 
            class="w-3 h-3 rounded-full"
            :class="marketStatus.TW?.is_open ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'"
          ></span>
          <span :class="marketStatus.TW?.is_open ? 'text-emerald-400' : 'text-rose-400'">
            {{ marketStatus.TW?.status || '載入中...' }}
          </span>
        </div>
      </div>

      <!-- 美股 -->
      <div v-if="!loading || stocks.TW?.length || stocks.US?.length" class="glass rounded-2xl p-6">
        <div class="flex items-center gap-3 mb-4">
          <span class="text-3xl">🇺🇸</span>
          <div>
            <h3 class="font-semibold text-lg">美股市場</h3>
            <p class="text-gray-400 text-sm">{{ marketStatus.US?.local_time || '--:--' }}</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <span 
            class="w-3 h-3 rounded-full"
            :class="marketStatus.US?.is_open ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'"
          ></span>
          <span :class="marketStatus.US?.is_open ? 'text-emerald-400' : 'text-rose-400'">
            {{ marketStatus.US?.status || '載入中...' }}
          </span>
        </div>
      </div>

      <!-- 監控統計 -->
      <div v-if="!loading || stocks.TW?.length || stocks.US?.length" class="glass rounded-2xl p-6">
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

    <!-- 漲跌幅摘要卡片 -->
    <div v-if="allStocks.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- 今日最佳 -->
      <div 
        @click="openChart(bestStock)"
        class="glass rounded-2xl p-6 border-l-4 border-emerald-400 cursor-pointer hover:bg-white/5 transition-all"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-400 text-sm mb-1">📈 今日最佳表現 <span class="text-xs">(點擊查看走勢)</span></p>
            <p class="text-2xl font-bold">{{ bestStock?.symbol || '--' }}</p>
            <p class="text-gray-500 text-sm">{{ bestStock?.name || '' }}</p>
          </div>
          <div class="text-right">
            <p class="text-3xl font-bold text-emerald-400">
              {{ bestStock ? formatChange(bestStock.change_pct) : '--' }}
            </p>
            <p class="text-gray-400">${{ bestStock?.price?.toFixed(2) || '--' }}</p>
          </div>
        </div>
        <div class="mt-4 flex items-center gap-1">
          <div v-for="i in 7" :key="i" 
            class="flex-1 rounded-sm transition-all"
            :class="i <= 4 ? 'bg-emerald-600/30 h-2' : 'bg-emerald-400 h-' + (i-2)"
            :style="{ height: (i * 4) + 'px' }"
          ></div>
        </div>
      </div>

      <!-- 今日最差 -->
      <div 
        @click="openChart(worstStock)"
        class="glass rounded-2xl p-6 border-l-4 border-rose-400 cursor-pointer hover:bg-white/5 transition-all"
      >
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-400 text-sm mb-1">📉 今日最差表現 <span class="text-xs">(點擊查看走勢)</span></p>
            <p class="text-2xl font-bold">{{ worstStock?.symbol || '--' }}</p>
            <p class="text-gray-500 text-sm">{{ worstStock?.name || '' }}</p>
          </div>
          <div class="text-right">
            <p class="text-3xl font-bold text-rose-400">
              {{ worstStock ? formatChange(worstStock.change_pct) : '--' }}
            </p>
            <p class="text-gray-400">${{ worstStock?.price?.toFixed(2) || '--' }}</p>
          </div>
        </div>
        <div class="mt-4 flex items-center gap-1">
          <div v-for="i in 7" :key="i" 
            class="flex-1 rounded-sm transition-all"
            :class="i > 3 ? 'bg-rose-600/30 h-2' : 'bg-rose-400'"
            :style="{ height: ((8 - i) * 4) + 'px' }"
          ></div>
        </div>
      </div>
    </div>

    <!-- 走勢圖彈窗 -->
    <StockChart 
      :visible="chartVisible"
      :symbol="chartSymbol"
      :stockName="chartStockName"
      :market="chartMarket"
      @close="chartVisible = false"
    />

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
              <th @click="toggleSortUS('symbol')" class="px-6 py-4 text-left cursor-pointer hover:text-white transition-colors">
                代號{{ getSortArrow('symbol', sortKeyUS, sortOrderUS) }}
              </th>
              <th @click="toggleSortUS('name')" class="px-6 py-4 text-left cursor-pointer hover:text-white transition-colors">
                名稱{{ getSortArrow('name', sortKeyUS, sortOrderUS) }}
              </th>
              <th @click="toggleSortUS('avg_cost')" class="px-6 py-4 text-right cursor-pointer hover:text-orange-400 transition-colors text-orange-400">
                平均成本{{ getSortArrow('avg_cost', sortKeyUS, sortOrderUS) }}
              </th>
              <th @click="toggleSortUS('price')" class="px-6 py-4 text-right cursor-pointer hover:text-white transition-colors">
                現價{{ getSortArrow('price', sortKeyUS, sortOrderUS) }}
              </th>
              <th class="px-6 py-4 text-right">昨收</th>
              <th @click="toggleSortUS('change_pct')" class="px-6 py-4 text-right cursor-pointer hover:text-white transition-colors">
                漲跌幅{{ getSortArrow('change_pct', sortKeyUS, sortOrderUS) }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="stock in sortedUSStocks" 
              :key="stock.symbol"
              @click="openChart(stock)"
              class="border-b border-white/5 hover:bg-white/5 transition-colors cursor-pointer"
            >
              <td class="px-6 py-4 font-semibold">{{ stock.symbol }}</td>
              <td class="px-6 py-4 text-gray-300">{{ stock.name || '--' }}</td>
              <td class="px-6 py-4 text-right font-mono text-orange-400">
                {{ stock.avg_cost ? `$${stock.avg_cost.toFixed(2)}` : '--' }}
              </td>
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
              <th @click="toggleSortTW('symbol')" class="px-6 py-4 text-left cursor-pointer hover:text-white transition-colors">
                代號{{ getSortArrow('symbol', sortKeyTW, sortOrderTW) }}
              </th>
              <th @click="toggleSortTW('name')" class="px-6 py-4 text-left cursor-pointer hover:text-white transition-colors">
                名稱{{ getSortArrow('name', sortKeyTW, sortOrderTW) }}
              </th>
              <th @click="toggleSortTW('avg_cost')" class="px-6 py-4 text-right cursor-pointer hover:text-orange-400 transition-colors text-orange-400">
                平均成本{{ getSortArrow('avg_cost', sortKeyTW, sortOrderTW) }}
              </th>
              <th @click="toggleSortTW('price')" class="px-6 py-4 text-right cursor-pointer hover:text-white transition-colors">
                現價{{ getSortArrow('price', sortKeyTW, sortOrderTW) }}
              </th>
              <th class="px-6 py-4 text-right">昨收</th>
              <th @click="toggleSortTW('change_pct')" class="px-6 py-4 text-right cursor-pointer hover:text-white transition-colors">
                漲跌幅{{ getSortArrow('change_pct', sortKeyTW, sortOrderTW) }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="stock in sortedTWStocks" 
              :key="stock.symbol"
              @click="openChart(stock)"
              class="border-b border-white/5 hover:bg-white/5 transition-colors cursor-pointer"
            >
              <td class="px-6 py-4 font-semibold">{{ stock.symbol.replace('.TW', '') }}</td>
              <td class="px-6 py-4 text-gray-300">{{ stock.name || '--' }}</td>
              <td class="px-6 py-4 text-right font-mono text-orange-400">
                {{ stock.avg_cost ? `NT$${stock.avg_cost.toFixed(2)}` : '--' }}
              </td>
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { getMarketStatus, getStocks } from '../api'
import StockChart from '../components/StockChart.vue'
import RefreshCountdown from '../components/RefreshCountdown.vue'
import StockSearch from '../components/StockSearch.vue'

const loading = ref(false)
const serverTime = ref('')
const marketStatus = ref({})
const stocks = ref({ TW: [], US: [] })

// 電源模式相關
const powerMode = ref('normal')  // normal, low, sleep
const pollingInterval = ref(30)  // 從 API 取得的輪詢間隔

// 倒數計時相關
const countdown = ref(30)
let countdownTimer = null

// 電源模式圖示
const powerModeDisplay = computed(() => {
  switch (powerMode.value) {
    case 'normal': return '🟢 正常模式'
    case 'low': return '🟡 省電模式'
    case 'sleep': return '🔴 休眠模式'
    default: return '❓ 未知'
  }
})

// 排序相關
const sortKeyUS = ref('')
const sortOrderUS = ref('asc')  // 'asc' 或 'desc'
const sortKeyTW = ref('')
const sortOrderTW = ref('asc')

// 排序函數
function sortStocks(stocks, key, order) {
  if (!key) return stocks
  
  return [...stocks].sort((a, b) => {
    let valA = a[key]
    let valB = b[key]
    
    // 處理 null/undefined
    if (valA == null) valA = order === 'asc' ? Infinity : -Infinity
    if (valB == null) valB = order === 'asc' ? Infinity : -Infinity
    
    // 字串比較
    if (typeof valA === 'string') {
      valA = valA.toLowerCase()
      valB = valB.toLowerCase()
    }
    
    if (valA < valB) return order === 'asc' ? -1 : 1
    if (valA > valB) return order === 'asc' ? 1 : -1
    return 0
  })
}

// 排序後的美股
const sortedUSStocks = computed(() => {
  return sortStocks(stocks.value.US || [], sortKeyUS.value, sortOrderUS.value)
})

// 排序後的台股
const sortedTWStocks = computed(() => {
  return sortStocks(stocks.value.TW || [], sortKeyTW.value, sortOrderTW.value)
})

// 切換排序
function toggleSortUS(key) {
  if (sortKeyUS.value === key) {
    sortOrderUS.value = sortOrderUS.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKeyUS.value = key
    sortOrderUS.value = 'asc'
  }
}

function toggleSortTW(key) {
  if (sortKeyTW.value === key) {
    sortOrderTW.value = sortOrderTW.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKeyTW.value = key
    sortOrderTW.value = 'asc'
  }
}

// 排序箭頭
function getSortArrow(currentKey, sortKey, sortOrder) {
  if (currentKey !== sortKey) return ''
  return sortOrder === 'asc' ? ' ▲' : ' ▼'
}

// 走勢圖相關
const chartVisible = ref(false)
const chartSymbol = ref('')
const chartStockName = ref('')
const chartMarket = ref('US')

function openChart(stock) {
  if (!stock) return
  chartSymbol.value = stock.symbol.replace('.TW', '')
  chartStockName.value = stock.name || ''
  chartMarket.value = stock.symbol.includes('.TW') ? 'TW' : 'US'
  chartVisible.value = true
}

// 計算所有股票（合併台股美股）
const allStocks = computed(() => {
  const tw = stocks.value.TW || []
  const us = stocks.value.US || []
  return [...tw, ...us].filter(s => s.change_pct !== null && s.change_pct !== undefined)
})

// 今日最佳表現
const bestStock = computed(() => {
  if (allStocks.value.length === 0) return null
  return allStocks.value.reduce((best, current) => 
    (current.change_pct > best.change_pct) ? current : best
  )
})

// 今日最差表現
const worstStock = computed(() => {
  if (allStocks.value.length === 0) return null
  return allStocks.value.reduce((worst, current) => 
    (current.change_pct < worst.change_pct) ? current : worst
  )
})

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
    
    // 更新電源模式
    if (status.power_mode) {
      powerMode.value = status.power_mode
      pollingInterval.value = status.polling_interval || 30
      
      // 根據模式調整倒數計時
      if (status.polling_interval > 0) {
        countdown.value = status.polling_interval
      }
    }
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
  // 啟動倒數計時（動態間隔）
  countdownTimer = setInterval(() => {
    // 休眠模式不自動刷新
    if (powerMode.value === 'sleep' || pollingInterval.value === 0) {
      return
    }
    
    countdown.value--
    if (countdown.value <= 0) {
      countdown.value = pollingInterval.value
      fetchData()
    }
  }, 1000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  if (countdownTimer) clearInterval(countdownTimer)
})
</script>
