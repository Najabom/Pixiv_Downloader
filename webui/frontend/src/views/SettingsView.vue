<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { api } from '../api/client'
import type { Settings } from '../types'
import { Save, TestTube } from 'lucide-vue-next'

const settings = ref<Partial<Settings>>({})
const uiConfig = ref({ global_background_source: '' })
const loading = ref(true)
const saving = ref(false)
const savingUi = ref(false)
const testing = ref(false)
const cookieInput = ref('')

const globalTags = computed({
  get: () => (settings.value.global_exclude_tags || []).join('\n'),
  set: (val: string) => {
    settings.value.global_exclude_tags = val
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean)
  },
})

onMounted(async () => {
  settings.value = await api.settings.get()
  cookieInput.value = settings.value.pixiv_cookie_string || ''
  uiConfig.value = await api.ui.get()
  loading.value = false
})

const save = async () => {
  saving.value = true
  const payload = { ...settings.value }
  delete payload.pixiv_cookie_string
  delete payload.pixiv_refresh_token
  await api.settings.update(payload)
  saving.value = false
}

const saveCookie = async () => {
  await api.settings.updateCookie(cookieInput.value)
}

const saveUiConfig = async () => {
  savingUi.value = true
  await api.ui.update(uiConfig.value)
  savingUi.value = false
}

const testLogin = async () => {
  testing.value = true
  const res = await api.settings.testLogin()
  alert(res.authenticated ? '登录有效' : '登录失效，请检查 Cookie/Token')
  testing.value = false
}
</script>

<template>
  <div>
    <header class="mb-8">
      <h1 class="text-3xl font-bold mb-1">设置</h1>
      <p class="text-muted">管理登录信息、下载参数与过滤规则</p>
    </header>

    <div v-if="loading" class="card h-96 animate-pulse bg-text-muted/5" />

    <div v-else class="space-y-6">
      <!-- Pixiv Auth -->
      <section class="card p-6">
        <h2 class="text-lg font-bold mb-4">Pixiv 登录</h2>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium mb-2">Cookie String</label>
            <textarea
              v-model="cookieInput"
              rows="4"
              class="input font-mono text-xs"
              placeholder="粘贴浏览器 Cookie 整行"
            />
          </div>
          <div class="flex gap-3">
            <button class="btn-primary" @click="saveCookie">
              <Save class="w-4 h-4" /> 保存 Cookie
            </button>
            <button class="btn-secondary" :disabled="testing" @click="testLogin">
              <TestTube class="w-4 h-4" /> 测试登录
            </button>
          </div>
        </div>
      </section>

      <!-- Download -->
      <section class="card p-6">
        <h2 class="text-lg font-bold mb-4">下载参数</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label class="block text-sm font-medium mb-2">下载目录</label>
            <input v-model="settings.download_dir" class="input" />
          </div>
          <div>
            <label class="block text-sm font-medium mb-2">请求间隔（秒）</label>
            <input
              v-model.number="settings.request_delay"
              type="number"
              step="0.1"
              min="0.5"
              class="input"
            />
          </div>
          <div>
            <label class="block text-sm font-medium mb-2">最大搜索页数</label>
            <input v-model.number="settings.max_search_pages" type="number" min="1" class="input" />
          </div>
          <div>
            <label class="block text-sm font-medium mb-2">失败重试次数</label>
            <input v-model.number="settings.max_retries" type="number" min="0" class="input" />
          </div>
        </div>
      </section>

      <!-- NSFW -->
      <section class="card p-6">
        <h2 class="text-lg font-bold mb-4">NSFW 检测</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-5 items-end">
          <div class="flex items-center gap-3">
            <input
              id="nsfw"
              v-model="settings.nsfw_enabled"
              type="checkbox"
              class="w-5 h-5 rounded border-text-muted/30 text-primary focus:ring-primary"
            />
            <label for="nsfw" class="font-medium">启用检测</label>
          </div>
          <div>
            <label class="block text-sm font-medium mb-2">阈值（0~1）</label>
            <input
              v-model.number="settings.nsfw_threshold"
              type="number"
              step="0.01"
              min="0"
              max="1"
              class="input"
            />
          </div>
          <div>
            <label class="block text-sm font-medium mb-2">推理设备</label>
            <select v-model="settings.nsfw_device" class="input">
              <option value="cpu">CPU</option>
              <option value="cuda">CUDA</option>
              <option value="directml">DirectML</option>
            </select>
          </div>
        </div>
      </section>

      <!-- Global Filter -->
      <section class="card p-6">
        <h2 class="text-lg font-bold mb-4">全局过滤标签</h2>
        <textarea
          v-model="globalTags"
          rows="3"
          class="input font-mono text-sm"
          placeholder="每行一个标签"
        />
        <p class="text-xs text-muted mt-2">用换行分隔，保存后会自动写入 settings.yaml</p>
      </section>

      <!-- Global Background -->
      <section class="card p-6">
        <h2 class="text-lg font-bold mb-4">全局背景</h2>
        <div>
          <label class="block text-sm font-medium mb-2"
            >来源文件夹（相对 downloads/，留空为全部）</label
          >
          <input
            v-model="uiConfig.global_background_source"
            class="input"
            placeholder="例如：魔法少女的魔女审判/黑部奈叶香x宝生玛格"
          />
          <p class="text-xs text-muted mt-2">只使用横屏图片，忽略组图；刷新页面后生效</p>
        </div>
        <div class="flex justify-end mt-4">
          <button class="btn-primary" :disabled="savingUi" @click="saveUiConfig">
            <Save class="w-4 h-4" /> {{ savingUi ? '保存中...' : '保存背景设置' }}
          </button>
        </div>
      </section>

      <div class="flex justify-end">
        <button class="btn-primary px-8" :disabled="saving" @click="save">
          <Save class="w-4 h-4" /> {{ saving ? '保存中...' : '保存设置' }}
        </button>
      </div>
    </div>
  </div>
</template>
