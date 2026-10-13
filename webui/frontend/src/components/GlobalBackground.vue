<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { api } from '../api/client'

const bgUrl = ref('')
const showBg = ref(false)

watch(bgUrl, (url) => {
  showBg.value = false
  if (!url) return
  const img = new Image()
  img.onload = () => { showBg.value = true }
  img.onerror = () => { showBg.value = false }
  img.src = url
  if (img.complete) showBg.value = true
})

const loadBg = async () => {
  try {
    const config = await api.ui.get()
    const source = config.global_background_source || ''
    const res = await api.gallery.random(1, { source_folder: source })
    bgUrl.value = api.gallery.thumbUrl(res.paths[0], 1200) || ''
  } catch {
    bgUrl.value = ''
  }
}

onMounted(loadBg)
</script>

<template>
  <div class="fixed inset-0 z-0 pointer-events-none">
    <div
      v-show="bgUrl"
      class="absolute inset-0 bg-cover bg-center bg-no-repeat transition-opacity duration-1000 ease-lusion"
      :class="showBg ? 'opacity-50' : 'opacity-0'"
      :style="{ backgroundImage: `url(${bgUrl})` }"
    />
    <div class="absolute inset-0 bg-bg/75" />
  </div>
</template>
