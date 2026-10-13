"""
下载历史重建工具 —— 从本地 downloads/ 目录重建 download_history.json
零 API 调用，纯本地扫描
"""
import sys
import json
import re
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from src.config_loader import load_settings, load_works
from src.organizer import sanitize

PROJECT_ROOT = Path(__file__).parent
HISTORY_PATH = PROJECT_ROOT / "data" / "download_history.json"


def extract_illust_id(filename: str) -> int | None:
    m = re.search(r"_(\d{6,})_", filename)
    return int(m.group(1)) if m else None


def extract_page_index(filename: str) -> int:
    m = re.search(r"_p(\d+)_", filename)
    if m:
        return int(m.group(1))
    m = re.search(r"_(\d{6,})_00_", filename)
    if m:
        return 0
    m = re.search(r"_(\d{6,})_(\d)(?:_横|_竖)", filename)
    if m:
        try:
            return int(m.group(2))
        except ValueError:
            pass
    return 0


def main():
    s = load_settings()
    works = load_works()
    dl_root = Path(s.download_dir)

    if not dl_root.exists():
        print(f"下载目录不存在: {dl_root}")
        return

    print("\n=== 下载历史重建工具 ===")
    print(f"扫描: {dl_root}")

    if HISTORY_PATH.exists():
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            history = json.load(f)
        print(f"现有记录: {sum(len(v) for v in history.values() if isinstance(v, list))} 条")
    else:
        history = {}

    # Build work name → sanitized name map
    work_map = {}
    for w in works:
        work_map[sanitize(w.name)] = w.name

    found = 0
    skipped = 0

    for work_dir in sorted(dl_root.iterdir()):
        if not work_dir.is_dir() or work_dir.name.startswith("_"):
            continue

        # Match work
        work_name = work_map.get(work_dir.name)
        if not work_name:
            print(f"\n  未知作品: [{work_dir.name}]")
            print(f"  现有作品:")
            for i, w in enumerate(works):
                print(f"    [{i + 1}] {w.name}")
            print(f"    [S] 跳过")
            choice = input("  映射到: ").strip()
            if choice.lower() == "s":
                continue
            try:
                i = int(choice) - 1
                if 0 <= i < len(works):
                    work_name = works[i].name
                    work_map[work_dir.name] = work_name
            except ValueError:
                continue

        if work_name not in history:
            history[work_name] = []
        pages_key = f"{work_name}_pages"
        if pages_key not in history:
            history[pages_key] = []

        existing_ids = set(history[work_name])
        existing_pages = set(history[pages_key])

        work_new = 0
        for img_file in work_dir.rglob("*"):
            if not img_file.is_file():
                continue
            if img_file.suffix.lower() not in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"):
                continue

            iid = extract_illust_id(img_file.name)
            if not iid:
                continue

            pg = extract_page_index(img_file.name)
            page_entry = f"{iid}_{pg}"

            if iid not in existing_ids:
                history[work_name].append(iid)
                existing_ids.add(iid)
                work_new += 1
            if page_entry not in existing_pages:
                history[pages_key].append(page_entry)
                existing_pages.add(page_entry)
                work_new += 1

        if work_new:
            print(f"  [{work_name}] +{work_new} 条")
            found += work_new
        else:
            skipped += 1

    if found == 0 and skipped > 0:
        print("  无新增，历史已是最新")
    else:
        HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print(f"\n重建完成: 新增 {found} 条记录")

    if not any(history.get(w.name) for w in works):
        # All empty
        pass

    try:
        input("\n按 Enter 退出...")
    except EOFError:
        pass


if __name__ == "__main__":
    main()
