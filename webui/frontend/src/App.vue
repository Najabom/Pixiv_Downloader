<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import AppSidebar from './components/AppSidebar.vue'
import ThemeToggle from './components/ThemeToggle.vue'
import GlobalBackground from './components/GlobalBackground.vue'
import { useThemeStore } from './stores/theme'
import { useDownloadStore } from './stores/download'

const theme = useThemeStore()
const download = useDownloadStore()

onMounted(() => {
  theme.init()
  download.fetchStatus()
})
</script>

<template>
  <GlobalBackground />
  <div class="relative z-10 min-h-screen flex">
    <AppSidebar />
    <main
      class="flex-1 lg:ml-[var(--sidebar-width)] min-h-screen transition-all duration-500 ease-lusion"
    >
      <header
        class="sticky top-0 z-30 flex items-center justify-end h-[var(--header-height)] px-6 lg:px-10 bg-bg/80 backdrop-blur-md border-b border-text-muted/10"
      >
        <ThemeToggle />
      </header>
      <div class="p-6 lg:p-10 max-w-[1600px] mx-auto">
        <RouterView v-slot="{ Component, route }">
          <transition name="fade" mode="out-in">
            <component :is="Component" :key="route.fullPath" />
          </transition>
        </RouterView>
      </div>
    </main>
  </div>
</template>

<style>
.fade-enter-active,
.fade-leave-active {
  transition:
    opacity 0.3s cubic-bezier(0.35, 0, 0, 1),
    transform 0.3s cubic-bezier(0.35, 0, 0, 1);
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
