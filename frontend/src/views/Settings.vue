<template>
  <div class="space-y-8">
    <!-- 標題 -->
    <div>
      <h2 class="text-3xl font-bold">設定</h2>
      <p class="text-gray-400 mt-1">管理監控的投資組合與門檻設定</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- 台股設定 -->
      <div class="glass rounded-2xl p-6">
        <div class="flex items-center gap-3 mb-6">
          <span class="text-3xl">🇹🇼</span>
          <h3 class="font-semibold text-xl">台股設定</h3>
        </div>

        <!-- 門檻 -->
        <div class="mb-6">
          <label class="block text-gray-400 text-sm mb-2">通知門檻 (空白分隔)</label>
          <input 
            v-model="config.TW.thresholds"
            type="text"
            placeholder="+3 +5 -5 -10"
            class="w-full bg-dark-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          <p class="text-gray-500 text-xs mt-1">例如: +3 表示上漲 3% 時通知</p>
        </div>

        <!-- 群組列表 -->
        <div class="space-y-3 mb-4">
          <div 
            v-for="(stocks, name) in config.TW.groups" 
            :key="name"
            class="bg-dark-700 rounded-lg p-4 flex items-center justify-between"
          >
            <div>
              <p class="font-semibold">{{ name }}</p>
              <p class="text-gray-400 text-sm">{{ stocks.join(', ').replace(/.TW/g, '') }}</p>
            </div>
            <button 
              @click="removeGroup('TW', name)"
              class="text-rose-400 hover:text-rose-300 px-3 py-1"
            >
              🗑️
            </button>
          </div>
        </div>

        <!-- 新增群組 -->
        <div class="bg-dark-700 rounded-lg p-4">
          <p class="text-sm text-gray-400 mb-3">新增投資組合</p>
          <input 
            v-model="newGroup.TW.name"
            type="text"
            placeholder="組合名稱"
            class="w-full bg-dark-800 rounded-lg px-4 py-2 mb-2 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          <input 
            v-model="newGroup.TW.stocks"
            type="text"
            placeholder="股票代號 (空白分隔)"
            class="w-full bg-dark-800 rounded-lg px-4 py-2 mb-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          <button 
            @click="addGroup('TW')"
            class="btn-gradient w-full py-2 rounded-lg font-semibold"
          >
            ➕ 新增
          </button>
        </div>
      </div>

      <!-- 美股設定 -->
      <div class="glass rounded-2xl p-6">
        <div class="flex items-center gap-3 mb-6">
          <span class="text-3xl">🇺🇸</span>
          <h3 class="font-semibold text-xl">美股設定</h3>
        </div>

        <!-- 門檻 -->
        <div class="mb-6">
          <label class="block text-gray-400 text-sm mb-2">通知門檻 (空白分隔)</label>
          <input 
            v-model="config.US.thresholds"
            type="text"
            placeholder="+5 +10 -5 -10"
            class="w-full bg-dark-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500"
          />
          <p class="text-gray-500 text-xs mt-1">例如: -10 表示下跌 10% 時通知</p>
        </div>

        <!-- 群組列表 -->
        <div class="space-y-3 mb-4">
          <div 
            v-for="(stocks, name) in config.US.groups" 
            :key="name"
            class="bg-dark-700 rounded-lg p-4 flex items-center justify-between"
          >
            <div>
              <p class="font-semibold">{{ name }}</p>
              <p class="text-gray-400 text-sm">{{ stocks.join(', ') }}</p>
            </div>
            <button 
              @click="removeGroup('US', name)"
              class="text-rose-400 hover:text-rose-300 px-3 py-1"
            >
              🗑️
            </button>
          </div>
        </div>

        <!-- 新增群組 -->
        <div class="bg-dark-700 rounded-lg p-4">
          <p class="text-sm text-gray-400 mb-3">新增投資組合</p>
          <input 
            v-model="newGroup.US.name"
            type="text"
            placeholder="組合名稱"
            class="w-full bg-dark-800 rounded-lg px-4 py-2 mb-2 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500"
          />
          <input 
            v-model="newGroup.US.stocks"
            type="text"
            placeholder="股票代號 (空白分隔)"
            class="w-full bg-dark-800 rounded-lg px-4 py-2 mb-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500"
          />
          <button 
            @click="addGroup('US')"
            class="btn-gradient w-full py-2 rounded-lg font-semibold"
          >
            ➕ 新增
          </button>
        </div>
      </div>
    </div>

    <!-- 儲存按鈕 -->
    <div class="flex justify-center">
      <button 
        @click="saveThresholds"
        :disabled="saving"
        class="btn-gradient px-8 py-4 rounded-xl font-semibold text-lg flex items-center gap-2"
      >
        <span v-if="saving" class="animate-spin">⟳</span>
        <span v-else>💾</span>
        儲存所有設定
      </button>
    </div>

    <!-- 提示訊息 -->
    <div 
      v-if="message"
      class="fixed bottom-8 right-8 px-6 py-4 rounded-xl shadow-lg transition-all"
      :class="messageType === 'success' ? 'bg-emerald-500' : 'bg-rose-500'"
    >
      {{ message }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getConfig, updateThresholds, createGroup, deleteGroup } from '../api'

const config = ref({
  TW: { thresholds: '', groups: {} },
  US: { thresholds: '', groups: {} }
})

const newGroup = ref({
  TW: { name: '', stocks: '' },
  US: { name: '', stocks: '' }
})

const saving = ref(false)
const message = ref('')
const messageType = ref('success')

async function loadConfig() {
  try {
    config.value = await getConfig()
  } catch (error) {
    showMessage('載入設定失敗', 'error')
  }
}

async function saveThresholds() {
  saving.value = true
  try {
    await updateThresholds('TW', config.value.TW.thresholds)
    await updateThresholds('US', config.value.US.thresholds)
    showMessage('設定已儲存！', 'success')
  } catch (error) {
    showMessage('儲存失敗', 'error')
  } finally {
    saving.value = false
  }
}

async function addGroup(market) {
  const group = newGroup.value[market]
  if (!group.name || !group.stocks) {
    showMessage('請填寫完整資訊', 'error')
    return
  }

  try {
    const stocks = group.stocks.split(/\s+/).filter(s => s)
    await createGroup(market, group.name, stocks)
    await loadConfig()
    newGroup.value[market] = { name: '', stocks: '' }
    showMessage(`已新增 ${group.name}`, 'success')
  } catch (error) {
    showMessage(error.response?.data?.detail || '新增失敗', 'error')
  }
}

async function removeGroup(market, name) {
  if (!confirm(`確定要刪除「${name}」嗎？`)) return

  try {
    await deleteGroup(market, name)
    await loadConfig()
    showMessage(`已刪除 ${name}`, 'success')
  } catch (error) {
    showMessage('刪除失敗', 'error')
  }
}

function showMessage(msg, type = 'success') {
  message.value = msg
  messageType.value = type
  setTimeout(() => {
    message.value = ''
  }, 3000)
}

onMounted(loadConfig)
</script>
