import re
from dataclasses import dataclass, field
from typing import List


@dataclass
class Settings:
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


@dataclass
class TagConfig:
    folder: str
    tags: List[str] = field(default_factory=list)
    active: bool = True
    _compiled_patterns: list = field(default_factory=list, repr=False)

    def __post_init__(self):
        candidates = self.tags if self.tags else [self.folder]
        self._compiled_patterns = []
        for name in candidates:
            nl = name.lower()
            self._compiled_patterns.append((
                nl,
                re.compile(
                    r'(?:^|[^a-zA-Z0-9\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff])'
                    + re.escape(nl) +
                    r'(?:$|[^a-zA-Z0-9\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff])'
                ),
            ))

    @property
    def name(self) -> str:
        return self.folder

    def all_match_names(self) -> List[str]:
        return self.tags if self.tags else [self.folder]

    def effective_search_tags(self, work_name: str = "") -> List[str]:
        return self.tags if self.tags else [self.folder]


@dataclass
class CPConfig:
    members: List[str]
    search_tags: List[str] = field(default_factory=list)

    @property
    def name(self) -> str:
        return "x".join(self.members)


@dataclass
class WorkConfig:
    name: str
    search_tags: List[str]
    tags: List[TagConfig]
    exclude_tags: List[str] = field(default_factory=list)
    cp_tags: List[CPConfig] = field(default_factory=list)
    active: bool = True

    @property
    def all_search_tags(self) -> List[str]:
        result = []
        for t in self.tags:
            result.extend(t.effective_search_tags(self.name))
        for cp in self.cp_tags:
            result.extend(cp.search_tags)
        if not result:
            result.extend(self.search_tags)
        return result


@dataclass
class IllustInfo:
    illust_id: int
    title: str
    artist_name: str
    artist_account: str
    tags: List[str]
    page_count: int
    width: int
    height: int
    illust_type: str

    @property
    def orientation(self) -> str:
        return "横" if self.width >= self.height else "竖"


@dataclass
class DownloadRecord:
    work_name: str
    image_name: str
    tag: str
    artist: str
    page_index: int
    resolution: str
    orientation: str
    source: str
    illust_id: int
    download_time: str

    def to_csv_row(self) -> str:
        return (
            f"{self.work_name},{self.image_name},{self.tag},{self.artist},"
            f"{self.page_index},{self.resolution},{self.orientation},"
            f"{self.source},{self.illust_id},{self.download_time}"
        )
