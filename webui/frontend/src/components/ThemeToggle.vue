<script setup lang="ts">
import { computed } from 'vue'
import { Sun, Moon, Monitor } from 'lucide-vue-next'
import { useThemeStore } from '../stores/theme'

const theme = useThemeStore()
const icon = computed(() =>
  theme.mode === 'auto' ? Monitor : theme.mode === 'dark' ? Moon : Sun
)
const label = computed(() =>
  theme.mode === 'auto' ? '自动' : theme.mode === 'dark' ? '暗色' : '明亮'
)
</script>

<template>
  <button
    class="flex items-center gap-2 px-3 py-2 rounded-full bg-surface border border-text-muted/10 text-sm font-medium text-text-muted hover:text-text-main hover:border-primary/30 transition-all duration-300 ease-lusion"
    :title="`主题：${label}（点击切换）`"
    @click="theme.cycle"
  >
    <transition name="spin" mode="out-in">
      <component :is="icon" :key="theme.mode" class="w-4 h-4" />
    </transition>
    <span class="hidden sm:inline">{{ label }}</span>
  </button>
</template>

<style scoped>
.spin-enter-active,
.spin-leave-active {
  transition:
    transform 0.3s cubic-bezier(0.35, 0, 0, 1),
    opacity 0.3s;
}
.spin-enter-from {
  opacity: 0;
  transform: rotate(-90deg);
}
.spin-leave-to {
  opacity: 0;
  transform: rotate(90deg);
}
</style>
