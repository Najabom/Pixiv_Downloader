import os
import random
import time
from pathlib import Path
from typing import List, Optional, Dict, Set
from PIL import Image

from src.config_loader import PROJECT_ROOT, load_settings

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}

_image_index: Dict[str, dict] = {}
_index_mtime: float = 0.0


def get_download_root() -> Path:
    settings = load_settings()
    path = Path(settings.download_dir)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def safe_path(relative: str) -> Optional[Path]:
    root = get_download_root()
    try:
        target = (root / relative).resolve()
        if str(target).startswith(str(root.resolve())):
            return target
    except Exception:
        pass
    return None


def _is_horizontal(filename: str) -> bool:
    return "横" in filename


def _is_gallery_group(rel_parts: List[str]) -> bool:
    # 路径结构: 作品/分类/图片 (深度 3)
    # 组图结构: 作品/分类/子文件夹/图片 (深度 >= 4)
    return len(rel_parts) >= 4


def refresh_index() -> int:
    global _image_index, _index_mtime
    root = get_download_root()
    index: Dict[str, dict] = {}

    if root.exists():
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in IMAGE_EXTS:
                continue
            if path.name.startswith("_"):
                continue
            try:
                rel = path.relative_to(root)
            except ValueError:
                continue
            parts = rel.parts
            if len(parts) < 2:
                continue
            rel_str = str(rel).replace("\\", "/")
            st = path.stat()
            index[rel_str] = {
                "path": rel_str,
                "name": path.name,
                "work": parts[0],
                "category": parts[1] if len(parts) >= 2 else "",
                "parts": parts,
                "modified": st.st_mtime,
                "size": st.st_size,
            }

    _image_index = index
    _index_mtime = time.time()
    return len(index)


def get_index() -> Dict[str, dict]:
    global _image_index
    if not _image_index:
        refresh_index()
    return _image_index


def _filter_images(
    horizontal_only: bool = True,
    ignore_gallery_groups: bool = True,
    work: Optional[str] = None,
    category: Optional[str] = None,
    source_folder: Optional[str] = None,
) -> List[dict]:
    index = get_index()
    root = get_download_root()
    candidates = []

    source_root = None
    if source_folder:
        source_root = (root / source_folder).resolve()

    for item in index.values():
        parts = item["parts"]

        if source_root:
            item_path = (root / item["path"]).resolve()
            try:
                if not str(item_path).startswith(str(source_root)):
                    continue
            except Exception:
                continue

        if work and item["work"] != work:
            continue
        if category and item["category"] != category:
            continue
        if horizontal_only and not _is_horizontal(item["name"]):
            continue
        if ignore_gallery_groups and _is_gallery_group(parts):
            continue

        candidates.append(item)

    return candidates


def get_random_images(
    count: int = 1,
    horizontal_only: bool = True,
    ignore_gallery_groups: bool = True,
    work: Optional[str] = None,
    category: Optional[str] = None,
    source_folder: Optional[str] = None,
) -> List[str]:
    # Try strict filters first; if no match, progressively relax constraints
    for h_only, ignore_g in [
        (horizontal_only, ignore_gallery_groups),
        (False, ignore_gallery_groups),
        (False, False),
    ]:
        candidates = _filter_images(h_only, ignore_g, work, category, source_folder)
        if candidates:
            break

    if not candidates:
        return []
    if len(candidates) <= count:
        return [item["path"] for item in candidates]
    chosen = random.sample(candidates, count)
    return [item["path"] for item in chosen]


