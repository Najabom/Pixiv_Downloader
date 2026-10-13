"""
文件夹名重映射工具 —— 根据 works.yaml 配置，将旧文件夹名映射到新文件夹名
零 API 调用，纯本地 rename 操作
"""
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from src.config_loader import load_settings, load_works
from src.organizer import sanitize


def update_text_records(root: Path, old: str, new: str):
    for f in root.rglob("*"):
        if f.is_file() and f.suffix in (".csv", ".tsv", ".txt"):
            try:
                text = f.read_text(encoding="utf-8")
                if old in text:
                    f.write_text(text.replace(old, new), encoding="utf-8")
            except Exception:
                pass


def update_json_records(parent: Path, replacements: dict, project_root: Path):
    """Update JSON key names in data/*.json files using old→new mappings."""
    data_dir = project_root / "data"
    if not data_dir.exists():
        return
    for jf in sorted(data_dir.rglob("*.json")):
        try:
            text = jf.read_text(encoding="utf-8")
            modified = False
            for old, new in replacements.items():
                if old in text:
                    text = text.replace(old, new)
                    modified = True
            if modified:
                data = json.loads(text)
                jf.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass


def ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def main():
    s = load_settings()
    works = load_works()
    dl_root = Path(s.download_dir)

    if not dl_root.exists():
        print(f"下载目录不存在: {dl_root}")
        return

    print("\n=== 文件夹名映射工具 ===")
    print(f"下载目录: {dl_root}")

    project_root = Path(__file__).parent

    # ===== Step 0: Scan JSON records for orphan keys =====
    json_remap = {}
    data_dir = project_root / "data"
    if data_dir.exists():
        config_names = {sanitize(w.name) for w in works}
        orphan_keys = set()
        for jf in sorted(data_dir.rglob("*.json")):
            try:
                data = json.loads(jf.read_text(encoding="utf-8"))
                for key in data:
                    base_key = key.split("|")[0].split("_pages")[0].rstrip("_pages")
                    if base_key not in config_names and not key.startswith("_"):
                        orphan_keys.add(base_key)
            except Exception:
                pass

        orphan_keys -= config_names
        if orphan_keys:
            print("\n--- Step 0: JSON 记录中有孤立 key ---")
            for old in sorted(orphan_keys):
                print(f"\n  孤立 key: [{old}]")
                print(f"  现有作品:")
                for i, w in enumerate(works):
                    print(f"    [{i + 1}] {w.name}")
                print(f"    [S] 跳过（保留旧记录）")
                print(f"    [D] 删除旧记录")
                choice = input("  映射到: ").strip()
                if choice.lower() == "s":
                    continue
                elif choice.lower() == "d":
                    for jf in sorted(data_dir.rglob("*.json")):
                        try:
                            data = json.loads(jf.read_text(encoding="utf-8"))
                            new_data = {}
                            for k, v in data.items():
                                if not (k == old or k.startswith(old + "|") or k.startswith(old + "_pages")):
                                    new_data[k] = v
                            if len(new_data) != len(data):
                                jf.write_text(json.dumps(new_data, ensure_ascii=False, indent=2), encoding="utf-8")
                        except Exception:
                            pass
                    print(f"  [OK] 已删除 [{old}] 的记录")
                    continue
                try:
                    i = int(choice) - 1
                    if 0 <= i < len(works):
                        new_name = sanitize(works[i].name)
                        json_remap[old] = new_name
                        print(f"  [OK] {old} → {new_name}")
                except ValueError:
                    print("  跳过")

            if json_remap:
                confirm = input(f"\n  确认更新 {len(json_remap)} 组 JSON 记录? (y/N): ").strip().lower()
                if confirm == "y":
                    for old, new in json_remap.items():
                        for jf in sorted(data_dir.rglob("*.json")):
                            try:
                                text = jf.read_text(encoding="utf-8")
                                if old in text:
                                    text = text.replace(old, new)
                                    data = json.loads(text)
                                    jf.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                            except Exception:
                                pass
                        print(f"  [OK] JSON: {old} → {new}")

                        old_dl = dl_root / old
                        new_dl = dl_root / new
                        if old_dl.exists():
                            if new_dl.exists():
                                for item in list(old_dl.iterdir()):
                                    dest = new_dl / item.name
                                    counter = 1
                                    while dest.exists():
                                        dest = new_dl / f"{item.stem}_{counter}{item.suffix}"
                                        counter += 1
                                    item.rename(dest)
                                if not any(old_dl.iterdir()):
                                    old_dl.rmdir()
                            else:
                                old_dl.rename(new_dl)
                            update_text_records(new_dl if new_dl.exists() else old_dl, old, new)
                            print(f"  [OK] 文件夹: {old} → {new}")

    actual_dirs = sorted([d for d in dl_root.iterdir() if d.is_dir() and not d.name.startswith("_")])

    if not actual_dirs:
        print("下载目录为空")
        return

    # ===== Step 1: Map work folders =====
    work_config_names = {sanitize(w.name) for w in works}
    work_obj_map = {sanitize(w.name): w for w in works}
    work_remap = {}  # old_name → new_name

    print(f"\n--- 作品文件夹映射 ---")
    for actual_dir in actual_dirs:
        actual_name = actual_dir.name
        if actual_name in work_config_names:
            continue  # Already matches

        print(f"\n  未匹配: [{actual_name}]")
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
                work_remap[actual_name] = sanitize(works[i].name)
                print(f"  [OK] {actual_name} → {works[i].name}")
        except ValueError:
            print("  跳过")

    if not work_remap:
        print("  无需映射")
    else:
        print(f"\n  作品映射: {len(work_remap)} 项")
        confirm = input("  确认执行? (y/N): ").strip().lower()
        if confirm == "y":
            for old_name, new_name in work_remap.items():
                old_path = dl_root / old_name
                new_path = dl_root / new_name
                print(f"  更新记录: {old_name} → {new_name}")
                update_text_records(old_path, old_name, new_name)
                update_json_records(old_path, {old_name: new_name}, project_root)
                if new_path.exists():
                    for item in list(old_path.iterdir()):
                        dest = new_path / item.name
                        counter = 1
                        while dest.exists():
                            dest = new_path / f"{item.stem}_{counter}{item.suffix}"
                            counter += 1
                        item.rename(dest)
                    if not any(old_path.iterdir()):
                        old_path.rmdir()
                else:
                    old_path.rename(new_path)
                print(f"  [OK] {old_name} → {new_name}")

    # ===== Step 2: Map tag & CP folders =====
    # Rebuild actual_dirs after potential renames
    actual_dirs = sorted([d for d in dl_root.iterdir() if d.is_dir() and not d.name.startswith("_")])

    tag_moves = []  # (from_path, to_path, old_tag_name, new_tag_name, work_dir)

    for work_dir in actual_dirs:
        work_name = work_dir.name
        # Find matching work
        matched_work = None
        for w in works:
            if sanitize(w.name) == work_name:
                matched_work = w
                break
        if not matched_work:
            continue

        tag_config_names = {sanitize(t.folder) for t in matched_work.tags}
        cp_config_names = {sanitize(cp.name) for cp in matched_work.cp_tags}
        known_names = tag_config_names | cp_config_names | {"未分类", "组图", "多人图", "_待审核"}

        sub_dirs = sorted([d for d in work_dir.iterdir() if d.is_dir()])
        if not sub_dirs:
            continue

        needs_mapping = any(sd.name not in known_names for sd in sub_dirs)

        if not needs_mapping:
            continue

        print(f"\n--- 角色/CP 文件夹映射 [{matched_work.name}] ---")
        for sd in sub_dirs:
            if sd.name in known_names:
                continue

            print(f"\n  未匹配: [{sd.name}]")
            print(f"  [{matched_work.name}] 的角色:")
            for i, t in enumerate(matched_work.tags):
                print(f"    [{i + 1}] {t.folder}")
            if matched_work.cp_tags:
                print(f"  [{matched_work.name}] 的 CP:")
                for i, cp in enumerate(matched_work.cp_tags):
                    print(f"    [{len(matched_work.tags) + i + 1}] {cp.name}")
            print(f"    [S] 跳过")
            choice = input("  映射到: ").strip()
            if choice.lower() == "s":
                continue
            try:
                i = int(choice) - 1
                total_targets = len(matched_work.tags) + len(matched_work.cp_tags)
                if 0 <= i < total_targets:
                    if i < len(matched_work.tags):
                        new_name = sanitize(matched_work.tags[i].folder)
                    else:
                        new_name = sanitize(matched_work.cp_tags[i - len(matched_work.tags)].name)
                    # Also map gallery subdirs if any
                    for subsd in sorted(sd.iterdir()):
                        if subsd.is_dir() and not subsd.name.startswith("_"):
                            target = work_dir / new_name
                            tag_moves.append((subsd, target / subsd.name, sd.name, new_name, work_dir))
                    target = work_dir / new_name
                    tag_moves.append((sd, target, sd.name, new_name, work_dir))
                    print(f"  [OK] {sd.name} → {new_name}")
            except ValueError:
                print("  跳过")

    if not tag_moves:
        print("\n  无需映射")
    else:
        unique_changes = set()
        for src, dst, old_tag, new_tag, wd in tag_moves:
            if old_tag != new_tag:
                unique_changes.add((old_tag, new_tag, wd))
        print(f"\n  角色移动: {len(tag_moves)} 项")
        print(f"  记录更新: {len(unique_changes)} 组")
        for src, dst, old_tag, new_tag, wd in tag_moves:
            print(f"    {src.relative_to(dl_root)} → {dst.relative_to(dl_root)}")
        confirm = input("  确认执行? (y/N): ").strip().lower()
        if confirm == "y":
            for old_tag, new_tag, work_dir in unique_changes:
                print(f"  更新记录: {old_tag} → {new_tag}")
                update_text_records(work_dir, old_tag, new_tag)
                update_json_records(work_dir, {old_tag: new_tag}, project_root)
            for src, dst, old_tag, new_tag, wd in tag_moves:
                dst.parent.mkdir(parents=True, exist_ok=True)
                if dst.exists():
                    for item in list(src.iterdir()):
                        dest = dst / item.name
                        counter = 1
                        while dest.exists():
                            dest = dst / f"{item.stem}_{counter}{item.suffix}"
                            counter += 1
                        item.rename(dest)
                    if not any(src.iterdir()):
                        src.rmdir()
                else:
                    src.rename(dst)
                print(f"  [OK] {src.relative_to(dl_root)} → {dst.relative_to(dl_root)}")

    # ===== Step 3: Clean empty dirs =====
    print(f"\n[{ts()}] 检查空目录 ...")
    removed = 0
    for work_dir in dl_root.iterdir():
        if work_dir.is_dir():
            for dirpath in sorted(list(work_dir.rglob("*")), reverse=True):
                if dirpath.is_dir() and dirpath != work_dir:
                    try:
                        if not any(dirpath.iterdir()):
                            dirpath.rmdir()
                            removed += 1
                    except OSError:
                        pass
    if removed:
        print(f"  清理空目录: {removed} 个")

    print(f"\n[{ts()}] === 完成 ===")
    input("\n按 Enter 退出...")


if __name__ == "__main__":
    main()
