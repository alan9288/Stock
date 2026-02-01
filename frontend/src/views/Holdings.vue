<template>
  <div class="space-y-8">
    <!-- 標題區 -->
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-3xl font-bold">💼 我的持股</h2>
        <p class="text-gray-400 mt-1">追蹤持股成本與損益</p>
      </div>
      <button 
        @click="showAddModal = true"
        class="btn-gradient px-6 py-3 rounded-xl font-semibold flex items-center gap-2"
      >
        <span>➕</span>
        新增持股
      </button>
    </div>

    <!-- 總覽卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <!-- 🇺🇸 美股 -->
      <div class="glass rounded-xl p-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-lg">🇺🇸</span>
            <span class="text-gray-400 text-sm">美股投資</span>
          </div>
          <span class="text-lg font-bold" :class="usReturnPct >= 0 ? 'text-green-400' : 'text-red-400'">
            {{ usReturnPct >= 0 ? '+' : '' }}{{ usReturnPct.toFixed(2) }}%
          </span>
        </div>
        <p class="text-xl font-bold mt-1">${{ usTotalCost.toLocaleString() }}</p>
      </div>
      
      <!-- 🇹🇼 台股 -->
      <div class="glass rounded-xl p-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-lg">🇹🇼</span>
            <span class="text-gray-400 text-sm">台股投資</span>
          </div>
          <span class="text-lg font-bold" :class="twReturnPct >= 0 ? 'text-green-400' : 'text-red-400'">
            {{ twReturnPct >= 0 ? '+' : '' }}{{ twReturnPct.toFixed(2) }}%
          </span>
        </div>
        <p class="text-xl font-bold mt-1">NT${{ twTotalCost.toLocaleString() }}</p>
      </div>
      
      <!-- 📊 總計 -->
      <div class="glass rounded-xl p-4 bg-gradient-to-br from-purple-500/20 to-cyan-500/20 border border-cyan-500/30">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-lg">📊</span>
            <span class="text-cyan-400 font-semibold text-sm">投資總覽</span>
          </div>
          <span class="text-lg font-bold" :class="totalReturnPct >= 0 ? 'text-cyan-400' : 'text-red-400'">
            {{ totalReturnPct >= 0 ? '+' : '' }}{{ totalReturnPct.toFixed(2) }}%
          </span>
        </div>
        <div class="flex gap-4 mt-1 text-sm">
          <span class="font-mono">${{ usTotalCost.toLocaleString() }}</span>
          <span class="text-gray-500">+</span>
          <span class="font-mono">NT${{ twTotalCost.toLocaleString() }}</span>
        </div>
      </div>
    </div>

    <!-- 🇺🇸 美股持股 -->
    <div class="glass rounded-2xl overflow-hidden" v-if="usHoldings.length">
      <div class="px-6 py-3 border-b border-white/10 flex items-center gap-2">
        <span class="text-xl">🇺🇸</span>
        <h3 class="font-semibold">美股持股</h3>
        <span class="text-gray-400 text-sm">({{ usHoldings.length }} 檔)</span>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="text-gray-400 text-sm border-b border-white/10">
              <th @click="toggleSort('symbol', 'US')" class="px-4 py-3 text-left cursor-pointer hover:text-white transition-colors">股票 {{ getSortArrow('symbol', 'US') }}</th>
              <th @click="toggleSort('total_quantity', 'US')" class="px-4 py-3 text-right cursor-pointer hover:text-white transition-colors">股數 {{ getSortArrow('total_quantity', 'US') }}</th>
              <th @click="toggleSort('avg_cost', 'US')" class="px-4 py-3 text-right cursor-pointer hover:text-white transition-colors">成本 {{ getSortArrow('avg_cost', 'US') }}</th>
              <th @click="toggleSort('current_price', 'US')" class="px-4 py-3 text-right cursor-pointer hover:text-white transition-colors">現價 {{ getSortArrow('current_price', 'US') }}</th>
              <th @click="toggleSort('return_pct', 'US')" class="px-4 py-3 text-right cursor-pointer hover:text-white transition-colors">報酬 {{ getSortArrow('return_pct', 'US') }}</th>
              <th class="px-4 py-3 text-left">智慧分析</th>
              <th class="px-4 py-3 text-center">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="holding in sortedUSHoldings" 
              :key="holding.id"
              class="border-b border-white/5 hover:bg-white/5 transition-colors"
            >
              <!-- 股票：代號+名稱合併 -->
              <td class="px-4 py-3">
                <div class="font-semibold">{{ holding.symbol }}</div>
                <div class="text-xs text-gray-500">{{ holding.name || '--' }}</div>
              </td>
              <td class="px-4 py-3 text-right font-mono">{{ formatQuantity(holding.total_quantity) }}</td>
              <td class="px-4 py-3 text-right font-mono text-sm">{{ formatCurrency(holding.avg_cost, 'US') }}</td>
              <td class="px-4 py-3 text-right font-mono text-sm">
                {{ holding.current_price ? formatCurrency(holding.current_price, 'US') : '--' }}
              </td>
              <td class="px-4 py-3 text-right font-semibold">
                <span :class="holding.return_pct >= 0 ? 'text-green-400' : 'text-red-400'">
                  {{ holding.return_pct >= 0 ? '+' : '' }}{{ holding.return_pct?.toFixed(2) }}%
                </span>
              </td>
              <!-- 智慧分析：合併多個欄位 -->
              <td class="px-4 py-3">
                <div v-if="holding.buy_signal" class="space-y-1">
                  <div class="flex items-center gap-2">
                    <span class="px-2 py-0.5 rounded text-xs font-semibold"
                          :class="getBuyScoreClass(holding.buy_signal.buy_score)">
                      {{ holding.buy_signal.buy_score }}分
                    </span>
                    <span v-if="holding.buy_signal.suggested_amount > 0" class="text-cyan-400 text-xs">
                      +{{ formatCurrency(holding.buy_signal.suggested_amount, 'US') }}
                    </span>
                  </div>
                  <div class="text-xs text-gray-500">
                    {{ holding.buy_signal.buy_status }}
                    <span v-if="holding.buy_signal.earnings_date" :class="getEarningsDateClass(holding.buy_signal.earnings_date)">
                      · {{ formatEarningsDate(holding.buy_signal.earnings_date) }}
                    </span>
                  </div>
                </div>
                <span v-else class="text-gray-500 text-sm">--</span>
              </td>
              <td class="px-4 py-3 text-center">
                <div class="flex items-center justify-center gap-1">
                  <button @click="openAddTransaction(holding)" class="p-1.5 hover:bg-white/10 rounded-lg" title="補倉">➕</button>
                  <button @click="viewTransactions(holding)" class="p-1.5 hover:bg-white/10 rounded-lg" title="查看記錄">📋</button>
                  <button @click="confirmDelete(holding)" class="p-1.5 hover:bg-red-500/20 rounded-lg text-red-400" title="刪除">🗑️</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 🇹🇼 台股持股 -->
    <div class="glass rounded-2xl overflow-hidden" v-if="twHoldings.length">
      <div class="px-6 py-3 border-b border-white/10 flex items-center gap-2">
        <span class="text-xl">🇹🇼</span>
        <h3 class="font-semibold">台股持股</h3>
        <span class="text-gray-400 text-sm">({{ twHoldings.length }} 檔)</span>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="text-gray-400 text-sm border-b border-white/10">
              <th @click="toggleSort('symbol', 'TW')" class="px-4 py-3 text-left cursor-pointer hover:text-white transition-colors">股票 {{ getSortArrow('symbol', 'TW') }}</th>
              <th @click="toggleSort('total_quantity', 'TW')" class="px-4 py-3 text-right cursor-pointer hover:text-white transition-colors">股數 {{ getSortArrow('total_quantity', 'TW') }}</th>
              <th @click="toggleSort('avg_cost', 'TW')" class="px-4 py-3 text-right cursor-pointer hover:text-white transition-colors">成本 {{ getSortArrow('avg_cost', 'TW') }}</th>
              <th @click="toggleSort('current_price', 'TW')" class="px-4 py-3 text-right cursor-pointer hover:text-white transition-colors">現價 {{ getSortArrow('current_price', 'TW') }}</th>
              <th @click="toggleSort('return_pct', 'TW')" class="px-4 py-3 text-right cursor-pointer hover:text-white transition-colors">報酬 {{ getSortArrow('return_pct', 'TW') }}</th>
              <th class="px-4 py-3 text-left">智慧分析</th>
              <th class="px-4 py-3 text-center">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="holding in sortedTWHoldings" 
              :key="holding.id"
              class="border-b border-white/5 hover:bg-white/5 transition-colors"
            >
              <!-- 股票：代號+名稱合併 -->
              <td class="px-4 py-3">
                <div class="font-semibold">{{ holding.symbol.replace('.TW', '') }}</div>
                <div class="text-xs text-gray-500">{{ holding.name || '--' }}</div>
              </td>
              <td class="px-4 py-3 text-right font-mono">{{ formatQuantity(holding.total_quantity) }}</td>
              <td class="px-4 py-3 text-right font-mono text-sm">{{ formatCurrency(holding.avg_cost, 'TW') }}</td>
              <td class="px-4 py-3 text-right font-mono text-sm">
                {{ holding.current_price ? formatCurrency(holding.current_price, 'TW') : '--' }}
              </td>
              <td class="px-4 py-3 text-right font-semibold">
                <span :class="holding.return_pct >= 0 ? 'text-green-400' : 'text-red-400'">
                  {{ holding.return_pct >= 0 ? '+' : '' }}{{ holding.return_pct?.toFixed(2) }}%
                </span>
              </td>
              <!-- 智慧分析：合併多個欄位 -->
              <td class="px-4 py-3">
                <div v-if="holding.buy_signal" class="space-y-1">
                  <div class="flex items-center gap-2">
                    <span class="px-2 py-0.5 rounded text-xs font-semibold"
                          :class="getBuyScoreClass(holding.buy_signal.buy_score)">
                      {{ holding.buy_signal.buy_score }}分
                    </span>
                    <span v-if="holding.buy_signal.suggested_amount > 0" class="text-cyan-400 text-xs">
                      +{{ formatCurrency(holding.buy_signal.suggested_amount, 'TW') }}
                    </span>
                  </div>
                  <div class="text-xs text-gray-500">
                    {{ holding.buy_signal.buy_status }}
                    <span v-if="holding.buy_signal.earnings_date" :class="getEarningsDateClass(holding.buy_signal.earnings_date)">
                      · {{ formatEarningsDate(holding.buy_signal.earnings_date) }}
                    </span>
                  </div>
                </div>
                <span v-else class="text-gray-500 text-sm">--</span>
              </td>
              <td class="px-4 py-3 text-center">
                <div class="flex items-center justify-center gap-1">
                  <button @click="openAddTransaction(holding)" class="p-1.5 hover:bg-white/10 rounded-lg" title="補倉">➕</button>
                  <button @click="viewTransactions(holding)" class="p-1.5 hover:bg-white/10 rounded-lg" title="查看記錄">📋</button>
                  <button @click="confirmDelete(holding)" class="p-1.5 hover:bg-red-500/20 rounded-lg text-red-400" title="刪除">🗑️</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 骨架屏 -->
    <div v-if="loading && !holdings.length" class="space-y-6">
      <div class="glass rounded-2xl p-6 animate-pulse">
        <div class="h-6 w-32 bg-white/10 rounded mb-4"></div>
        <div class="space-y-3">
          <div v-for="i in 3" :key="i" class="flex gap-4">
            <div class="h-4 w-16 bg-white/10 rounded"></div>
            <div class="h-4 w-24 bg-white/10 rounded"></div>
            <div class="h-4 flex-1 bg-white/10 rounded"></div>
            <div class="h-4 w-20 bg-white/10 rounded"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空狀態 -->
    <div v-else-if="!holdings.length" class="glass rounded-2xl p-12 text-center">
      <div class="max-w-md mx-auto">
        <span class="text-7xl mb-6 block animate-bounce">📈</span>
        <h3 class="text-2xl font-bold mb-3 bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
          開始追蹤您的投資
        </h3>
        <p class="text-gray-400 mb-8">
          新增您的第一筆持股，開始追蹤成本與損益。<br>
          支援美股與台股！
        </p>
        <button 
          @click="showAddModal = true"
          class="btn-gradient px-8 py-4 rounded-xl font-semibold text-lg flex items-center gap-3 mx-auto hover:scale-105 transition-transform"
        >
          <span class="text-2xl">➕</span>
          新增第一筆持股
        </button>
        <div class="mt-8 flex justify-center gap-8 text-sm text-gray-500">
          <div class="flex items-center gap-2">
            <span>🇺🇸</span> 美股
          </div>
          <div class="flex items-center gap-2">
            <span>🇹🇼</span> 台股
          </div>
        </div>
      </div>
    </div>

    <!-- 新增持股彈窗 -->
    <div v-if="showAddModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showAddModal = false">
      <div class="glass rounded-2xl p-8 w-full max-w-md mx-4">
        <h3 class="text-xl font-bold mb-6">➕ 新增持股</h3>
        <form @submit.prevent="addHolding">
          <div class="space-y-4">
            <div>
              <label class="block text-sm text-gray-400 mb-2">市場</label>
              <select v-model="form.market" class="w-full bg-white/10 rounded-xl px-4 py-3 border border-white/10">
                <option value="TW">🇹🇼 台股</option>
                <option value="US">🇺🇸 美股</option>
              </select>
            </div>
            <div>
              <label class="block text-sm text-gray-400 mb-2">股票代號</label>
              <input 
                v-model="form.symbol" 
                type="text" 
                class="w-full bg-white/10 rounded-xl px-4 py-3 border transition-colors"
                :class="symbolError ? 'border-rose-500' : 'border-white/10'"
                :placeholder="form.market === 'TW' ? '例如: 2330, 0050' : '例如: AAPL, TSLA'"
                required
                @input="validateSymbolInput"
                @blur="validateSymbolInput"
              >
              <p v-if="symbolError" class="text-rose-400 text-xs mt-1">{{ symbolError }}</p>
            </div>
            <div>
              <label class="block text-sm text-gray-400 mb-2">買入價格 {{ form.market === 'US' ? '(USD)' : '(TWD)' }}</label>
              <div class="relative">
                <span class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">{{ form.market === 'US' ? '$' : 'NT$' }}</span>
                <input 
                  v-model.number="form.price" 
                  type="number" 
                  step="0.01"
                  min="0.01"
                  class="w-full bg-white/10 rounded-xl pl-12 pr-4 py-3 border border-white/10"
                  placeholder="100.00"
                  required
                >
              </div>
              <p v-if="form.price !== null && form.price <= 0" class="text-rose-400 text-xs mt-1">價格必須大於 0</p>
            </div>
            
            <!-- 輸入模式切換 -->
            <div class="flex bg-white/5 rounded-xl p-1">
              <button 
                type="button"
                @click="switchInputMode('amount')"
                :class="form.inputMode === 'amount' ? 'bg-cyan-500/20 text-cyan-400' : 'text-gray-400 hover:text-gray-300'"
                class="flex-1 py-2 rounded-lg text-sm font-medium transition-colors"
              >
                💰 填金額算股數
              </button>
              <button
                type="button"
                @click="switchInputMode('quantity')"
                :class="form.inputMode === 'quantity' ? 'bg-cyan-500/20 text-cyan-400' : 'text-gray-400 hover:text-gray-300'"
                class="flex-1 py-2 rounded-lg text-sm font-medium transition-colors"
              >
                📊 填股數算金額
              </button>
            </div>
            
            <!-- 模式 A：填金額算股數 -->
            <div v-if="form.inputMode === 'amount'">
              <label class="block text-sm text-gray-400 mb-2">買入金額 {{ form.market === 'US' ? '(USD)' : '(TWD)' }}</label>
              <div class="relative">
                <span class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">{{ form.market === 'US' ? '$' : 'NT$' }}</span>
                <input 
                  v-model.number="form.amount" 
                  type="number" 
                  step="0.01"
                  min="1"
                  class="w-full bg-white/10 rounded-xl pl-12 pr-4 py-3 border border-white/10"
                  placeholder="10000"
                  required
                >
              </div>
              <p v-if="form.amount !== null && form.amount <= 0" class="text-rose-400 text-xs mt-1">金額必須大於 0</p>
            </div>
            
            <!-- 模式 B：填股數算金額 -->
            <div v-if="form.inputMode === 'quantity'">
              <label class="block text-sm text-gray-400 mb-2">買入股數</label>
              <input 
                v-model.number="form.quantity" 
                type="number" 
                :step="form.market === 'TW' ? '1' : '0.00001'"
                min="0.00001"
                class="w-full bg-white/10 rounded-xl px-4 py-3 border border-white/10"
                :placeholder="form.market === 'TW' ? '100' : '10.5'"
                required
              >
              <p v-if="form.quantity !== null && form.quantity <= 0" class="text-rose-400 text-xs mt-1">股數必須大於 0</p>
            </div>
            
            <!-- 計算結果顯示 -->
            <div class="glass rounded-xl p-4 bg-gradient-to-r from-cyan-500/10 to-purple-500/10 border border-cyan-500/20">
              <div class="flex justify-between items-center">
                <span class="text-gray-400">{{ form.inputMode === 'amount' ? '可持有股數' : '需投入金額' }}</span>
                <span class="text-2xl font-bold text-cyan-400">
                  {{ form.inputMode === 'amount' ? calculatedQuantity : calculatedAmountDisplay }}
                </span>
              </div>
              <p class="text-xs text-gray-500 mt-1" v-if="form.price && (form.inputMode === 'amount' ? form.amount : form.quantity)">
                <template v-if="form.inputMode === 'amount'">
                  {{ form.amount }} ÷ {{ form.price }} = {{ calculatedQuantity }} 股
                </template>
                <template v-else>
                  {{ form.price }} × {{ form.quantity }} = {{ calculatedAmountDisplay }}
                </template>
              </p>
            </div>
            
            <div>
              <label class="block text-sm text-gray-400 mb-2">備註（選填）</label>
              <input 
                v-model="form.note" 
                type="text" 
                class="w-full bg-white/10 rounded-xl px-4 py-3 border border-white/10"
                placeholder="首次買入"
              >
            </div>
          </div>
          <div class="flex gap-4 mt-6">
            <button type="button" @click="showAddModal = false" class="flex-1 px-6 py-3 rounded-xl bg-white/10 hover:bg-white/20 transition-colors">
              取消
            </button>
            <button type="submit" :disabled="loading" class="flex-1 btn-gradient px-6 py-3 rounded-xl font-semibold">
              {{ loading ? '處理中...' : '確認新增' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 補倉彈窗 -->
    <div v-if="showTransactionModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showTransactionModal = false">
      <div class="glass rounded-2xl p-8 w-full max-w-md mx-4">
        <h3 class="text-xl font-bold mb-6">➕ 補倉 - {{ selectedHolding?.symbol }}</h3>
        <form @submit.prevent="addTransactionSubmit">
          <div class="space-y-4">
            <div>
              <label class="block text-sm text-gray-400 mb-2">補倉價格 {{ selectedHolding?.market === 'US' ? '(USD)' : '(TWD)' }}</label>
              <div class="relative">
                <span class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">{{ selectedHolding?.market === 'US' ? '$' : 'NT$' }}</span>
                <input 
                  v-model.number="transactionForm.price" 
                  type="number" 
                  step="0.01"
                  class="w-full bg-white/10 rounded-xl pl-12 pr-4 py-3 border border-white/10"
                  required
                >
              </div>
            </div>
            
            <!-- 輸入模式切換 -->
            <div class="flex bg-white/5 rounded-xl p-1">
              <button 
                type="button"
                @click="switchTransactionInputMode('amount')"
                :class="transactionForm.inputMode === 'amount' ? 'bg-cyan-500/20 text-cyan-400' : 'text-gray-400 hover:text-gray-300'"
                class="flex-1 py-2 rounded-lg text-sm font-medium transition-colors"
              >
                💰 填金額算股數
              </button>
              <button
                type="button"
                @click="switchTransactionInputMode('quantity')"
                :class="transactionForm.inputMode === 'quantity' ? 'bg-cyan-500/20 text-cyan-400' : 'text-gray-400 hover:text-gray-300'"
                class="flex-1 py-2 rounded-lg text-sm font-medium transition-colors"
              >
                📊 填股數算金額
              </button>
            </div>
            
            <!-- 模式 A：填金額算股數 -->
            <div v-if="transactionForm.inputMode === 'amount'">
              <label class="block text-sm text-gray-400 mb-2">補倉金額 {{ selectedHolding?.market === 'US' ? '(USD)' : '(TWD)' }}</label>
              <div class="relative">
                <span class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">{{ selectedHolding?.market === 'US' ? '$' : 'NT$' }}</span>
                <input 
                  v-model.number="transactionForm.amount" 
                  type="number" 
                  step="0.01"
                  class="w-full bg-white/10 rounded-xl pl-12 pr-4 py-3 border border-white/10"
                  placeholder="5000"
                  required
                >
              </div>
            </div>
            
            <!-- 模式 B：填股數算金額 -->
            <div v-if="transactionForm.inputMode === 'quantity'">
              <label class="block text-sm text-gray-400 mb-2">補倉股數</label>
              <input 
                v-model.number="transactionForm.quantity" 
                type="number" 
                :step="selectedHolding?.market === 'TW' ? '1' : '0.00001'"
                min="0.00001"
                class="w-full bg-white/10 rounded-xl px-4 py-3 border border-white/10"
                :placeholder="selectedHolding?.market === 'TW' ? '100' : '10.5'"
                required
              >
            </div>
            
            <!-- 計算結果顯示 -->
            <div class="glass rounded-xl p-4 bg-gradient-to-r from-cyan-500/10 to-purple-500/10 border border-cyan-500/20">
              <div class="flex justify-between items-center">
                <span class="text-gray-400">{{ transactionForm.inputMode === 'amount' ? '可持有股數' : '需投入金額' }}</span>
                <span class="text-2xl font-bold text-cyan-400">
                  {{ transactionForm.inputMode === 'amount' ? calculatedTransactionQty : calculatedTransactionAmountDisplay }}
                </span>
              </div>
              <p class="text-xs text-gray-500 mt-1" v-if="transactionForm.price && (transactionForm.inputMode === 'amount' ? transactionForm.amount : transactionForm.quantity)">
                <template v-if="transactionForm.inputMode === 'amount'">
                  {{ transactionForm.amount }} ÷ {{ transactionForm.price }} = {{ calculatedTransactionQty }} 股
                </template>
                <template v-else>
                  {{ transactionForm.price }} × {{ transactionForm.quantity }} = {{ calculatedTransactionAmountDisplay }}
                </template>
              </p>
            </div>
            
            <div>
              <label class="block text-sm text-gray-400 mb-2">備註（選填）</label>
              <input 
                v-model="transactionForm.note" 
                type="text" 
                class="w-full bg-white/10 rounded-xl px-4 py-3 border border-white/10"
                placeholder="補倉"
              >
            </div>
          </div>
          <div class="flex gap-4 mt-6">
            <button type="button" @click="showTransactionModal = false" class="flex-1 px-6 py-3 rounded-xl bg-white/10 hover:bg-white/20 transition-colors">
              取消
            </button>
            <button type="submit" :disabled="loading" class="flex-1 btn-gradient px-6 py-3 rounded-xl font-semibold">
              {{ loading ? '處理中...' : '確認補倉' }}
            </button>
          </div>
        </form>
      </div>
    </div>


    <!-- 交易記錄彈窗 -->
    <div v-if="showHistoryModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showHistoryModal = false">
      <div class="glass rounded-2xl p-8 w-full max-w-2xl mx-4 max-h-[80vh] overflow-auto">
        <h3 class="text-xl font-bold mb-6">📋 交易記錄 - {{ selectedHolding?.symbol }}</h3>
        <table class="w-full">
          <thead>
            <tr class="text-gray-400 text-sm border-b border-white/10">
              <th class="px-4 py-2 text-left">日期</th>
              <th class="px-4 py-2 text-right">股數</th>
              <th class="px-4 py-2 text-right">價格</th>
              <th class="px-4 py-2 text-left">備註</th>
              <th class="px-4 py-2 text-center">刪除</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="txn in transactionHistory" :key="txn.id" class="border-b border-white/5">
              <td class="px-4 py-3">{{ formatDate(txn.transaction_date) }}</td>
              <td class="px-4 py-3 text-right font-mono">{{ txn.quantity }}</td>
              <td class="px-4 py-3 text-right font-mono">${{ txn.price }}</td>
              <td class="px-4 py-3 text-gray-400">{{ txn.note || '--' }}</td>
              <td class="px-4 py-3 text-center">
                <button @click="deleteTransactionItem(txn.id)" class="text-red-400 hover:text-red-300">🗑️</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div class="mt-6 text-right">
          <button @click="showHistoryModal = false" class="px-6 py-2 rounded-xl bg-white/10 hover:bg-white/20 transition-colors">
            關閉
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getHoldings, createHolding, addTransaction, getTransactions, deleteHolding, deleteTransaction } from '../api'
import { useToast } from '../composables/useToast'

const toast = useToast()

const loading = ref(false)
const holdings = ref([])
const summary = ref(null)

// 彈窗控制
const showAddModal = ref(false)
const showTransactionModal = ref(false)
const showHistoryModal = ref(false)
const selectedHolding = ref(null)
const transactionHistory = ref([])

// 排序狀態
const sortKeyUS = ref('symbol')
const sortOrderUS = ref('asc')
const sortKeyTW = ref('symbol')
const sortOrderTW = ref('asc')

// 分開美股和台股
const usHoldings = computed(() => holdings.value.filter(h => h.market === 'US'))
const twHoldings = computed(() => holdings.value.filter(h => h.market === 'TW'))

// 排序後的持股
const sortedUSHoldings = computed(() => {
  return [...usHoldings.value].sort((a, b) => {
    const key = sortKeyUS.value
    const order = sortOrderUS.value === 'asc' ? 1 : -1
    if (key === 'symbol') return a.symbol.localeCompare(b.symbol) * order
    return ((a[key] || 0) - (b[key] || 0)) * order
  })
})

const sortedTWHoldings = computed(() => {
  return [...twHoldings.value].sort((a, b) => {
    const key = sortKeyTW.value
    const order = sortOrderTW.value === 'asc' ? 1 : -1
    if (key === 'symbol') return a.symbol.localeCompare(b.symbol) * order
    return ((a[key] || 0) - (b[key] || 0)) * order
  })
})

// 切換排序
function toggleSort(key, market) {
  if (market === 'US') {
    if (sortKeyUS.value === key) {
      sortOrderUS.value = sortOrderUS.value === 'asc' ? 'desc' : 'asc'
    } else {
      sortKeyUS.value = key
      sortOrderUS.value = 'asc'
    }
  } else {
    if (sortKeyTW.value === key) {
      sortOrderTW.value = sortOrderTW.value === 'asc' ? 'desc' : 'asc'
    } else {
      sortKeyTW.value = key
      sortOrderTW.value = 'asc'
    }
  }
}

// 取得排序箭頭
function getSortArrow(key, market) {
  const sortKey = market === 'US' ? sortKeyUS.value : sortKeyTW.value
  const sortOrder = market === 'US' ? sortOrderUS.value : sortOrderTW.value
  if (sortKey !== key) return ''
  return sortOrder === 'asc' ? '↑' : '↓'
}

// 分開計算總成本
const usTotalCost = computed(() => {
  return usHoldings.value.reduce((sum, h) => sum + (h.total_cost || 0), 0)
})
const twTotalCost = computed(() => {
  return twHoldings.value.reduce((sum, h) => sum + (h.total_cost || 0), 0)
})

// 分開計算未實現損益
const usUnrealizedPnl = computed(() => {
  return usHoldings.value.reduce((sum, h) => sum + (h.unrealized_pnl || 0), 0)
})
const twUnrealizedPnl = computed(() => {
  return twHoldings.value.reduce((sum, h) => sum + (h.unrealized_pnl || 0), 0)
})

// 分開計算報酬率
const usReturnPct = computed(() => {
  if (usTotalCost.value <= 0) return 0
  return (usUnrealizedPnl.value / usTotalCost.value) * 100
})
const twReturnPct = computed(() => {
  if (twTotalCost.value <= 0) return 0
  return (twUnrealizedPnl.value / twTotalCost.value) * 100
})
const totalReturnPct = computed(() => {
  return summary.value?.total_return_pct || 0
})

// 表單資料
const form = ref({
  market: 'TW',
  symbol: '',
  price: null,
  amount: null,      // 買入金額
  quantity: null,    // 買入股數（新增）
  inputMode: 'amount', // 'amount' 或 'quantity'（新增）
  note: ''
})

// 表單驗證錯誤
const symbolError = ref('')

// 即時驗證股票代號
function validateSymbolInput() {
  const symbol = form.value.symbol.toUpperCase().trim()
  if (!symbol) {
    symbolError.value = ''
    return true
  }
  
  if (form.value.market === 'US') {
    // 美股：1-5 個大寫字母
    if (!/^[A-Z]{1,5}$/.test(symbol)) {
      symbolError.value = '美股代號必須是 1-5 個英文字母（如 AAPL, TSLA）'
      return false
    }
  } else {
    // 台股：4-6 位數字
    const clean = symbol.replace('.TW', '')
    if (!/^\d{4,6}$/.test(clean)) {
      symbolError.value = '台股代號必須是 4-6 位數字（如 2330, 0050）'
      return false
    }
  }
  
  symbolError.value = ''
  return true
}

const transactionForm = ref({
  quantity: null,
  price: null,
  amount: null,
  inputMode: 'amount', // 'amount' 或 'quantity'（新增）
  note: ''
})

// 計算可持有股數（模式：金額 → 股數）
const calculatedQuantity = computed(() => {
  if (form.value.inputMode !== 'amount') return '--'
  if (!form.value.price || !form.value.amount || form.value.price <= 0) {
    return '--'
  }
  const qty = form.value.amount / form.value.price
  // 台股取整數，美股保留5位小數
  if (form.value.market === 'TW') {
    return Math.floor(qty)
  }
  return parseFloat(qty.toFixed(5))
})

// 計算需投入金額（模式：股數 → 金額）
const calculatedAmount = computed(() => {
  if (form.value.inputMode !== 'quantity') return null
  if (!form.value.price || !form.value.quantity || form.value.price <= 0) {
    return null
  }
  return parseFloat((form.value.price * form.value.quantity).toFixed(2))
})

// 格式化顯示金額
const calculatedAmountDisplay = computed(() => {
  const amount = calculatedAmount.value
  if (amount === null) return '--'
  const prefix = form.value.market === 'US' ? '$' : 'NT$'
  return `${prefix}${amount.toLocaleString()}`
})

// 補倉計算股數（模式：金額 → 股數）
const calculatedTransactionQty = computed(() => {
  if (transactionForm.value.inputMode !== 'amount') return '--'
  if (!transactionForm.value.price || !transactionForm.value.amount || transactionForm.value.price <= 0) {
    return '--'
  }
  const qty = transactionForm.value.amount / transactionForm.value.price
  if (selectedHolding.value?.market === 'TW') {
    return Math.floor(qty)
  }
  return parseFloat(qty.toFixed(5))
})

// 補倉計算金額（模式：股數 → 金額）
const calculatedTransactionAmount = computed(() => {
  if (transactionForm.value.inputMode !== 'quantity') return null
  if (!transactionForm.value.price || !transactionForm.value.quantity || transactionForm.value.price <= 0) {
    return null
  }
  return parseFloat((transactionForm.value.price * transactionForm.value.quantity).toFixed(2))
})

// 補倉格式化顯示金額
const calculatedTransactionAmountDisplay = computed(() => {
  const amount = calculatedTransactionAmount.value
  if (amount === null) return '--'
  const prefix = selectedHolding.value?.market === 'US' ? '$' : 'NT$'
  return `${prefix}${amount.toLocaleString()}`
})

// 切換新增持股的輸入模式
function switchInputMode(mode) {
  form.value.inputMode = mode
  // 切換時清除對應欄位
  if (mode === 'amount') {
    form.value.quantity = null
  } else {
    form.value.amount = null
  }
}

// 切換補倉的輸入模式
function switchTransactionInputMode(mode) {
  transactionForm.value.inputMode = mode
  // 切換時清除對應欄位
  if (mode === 'amount') {
    transactionForm.value.quantity = null
  } else {
    transactionForm.value.amount = null
  }
}

// 取得持股列表
async function fetchHoldings() {
  try {
    loading.value = true
    const data = await getHoldings()
    holdings.value = data.holdings || []
    summary.value = data.summary || null
  } catch (error) {
    console.error('取得持股失敗:', error)
  } finally {
    loading.value = false
  }
}

// 新增持股
async function addHolding() {
  // 前端驗證
  if (!form.value.symbol.trim()) {
    toast.error('請輸入股票代號')
    return
  }
  if (!validateSymbolInput()) {
    toast.error(symbolError.value)
    return
  }
  if (!form.value.price || form.value.price <= 0) {
    toast.error('價格必須大於 0')
    return
  }
  
  // 根據模式驗證對應欄位
  let finalQuantity
  if (form.value.inputMode === 'amount') {
    if (!form.value.amount || form.value.amount <= 0) {
      toast.error('金額必須大於 0')
      return
    }
    if (calculatedQuantity.value === '--' || calculatedQuantity.value <= 0) {
      toast.error('請輸入有效的價格和金額')
      return
    }
    finalQuantity = calculatedQuantity.value
  } else {
    if (!form.value.quantity || form.value.quantity <= 0) {
      toast.error('股數必須大於 0')
      return
    }
    finalQuantity = form.value.quantity
  }
  
  try {
    loading.value = true
    const data = {
      symbol: form.value.symbol,
      market: form.value.market,
      price: form.value.price,
      quantity: finalQuantity,
      note: form.value.note
    }
    await createHolding(data)
    showAddModal.value = false
    form.value = { market: 'TW', symbol: '', price: null, amount: null, quantity: null, inputMode: 'amount', note: '' }
    toast.success(`成功新增 ${data.symbol} 持股！`)
    await fetchHoldings()
  } catch (error) {
    console.error('新增持股失敗:', error)
    toast.error('新增失敗: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

// 開啟補倉彈窗
function openAddTransaction(holding) {
  selectedHolding.value = holding
  transactionForm.value = { price: null, amount: null, quantity: null, inputMode: 'amount', note: '' }
  showTransactionModal.value = true
}

// 新增補倉
async function addTransactionSubmit() {
  if (!transactionForm.value.price || transactionForm.value.price <= 0) {
    toast.error('價格必須大於 0')
    return
  }
  
  // 根據模式驗證對應欄位
  let finalQuantity
  if (transactionForm.value.inputMode === 'amount') {
    if (!transactionForm.value.amount || transactionForm.value.amount <= 0) {
      toast.error('金額必須大於 0')
      return
    }
    if (calculatedTransactionQty.value === '--' || calculatedTransactionQty.value <= 0) {
      toast.error('請輸入有效的價格和金額')
      return
    }
    finalQuantity = calculatedTransactionQty.value
  } else {
    if (!transactionForm.value.quantity || transactionForm.value.quantity <= 0) {
      toast.error('股數必須大於 0')
      return
    }
    finalQuantity = transactionForm.value.quantity
  }
  
  try {
    loading.value = true
    const data = {
      price: transactionForm.value.price,
      quantity: finalQuantity,
      note: transactionForm.value.note
    }
    await addTransaction(selectedHolding.value.id, data)
    showTransactionModal.value = false
    toast.success(`${selectedHolding.value.symbol} 補倉成功！`)
    await fetchHoldings()
  } catch (error) {
    console.error('補倉失敗:', error)
    toast.error('補倉失敗: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

// 查看交易記錄
async function viewTransactions(holding) {
  try {
    selectedHolding.value = holding
    const data = await getTransactions(holding.id)
    transactionHistory.value = data.transactions || []
    showHistoryModal.value = true
  } catch (error) {
    console.error('取得交易記錄失敗:', error)
  }
}

// 刪除持股
async function confirmDelete(holding) {
  if (confirm(`確定要刪除 ${holding.symbol} 的所有持股記錄嗎？`)) {
    try {
      await deleteHolding(holding.id)
      toast.success(`已刪除 ${holding.symbol}`)
      await fetchHoldings()
    } catch (error) {
      console.error('刪除失敗:', error)
      toast.error('刪除失敗')
    }
  }
}

// 刪除交易記錄
async function deleteTransactionItem(txnId) {
  if (confirm('確定要刪除此交易記錄嗎？')) {
    try {
      await deleteTransaction(selectedHolding.value.id, txnId)
      await viewTransactions(selectedHolding.value)
      await fetchHoldings()
    } catch (error) {
      console.error('刪除交易記錄失敗:', error)
    }
  }
}

// 格式化日期
function formatDate(dateStr) {
  if (!dateStr) return '--'
  return new Date(dateStr).toLocaleDateString('zh-TW')
}

// 格式化幣別
function formatCurrency(value, market) {
  if (value == null) return '--'
  const prefix = market === 'US' ? '$' : 'NT$'
  return `${prefix}${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

// 格式化股數
function formatQuantity(qty) {
  if (qty == null) return '--'
  // 如果是整數，不顯示小數點
  return Number.isInteger(qty) ? qty : qty.toFixed(5)
}

// 買入分數樣式
function getBuyScoreClass(score) {
  if (score >= 80) return 'bg-green-500/30 text-green-400'
  if (score >= 60) return 'bg-yellow-500/30 text-yellow-400'
  if (score >= 40) return 'bg-blue-500/30 text-blue-400'
  if (score >= 20) return 'bg-orange-500/30 text-orange-400'
  return 'bg-red-500/30 text-red-400'
}

// 格式化財報日期
function formatEarningsDate(dateStr) {
  if (!dateStr) return '--'
  const date = new Date(dateStr)
  const month = date.getMonth() + 1
  const day = date.getDate()
  return `${month}/${day}`
}

// 財報日期樣式（距離越近顏色越醒目）
function getEarningsDateClass(dateStr) {
  if (!dateStr) return 'text-gray-500'
  
  const today = new Date()
  const earningsDate = new Date(dateStr)
  const diffDays = Math.ceil((earningsDate - today) / (1000 * 60 * 60 * 24))
  
  if (diffDays <= 0) return 'text-gray-500'  // 已過期
  if (diffDays <= 3) return 'text-red-400 font-semibold'  // 3 天內
  if (diffDays <= 7) return 'text-orange-400'  // 7 天內
  if (diffDays <= 14) return 'text-yellow-400'  // 14 天內
  return 'text-gray-400'  // 更久
}

onMounted(() => {
  fetchHoldings()
})
</script>