def get_dashboard_backgrounds() -> dict:
    index = get_index()
    if not index:
        return {}

    def pick(items: List[dict]) -> Optional[str]:
        if not items:
            return None
        return random.choice(items)["path"]

    all_items = list(index.values())
    non_group = [i for i in all_items if not _is_gallery_group(i["parts"])]
    horizontal = [i for i in non_group if _is_horizontal(i["name"])]

    # 按 (work, category) 聚合具体分类
    tag_categories: Dict[tuple, List[dict]] = {}
    cp_categories: Dict[tuple, List[dict]] = {}

    for item in horizontal:
        work = item["work"]
        category = item["category"]
        if category in {"未分类", "多人图", "组图"}:
            continue
        key = (work, category)
        if "x" in category:
            cp_categories.setdefault(key, []).append(item)
        else:
            tag_categories.setdefault(key, []).append(item)

    # 作品背景：随机选一个作品，从该作品下选
    works_with_images = list({i["work"] for i in horizontal})
    work_bg = None
    if works_with_images:
        chosen_work = random.choice(works_with_images)
        work_bg = pick([i for i in horizontal if i["work"] == chosen_work])

    # 角色背景：随机选一个具体角色分类
    tag_bg = None
    if tag_categories:
        tag_bg = pick(tag_categories[random.choice(list(tag_categories.keys()))])

    # CP 背景：随机选一个具体 CP 分类
    cp_bg = None
    if cp_categories:
        cp_bg = pick(cp_categories[random.choice(list(cp_categories.keys()))])

    return {
        "work_bg": work_bg,
        "tag_bg": tag_bg,
        "cp_bg": cp_bg,
        "download_bg": pick(horizontal),
        "storage_bg": pick(horizontal),
    }


def get_works() -> List[str]:
    index = get_index()
    works: Set[str] = set()
    for item in index.values():
        works.add(item["work"])
    return sorted(works)


def get_categories(work: str) -> List[str]:
    index = get_index()
    categories: Set[str] = set()
    for item in index.values():
        if item["work"] == work:
            categories.add(item["category"])
    return sorted(categories)


def get_gallery_subfolders(work: str, category: str) -> List[str]:
    index = get_index()
    subfolders: Set[str] = set()
    for item in index.values():
        parts = item["parts"]
        if item["work"] == work and item["category"] == category and len(parts) >= 4:
            subfolders.add(parts[2])
    return sorted(subfolders)


def list_gallery(
    work: Optional[str] = None,
    category: Optional[str] = None,
    subfolder: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    horizontal_only: bool = False,
    ignore_gallery_groups: bool = False,
) -> tuple:
    index = get_index()
    candidates = []

    for item in index.values():
        parts = item["parts"]
        if work and item["work"] != work:
            continue
        if category and item["category"] != category:
            continue
        if subfolder and (len(parts) < 4 or parts[2] != subfolder):
            continue
        if horizontal_only and not _is_horizontal(item["name"]):
            continue
        if ignore_gallery_groups and _is_gallery_group(parts):
            continue

        candidates.append({
            **item,
            "size_mb": round(item["size"] / (1024 * 1024), 2) if item.get("size") else 0,
            "width": None,
            "height": None,
        })

    candidates.sort(key=lambda x: x["modified"], reverse=True)
    total = len(candidates)
    start = (page - 1) * page_size
    return candidates[start:start + page_size], total


def calculate_storage() -> float:
    index = get_index()
    total = sum(item.get("size", 0) for item in index.values())
    return round(total / (1024 * 1024), 2)


THUMB_DIR = Path(__file__).parent.parent / "thumbnails"


def get_thumbnail_path(relative: str, width: int = 400) -> Optional[Path]:
    src = safe_path(relative)
    if not src or not src.exists():
        return None

    import hashlib
    key = hashlib.md5(f"{relative}|{width}".encode()).hexdigest()
    thumb_path = THUMB_DIR / f"{key}.webp"
    if thumb_path.exists():
        return thumb_path

    try:
        from PIL import Image
        THUMB_DIR.mkdir(parents=True, exist_ok=True)
        with Image.open(src) as img:
            img = img.convert("RGB")
            ratio = width / img.width
            height = int(img.height * ratio)
            img = img.resize((width, height), Image.LANCZOS)
            img.save(thumb_path, "WEBP", quality=80)
        return thumb_path
    except Exception:
        return None
