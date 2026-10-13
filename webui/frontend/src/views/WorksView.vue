<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
import type { Work } from '../types'
import { Plus, Trash2, Power, Users, Heart, ChevronRight } from 'lucide-vue-next'

const router = useRouter()
const works = ref<Work[]>([])
const backgrounds = ref<Record<string, string>>({})
const loading = ref(true)
const newName = ref('')
const showBg = reactive<Record<string, boolean>>({})

const preloadBg = (key: string, url: string) => {
  if (!url) { showBg[key] = false; return }
  const img = new Image()
  img.onload = () => { showBg[key] = true }
  img.onerror = () => { showBg[key] = false }
  img.src = url
  if (img.complete) showBg[key] = true
}

const load = async () => {
  loading.value = true
  works.value = await api.works.list()
  const map: Record<string, string> = {}
  await Promise.all(
    works.value.map(async (w) => {
      let url = ''
      try {
        const res = await api.gallery.random(1, { work: w.name })
        url = api.gallery.thumbUrl(res.paths[0], 600) || ''
      } catch { url = '' }
      map[w.name] = url
      preloadBg(w.name, url)
    }),
  )
  backgrounds.value = map
  loading.value = false
}

const create = async () => {
  if (!newName.value.trim()) return
  await api.works.create(newName.value.trim())
  newName.value = ''
  await load()
}

const toggle = async (name: string) => { await api.works.toggle(name); await load() }
const remove = async (name: string) => {
  if (!confirm(`确定删除作品「${name}」？`)) return
  await api.works.delete(name)
  await load()
}

onMounted(load)
</script>

<template>
  <div>
    <header class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
      <div>
        <h1 class="text-3xl font-bold mb-1">作品管理</h1>
        <p class="text-muted">管理作品、角色与 CP 配置</p>
      </div>
      <div class="flex items-center gap-3">
        <input v-model="newName" placeholder="新作品名" class="input w-48" @keyup.enter="create" />
        <button class="btn-primary" @click="create"><Plus class="w-4 h-4" /> 添加</button>
      </div>
    </header>

    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      <div v-for="i in 6" :key="i" class="card h-44 animate-pulse bg-text-muted/5" />
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      <div
        v-for="work in works"
        :key="work.name"
        class="card card-hover p-6 cursor-pointer group relative overflow-hidden min-h-[180px]"
        :class="!backgrounds[work.name] ? 'bg-text-muted/5' : ''"
        @click="router.push(`/works/${encodeURIComponent(work.name)}`)"
      >
        <div
          v-show="backgrounds[work.name]"
              class="absolute inset-0 bg-cover bg-center transition-opacity duration-1000 ease-lusion"
          :class="showBg[work.name] ? 'opacity-40' : 'opacity-0'"
          :style="{ backgroundImage: `url(${backgrounds[work.name]})` }"
        />
        <div class="absolute inset-0 bg-gradient-to-t from-surface via-surface/90 to-surface/70" />
        <div class="relative z-10">
          <div
            class="absolute top-0 left-0 w-1 h-full transition-all duration-500"
            :class="work.active ? 'bg-primary' : 'bg-text-muted/20'"
          />
          <div class="flex items-start justify-between mb-4 pl-2">
            <h3 class="text-xl font-bold">{{ work.name }}</h3>
            <button
              class="p-2 rounded-lg transition-colors"
              :class="work.active ? 'text-success bg-success/10' : 'text-muted bg-text-muted/10'"
              @click.stop="toggle(work.name)"
            >
              <Power class="w-4 h-4" />
            </button>
          </div>
          <div class="flex items-center gap-4 text-sm text-muted mb-6 pl-2">
            <span class="flex items-center gap-1"><Users class="w-4 h-4" /> {{ work.tags.length }} 角色</span>
            <span class="flex items-center gap-1"><Heart class="w-4 h-4" /> {{ work.cp_tags.length }} CP</span>
          </div>
          <div class="flex items-center justify-between pl-2">
            <span
              class="text-xs px-2.5 py-1 rounded-full font-medium"
              :class="work.active ? 'bg-success/10 text-success' : 'bg-text-muted/10 text-muted'"
            >
              {{ work.active ? '启用' : '停用' }}
            </span>
            <div class="flex items-center gap-1">
              <button class="p-2 rounded-lg text-muted hover:text-danger hover:bg-danger/10 transition-colors" @click.stop="remove(work.name)">
                <Trash2 class="w-4 h-4" />
              </button>
              <ChevronRight class="w-5 h-5 text-muted transition-transform duration-300 group-hover:translate-x-1" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
