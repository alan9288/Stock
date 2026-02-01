<template>
  <Transition name="fade-loader">
    <div v-if="loading" class="loading-overlay">
      <div class="loader-container">
        <div class="loader-ring">
          <div></div>
          <div></div>
          <div></div>
          <div></div>
        </div>
        <p class="loader-text">{{ message }}</p>
      </div>
    </div>
  </Transition>
</template>

<script setup>
defineProps({
  loading: { type: Boolean, default: false },
  message: { type: String, default: '載入中...' }
})
</script>

<style scoped>
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(15, 15, 30, 0.85);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.loader-container {
  text-align: center;
}

.loader-ring {
  display: inline-block;
  position: relative;
  width: 64px;
  height: 64px;
}

.loader-ring div {
  box-sizing: border-box;
  display: block;
  position: absolute;
  width: 48px;
  height: 48px;
  margin: 8px;
  border: 4px solid;
  border-radius: 50%;
  animation: ring-spin 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite;
  border-color: #a855f7 transparent transparent transparent;
}

.loader-ring div:nth-child(1) { animation-delay: -0.45s; }
.loader-ring div:nth-child(2) { animation-delay: -0.3s; }
.loader-ring div:nth-child(3) { animation-delay: -0.15s; }

@keyframes ring-spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loader-text {
  margin-top: 16px;
  color: #a78bfa;
  font-size: 14px;
  letter-spacing: 1px;
}

/* 過場動畫 */
.fade-loader-enter-active,
.fade-loader-leave-active {
  transition: opacity 0.3s ease;
}

.fade-loader-enter-from,
.fade-loader-leave-to {
  opacity: 0;
}
</style>
