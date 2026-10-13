<script setup lang="ts">
import { ref, onMounted, watch, reactive, nextTick } from 'vue'
import { api } from '../api/client'
import type { Work, GalleryItem } from '../types'
import { ArrowLeft, Images, FolderOpen } from 'lucide-vue-next'
import ImageModal from '../components/ImageModal.vue'

const works = ref<Work[]>([])
const categories = ref<string[]>([])
const subfolders = ref<string[]>([])
const items = ref<GalleryItem[]>([])
const selectedWork = ref('')
const selectedCategory = ref('')
const selectedSubfolder = ref('')
const loadingWorks = ref(false)
const loadingCategories = ref(false)
const loadingImages = ref(false)
const backgrounds = ref<Record<string, string>>({})
const categoryBackgrounds = ref<Record<string, string>>({})
const showWorkBg = reactive<Record<string, boolean>>({})
const showCatBg = reactive<Record<string, boolean>>({})
const page = ref(1)
const pageSize = 30
const total = ref(0)
const step = ref<'works' | 'categories' | 'subfolders' | 'images'>('works')
const stepKey = ref(0)
const modalSrc = ref('')
const showModal = ref(false)
const contentRef = ref<HTMLElement | null>(null)

watch([selectedCategory, selectedSubfolder], () => {
  nextTick(() => contentRef.value?.scrollIntoView({ behavior: 'instant', block: 'start' }))
})

watch(step, () => { stepKey.value++ })
const openImage = (path: string) => { modalSrc.value = api.gallery.imageUrl(path); showModal.value = true }

const preload = (map: Record<string, boolean>, key: string, url: string) => {
  if (!url) { map[key] = false; return }
  const img = new Image()
  img.onload = () => { map[key] = true }
  img.onerror = () => { map[key] = false }
  img.src = url
  if (img.complete) map[key] = true
}

const loadWorks = async () => {
  loadingWorks.value = true
  works.value = await api.works.list()
  const map: Record<string, string> = {}
  await Promise.all(works.value.map(async (w) => {
    let url = ''
    try { const r = await api.gallery.random(1, { work: w.name }); url = api.gallery.thumbUrl(r.paths[0], 600) || '' } catch { url = '' }
    map[w.name] = url; preload(showWorkBg, w.name, url)
  }))
  backgrounds.value = map
  loadingWorks.value = false
}

const selectWork = async (name: string) => {
  selectedWork.value = name; selectedCategory.value = ''; selectedSubfolder.value = ''
  step.value = 'categories'; loadingCategories.value = true
  const res = await api.gallery.categories(name)
  categories.value = res.categories
  const map: Record<string, string> = {}
  await Promise.all(categories.value.map(async (c) => {
    let url = ''
    try { const r = await api.gallery.random(1, { work: name, category: c }); url = api.gallery.thumbUrl(r.paths[0], 600) || '' }
    catch { try { const r = await api.gallery.random(1, { work: name }); url = api.gallery.thumbUrl(r.paths[0], 600) || '' } catch { url = '' } }
    map[c] = url; preload(showCatBg, c, url)
  }))
  categoryBackgrounds.value = map
  loadingCategories.value = false
}

const selectCategory = async (category: string) => {
  selectedCategory.value = category; selectedSubfolder.value = ''; page.value = 1
  if (category === '组图') {
    step.value = 'subfolders'
    const res = await api.gallery.subfolders(selectedWork.value, category)
    subfolders.value = res.subfolders
    if (subfolders.value.length === 0) await loadImages()
    return
  }
  await loadImages()
}

const selectSubfolder = async (subfolder: string) => { selectedSubfolder.value = subfolder; page.value = 1; await loadImages() }

const loadImages = async () => {
  loadingImages.value = true; step.value = 'images'
  const params: Record<string, string | number> = { work: selectedWork.value, category: selectedCategory.value, page: page.value, page_size: pageSize }
  if (selectedSubfolder.value) params.subfolder = selectedSubfolder.value
  const res = await api.gallery.list(params)
  items.value = res.items; total.value = res.total; loadingImages.value = false
}

const goBack = () => {
  if (step.value === 'images') { if (selectedSubfolder.value) { selectedSubfolder.value = ''; step.value = 'subfolders' } else { selectedCategory.value = ''; step.value = 'categories' }; items.value = [] }
  else if (step.value === 'subfolders') { selectedCategory.value = ''; step.value = 'categories'; subfolders.value = [] }
  else if (step.value === 'categories') { selectedWork.value = ''; step.value = 'works'; categories.value = [] }
}

watch(page, () => { if (step.value === 'images') loadImages() })
onMounted(loadWorks)
</script>

