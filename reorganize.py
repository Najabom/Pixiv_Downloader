"""
重新整理已有下载文件 —— 按最新分类规则重新存放
用法: python reorganize.py          (交互选择预览/执行)
      python reorganize.py --work 原神 (仅处理指定作品)
"""
import sys
import re
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from src.config_loader import load_settings, load_works
from src.pixiv_client import PixivClient
from src.organizer import (
    classify_illust_full, generate_filename, get_target_dir, sanitize, get_image_info
)


def ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def extract_illust_id(filename: str) -> int | None:
    m = re.search(r"_(\d{6,})_", filename)
    return int(m.group(1)) if m else None


def main():
    work_filter = None
    if "--work" in sys.argv:
        try:
            idx = sys.argv.index("--work")
            work_filter = sys.argv[idx + 1]
        except (ValueError, IndexError):
            pass

    s = load_settings()
    works = load_works()
    c = PixivClient(cookie_string=s.pixiv_cookie_string, request_delay=s.request_delay)

    if not c.is_authenticated:
        print("登录失败")
        return

    dl_root = Path(s.download_dir)
    if not dl_root.exists():
        print(f"下载目录不存在: {dl_root}")
        return

    print("\n=== 图片整理工具 ===")
    print(f"下载目录: {dl_root}")
    print(f"作品数: {len(works)}")
    print(f"\n  [P] 预览模式 — 仅显示变动，不实际移动")
    print(f"  [E] 执行模式 — 实际移动文件")
    print(f"  [0] 取消")
    choice = input("\n请选择: ").strip().lower()

    if choice == "p":
        dry_run = True
        print("\n[预览模式] 仅显示变动，不实际移动\n")
    elif choice == "e":
        dry_run = False
        print("\n[执行模式] 将实际移动文件\n")
    else:
        print("已取消")
        return

    changes = 0
    skipped = 0
    failed = 0

    for work in works:
        if work_filter and work.name != work_filter:
            continue
        if not work.active and not work_filter:
            continue

        work_dir = dl_root / sanitize(work.name)
        if not work_dir.exists():
            continue

        print(f"\n[{ts()}] === 整理 [{work.name}] ===")

        files = list(work_dir.rglob("*"))
        illust_ids = set()
        for f in files:
            if f.is_file() and not f.name.startswith("_") and not f.name.endswith(".tsv") \
                    and not f.name.endswith(".txt") and not f.name.endswith(".csv"):
                iid = extract_illust_id(f.name)
                if iid:
                    illust_ids.add(iid)

        print(f"[{ts()}]   发现 {len(illust_ids)} 个作品")

        for idx, iid in enumerate(sorted(illust_ids), 1):
            try:
                print(f"[{ts()}]   [{idx}/{len(illust_ids)}] id={iid} ...", end=" ")
                # ... 不变部分 ...

                detail = c.get_illust_detail(iid)
                if not detail:
                    print("无详情")
                    failed += 1
                    continue

                info = c.parse_illust_info(detail)
                cr = classify_illust_full(info.tags, info.title, work.tags, work.cp_tags)
                cr.is_multi_page = info.page_count > 1

                new_cat = cr.dir_category
                if new_cat == "未分类" and info.page_count > 1:
                    new_cat = "组图"
                artist = info.artist_name or info.artist_account or "X"
                title = info.title or "untitled"

                old_files = [f for f in files if f.is_file() and str(iid) in f.name
                             and not f.name.startswith("_")]
                if not old_files:
                    print("无文件")
                    skipped += 1
                    continue

                old_dir = old_files[0].parent
                old_cat = old_dir.relative_to(work_dir).parts[0] if len(old_dir.relative_to(work_dir).parts) > 0 else ""

                new_dir = get_target_dir(dl_root, work.name, new_cat)
                if info.page_count > 1:
                    safe_title = sanitize(title)
                    if len(safe_title) > 40:
                        safe_title = safe_title[:40]
                    safe_artist = sanitize(artist)
                    new_dir = new_dir / f"{safe_title}_{safe_artist}_{iid}"

                if new_dir == old_dir:
                    print("无需移动")
                    skipped += 1
                    continue

                print(f"[{old_cat}] -> [{new_cat}]", end=" ")

                if not dry_run:
                    new_dir.mkdir(parents=True, exist_ok=True)
                    moved = 0
                    for f in old_files:
                        new_path = new_dir / f.name
                        counter = 1
                        while new_path.exists():
                            stem = f.stem
                            new_path = new_dir / f"{stem}_{counter}{f.suffix}"
                            counter += 1
                        f.rename(new_path)
                        moved += 1
                    if info.page_count > 1:
                        for sibling in old_dir.iterdir():
                            if sibling.is_dir() and str(iid) in sibling.name:
                                target_subdir = new_dir / sibling.name
                                if not target_subdir.exists() and sibling != new_dir:
                                    sibling.rename(target_subdir)
                    print(f"({moved} 文件)")
                else:
                    print()

                changes += 1
            except Exception as e:
                print(f"错误: {e}")
                failed += 1

        if not dry_run:
            removed = 0
            for dirpath in sorted(list(work_dir.rglob("*")), reverse=True):
                if dirpath.is_dir() and dirpath != work_dir:
                    try:
                        if not any(dirpath.iterdir()):
                            dirpath.rmdir()
                            removed += 1
                    except OSError:
                        pass
            if removed:
                print(f"[{ts()}]   清理空目录: {removed} 个")

    print(f"\n[{ts()}] === 完成 ===")
    print(f"  移动: {changes}, 跳过: {skipped}, 失败: {failed}")
    if dry_run:
        print("  (仅预览，未实际改动。选 [E] 执行模式可实际移动)")
    input("\n按 Enter 退出...")


if __name__ == "__main__":
    main()
