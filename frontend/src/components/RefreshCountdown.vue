<template>
  <div class="flex items-center gap-3">
    <!-- 圓環倒數器 -->
    <div class="relative w-14 h-14">
      <svg class="w-14 h-14 transform -rotate-90">
        <!-- 背景圓 -->
        <circle
          cx="28" cy="28" r="24"
          stroke="rgba(255,255,255,0.1)"
          stroke-width="4"
          fill="none"
        />
        <!-- 進度圓 -->
        <circle
          cx="28" cy="28" r="24"
          stroke="url(#gradient)"
          stroke-width="4"
          fill="none"
          stroke-linecap="round"
          :stroke-dasharray="circumference"
          :stroke-dashoffset="dashOffset"
          class="transition-all duration-1000"
        />
        <defs>
          <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#06b6d4" />
            <stop offset="100%" stop-color="#a855f7" />
          </linearGradient>
        </defs>
      </svg>
      <!-- 秒數 -->
      <div class="absolute inset-0 flex items-center justify-center">
        <span class="text-sm font-bold">{{ seconds }}</span>
      </div>
    </div>
    
    <!-- 文字 -->
    <div class="text-sm text-gray-400">
      <p>自動刷新</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  seconds: {
    type: Number,
    required: true
  },
  total: {
    type: Number,
    default: 30
  }
})

const circumference = 2 * Math.PI * 24 // r = 24

const dashOffset = computed(() => {
  const progress = props.seconds / props.total
  return circumference * (1 - progress)
})
</script>
