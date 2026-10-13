<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '../api/client'
import type { Stats } from '../types'
import StatCard from '../components/StatCard.vue'

const stats = ref<Stats>({
  work_count: 0,
  tag_count: 0,
  cp_count: 0,
  total_downloads: 0,
  total_storage_mb: 0,
})
const loading = ref(true)
const backgrounds = ref<string[]>([])

onMounted(async () => {
  try {
    stats.value = await api.stats()
    const res = await api.gallery.random(5, {})
    backgrounds.value = res.paths.map((p) => api.gallery.thumbUrl(p, 500) || '')
  } catch {
    backgrounds.value = []
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <header class="mb-10">
      <h1 class="text-3xl font-bold mb-2 animate-fade-in-up">仪表盘</h1>
      <p class="text-muted animate-fade-in-up stagger-1">概览你的 Pixiv 下载任务与图库状态</p>
    </header>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-5 mb-10">
      <StatCard
        title="作品"
        :value="stats.work_count"
        icon="Library"
        :loading="loading"
        :background="backgrounds[0]"
        class="animate-fade-in-up stagger-1"
      />
      <StatCard
        title="角色"
        :value="stats.tag_count"
        icon="Users"
        :loading="loading"
        :background="backgrounds[1]"
        class="animate-fade-in-up stagger-2"
      />
      <StatCard
        title="CP"
        :value="stats.cp_count"
        icon="Tags"
        :loading="loading"
        :background="backgrounds[2]"
        class="animate-fade-in-up stagger-3"
      />
      <StatCard
        title="下载图片"
        :value="stats.total_downloads"
        icon="ImageIcon"
        :loading="loading"
        :background="backgrounds[3]"
        class="animate-fade-in-up stagger-4"
      />
      <StatCard
        title="存储占用 (MB)"
        :value="Math.round(stats.total_storage_mb ?? 0)"
        icon="HardDrive"
        :loading="loading"
        :background="backgrounds[4]"
        class="animate-fade-in-up stagger-5"
      />
    </div>
  </div>
</template>
