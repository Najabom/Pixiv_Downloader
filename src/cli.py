import json
import re
from .config_loader import PROJECT_ROOT, load_works, save_works
from .models import WorkConfig, TagConfig, CPConfig
from .downloader import Downloader


class CLI:

    @staticmethod
    def _split_commas(text: str) -> list:
        return [x.strip() for x in text.replace("，", ",").split(",") if x.strip()]

    @staticmethod
    def _pick_index(prompt: str, max_val: int) -> int | None:
        raw = input(prompt).strip()
        try:
            i = int(raw)
            if 1 <= i <= max_val:
                return i - 1
        except ValueError:
            pass
        return None

    def run(self):
        self._check_login()
        while True:
            self._print_main_menu()
            choice = input("请选择: ").strip()
            if choice == "1":
                self._do_download()
            elif choice == "2":
                self._manage_works()
            elif choice == "3":
                self._show_stats()
            elif choice == "4":
                self._update_cookie()
            elif choice == "5":
                self._nsfw_settings()
            elif choice == "0":
                print("再见！")
                break
            else:
                print("无效选择，请重新输入")

    def _check_login(self):
        from .config_loader import load_settings
        from .pixiv_client import PixivClient

        s = load_settings()
        if not s.pixiv_refresh_token and not s.pixiv_cookie_string:
            print("\n[!] 未配置 Pixiv 登录信息，请先通过菜单 [4] 更新 Cookie")
            return

        print("检查登录状态 ...")
        client = PixivClient(
            refresh_token=s.pixiv_refresh_token,
            cookie_string=s.pixiv_cookie_string,
            request_delay=s.request_delay,
        )
        if client.is_authenticated:
            print("  [OK] 登录有效\n")
        else:
            print("  [!!] 登录失效，请通过菜单 [4] 更新 Cookie\n")

    def _print_main_menu(self):
        print()
        print("=" * 42)
        print("      Pixiv 图片下载管理器 v1.0")
        print("=" * 42)
        print("  1. 开始下载（按配置批量）")
        print("  2. 管理（添加 / 删除 / 编辑作品）")
        print("  3. 查看下载统计")
        print("  4. 更新 Cookie（粘贴即更新）")
        print("  5. NSFW 设置")
        print("  0. 退出")
        print("=" * 42)

    def _do_download(self):
        try:
            downloader = Downloader()
            downloader.run_all()
        except Exception:
            import sys, traceback
            from pathlib import Path
            log_dir = Path(__file__).parent.parent / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / "crash.log"
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(f"崩溃时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                exc_type, exc_value, exc_tb = sys.exc_info()
                f.write(f"异常类型: {exc_type.__name__}\n")
                f.write(f"异常信息: {exc_value}\n")
                f.write("堆栈跟踪:\n")
                traceback.print_exception(exc_type, exc_value, exc_tb, file=f)
            print(f"\n[!] 下载过程出错! 错误详情已写入: {log_path}")
            print(f"[!] {exc_type.__name__}: {exc_value}")

    # ==================== Management ====================

    def _manage_works(self):
        from .config_loader import load_settings
        while True:
            works = load_works()
            s = load_settings()
            print()
            print("-" * 40)
            print("  管理")
            print("-" * 40)
            for i, w in enumerate(works):
                status = "[启用]" if w.active else "[停用]"
                tag_parts = []
                for t in w.tags:
                    name = f"--{t.folder}--" if not t.active else t.folder
                    tag_parts.append(name)
                tag_names = ", ".join(tag_parts) if w.tags else "(全部标签)"
                cp_names = ", ".join(cp.name for cp in w.cp_tags) if w.cp_tags else ""
                print(f"  [{i + 1}] {status} {w.name}")
                print(f"      角色: {tag_names}")
                if cp_names:
                    print(f"      CP: {cp_names}")
            gtags = ", ".join(s.global_exclude_tags) if s.global_exclude_tags else "(空)"
            print(f"\n  全局过滤: {gtags}")
            print(f"  [A] 添加  [D] 删除  [T] 切换启停  [E] 作品编辑  [G] 全局过滤  [Y] 编辑配置文件  [0] 返回")
            choice = input("请选择: ").strip().lower()
            if choice == "a":
                self._add_work(works)
            elif choice == "d":
                self._remove_work(works)
            elif choice == "t":
                self._toggle_work(works)
            elif choice == "e":
                self._work_editor(works)
            elif choice == "g":
                self._global_filter_settings()
            elif choice == "y":
                self._open_config_editor()
            elif choice == "0":
                break
            else:
                print("无效选择")

    def _add_work(self, works):
        print("\n--- 添加作品 ---")
        name = input("  作品名: ").strip()
        if not name:
            return

        print("\n  逐个添加角色（空行结束）:")
        tags = []
        idx = 1
        while True:
            folder = input(f"  [{idx}] 文件夹名: ").strip()
            if not folder:
                break
            tag_raw = input(f"       Pixiv标签 (逗号分隔，留空=同文件夹名): ").strip()
            tag_list = self._split_commas(tag_raw) if tag_raw else []
            tags.append(TagConfig(folder=folder, tags=tag_list))
            idx += 1

        if not tags:
            print("  未添加任何角色，取消")
            return

        works.append(WorkConfig(name=name, search_tags=[], tags=tags, active=True))
        save_works(works)
        print(f"  [OK] 已添加: {name} (含 {len(tags)} 个角色)")

    def _remove_work(self, works):
        idx = self._pick_index("  输入要删除的序号: ", len(works))
        if idx is not None:
            removed = works.pop(idx)
            save_works(works)
            print(f"  [OK] 已删除: {removed.name}")
        else:
            print("  无效序号")

    def _toggle_work(self, works):
        idx = self._pick_index("  输入要切换的序号: ", len(works))
        if idx is not None:
            works[idx].active = not works[idx].active
            save_works(works)
            status = "启用" if works[idx].active else "停用"
            print(f"  [OK] {works[idx].name} 已{status}")
        else:
            print("  无效序号")

    # ==================== Work Editor ====================

    def _work_editor(self, works):
        print()
        print("-" * 40)
        print("  作品编辑 — 选择作品")
        print("-" * 40)
        for i, w in enumerate(works):
            print(f"  [{i + 1}] {w.name}")
        idx = self._pick_index("\n选择作品序号 (0 返回): ", len(works))
        if idx is not None:
            self._work_edit_one(works, idx)

    def _work_edit_one(self, works, work_idx):
        all_works = load_works()
        w = all_works[work_idx]
        while True:
            print(f"\n--- 作品编辑 [{w.name}] ---")
            print(f"  角色: {len(w.tags)} 个")
            print(f"  CP: {len(w.cp_tags)} 个")
            wtags = ", ".join(w.exclude_tags) if w.exclude_tags else "(空)"
            print(f"  过滤: {wtags}")
            print(f"\n  [N] 重命名  [R] 角色管理  [C] CP管理  [X] 过滤标签  [0] 返回")
            choice = input("请选择: ").strip().lower()
            if choice == "n":
                new_name = input(f"  新名 [{w.name}]: ").strip()
                if new_name and new_name != w.name:
                    w.name = new_name
                    save_works(all_works)
                    print(f"  [OK] 已重命名为: {new_name}")
                    return
            elif choice == "r":
                self._tag_manage_one(all_works, work_idx)
                all_works = load_works()
                w = all_works[work_idx]
            elif choice == "c":
                self._cp_manage_one(all_works, work_idx)
                all_works = load_works()
                w = all_works[work_idx]
            elif choice == "x":
                raw = input(f"  过滤标签 (逗号分隔) [{', '.join(w.exclude_tags)}]: ").strip()
                w.exclude_tags = self._split_commas(raw) if raw else []
                save_works(all_works)
                print(f"  [OK] 已更新: {', '.join(w.exclude_tags) if w.exclude_tags else '(空)'}")
            elif choice == "0":
                break
            else:
                print("无效选择")

    # ==================== Global Filter ====================

    def _global_filter_settings(self):
        yaml_path = PROJECT_ROOT / "config" / "settings.yaml"
        from .config_loader import load_settings
        while True:
            s = load_settings()
            tags = s.global_exclude_tags
            print(f"\n--- 全局过滤 ---")
            if tags:
                for i, t in enumerate(tags):
                    print(f"  [{i + 1}] {t}")
            else:
                print("  (空)")
            print(f"\n  [A] 添加  [D] 删除  [0] 返回")
            choice = input("请选择: ").strip().lower()
            if choice == "a":
                raw = input("  新过滤标签: ").strip()
                if raw and raw not in tags:
                    tags.append(raw)
                    self._write_global_filter(yaml_path, tags)
                    print(f"  [OK] 已添加: {raw}")
            elif choice == "d":
                if not tags:
                    print("  没有可删除的")
                    continue
                idx = self._pick_index("  输入要删除的序号: ", len(tags))
                if idx is not None:
                    removed = tags.pop(idx)
                    self._write_global_filter(yaml_path, tags)
                    print(f"  [OK] 已删除: {removed}")
            elif choice == "0":
                break
            else:
                print("无效选择")

    @staticmethod
    def _write_global_filter(yaml_path, tags):
        text = yaml_path.read_text(encoding="utf-8")
        tag_lines = "\n".join(f'  - "{t}"' for t in tags) if tags else "  []"
        text = re.sub(
            r'global_exclude_tags:.*?(?=\n\S|\Z)',
            f'global_exclude_tags:\n{tag_lines}',
            text, flags=re.DOTALL, count=1,
        )
        yaml_path.write_text(text, encoding="utf-8")

    @staticmethod
    def _open_config_editor():
        import os, sys, subprocess
        works_path = PROJECT_ROOT / "config" / "works.yaml"
        path = str(works_path)
        if sys.platform == "win32":
            subprocess.Popen(["notepad", path], creationflags=subprocess.DETACHED_PROCESS)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        print(f"  已在外部编辑器中打开: works.yaml（修改后需重新加载才能生效）")

    # ==================== Character Management ====================

    def _tag_manage_one(self, works, work_idx):
        all_works = load_works()
        w = all_works[work_idx]
        while True:
            print(f"\n--- 角色管理 [{w.name}] ---")
            for i, t in enumerate(w.tags):
                status = "[启用]" if t.active else "[停用]"
                tag_list = ", ".join(t.tags) if t.tags else t.folder
                print(f"  [{i + 1}] {status} {t.folder} -> {tag_list}")
            print(f"\n  输入序号进入角色编辑  [A] 添加新角色  [D] 删除角色  [0] 返回")
            choice = input("请选择: ").strip().lower()
            if choice == "a":
                folder = input("  文件夹名: ").strip()
                if folder:
                    tag_raw = input("  Pixiv标签 (逗号分隔，留空=同文件夹名): ").strip()
                    tag_list = self._split_commas(tag_raw) if tag_raw else []
                    w.tags.append(TagConfig(folder=folder, tags=tag_list))
                    save_works(all_works)
                    print(f"  [OK] 已添加: {folder}")
            elif choice == "d":
                if not w.tags:
                    print("  没有可删除的角色")
                else:
                    idx2 = self._pick_index("  输入要删除的角色序号: ", len(w.tags))
                    if idx2 is not None:
                        removed = w.tags.pop(idx2)
                        save_works(all_works)
                        print(f"  [OK] 已删除: {removed.folder}")
            elif choice == "0":
                break
            else:
                try:
                    i = int(choice) - 1
                    if 0 <= i < len(w.tags):
                        self._tag_edit_one(all_works, w, i)
                        all_works = load_works()
                        w = all_works[work_idx]
                    else:
                        print("无效选择")
                except ValueError:
                    print("无效选择")

    def _tag_edit_one(self, all_works, w, idx):
        t = w.tags[idx]
        while True:
            print(f"\n--- 编辑角色 [{t.folder}] ---")
            status = "启用" if t.active else "停用"
            tag_list = ", ".join(t.tags) if t.tags else t.folder
            print(f"  状态: {status}  |  标签: [{tag_list}]")
            print(f"\n  [T] 切换启停  [A] 添加标签  [R] 移除标签  [N] 重命名  [0] 返回")
            choice = input("请选择: ").strip().lower()
            if choice == "t":
                t.active = not t.active
                save_works(all_works)
                print(f"  [OK] {t.folder} 已{'启用' if t.active else '停用'}")
                if not t.active:
                    return
            elif choice == "a":
                new_tag = input(f"  新标签: ").strip()
                if new_tag and new_tag not in t.tags:
                    t.tags.append(new_tag)
                    save_works(all_works)
                    print(f"  [OK] 已添加: {new_tag}")
            elif choice == "r":
                if not t.tags:
                    print("  当前没有标签可移除")
                else:
                    for i, tag in enumerate(t.tags):
                        print(f"  [{i + 1}] {tag}")
                    idx2 = self._pick_index("  移除序号: ", len(t.tags))
                    if idx2 is not None:
                        removed = t.tags.pop(idx2)
                        save_works(all_works)
                        print(f"  [OK] 已移除: {removed}")
            elif choice == "n":
                new_name = input(f"  新名 [{t.folder}]: ").strip()
                if new_name and new_name != t.folder:
                    t.folder = new_name
                    save_works(all_works)
                    print(f"  [OK] 已重命名为: {new_name}")
                    return
            elif choice == "0":
                break
            else:
                print("无效选择")

    # ==================== CP Management ====================


    def _cp_manage_one(self, works, work_idx):
        all_works = load_works()
        w = all_works[work_idx]
        while True:
            print(f"\n--- CP 管理 [{w.name}] ---")
            if w.cp_tags:
                for i, cp in enumerate(w.cp_tags):
                    search_info = f" 搜索: {', '.join(cp.search_tags)}" if cp.search_tags else ""
                    print(f"  [{i + 1}] {cp.name}{search_info}")
            else:
                print("  (暂无 CP)")
            print(f"\n  [A] 添加CP  [D] 删除CP  [0] 返回")
            choice = input("请选择: ").strip().lower()
            if choice == "a":
                self._add_cps(all_works, w)
                save_works(all_works)
            elif choice == "d":
                self._remove_cp(all_works, w)
                save_works(all_works)
            elif choice == "0":
                break
            else:
                print("无效选择")

    def _add_cps(self, all_works, current_work):
        print(f"\n--- 添加 CP [{current_work.name}] ---")

        while True:
            print(f"\n当前作品 [{current_work.name}] 的角色库:")
            self._print_tag_pool(current_work)

            print("\n选择一个 CP 的成员（输入角色序号，逗号分隔）:")
            print("  例: 1,2  表示选择前两个角色组成 CP")
            print("  [O] 从其他作品选角色")
            print("  [N] 添加新角色到库")
            print("  [Done] 完成添加")
            raw = input("选择: ").strip()

            if raw.lower() == "done" or raw.lower() == "":
                break
            if raw.lower() == "o":
                self._pick_from_other_works(all_works, current_work)
                continue
            if raw.lower() == "n":
                self._add_new_tag(current_work)
                continue

            try:
                indices = [int(x.strip()) - 1 for x in raw.split(",")]
            except ValueError:
                print("  无效输入，请输入序号（如 1,2）")
                continue

            members = []
            for i in indices:
                if 0 <= i < len(current_work.tags):
                    members.append(current_work.tags[i].folder)
                else:
                    print(f"  序号 {i + 1} 超出范围，跳过")
            if len(members) < 2:
                print("  CP 至少需要 2 个成员")
                continue

            search_raw = input(f"  [{('x'.join(members))}] 搜索标签（逗号分隔，留空跳过）: ").strip()
            search_tags = self._split_commas(search_raw) if search_raw else []
            current_work.cp_tags.append(CPConfig(members=members, search_tags=search_tags))
            print(f"  [OK] 已添加 CP: {'x'.join(members)}")

    def _remove_cp(self, all_works, w):
        if not w.cp_tags:
            print("  没有可删除的 CP")
            return
        idx = self._pick_index("  输入要删除的 CP 序号: ", len(w.cp_tags))
        if idx is not None:
            removed = w.cp_tags.pop(idx)
            print(f"  [OK] 已删除: {removed.name}")
        else:
            print("  无效序号")

    def _print_tag_pool(self, work):
        if work.tags:
            for i, t in enumerate(work.tags):
                print(f"  [{i + 1}] {t.folder}")
        else:
            print("  (空)")

    def _pick_from_other_works(self, all_works, current_work):
        print("\n--- 从其他作品选择角色 ---")
        others = [w for w in all_works if w.name != current_work.name]
        if not others:
            print("  没有其他作品")
            return
        for i, w in enumerate(others):
            tag_names = ", ".join(t.folder for t in w.tags)
            print(f"  [{i + 1}] {w.name}: {tag_names}")
        idx = self._pick_index("选择作品序号 (0 返回): ", len(others))
        if idx is None:
            return
        w = others[idx]
        print(f"\n[{w.name}] 角色:")
        for i, t in enumerate(w.tags):
            print(f"  [{i + 1}] {t.folder}")
        raw2 = input("选择角色序号（逗号分隔，0 返回）: ").strip()
        if raw2 == "0":
            return
        try:
            indices = [int(x.strip()) - 1 for x in raw2.split(",")]
        except ValueError:
            print("  无效输入")
            return
        for i in indices:
            if 0 <= i < len(w.tags):
                name = w.tags[i].folder
                if not any(t.folder == name for t in current_work.tags):
                    current_work.tags.append(TagConfig(folder=name))
                    print(f"  [OK] 已从 [{w.name}] 引入角色: {name}")
                else:
                    print(f"  [--] {name} 已存在，跳过")

    def _add_new_tag(self, work):
        raw = input("  新角色名（逗号分隔可多个）: ").strip()
        if not raw:
            return
        for name in self._split_commas(raw):
            name = name.strip()
            if name and not any(t.folder == name for t in work.tags):
                work.tags.append(TagConfig(folder=name))
                print(f"  [OK] 已添加角色: {name}")

    # ==================== NSFW Settings ====================

    def _nsfw_settings(self):
        from .config_loader import load_settings
        from .organizer import validate_nsfw_device, get_nsfw_warning

        s = load_settings()
        yaml_path = PROJECT_ROOT / "config" / "settings.yaml"

        while True:
            print(f"\n--- NSFW 设置 ---")
            status = "开启" if s.nsfw_enabled else "关闭"
            print(f"  状态: {status}")
            print(f"  阈值: {s.nsfw_threshold}")
            print(f"  设备: {s.nsfw_device}")
            print(f"\n  [T] 切换开关  [H] 修改阈值  [D] 切换设备  [0] 返回")
            choice = input("请选择: ").strip().lower()

            if choice == "t":
                s.nsfw_enabled = not s.nsfw_enabled
                if s.nsfw_enabled:
                    actual = validate_nsfw_device(s.nsfw_device)
                    if actual != s.nsfw_device:
                        print(f"  [!] {get_nsfw_warning()}")
                self._save_nsfw_settings(yaml_path, s)
            elif choice == "h":
                raw = input("  新阈值 (0~1, 当前 {:.2f}): ".format(s.nsfw_threshold)).strip()
                try:
                    val = float(raw)
                    if 0 <= val <= 1:
                        s.nsfw_threshold = val
                        self._save_nsfw_settings(yaml_path, s)
                        print(f"  [OK] 阈值已设为 {val}")
                    else:
                        print("  值必须在 0~1 之间")
                except ValueError:
                    print("  无效数值")
            elif choice == "d":
                print("\n  可选设备:")
                print("    cpu      - CPU 推理（通用）")
                print("    cuda     - NVIDIA GPU（需 CUDA + tensorflow）")
                print("    directml - DirectML 通用 GPU（Windows）")
                raw = input(f"  设备 (当前 {s.nsfw_device}): ").strip().lower()
                if raw in ("cpu", "cuda", "directml"):
                    s.nsfw_device = raw
                    if s.nsfw_enabled:
                        actual = validate_nsfw_device(s.nsfw_device)
                        if actual != s.nsfw_device:
                            print(f"  [!] {get_nsfw_warning()}")
                        else:
                            print(f"  [OK] 设备已设为 {raw}，验证通过")
                    else:
                        print(f"  [OK] 设备已设为 {raw}（NSFW 关闭中，未验证）")
                    self._save_nsfw_settings(yaml_path, s)
                else:
                    print("  无效设备名")
            elif choice == "0":
                break
            else:
                print("  无效选择")

    def _save_nsfw_settings(self, yaml_path, s):
        text = yaml_path.read_text(encoding="utf-8")
        text = re.sub(r"enabled:\s*(true|false)", f"enabled: {str(s.nsfw_enabled).lower()}", text)
        text = re.sub(r"threshold:\s*[\d.]+", f"threshold: {s.nsfw_threshold}", text)
        text = re.sub(r'device:\s*"\w+"', f'device: "{s.nsfw_device}"', text)
        yaml_path.write_text(text, encoding="utf-8")

    # ==================== Stats & Cookie ====================

    def _show_stats(self):
        works = load_works()
        history_path = PROJECT_ROOT / "data" / "download_history.json"
        print("\n--- 下载统计 ---")
        if history_path.exists():
            with open(history_path, "r", encoding="utf-8") as f:
                history = json.load(f)
            total = 0
            for w in works:
                count = len(history.get(w.name, []))
                page_count = len(history.get(f"{w.name}_pages", []))
                print(f"  {w.name}: {count} 个作品 / {page_count} 张图片")
                total += page_count
            print(f"\n  总计: {total} 张图片")
        else:
            print("  暂无下载记录")

    def _update_cookie(self):
        yaml_path = PROJECT_ROOT / "config" / "settings.yaml"
        print("""
--- 更新 Cookie ---
1. 浏览器打开 https://www.pixiv.net/ 并登录
2. F12 → Network → 清空 → F5 刷新
3. 筛选 ajax → 点任一条 → Request Headers → Cookie: 整行复制
4. 粘贴到下面即可自动写入配置
""")
        raw = input("粘贴 Cookie 整行 (留空返回): ").strip()
        if not raw:
            return

        config_text = yaml_path.read_text(encoding="utf-8")
        config_text = re.sub(
            r'cookie_string:\s*".*"',
            f'cookie_string: "{raw}"',
            config_text,
            count=1,
        )
        yaml_path.write_text(config_text, encoding="utf-8")
        print("  [OK] Cookie 已更新，返回主菜单即可下载。")
