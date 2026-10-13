from typing import List, Optional
from pydantic import BaseModel


class TagConfigOut(BaseModel):
    folder: str
    tags: List[str]
    active: bool


class CPConfigOut(BaseModel):
    members: List[str]
    search_tags: List[str]
    name: str


class WorkOut(BaseModel):
    name: str
    search_tags: List[str]
    tags: List[TagConfigOut]
    cp_tags: List[CPConfigOut]
    exclude_tags: List[str]
    active: bool


class WorkCreate(BaseModel):
    name: str


class WorkRename(BaseModel):
    new_name: str


class TagCreate(BaseModel):
    folder: str
    tags: List[str] = []


class TagUpdate(BaseModel):
    tags: Optional[List[str]] = None
    active: Optional[bool] = None


class CPCreate(BaseModel):
    members: List[str]
    search_tags: List[str] = []


class SettingsOut(BaseModel):
    download_dir: str
    max_search_pages: int
    request_delay: float
    max_retries: int
    max_workers: int
    nsfw_enabled: bool
    nsfw_threshold: float
    nsfw_device: str
    global_exclude_tags: List[str]
    pixiv_refresh_token: str
    pixiv_cookie_string: str


class SettingsUpdate(BaseModel):
    download_dir: Optional[str] = None
    max_search_pages: Optional[int] = None
    request_delay: Optional[float] = None
    max_retries: Optional[int] = None
    max_workers: Optional[int] = None
    nsfw_enabled: Optional[bool] = None
    nsfw_threshold: Optional[float] = None
    nsfw_device: Optional[str] = None
    global_exclude_tags: Optional[List[str]] = None


class CookieUpdate(BaseModel):
    cookie_string: str


class StatsOut(BaseModel):
    work_count: int
    tag_count: int
    cp_count: int
    total_downloads: int
    total_storage_mb: float


class GalleryItem(BaseModel):
    path: str
    name: str
    work: str
    category: str
    size_mb: float
    width: Optional[int] = None
    height: Optional[int] = None
    modified: float


class ExcludeTagsUpdate(BaseModel):
    tags: List[str]
