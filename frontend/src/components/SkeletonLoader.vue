<template>
  <div class="space-y-4">
    <!-- 市場狀態卡片骨架 -->
    <div v-if="type === 'market'" class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div v-for="i in 3" :key="i" class="glass rounded-2xl p-6 animate-pulse">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 bg-white/10 rounded-full"></div>
          <div class="space-y-2">
            <div class="h-4 w-24 bg-white/10 rounded"></div>
            <div class="h-3 w-16 bg-white/10 rounded"></div>
          </div>
        </div>
        <div class="h-4 w-20 bg-white/10 rounded"></div>
      </div>
    </div>

    <!-- 摘要卡片骨架 -->
    <div v-else-if="type === 'summary'" class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div v-for="i in 2" :key="i" class="glass rounded-2xl p-6 animate-pulse border-l-4 border-white/20">
        <div class="flex items-center justify-between">
          <div class="space-y-2">
            <div class="h-3 w-28 bg-white/10 rounded"></div>
            <div class="h-6 w-20 bg-white/10 rounded"></div>
            <div class="h-3 w-24 bg-white/10 rounded"></div>
          </div>
          <div class="text-right space-y-2">
            <div class="h-8 w-24 bg-white/10 rounded"></div>
            <div class="h-4 w-16 bg-white/10 rounded ml-auto"></div>
          </div>
        </div>
        <div class="mt-4 flex gap-1">
          <div v-for="j in 7" :key="j" class="flex-1 bg-white/10 rounded-sm" :style="{ height: (j * 4) + 'px' }"></div>
        </div>
      </div>
    </div>

    <!-- 表格骨架 -->
    <div v-else-if="type === 'table'" class="glass rounded-2xl overflow-hidden animate-pulse">
      <div class="px-6 py-4 border-b border-white/10">
        <div class="h-5 w-32 bg-white/10 rounded"></div>
      </div>
      <div class="p-4 space-y-3">
        <div v-for="i in rows" :key="i" class="flex items-center gap-4">
          <div class="h-4 w-16 bg-white/10 rounded"></div>
          <div class="h-4 w-20 bg-white/10 rounded"></div>
          <div class="h-4 flex-1 bg-white/10 rounded"></div>
          <div class="h-4 w-16 bg-white/10 rounded"></div>
          <div class="h-4 w-16 bg-white/10 rounded"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  type: {
    type: String,
    default: 'table', // 'market', 'summary', 'table'
  },
  rows: {
    type: Number,
    default: 5
  }
})
</script>

<style scoped>
@keyframes shimmer {
  0% { opacity: 0.3; }
  50% { opacity: 0.5; }
  100% { opacity: 0.3; }
}

.animate-pulse > div {
  animation: shimmer 1.5s ease-in-out infinite;
}
</style>
