<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { Component } from 'vue'
import { Library, Tags, Users, Image as ImageIcon, HardDrive } from 'lucide-vue-next'

const props = defineProps<{
  title: string
  value: number | undefined
  icon: string
  loading?: boolean
  background?: string
}>()

const icons: Record<string, Component> = { Library, Tags, Users, ImageIcon, HardDrive }
const Icon = computed(() => icons[props.icon] || Library)
const displayValue = computed(() => (props.value ?? 0).toLocaleString())

const showBg = ref(false)

watch(
  () => props.background,
  (url) => {
    showBg.value = false
    if (!url) return
    const img = new Image()
    img.onload = () => { showBg.value = true }
    img.onerror = () => { showBg.value = false }
    img.src = url
    if (img.complete) showBg.value = true
  },
  { immediate: true },
)
</script>

<template>
  <div
    class="card card-hover p-6 relative overflow-hidden min-h-[140px]"
    :class="!background ? 'bg-text-muted/5' : ''"
  >
    <div
      v-show="background"
      class="absolute inset-0 bg-cover bg-center transition-opacity duration-1000 ease-lusion"
      :class="showBg ? 'opacity-35' : 'opacity-0'"
      :style="{ backgroundImage: `url(${background})` }"
    />
    <div class="absolute inset-0 bg-gradient-to-t from-surface via-surface/95 to-surface/80" />
    <div class="relative z-10">
      <div class="flex items-start justify-between mb-4">
        <div class="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
          <component :is="Icon" class="w-5 h-5" />
        </div>
        <div v-if="loading" class="w-8 h-4 rounded bg-text-muted/10 animate-pulse" />
      </div>
      <div class="text-3xl font-bold mb-1">{{ displayValue }}</div>
      <div class="text-sm text-muted">{{ title }}</div>
    </div>
  </div>
</template>
