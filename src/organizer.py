from pathlib import Path
from PIL import Image
from typing import Optional, List, Set, Tuple
from dataclasses import dataclass, field

from .models import TagConfig, CPConfig

INVALID_CHARS = '<>:"/\\|?*'
CONTROL_CHARS = ''.join(chr(i) for i in range(32)) + chr(127)


def sanitize(name: str) -> str:
    for c in INVALID_CHARS:
        name = name.replace(c, "_")
    for c in CONTROL_CHARS:
        name = name.replace(c, "_")
    return name.strip("_ ")


FORMAT_MAP = {"JPEG": ".jpg", "PNG": ".png", "GIF": ".gif", "WEBP": ".webp", "BMP": ".bmp"}

_nsfw_validated = False
_nsfw_device = "cpu"
_nsfw_warning = ""


def validate_nsfw_device(requested_device: str) -> str:
    global _nsfw_validated, _nsfw_device, _nsfw_warning
    _nsfw_validated = True
    _nsfw_device = "cpu"
    _nsfw_warning = ""

    import os
    if requested_device == "cuda":
        try:
            import tensorflow as tf
            gpus = tf.config.list_physical_devices("GPU")
            if gpus:
                os.environ.setdefault("CUDA_VISIBLE_DEVICES", "0")
                _nsfw_device = "cuda"
                return "cuda"
        except ImportError:
            _nsfw_warning = "TensorFlow 未安装，NSFW 降级为 CPU"
        except Exception as e:
            _nsfw_warning = f"TensorFlow CUDA 不可用 ({e})，NSFW 降级为 CPU"
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
        return "cpu"
    elif requested_device == "directml":
        try:
            import tensorflow as tf
            os.environ["TF_DIRECTML_MAX_ALLOC"] = "0"
            _nsfw_device = "directml"
            return "directml"
        except ImportError:
            _nsfw_warning = "TensorFlow 未安装，NSFW 降级为 CPU"
        except Exception as e:
            _nsfw_warning = f"TensorFlow DirectML 不可用 ({e})，NSFW 降级为 CPU"
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
        return "cpu"
    else:
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
        return "cpu"


def get_nsfw_device() -> str:
    return _nsfw_device


def get_nsfw_warning() -> str:
    return _nsfw_warning


def check_nsfw(filepath: Path) -> float:
    try:
        from opennsfw2 import predict_image
        return predict_image(str(filepath))
    except Exception:
        return -1.0


def get_image_info(filepath: Path):
    with Image.open(filepath) as img:
        w, h = img.size
        detected_format = img.format or ""
    resolution = f"{w}x{h}"
    orientation = "横" if w >= h else "竖"
    ext = FORMAT_MAP.get(detected_format.upper(), filepath.suffix.lower() or ".jpg")
    return w, h, resolution, orientation, ext


def generate_filename(
    title: str,
    artist: str,
    illust_id: int,
    page_index: int,
    orientation: str,
    ext: str,
) -> str:
    safe_title = sanitize(title)
    if len(safe_title) > 60:
        safe_title = safe_title[:60]
    safe_artist = sanitize(artist)
    page_str = f"p{page_index}" if page_index > 0 else "00"
    return f"{safe_title}_{safe_artist}_{illust_id}_{page_str}_{orientation}{ext}"


def generate_new_filename(
    title: str,
    artist: str,
    illust_id: int,
    page_index: int,
    orientation: str,
    ext: str,
) -> str:
    return "新_" + generate_filename(title, artist, illust_id, page_index, orientation, ext)


def get_target_dir(download_root: Path, work_name: str, tag: str) -> Path:
    safe_work = sanitize(work_name)
    safe_tag = sanitize(tag) if tag else "未分类"
    return download_root / safe_work / safe_tag


def _tag_matches(tag_config: TagConfig, illust_tags_lower: List[str], title_lower: str) -> bool:
    for name_lower, title_pattern in tag_config._compiled_patterns:
        for tag in illust_tags_lower:
            if tag == name_lower:
                return True
            if tag.startswith(name_lower + '('):
                return True
        if title_pattern.search(title_lower):
            return True
    return False


