import json
import time
from pathlib import Path
from typing import Set, Dict
from datetime import datetime

from .models import DownloadRecord
from .config_loader import PROJECT_ROOT


class MetadataManager:
    def __init__(self):
        self.history_path = PROJECT_ROOT / "data" / "download_history.json"
        self.work_records: Dict[str, Set[int]] = {}
        self.page_records: Dict[str, Set[str]] = {}
        self._load()

    def _load(self):
        if not self.history_path.exists():
            return
        for attempt in range(5):
            try:
                with open(self.history_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for key, value in data.items():
                    if key.endswith("_pages"):
                        self.page_records[key] = set(value)
                    else:
                        self.work_records[key] = set(value)
                return
            except (PermissionError, OSError):
                time.sleep(0.5)

    def _save(self):
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        combined = {}
        for k, v in self.work_records.items():
            combined[k] = sorted(list(v))
        for k, v in self.page_records.items():
            combined[k] = sorted(list(v))
        for attempt in range(5):
            try:
                with open(self.history_path, "w", encoding="utf-8") as f:
                    json.dump(combined, f, ensure_ascii=False, indent=2)
                return
            except (PermissionError, OSError):
                time.sleep(0.5)

    def is_downloaded(self, work_name: str, illust_id: int, page_index: int = 0) -> bool:
        pages_key = f"{work_name}_pages"
        page_id = f"{illust_id}_{page_index}"
        if pages_key in self.page_records:
            return page_id in self.page_records[pages_key]
        return False

    def all_pages_downloaded(self, work_name: str, illust_id: int, page_count: int) -> bool:
        pages_key = f"{work_name}_pages"
        if pages_key not in self.page_records:
            return False
        for p in range(page_count):
            if f"{illust_id}_{p}" not in self.page_records[pages_key]:
                return False
        return True

    def mark_downloaded(self, work_name: str, illust_id: int, page_index: int = 0):
        if work_name not in self.work_records:
            self.work_records[work_name] = set()
        self.work_records[work_name].add(illust_id)

        pages_key = f"{work_name}_pages"
        if pages_key not in self.page_records:
            self.page_records[pages_key] = set()
        self.page_records[pages_key].add(f"{illust_id}_{page_index}")
        self._save()

    @staticmethod
    def save_record_to_csv(record: DownloadRecord, csv_path: Path):
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        file_exists = csv_path.exists()
        for attempt in range(3):
            try:
                with open(csv_path, "a", encoding="utf-8", newline="") as f:
                    if not file_exists:
                        f.write("作品,图片名,标签,画师,多图编号,分辨率,横竖屏,来源,站内ID,下载时间\n")
                    f.write(record.to_csv_row() + "\n")
                return
            except (PermissionError, OSError):
                time.sleep(0.5 * (attempt + 1))
        # Silently fail — CSV is auxiliary, download data is in JSON
