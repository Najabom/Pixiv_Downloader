<script setup lang="ts">
import { ref, onMounted, watch, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'
import type { Work, TagConfig, CPConfig } from '../types'
import { Plus, Trash2, Power, ArrowLeft, Users, Heart, Save, Filter } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const workName = ref(decodeURIComponent(route.params.name as string))
const work = ref<Work | null>(null)
const tags = ref<TagConfig[]>([])
const cpTags = ref<CPConfig[]>([])
const tagBackgrounds = ref<Record<string, string>>({})
const cpBackgrounds = ref<Record<string, string>>({})
const loading = ref(true)
const newTag = ref({ folder: '', tags: '' })
const newCP = ref({ members: '', searchTags: '' })
const excludeTagsText = ref('')
const showTagBg = reactive<Record<string, boolean>>({})
const showCpBg = reactive<Record<string, boolean>>({})

const preload = (map: Record<string, boolean>, key: string, url: string) => {
  if (!url) { map[key] = false; return }
  const img = new Image()
  img.onload = () => { map[key] = true }
  img.onerror = () => { map[key] = false }
  img.src = url
  if (img.complete) map[key] = true
}

const load = async () => {
  loading.value = true
  const name = workName.value
  const [list, t, c] = await Promise.all([api.works.list(), api.works.tags.list(name), api.works.cpTags.list(name)])
  work.value = list.find((x) => x.name === name) || null
  excludeTagsText.value = (work.value?.exclude_tags || []).join('\n')
  tags.value = t
  cpTags.value = c

  const tgMap: Record<string, string> = {}
  await Promise.all(t.map(async (tag) => {
    let url = ''
    try { const r = await api.gallery.random(1, { work: name, category: tag.folder }); url = api.gallery.thumbUrl(r.paths[0], 600) || '' }
    catch { try { const r = await api.gallery.random(1, { work: name }); url = api.gallery.thumbUrl(r.paths[0], 600) || '' } catch { url = '' } }
    tgMap[tag.folder] = url
    preload(showTagBg, tag.folder, url)
  }))
  tagBackgrounds.value = tgMap

  const cpMap: Record<string, string> = {}
  await Promise.all(c.map(async (cp) => {
    let url = ''
    try { const r = await api.gallery.random(1, { work: name, category: cp.name }); url = api.gallery.thumbUrl(r.paths[0], 600) || '' }
    catch { try { const r = await api.gallery.random(1, { work: name }); url = api.gallery.thumbUrl(r.paths[0], 600) || '' } catch { url = '' } }
    cpMap[cp.name] = url
    preload(showCpBg, cp.name, url)
  }))
  cpBackgrounds.value = cpMap
  loading.value = false
}

const addTag = async () => {
  if (!newTag.value.folder.trim()) return
  const tagList = newTag.value.tags.split(',').map(s => s.trim()).filter(Boolean)
  await api.works.tags.add(workName.value, newTag.value.folder.trim(), tagList)
  newTag.value = { folder: '', tags: '' }
  await load()
}
const toggleTag = async (folder: string, active: boolean) => { await api.works.tags.update(workName.value, folder, { active: !active }); await load() }
const deleteTag = async (folder: string) => { if (!confirm('确定删除此角色？')) return; await api.works.tags.delete(workName.value, folder); await load() }
const addCP = async () => {
  const members = newCP.value.members.split(',').map(s => s.trim()).filter(Boolean)
  if (members.length < 2) { alert('CP 至少需要 2 个成员'); return }
  const searchTags = newCP.value.searchTags.split(',').map(s => s.trim()).filter(Boolean)
  await api.works.cpTags.add(workName.value, members, searchTags)
  newCP.value = { members: '', searchTags: '' }
  await load()
}
const deleteCP = async (index: number) => { if (!confirm('确定删除此 CP？')) return; await api.works.cpTags.delete(workName.value, index); await load() }

const saveExcludeTags = async () => {
  const tags = excludeTagsText.value.split('\n').map(s => s.trim()).filter(Boolean)
  await api.works.updateExcludeTags(workName.value, tags)
  await load()
}

onMounted(load)
watch(() => route.params.name, (val) => { workName.value = decodeURIComponent(val as string); load() })
</script>

<template>
  <div>
    <header class="flex items-center gap-4 mb-8">
      <button class="btn-secondary p-2.5" @click="router.push('/works')"><ArrowLeft class="w-4 h-4" /></button>
      <div><h1 class="text-3xl font-bold">{{ workName }}</h1><p class="text-muted text-sm">编辑角色标签与 CP 组合</p></div>
    </header>

    <div v-if="loading" class="card h-64 animate-pulse bg-text-muted/5" />

    <div v-else class="space-y-8">
      <section class="card p-6">
        <h2 class="text-lg font-bold mb-4 flex items-center gap-2"><Users class="w-5 h-5 text-primary" /> 角色</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          <div v-for="tag in tags" :key="tag.folder" class="flex items-center justify-between p-4 rounded-xl bg-bg relative overflow-hidden min-h-[72px]">
            <div
              v-show="tagBackgrounds[tag.folder]"
              class="absolute inset-0 bg-cover bg-center transition-opacity duration-1000 ease-lusion"
              :class="showTagBg[tag.folder] ? 'opacity-40' : 'opacity-0'"
              :style="{ backgroundImage: `url(${tagBackgrounds[tag.folder]})` }"
            />
            <div class="absolute inset-0 bg-gradient-to-r from-bg/90 to-bg/70" />
            <div class="relative z-10 flex items-center justify-between w-full">
              <div class="min-w-0"><div class="font-medium truncate">{{ tag.folder }}</div><div class="text-xs text-muted truncate">{{ tag.tags.join(', ') || '默认搜索' }}</div></div>
              <div class="flex items-center gap-2 ml-2">
                <button class="p-2 rounded-lg transition-colors" :class="tag.active ? 'text-success bg-success/10' : 'text-muted bg-text-muted/10'" @click="toggleTag(tag.folder, tag.active)"><Power class="w-4 h-4" /></button>
                <button class="p-2 rounded-lg text-muted hover:text-danger hover:bg-danger/10 transition-colors" @click="deleteTag(tag.folder)"><Trash2 class="w-4 h-4" /></button>
              </div>
            </div>
          </div>
        </div>
        <div class="flex flex-col sm:flex-row gap-3">
          <input v-model="newTag.folder" placeholder="角色名" class="input sm:w-40" />
          <input v-model="newTag.tags" placeholder="Pixiv 标签，逗号分隔" class="input flex-1" />
          <button class="btn-primary" @click="addTag"><Plus class="w-4 h-4" /> 添加</button>
        </div>
      </section>

      <section class="card p-6">
        <h2 class="text-lg font-bold mb-4 flex items-center gap-2"><Filter class="w-5 h-5 text-primary" /> 作品过滤标签</h2>
        <textarea v-model="excludeTagsText" rows="3" class="input font-mono text-sm" placeholder="每行一个标签，保存后写入 works.yaml" />
        <p class="text-xs text-muted mt-2">用换行分隔。下载时会跳过包含这些标签的作品</p>
        <div class="flex justify-end mt-4">
          <button class="btn-primary" @click="saveExcludeTags"><Save class="w-4 h-4" /> 保存过滤标签</button>
        </div>
      </section>

      <section class="card p-6">
        <h2 class="text-lg font-bold mb-4 flex items-center gap-2"><Heart class="w-5 h-5 text-primary" /> CP 组合</h2>
        <div class="space-y-3 mb-6">
          <div v-for="(cp, idx) in cpTags" :key="idx" class="flex items-center justify-between p-4 rounded-xl bg-bg relative overflow-hidden min-h-[72px]">
            <div
              v-show="cpBackgrounds[cp.name]"
              class="absolute inset-0 bg-cover bg-center transition-opacity duration-1000 ease-lusion"
              :class="showCpBg[cp.name] ? 'opacity-40' : 'opacity-0'"
              :style="{ backgroundImage: `url(${cpBackgrounds[cp.name]})` }"
            />
            <div class="absolute inset-0 bg-gradient-to-r from-bg/90 to-bg/70" />
            <div class="relative z-10 flex items-center justify-between w-full">
              <div class="min-w-0"><div class="font-medium">{{ cp.name }}</div><div class="text-xs text-muted">搜索：{{ cp.search_tags.join(', ') || '无' }}</div></div>
              <button class="p-2 rounded-lg text-muted hover:text-danger hover:bg-danger/10 transition-colors" @click="deleteCP(idx)"><Trash2 class="w-4 h-4" /></button>
            </div>
          </div>
        </div>
        <div class="flex flex-col sm:flex-row gap-3">
          <input v-model="newCP.members" placeholder="成员，逗号分隔" class="input flex-1" />
          <input v-model="newCP.searchTags" placeholder="搜索标签，逗号分隔" class="input flex-1" />
          <button class="btn-primary" @click="addCP"><Plus class="w-4 h-4" /> 添加</button>
        </div>
      </section>
    </div>
  </div>
</template>