def detect_tag(illust_tags: List[str], title: str, tags: List[TagConfig]) -> Optional[str]:
    tags_lower = [t.lower() for t in illust_tags]
    title_lower = title.lower()
    for tag_config in tags:
        if _tag_matches(tag_config, tags_lower, title_lower):
            return tag_config.name
    return None


def classify_illust(
    illust_tags: List[str],
    title: str,
    work_tags: List[TagConfig],
    cp_configs: List[CPConfig],
) -> str:
    tags_lower = [t.lower() for t in illust_tags]
    title_lower = title.lower()

    detected: Set[str] = set()
    for tag_config in work_tags:
        if _tag_matches(tag_config, tags_lower, title_lower):
            detected.add(tag_config.name)

    matched_cps: List[CPConfig] = []
    for cp in cp_configs:
        for stag in cp.search_tags:
            if stag.lower() in tags_lower or stag.lower() in title_lower:
                matched_cps.append(cp)
                break

    if matched_cps:
        for cp in matched_cps:
            cp_set = set(cp.members)
            if cp_set.issubset(detected):
                if detected == cp_set:
                    return cp.name
                else:
                    return "多人图"


@dataclass
class ClassificationResult:
    category: str
    detected: Set[str] = field(default_factory=set)
    matched_cps: List[CPConfig] = field(default_factory=list)
    is_multi_page: bool = False

    @property
    def dir_category(self) -> str:
        if not self.is_multi_page:
            return self.category
        if self.category == "未分类":
            return "组图"
        return self.category

    @property
    def reason(self) -> str:
        if not self.detected:
            return "未匹配到任何配置标签"
        if self.matched_cps:
            for cp in self.matched_cps:
                if set(cp.members).issubset(self.detected):
                    if self.detected != set(cp.members):
                        extra = self.detected - set(cp.members)
                        return f"CP [{cp.name}] 成员已检测，但额外包含: {', '.join(extra)}"
                    return f"CP [{cp.name}] 成员完整匹配"
                return f"CP标签 [{cp.name}] 存在但角色标签不完整"
        if len(self.detected) == 1:
            return "单角色匹配"
        if len(self.detected) >= 2:
            detected_str = ", ".join(sorted(self.detected))
            cp_members = [set(cp.members) for cp in self.matched_cps]
            if any(s.issubset(self.detected) for s in cp_members):
                return f"多角色 [{detected_str}]，CP成员存在但非精确匹配"
            return f"多角色 [{detected_str}]，未配置对应CP"
        return "未知"


def classify_illust_full(
    illust_tags: List[str],
    title: str,
    work_tags: List[TagConfig],
    cp_configs: List[CPConfig],
) -> ClassificationResult:
    tags_lower = [t.lower() for t in illust_tags]
    title_lower = title.lower()

    detected: Set[str] = set()
    for tag_config in work_tags:
        if _tag_matches(tag_config, tags_lower, title_lower):
            detected.add(tag_config.name)

    matched_cps: List[CPConfig] = []
    for cp in cp_configs:
        for stag in cp.search_tags:
            if stag.lower() in tags_lower or stag.lower() in title_lower:
                matched_cps.append(cp)
                break

    result = ClassificationResult(category="", detected=detected, matched_cps=matched_cps)

    if matched_cps:
        for cp in matched_cps:
            cp_set = set(cp.members)
            if cp_set.issubset(detected):
                if detected == cp_set:
                    result.category = cp.name
                else:
                    result.category = "多人图"
                return result
        result.category = matched_cps[0].name
        return result

    if not detected:
        result.category = "未分类"
        return result

    if len(detected) == 1:
        result.category = list(detected)[0]
        return result

    for cp in cp_configs:
        if set(cp.members) == detected:
            result.category = cp.name
            return result

    result.category = "多人图"
    return result
