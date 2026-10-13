export interface TagConfig {
  folder: string
  tags: string[]
  active: boolean
}

export interface CPConfig {
  members: string[]
  search_tags: string[]
  name: string
}

export interface Work {
  name: string
  search_tags: string[]
  tags: TagConfig[]
  cp_tags: CPConfig[]
  exclude_tags: string[]
  active: boolean
}

export interface Settings {
  download_dir: string
  max_search_pages: number
  request_delay: number
  max_retries: number
  max_workers: number
  nsfw_enabled: boolean
  nsfw_threshold: number
  nsfw_device: string
  global_exclude_tags: string[]
  global_background_source: string
  pixiv_refresh_token: string
  pixiv_cookie_string: string
}

export interface GalleryItem {
  path: string
  name: string
  work: string
  category: string
  size_mb: number
  width: number | null
  height: number | null
  modified: number
}

export interface Stats {
  work_count: number
  tag_count: number
  cp_count: number
  total_downloads: number
  total_storage_mb: number
}

export interface GalleryResponse {
  items: GalleryItem[]
  total: number
  page: number
  page_size: number
}
