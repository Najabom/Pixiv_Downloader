<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { LayoutDashboard, Library, Image, ScrollText, Settings, Download } from 'lucide-vue-next'
import { useDownloadStore } from '../stores/download'

const route = useRoute()
const download = useDownloadStore()

const navItems = [
  { name: 'dashboard', label: '仪表盘', icon: LayoutDashboard, path: '/' },
  { name: 'works', label: '作品管理', icon: Library, path: '/works' },
  { name: 'gallery', label: '图库浏览', icon: Image, path: '/gallery' },
  { name: 'logs', label: '下载', icon: ScrollText, path: '/logs' },
  { name: 'settings', label: '设置', icon: Settings, path: '/settings' },
]

const isActive = (path: string) => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

const indicatorStyle = computed(() => {
  const index = navItems.findIndex((item) => isActive(item.path))
  if (index === -1) return { opacity: 0 }
  return { transform: `translateY(${index * 56}px)`, opacity: 1 }
})
</script>

<template>
  <aside
    class="fixed left-0 top-0 z-40 h-screen w-[var(--sidebar-width)] bg-surface border-r border-text-muted/10 flex flex-col"
  >
    <div class="h-[var(--header-height)] flex items-center px-8 border-b border-text-muted/10">
      <div class="flex items-center gap-3">
        <div
          class="relative w-9 h-9 rounded-xl bg-primary flex items-center justify-center overflow-hidden"
        >
          <Download class="w-5 h-5 text-white relative z-10" />
          <div class="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent" />
        </div>
        <div>
          <h1 class="text-lg font-bold leading-tight">Pixiv DL</h1>
          <p class="text-xs text-muted">下载管理器</p>
        </div>
      </div>
    </div>

    <nav class="flex-1 px-4 py-6 relative">
      <div
        class="absolute left-4 w-1 h-10 rounded-full bg-primary transition-all duration-500 ease-lusion"
        :style="indicatorStyle"
      />
      <RouterLink
        v-for="item in navItems"
        :key="item.name"
        :to="item.path"
        class="relative flex items-center gap-3 px-4 h-14 rounded-xl text-sm font-medium transition-all duration-300 ease-lusion group"
        :class="
          isActive(item.path)
            ? 'text-primary'
            : 'text-text-muted hover:text-text-main hover:bg-text-muted/5'
        "
      >
        <component
          :is="item.icon"
          class="w-5 h-5 transition-transform duration-300 group-hover:scale-110"
        />
        <span>{{ item.label }}</span>
        <div
          v-if="item.name === 'logs' && download.running"
          class="ml-auto w-2 h-2 rounded-full bg-success animate-pulse-dot"
        />
      </RouterLink>
    </nav>

    <div class="p-4 border-t border-text-muted/10">
      <div class="px-4 py-3 rounded-xl bg-bg text-xs text-muted">
        <p class="font-medium text-text-main mb-1">状态</p>
        <p>{{ download.running ? '下载中...' : '空闲' }}</p>
      </div>
    </div>
  </aside>
</template>
