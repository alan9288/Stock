<template>
  <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center">
    <!-- 背景遮罩 -->
    <div class="absolute inset-0 bg-black/70 backdrop-blur-sm" @click="close"></div>
    
    <!-- 彈窗內容 -->
    <div class="relative glass rounded-2xl w-[90%] max-w-4xl p-6">
      <!-- 標題 -->
      <div class="flex items-center justify-between mb-4">
        <div>
          <h3 class="text-xl font-bold">{{ symbol }} 走勢圖</h3>
          <p class="text-gray-400 text-sm">{{ stockName || '' }}</p>
        </div>
        <div class="flex items-center gap-4">
          <!-- 時間區間選擇 -->
          <div class="flex gap-2">
            <button 
              v-for="p in periods" 
              :key="p.value"
              @click="changePeriod(p.value)"
              class="px-3 py-1 rounded-lg text-sm transition-all"
              :class="period === p.value ? 'bg-purple-500 text-white' : 'bg-dark-700 text-gray-400 hover:bg-dark-600'"
            >
              {{ p.label }}
            </button>
          </div>
          <!-- 關閉按鈕 -->
          <button @click="close" class="text-gray-400 hover:text-white text-2xl">
            ✕
          </button>
        </div>
      </div>
      
      <!-- 圖表容器 -->
      <div class="bg-dark-800 rounded-xl p-2">
        <div ref="chartContainer" class="w-full h-[400px]"></div>
      </div>
      
      <!-- 載入中 -->
      <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-black/50 rounded-2xl">
        <div class="text-xl animate-pulse">📊 載入中...</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onUnmounted, nextTick } from 'vue'
import { createChart, CandlestickSeries } from 'lightweight-charts'
import { getStockHistory } from '../api'

const props = defineProps({
  visible: Boolean,
  symbol: String,
  stockName: String,
  market: { type: String, default: 'US' }
})

const emit = defineEmits(['close'])

const chartContainer = ref(null)
const loading = ref(false)
const period = ref('5d')

let chart = null
let candleSeries = null

const periods = [
  { label: '日內', value: '1d' },
  { label: '5日', value: '5d' },
  { label: '1月', value: '1mo' },
  { label: '3月', value: '3mo' }
]

function close() {
  emit('close')
}

async function loadChart() {
  if (!props.symbol) return
  
  loading.value = true
  
  try {
    const result = await getStockHistory(props.symbol, props.market, period.value)
    console.log('圖表資料:', result) // 調試用
    
    if (result.data && result.data.length > 0) {
      await nextTick()
      initChart(result.data)
    } else {
      console.log('無資料或資料為空')
    }
  } catch (error) {
    console.error('載入圖表失敗:', error)
  } finally {
    loading.value = false
  }
}

function initChart(data) {
  // 清除舊圖表
  if (chart) {
    chart.remove()
    chart = null
  }
  
  if (!chartContainer.value) {
    console.log('chartContainer 不存在')
    return
  }
  
  console.log('建立圖表，資料筆數:', data.length)
  
  // 建立新圖表
  chart = createChart(chartContainer.value, {
    layout: {
      background: { type: 'solid', color: 'transparent' },
      textColor: '#a1a1aa'
    },
    grid: {
      vertLines: { color: 'rgba(255, 255, 255, 0.1)' },
      horzLines: { color: 'rgba(255, 255, 255, 0.1)' }
    },
    width: chartContainer.value.clientWidth,
    height: 400,
    timeScale: {
      timeVisible: true,
      secondsVisible: false
    }
  })
  
  // 新增 K 線 - v5 API (正確語法)
  candleSeries = chart.addSeries(CandlestickSeries, {
    upColor: '#22c55e',
    downColor: '#ef4444',
    borderUpColor: '#22c55e',
    borderDownColor: '#ef4444',
    wickUpColor: '#22c55e',
    wickDownColor: '#ef4444'
  })
  
  candleSeries.setData(data)
  chart.timeScale().fitContent()
}

function changePeriod(newPeriod) {
  period.value = newPeriod
  loadChart()
}

// 監聽彈窗開啟
watch(() => props.visible, (val) => {
  if (val) {
    period.value = '5d'  // 預設顯示 5 日
    loadChart()
  } else if (chart) {
    chart.remove()
    chart = null
  }
})

onUnmounted(() => {
  if (chart) {
    chart.remove()
  }
})
</script>
