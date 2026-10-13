import { ref } from 'vue'
import { defineStore } from 'pinia'

interface LogEvent {
  type: 'log' | 'error' | 'done'
  message: string
}

export const useDownloadStore = defineStore('download', () => {
  const running = ref(false)
  const logs = ref<string[]>([])
  let eventSource: EventSource | null = null

  const connectStream = () => {
    if (eventSource) return
    const es = new EventSource('/api/download/stream')
    es.onmessage = (e) => {
      try {
        const data: LogEvent = JSON.parse(e.data)
        if (data.type === 'log' || data.type === 'error') {
          logs.value.push(data.message)
          if (logs.value.length > 500) logs.value.shift()
        }
        if (data.type === 'done' || data.type === 'error') {
          running.value = false
          es.close()
          eventSource = null
        }
      } catch {
        logs.value.push(e.data)
      }
    }
    es.onerror = () => {
      es.close()
      eventSource = null
      running.value = false
    }
    eventSource = es
  }

  const start = async () => {
    await fetch('/api/download/start', { method: 'POST' })
    running.value = true
    connectStream()
  }

  const stop = async () => {
    await fetch('/api/download/stop', { method: 'POST' })
    running.value = false
  }

  const fetchStatus = async () => {
    const res = await fetch('/api/download/status')
    const data = await res.json()
    running.value = data.running
    if (running.value) connectStream()
  }

  const clearLogs = () => {
    logs.value = []
  }

  return { running, logs, start, stop, fetchStatus, clearLogs }
})
