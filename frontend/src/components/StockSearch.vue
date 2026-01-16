<template>
  <div class="relative">
    <!-- 搜尋輸入框 -->
    <div class="relative">
      <span class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">🔍</span>
      <input
        v-model="searchQuery"
        type="text"
        placeholder="搜尋股票代號..."
        class="w-full bg-dark-800 border border-white/10 rounded-xl pl-12 pr-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
        @focus="showDropdown = true"
        @blur="handleBlur"
        @input="filterStocks"
      />
      <button 
        v-if="searchQuery"
        @click="clearSearch"
        class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
      >
        ✕
      </button>
    </div>

    <!-- 下拉選單 -->
    <div 
      v-if="showDropdown && filteredStocks.length > 0"
      class="absolute top-full left-0 right-0 mt-2 bg-dark-800 border border-white/10 rounded-xl shadow-xl max-h-64 overflow-y-auto z-50"
    >
      <div
        v-for="stock in filteredStocks"
        :key="stock.symbol"
        @mousedown="selectStock(stock)"
        class="px-4 py-3 flex items-center justify-between hover:bg-white/5 cursor-pointer transition-colors"
      >
        <div class="flex items-center gap-3">
          <span class="text-lg">{{ stock.symbol.includes('.TW') ? '🇹🇼' : '🇺🇸' }}</span>
          <div>
            <p class="font-semibold">{{ stock.symbol.replace('.TW', '') }}</p>
            <p v-if="stock.name" class="text-gray-400 text-sm">{{ stock.name }}</p>
          </div>
        </div>
        <div class="text-right">
          <p class="font-mono">${{ stock.price?.toFixed(2) || '--' }}</p>
          <p 
            class="text-sm"
            :class="stock.change_pct >= 0 ? 'text-emerald-400' : 'text-rose-400'"
          >
            {{ stock.change_pct >= 0 ? '+' : '' }}{{ stock.change_pct?.toFixed(2) || 0 }}%
          </p>
        </div>
      </div>
    </div>

    <!-- 無結果 -->
    <div 
      v-if="showDropdown && searchQuery && filteredStocks.length === 0"
      class="absolute top-full left-0 right-0 mt-2 bg-dark-800 border border-white/10 rounded-xl shadow-xl p-4 text-center text-gray-400 z-50"
    >
      找不到「{{ searchQuery }}」
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  stocks: {
    type: Object,
    default: () => ({ TW: [], US: [] })
  }
})

const emit = defineEmits(['select'])

const searchQuery = ref('')
const showDropdown = ref(false)

// 合併所有股票
const allStocks = computed(() => {
  const tw = props.stocks.TW || []
  const us = props.stocks.US || []
  return [...tw, ...us]
})

// 過濾股票
const filteredStocks = computed(() => {
  if (!searchQuery.value) return allStocks.value.slice(0, 10)
  
  const query = searchQuery.value.toUpperCase()
  return allStocks.value.filter(stock => 
    stock.symbol.toUpperCase().includes(query) ||
    (stock.name && stock.name.includes(query))
  ).slice(0, 10)
})

function filterStocks() {
  showDropdown.value = true
}

function selectStock(stock) {
  emit('select', stock)
  searchQuery.value = ''
  showDropdown.value = false
}

function clearSearch() {
  searchQuery.value = ''
  showDropdown.value = false
}

function handleBlur() {
  // 延遲關閉，讓點擊事件先觸發
  setTimeout(() => {
    showDropdown.value = false
  }, 200)
}
</script>
