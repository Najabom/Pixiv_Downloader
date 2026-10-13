import sys
import yaml
from pathlib import Path
from typing import List

from .models import Settings, WorkConfig, TagConfig, CPConfig

if getattr(sys, "frozen", False):
    PROJECT_ROOT = Path(sys.executable).parent
else:
    PROJECT_ROOT = Path(__file__).parent.parent


def load_settings() -> Settings:
    path = PROJECT_ROOT / "config" / "settings.yaml"
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    pixiv = data.get("pixiv", {})
    nsfw = data.get("nsfw", {})
    return Settings(
        download_dir=data.get("download_dir", "downloads"),
        max_search_pages=data.get("max_search_pages", 5),
        request_delay=data.get("request_delay", 2.0),
        max_retries=data.get("max_retries", 3),
        max_workers=data.get("max_workers", 3),
        nsfw_enabled=nsfw.get("enabled", False),
        nsfw_threshold=nsfw.get("threshold", 0.85),
        nsfw_device=nsfw.get("device", "cpu"),
        global_exclude_tags=data.get("global_exclude_tags", []),
        pixiv_refresh_token=pixiv.get("refresh_token", ""),
        pixiv_cookie_string=pixiv.get("cookie_string", ""),
    )


def _parse_tags(raw_tags: List) -> List[TagConfig]:
    result = []
    for item in raw_tags:
        if isinstance(item, str):
            result.append(TagConfig(folder=item))
        elif isinstance(item, dict):
            if "folder" in item:
                result.append(TagConfig(
                    folder=item["folder"],
                    tags=item.get("tags", []),
                    active=item.get("active", True),
                ))
            elif "name" in item:
                tags = list(item.get("search_tags", []))
                for alias in item.get("aliases", []):
                    if alias not in tags:
                        tags.append(alias)
                if item["name"] not in tags:
                    tags.insert(0, item["name"])
                result.append(TagConfig(
                    folder=item["name"],
                    tags=tags,
                    active=item.get("active", True),
                ))
    return result


def _parse_cp_tags(raw_cp: List) -> List[CPConfig]:
    result = []
    for item in raw_cp:
        if isinstance(item, dict):
            result.append(CPConfig(
                members=item.get("members", []),
                search_tags=item.get("search_tags", []),
            ))
    return result


def load_works() -> List[WorkConfig]:
    path = PROJECT_ROOT / "config" / "works.yaml"
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    works = []
    for w in data.get("works", []):
        works.append(WorkConfig(
            name=w["name"],
            search_tags=w.get("search_tags", []),
            exclude_tags=w.get("exclude_tags", []),
            tags=_parse_tags(w.get("tags", w.get("characters", []))),
            cp_tags=_parse_cp_tags(w.get("cp_tags", [])),
            active=w.get("active", True),
        ))
    return works


def save_works(works: List[WorkConfig]) -> None:
    path = PROJECT_ROOT / "config" / "works.yaml"

    def serialize_tag(t: TagConfig):
        if t.tags or not t.active:
            d = {"folder": t.folder}
            if t.tags:
                d["tags"] = t.tags
            if not t.active:
                d["active"] = False
            return d
        return t.folder

    def serialize_cp(cp: CPConfig):
        d = {"members": cp.members}
        if cp.search_tags:
            d["search_tags"] = cp.search_tags
        return d

    data = {
        "works": [
            {
                "name": w.name,
                "search_tags": w.search_tags,
                "tags": [serialize_tag(t) for t in w.tags],
                "cp_tags": [serialize_cp(cp) for cp in w.cp_tags] if w.cp_tags else [],
                "active": w.active,
            }
            for w in works
        ]
    }
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
