"""
断点重建工具 —— 从已有下载记录重建 tag_checkpoint.json
不从零搜索，不重复下载，给断点填充已有 illust 数据
"""
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from src.config_loader import load_settings, load_works

PROJECT_ROOT = Path(__file__).parent
HISTORY_PATH = PROJECT_ROOT / "data" / "download_history.json"
CKPT_PATH = PROJECT_ROOT / "data" / "tag_checkpoint.json"


def main():
    if not HISTORY_PATH.exists():
        print("download_history.json 不存在，无法重建")
        return

    with open(HISTORY_PATH, "r", encoding="utf-8") as f:
        history = json.load(f)

    works = load_works()

    if CKPT_PATH.exists():
        with open(CKPT_PATH, "r", encoding="utf-8") as f:
            checkpoint = json.load(f)
    else:
        checkpoint = {}

    migrated = 0
    skipped = 0

    for work in works:
        work_dl_ids = set(history.get(work.name, []))
        work_pages = history.get(f"{work.name}_pages", [])
        if not work_dl_ids:
            continue

        # Build page_count map from _pages entries
        page_map = {}
        for entry in work_pages:
            parts = entry.rsplit("_", 1)
            if len(parts) == 2:
                try:
                    iid = int(parts[0])
                    pg = int(parts[1])
                    if iid not in page_map or pg > page_map[iid]:
                        page_map[iid] = pg
                except ValueError:
                    pass

        # Collect all search tags for this work
        search_tags = []
        for t in work.tags:
            search_tags.extend(t.effective_search_tags(work.name))
        for cp in work.cp_tags:
            search_tags.extend(cp.search_tags)

        for stag in set(search_tags):
            tag_key = f"{work.name}|{stag}"
            existing = checkpoint.get(tag_key, {}).get("illusts", {})

            illusts = dict(existing)  # Preserve existing entries
            new_count = 0
            for iid in work_dl_ids:
                iid_str = str(iid)
                if iid_str not in illusts:
                    pages = page_map.get(iid, 0) + 1  # +1 because page_map stores max index
                    illusts[iid_str] = {"p": pages}
                    new_count += 1

            if new_count > 0 or not checkpoint.get(tag_key):
                stored = dict(checkpoint.get(tag_key, {}))
                stored["illusts"] = illusts
                if "total" not in stored or stored["total"] == 0:
                    stored.setdefault("total", 0)
                    stored.setdefault("last_page", 0)
                    stored.setdefault("completed", False)
                checkpoint[tag_key] = stored
                migrated += new_count
            else:
                skipped += 1

    CKPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CKPT_PATH, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, ensure_ascii=False, indent=2)

    print(f"重建完成: 新增 {migrated} 条 illust 记录到断点")
    print(f"已有记录的 tag: {skipped} 个（跳过）")
    print(f"\n下次下载时: 已下载图会被断点认出，不重复搜索也不重复下载")
    try:
        input("\n按 Enter 退出...")
    except EOFError:
        pass


if __name__ == "__main__":
    main()