<template>
  <div ref="contentRef" class="min-h-[60vh]">
    <header class="flex items-center gap-4 mb-8">
      <button v-if="step !== 'works'" class="btn-secondary p-2.5" @click="goBack"><ArrowLeft class="w-4 h-4" /></button>
      <div>
        <h1 class="text-3xl font-bold mb-1">图库浏览</h1>
        <p class="text-muted">
          <span v-if="step === 'works'">选择作品</span>
          <span v-else-if="step === 'categories'">{{ selectedWork }} / 选择分类</span>
          <span v-else-if="step === 'subfolders'">{{ selectedWork }} / {{ selectedCategory }} / 选择子文件夹</span>
          <span v-else>{{ selectedWork }} / {{ selectedCategory }}{{ selectedSubfolder ? ' / ' + selectedSubfolder : '' }}</span>
        </p>
      </div>
    </header>

    <Transition name="step" mode="out-in">
      <template v-if="step === 'works'">
        <div :key="stepKey">
          <div v-if="loadingWorks" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            <div v-for="i in 6" :key="i" class="card h-44 animate-pulse bg-text-muted/5" />
          </div>
          <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            <div
              v-for="work in works" :key="work.name"
              class="card card-hover p-6 cursor-pointer group relative overflow-hidden min-h-[180px]"
              :class="!backgrounds[work.name] ? 'bg-text-muted/5' : ''"
              @click="selectWork(work.name)"
            >
              <div
                v-show="backgrounds[work.name]"
                class="absolute inset-0 bg-cover bg-center transition-opacity duration-1000 ease-lusion"
                :class="showWorkBg[work.name] ? 'opacity-40' : 'opacity-0'"
                :style="{ backgroundImage: `url(${backgrounds[work.name]})` }"
              />
              <div class="absolute inset-0 bg-gradient-to-t from-surface via-surface/90 to-surface/70" />
              <div class="relative z-10 h-full flex flex-col justify-between">
                <h3 class="text-xl font-bold">{{ work.name }}</h3>
                <div class="flex items-center gap-4 text-sm text-muted"><span>{{ work.tags.length }} 角色</span><span>{{ work.cp_tags.length }} CP</span></div>
              </div>
            </div>
          </div>
        </div>
      </template>

      <template v-else-if="step === 'categories'">
        <div :key="stepKey">
          <div v-if="loadingCategories" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            <div v-for="i in 6" :key="i" class="card aspect-square animate-pulse bg-text-muted/5" />
          </div>
          <div v-else-if="categories.length === 0" class="card p-12 text-center text-muted">该作品下暂无图片分类</div>
          <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            <div
              v-for="category in categories" :key="category"
              class="card card-hover aspect-square cursor-pointer group relative overflow-hidden flex items-center justify-center"
              :class="!categoryBackgrounds[category] ? 'bg-text-muted/5' : ''"
              @click="selectCategory(category)"
            >
              <div
                v-show="categoryBackgrounds[category]"
                class="absolute inset-0 bg-cover bg-center transition-opacity duration-1000 ease-lusion"
                :class="showCatBg[category] ? 'opacity-45' : 'opacity-0'"
                :style="{ backgroundImage: `url(${categoryBackgrounds[category]})` }"
              />
              <div class="absolute inset-0 bg-gradient-to-t from-surface via-surface/90 to-surface/70" />
              <div class="relative z-10 text-center"><Images class="w-8 h-8 mx-auto mb-2 text-primary" /><div class="text-lg font-bold">{{ category }}</div></div>
            </div>
          </div>
        </div>
      </template>

      <template v-else-if="step === 'subfolders'">
        <div :key="stepKey">
          <div v-if="subfolders.length === 0" class="card p-12 text-center text-muted">组图分类下暂无子文件夹</div>
          <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            <div
              v-for="subfolder in subfolders" :key="subfolder"
              class="card card-hover aspect-square cursor-pointer group relative overflow-hidden flex items-center justify-center"
              @click="selectSubfolder(subfolder)"
            >
              <div class="relative z-10 text-center"><FolderOpen class="w-8 h-8 mx-auto mb-2 text-primary" /><div class="text-sm font-medium px-2 truncate max-w-full">{{ subfolder }}</div></div>
            </div>
          </div>
        </div>
      </template>

      <template v-else>
        <div :key="stepKey">
          <div v-if="loadingImages" class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
            <div v-for="i in 10" :key="i" class="aspect-[3/4] rounded-xl bg-text-muted/10 animate-pulse" />
          </div>
          <div v-else-if="items.length === 0" class="card p-12 text-center text-muted">该分类下暂无图片</div>
          <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
            <div
              v-for="item in items" :key="item.path"
              class="group relative aspect-[3/4] rounded-xl overflow-hidden bg-bg shadow-card hover:shadow-card-hover transition-all duration-500 hover:-translate-y-1 cursor-pointer"
              @click="openImage(item.path)"
            >
              <img :src="api.gallery.thumbUrl(item.path, 300)" class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105" loading="lazy" />
              <div class="absolute inset-x-0 bottom-0 p-3 bg-gradient-to-t from-black/70 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <p class="text-white text-xs font-medium truncate">{{ item.name }}</p>
              </div>
            </div>
          </div>
          <div class="flex items-center justify-center gap-4 mt-8">
            <button class="btn-secondary" :disabled="page <= 1" @click="page--">上一页</button>
            <span class="text-sm text-muted">第 {{ page }} 页 / 共 {{ Math.ceil(total / pageSize) }} 页</span>
            <button class="btn-secondary" :disabled="page * pageSize >= total" @click="page++">下一页</button>
          </div>
        </div>
      </template>
    </Transition>

    <ImageModal :src="modalSrc" :show="showModal" @close="showModal = false" />
  </div>
</template>
