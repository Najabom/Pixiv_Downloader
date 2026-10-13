"""
清理散放的组图重复文件。
规则：若某个目录下同时存在
  - 子文件夹： 标题_画师_作品ID/
  - 散放文件： 标题_画师_作品ID_00_横.jpg / _p1_竖.png 等
则散放文件是旧 bug 产生的重复副本，可以安全删除。
"""

import re
import os
import sys
from pathlib import Path

PATTERN = re.compile(r'_(\d+)_(?:00|p\d+)_[横竖]')


def scan_duplicates(root: Path):
    """遍历 root，返回 (重复散放文件路径, 对应子文件夹路径) 列表。"""
    duplicates = []
    for dirpath, dirnames, filenames in os.walk(root):
        subfolder_ids = {}
        for d in dirnames:
            parts = d.rsplit('_', 1)
            if len(parts) == 2 and parts[1].isdigit():
                subfolder_ids[parts[1]] = d

        for filename in filenames:
            m = PATTERN.match(filename)
            if not m:
                continue
            illust_id = m.group(1)
            if illust_id not in subfolder_ids:
                continue
            subfolder_name = subfolder_ids[illust_id]
            if dirpath.name == subfolder_name:
                continue

            file_path = Path(dirpath) / filename
            subfolder_path = Path(dirpath) / subfolder_name
            duplicates.append((file_path, subfolder_path))
    return duplicates


PAUSE_TO_EXIT = True


def _pause():
    if PAUSE_TO_EXIT:
        input("\n按回车键退出...")


def main():
    global PAUSE_TO_EXIT

    if len(sys.argv) < 2:
        PAUSE_TO_EXIT = True
        root = input("请输入下载根目录路径: ").strip().strip('"')
        if not root:
            print("未输入路径，退出。")
            _pause()
            return
    else:
        PAUSE_TO_EXIT = False
        root = sys.argv[1]

    root = Path(root)
    if not root.is_dir():
        print(f"错误：目录不存在 - {root}")
        _pause()
        return

    do_delete = "--delete" in sys.argv
    duplicates = scan_duplicates(root)

    if not duplicates:
        print("没有发现重复的散放文件。")
        _pause()
        return

    print(f"发现 {len(duplicates)} 个重复散放文件：")
    print()

    total_size = 0
    for file_path, subfolder in duplicates:
        size = file_path.stat().st_size
        total_size += size
        kb = size / 1024
        print(f"  [重复] {file_path}")
        print(f"        子文件夹: {subfolder}  ({kb:.1f} KB)")

    print()
    print(f"共 {len(duplicates)} 个文件，占用 {total_size / 1024:.1f} KB")

    if not do_delete:
        print()
        answer = input("是否删除以上重复文件？(y/N): ").strip().lower()
        if answer == "y":
            do_delete = True

    if do_delete:
        deleted = 0
        for file_path, _ in duplicates:
            try:
                file_path.unlink()
                deleted += 1
            except Exception as e:
                print(f"  删除失败: {file_path} ({e})")
        print(f"已删除 {deleted} 个文件。")

    _pause()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        _pause()
