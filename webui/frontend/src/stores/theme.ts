import { computed, ref, watch } from 'vue'
import { defineStore } from 'pinia'

export type ThemeMode = 'auto' | 'light' | 'dark'

const media = window.matchMedia('(prefers-color-scheme: dark)')

export const useThemeStore = defineStore('theme', () => {
  const mode = ref<ThemeMode>(readMode())
  const systemDark = ref(media.matches)

  const isDark = computed(() =>
    mode.value === 'auto' ? systemDark.value : mode.value === 'dark'
  )

  function readMode(): ThemeMode {
    const saved = localStorage.getItem('theme')
    if (saved === 'light' || saved === 'dark' || saved === 'auto') return saved
    return 'auto'
  }

  const apply = () => {
    document.documentElement.classList.toggle('dark', isDark.value)
    localStorage.setItem('theme', mode.value)
  }

  watch([mode, systemDark], apply)

  const init = () => {
    media.addEventListener('change', (e) => {
      systemDark.value = e.matches
    })
    apply()
  }

  const cycle = () => {
    mode.value = mode.value === 'auto' ? 'light' : mode.value === 'light' ? 'dark' : 'auto'
  }

  return { mode, isDark, init, cycle }
})
