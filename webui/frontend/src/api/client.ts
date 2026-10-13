import type { Stats, Work, TagConfig, CPConfig, Settings, GalleryResponse } from '../types'

const API_BASE = ''

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, options)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: '请求失败' }))
    throw new Error(err.detail || '请求失败')
  }
  return res.json()
}

export const api = {
  stats: () => request<Stats>('/api/stats/'),

  works: {
    list: () => request<Work[]>('/api/works/'),
    create: (name: string) =>
      request<Work>('/api/works/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
      }),
    rename: (name: string, newName: string) =>
      request<Work>(`/api/works/${encodeURIComponent(name)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_name: newName }),
      }),
    delete: (name: string) =>
      request<{ ok: boolean }>(`/api/works/${encodeURIComponent(name)}`, { method: 'DELETE' }),
    toggle: (name: string) =>
      request<Work>(`/api/works/${encodeURIComponent(name)}/toggle`, { method: 'PATCH' }),
    updateExcludeTags: (name: string, tags: string[]) =>
      request<Work>(`/api/works/${encodeURIComponent(name)}/exclude-tags`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tags }),
      }),

    tags: {
      list: (name: string) => request<TagConfig[]>(`/api/works/${encodeURIComponent(name)}/tags`),
      add: (name: string, folder: string, tags: string[]) =>
        request<TagConfig>(`/api/works/${encodeURIComponent(name)}/tags`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ folder, tags }),
        }),
      update: (name: string, folder: string, payload: { tags?: string[]; active?: boolean }) =>
        request<TagConfig>(
          `/api/works/${encodeURIComponent(name)}/tags/${encodeURIComponent(folder)}`,
          {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
          },
        ),
      delete: (name: string, folder: string) =>
        request<{ ok: boolean }>(
          `/api/works/${encodeURIComponent(name)}/tags/${encodeURIComponent(folder)}`,
          {
            method: 'DELETE',
          },
        ),
    },

    cpTags: {
      list: (name: string) => request<CPConfig[]>(`/api/works/${encodeURIComponent(name)}/cp-tags`),
      add: (name: string, members: string[], searchTags: string[]) =>
        request<CPConfig>(`/api/works/${encodeURIComponent(name)}/cp-tags`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ members, search_tags: searchTags }),
        }),
      delete: (name: string, index: number) =>
        request<{ ok: boolean }>(`/api/works/${encodeURIComponent(name)}/cp-tags/${index}`, {
          method: 'DELETE',
        }),
    },
  },

  settings: {
    get: () => request<Settings>('/api/settings/'),
    update: (payload: Partial<Settings>) =>
      request<Settings>('/api/settings/', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }),
    updateCookie: (cookieString: string) =>
      request<Settings>('/api/settings/cookie', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cookie_string: cookieString }),
      }),
    testLogin: () =>
      request<{ authenticated: boolean }>('/api/settings/test-login', { method: 'POST' }),
  },

  gallery: {
    list: (params?: Record<string, string | number>) => {
      const qs = new URLSearchParams(params as Record<string, string>).toString()
      return request<GalleryResponse>(`/api/gallery/?${qs}`)
    },
    works: () => request<{ works: string[] }>('/api/gallery/works'),
    categories: (work: string) =>
      request<{ categories: string[] }>(`/api/gallery/categories?work=${encodeURIComponent(work)}`),
    subfolders: (work: string, category: string) =>
      request<{ subfolders: string[] }>(
        `/api/gallery/subfolders?work=${encodeURIComponent(work)}&category=${encodeURIComponent(category)}`,
      ),
    random: (count = 1, options?: { work?: string; category?: string; source_folder?: string }) => {
      const qs = new URLSearchParams()
      qs.set('count', String(count))
      if (options?.work) qs.set('work', options.work)
      if (options?.category) qs.set('category', options.category)
      if (options?.source_folder) qs.set('source_folder', options.source_folder)
      return request<{ paths: string[]; urls: string[] }>(`/api/gallery/random?${qs.toString()}`)
    },
    refresh: () => request<{ count: number }>('/api/gallery/refresh'),
    dashboardBackgrounds: () =>
      request<{
        work_bg: string | null
        tag_bg: string | null
        cp_bg: string | null
        download_bg: string | null
        storage_bg: string | null
      }>('/api/gallery/dashboard-backgrounds'),
    imageUrl: (path: string) => `/api/gallery/image?path=${encodeURIComponent(path)}`,
    thumbUrl: (path: string | undefined, width = 400) =>
      path ? `/api/gallery/thumb?path=${encodeURIComponent(path)}&width=${width}` : '',
  },

  download: {
    start: () => request<{ status: string }>('/api/download/start', { method: 'POST' }),
    stop: () => request<{ status: string }>('/api/download/stop', { method: 'POST' }),
    status: () => request<{ running: boolean }>('/api/download/status'),
  },

  ui: {
    get: () => request<{ global_background_source: string }>('/api/ui/'),
    update: (payload: { global_background_source: string }) =>
      request<{ global_background_source: string }>('/api/ui/', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }),
  },
}
