<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { useDownloadStore } from '../stores/download'
import { Play, Square, Trash2 } from 'lucide-vue-next'

const download = useDownloadStore()
const logContainer = ref<HTMLElement | null>(null)
const autoScroll = ref(true)

const scrollToBottom = async () => {
  if (!autoScroll.value || !logContainer.value) return
  await nextTick()
  logContainer.value.scrollTop = logContainer.value.scrollHeight
}

onMounted(() => {
  download.fetchStatus()
})

watch(() => download.logs.length, scrollToBottom)
</script>

<template>
  <div>
    <header class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
      <div>
        <h1 class="text-3xl font-bold mb-1">下载日志</h1>
        <p class="text-muted">实时查看下载进度与输出</p>
      </div>
      <div class="flex items-center gap-3">
        <button v-if="!download.running" class="btn-primary" @click="download.start">
          <Play class="w-4 h-4" /> 开始下载
        </button>
        <button
          v-else
          class="btn-secondary text-danger border-danger/30 hover:bg-danger/10"
          @click="download.stop"
        >
          <Square class="w-4 h-4" /> 停止
        </button>
        <button class="btn-secondary" @click="download.clearLogs">
          <Trash2 class="w-4 h-4" /> 清空
        </button>
      </div>
    </header>

    <div class="card overflow-hidden flex flex-col h-[calc(100vh-260px)] bg-surface/80 backdrop-blur-md">
      <div
        class="flex items-center justify-between px-4 py-3 border-b border-text-muted/10 bg-bg/50"
      >
        <div class="flex items-center gap-2">
          <div
            class="w-2 h-2 rounded-full"
            :class="download.running ? 'bg-success animate-pulse-dot' : 'bg-text-muted/30'"
          />
          <span class="text-sm font-medium">{{ download.running ? '运行中' : '已停止' }}</span>
        </div>
        <label class="flex items-center gap-2 text-sm text-muted cursor-pointer">
          <input v-model="autoScroll" type="checkbox" class="rounded border-text-muted/30" />
          自动滚动
        </label>
      </div>
      <div
        ref="logContainer"
        class="flex-1 overflow-y-auto p-4 font-mono text-sm space-y-1 bg-bg/30"
      >
        <div
          v-for="(log, idx) in download.logs"
          :key="idx"
          class="text-text-main/90 whitespace-pre-wrap break-all"
        >
          {{ log }}
        </div>
        <div v-if="download.logs.length === 0" class="text-muted text-center py-12">
          暂无日志，点击“开始下载”运行任务
        </div>
      </div>
    </div>
  </div>
</template>
