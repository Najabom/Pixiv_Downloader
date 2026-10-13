from pathlib import Path
from datetime import datetime
import json
import threading

from .config_loader import load_settings, load_works, PROJECT_ROOT
from .models import WorkConfig, DownloadRecord
from .pixiv_client import PixivClient
from .metadata import MetadataManager
from .organizer import (
    generate_filename, generate_new_filename, get_target_dir,
    classify_illust_full, get_image_info, sanitize,
    check_nsfw, validate_nsfw_device, get_nsfw_warning,
)


class Downloader:
    def __init__(self, stop_event: threading.Event | None = None):
        self.settings = load_settings()
        self.works = load_works()
        self.metadata = MetadataManager()
        self.client: PixivClient | None = None
        self._checkpoint_path = PROJECT_ROOT / "data" / "tag_checkpoint.json"
        self._checkpoint = self._load_checkpoint()
        self._stop_event = stop_event

    def _stopped(self) -> bool:
        return self._stop_event is not None and self._stop_event.is_set()


    def _ts(self) -> str:
        return datetime.now().strftime("%H:%M:%S")

    def login(self) -> bool:
        s = self.settings
        if not s.pixiv_refresh_token and not s.pixiv_cookie_string:
            print("错误: 未配置 Pixiv 登录信息")
            print("请在 config/settings.yaml 的 pixiv 节点填入 refresh_token 或 cookie_string")
            return False
        self.client = PixivClient(
            refresh_token=s.pixiv_refresh_token,
            cookie_string=s.pixiv_cookie_string,
            request_delay=s.request_delay,
        )
        ok = self.client.is_authenticated
        if ok and self.settings.nsfw_enabled:
            actual = validate_nsfw_device(self.settings.nsfw_device)
            if actual != self.settings.nsfw_device:
                print(f"  [!] {get_nsfw_warning()}")
            else:
                print(f"  NSFW 检测: {actual}")
        return ok

    def run_all(self):
        if not self.login():
            return
        works = [w for w in self.works if w.active]
        if not works:
            print("没有启用的作品，请在 config/works.yaml 中配置")
            return
        print(f"\n[{self._ts()}] === 开始处理 {len(works)} 个作品 ===\n")
        for work in works:
            if self._stopped():
                print(f"\n[{self._ts()}] [已停止] 用户中断")
                return
            self.process_work(work)
        print(f"[{self._ts()}] === 全部完成 ===")

    def _effective_exclude_tags(self, work: WorkConfig) -> set:
        result = set(t.lower() for t in self.settings.global_exclude_tags)
        for t in work.exclude_tags:
            result.add(t.lower())
        return result

    def _load_checkpoint(self) -> dict:
        if self._checkpoint_path.exists():
            with open(self._checkpoint_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_checkpoint(self):
        try:
            self._checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._checkpoint_path, "w", encoding="utf-8") as f:
                json.dump(self._checkpoint, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"  [警告] 保存检查点失败: {e}")

    # ==================== Main Work Loop ====================

    def process_work(self, work: WorkConfig):
        print(f"\n[{self._ts()}] {'='*30}")
        print(f"[{self._ts()}]   [{work.name}]")
        print(f"[{self._ts()}] {'='*30}")

        download_root = Path(self.settings.download_dir)
        csv_path = download_root / work.name / "metadata.csv"
        exclude_tags = self._effective_exclude_tags(work)
        seen_ids = set()
        download_count = 0

        all_search_terms = []
        if not work.tags:
            for tag in work.search_tags:
                all_search_terms.append((tag, None))
        else:
            for tag_config in work.tags:
                if not tag_config.active:
                    continue
                for stag in tag_config.effective_search_tags(work.name):
                    all_search_terms.append((stag, tag_config.name))
        for cp in work.cp_tags:
            for stag in cp.search_tags:
                all_search_terms.append((stag, None))

        for search_tag, source_tag in all_search_terms:
            if self._stopped():
                print(f"\n[{self._ts()}] [已停止] {work.name} 中断")
                return
            label = f"[{source_tag}] " if source_tag else "[CP] " if not work.tags else ""
            tag_key = f"{work.name}|{search_tag}"
            stored = self._checkpoint.get(tag_key, {})

            page1 = self.client.search_illustrations(search_tag, max_pages=1)
            total = self.client.last_search_total

            if stored.get("completed") and stored.get("total") == total and total > 0:
                print(f"[{self._ts()}]   [skip] {label}{search_tag} — 已完成 ({total} 张无变化)")
                continue

            print(f"[{self._ts()}]   搜索 {label}{search_tag} (总量 {total})")

            tag_illusts = stored.get("illusts", {})
            tag_completed = False
            tag_downloaded = 0
            page = 1
            if stored.get("total") == total and stored.get("last_page", 0) > 0:
                page = stored["last_page"] + 1
                print(f"[{self._ts()}]   [续搜] 从第 {page} 页继续")
            tag_processed = (page - 1) * 60

            while True:
                if self._stopped():
                    print(f"\n[{self._ts()}] [已停止] {search_tag} 中断")
                    return
                if page == 1:
                    illusts = page1
                else:
                    illusts = self.client.search_single_page(search_tag, page)
                    if not illusts:
                        tag_completed = True
                        break
                print(f"[{self._ts()}]    第{page}页: {len(illusts)} 张")

                skipped_count = 0
                for illust in illusts:
                    try:
                        iid = illust["id"]
                        if iid in seen_ids:
                            continue
                        seen_ids.add(iid)

                        iid_str = str(iid)
                        old_record = tag_illusts.get(iid_str, {})
                        old_pages = old_record.get("p", 0)
                        search_pages = illust.get("page_count", 1)

                        all_done = self.metadata.all_pages_downloaded(work.name, iid, search_pages)
                        truly_grew = old_pages > 0 and search_pages > old_pages
                        if all_done and not truly_grew:
                            title = illust.get("title", "")[:40]
                            artist = illust.get("user", {}).get("name", "")
                            tag_processed += 1
                            tag_illusts[iid_str] = {"p": search_pages}
                            print(f"[{self._ts()}][{tag_processed}/{total}][Skip] id={iid} {title} ({artist})")
                            skipped_count += 1
                            continue

                        download_pages, skipped_in_illust, actual_pages = self._process_illust(
                            illust, work, download_root, csv_path, exclude_tags,
                            old_pages, tag_processed + 1, total
                        )
                        if download_pages > 0 or skipped_in_illust > 0:
                            tag_processed += 1
                        if download_pages > 0:
                            tag_downloaded += download_pages
                            download_count += download_pages

                        tag_illusts[iid_str] = {"p": max(old_pages, actual_pages)}
                    except Exception:
                        import traceback
                        iid = illust.get("id", "?")
                        print(f"[{self._ts()}][ERROR] 处理作品 id={iid} 时出错，跳过:")
                        traceback.print_exc()
                        tag_illusts[str(iid)] = {"p": illust.get("page_count", 1)}
                        self._checkpoint[tag_key] = {
                            "illusts": tag_illusts,
                            "total": total,
                            "completed": False,
                            "last_page": page,
                        }
                        self._save_checkpoint()

                self._checkpoint[tag_key] = {
                    "illusts": tag_illusts,
                    "total": total,
                    "completed": False,
                    "last_page": page,
                }
                self._save_checkpoint()

                if page * 60 >= total or total <= 0:
                    tag_completed = True
                    break
                if page >= self.settings.max_search_pages:
                    break
                page += 1

            self._checkpoint[tag_key]["completed"] = tag_completed
            self._save_checkpoint()
            print(f"[{self._ts()}]   [{work.name}] {search_tag} 完成")

        print(f"[{self._ts()}]   [{work.name}] 本次下载: {download_count} 张")

    # ==================== Process Single Illust ====================

    def _process_illust(self, illust: dict, work: WorkConfig, download_root: Path,
                        csv_path: Path, exclude_tags: set, old_pages: int = 0,
                        progress: int = 0, progress_total: int = 0) -> tuple:
        illust_id = illust["id"]

        illust_tags = [t["name"] for t in illust.get("tags", [])]
        for etag in exclude_tags:
            if etag in [t.lower() for t in illust_tags]:
                title = illust.get("title", "")[:40]
                artist = illust.get("user", {}).get("name", "")
                print(f"[{self._ts()}][{progress}/{progress_total}][Skip{etag.upper()}] id={illust_id} {title} ({artist})")
                return 0, 0, 0

        detail = self.client.get_illust_detail(illust_id)
        if not detail:
            return 0, 0, 0
        if detail.get("type") == "ugoira":
            return 0, 0, 0

        info = self.client.parse_illust_info(detail)
        urls = self.client.get_original_urls(detail)
        if not urls:
            return 0, 0, 0

        if info.page_count > 1 and len(urls) < info.page_count:
            extra = self.client._get_web_pages(illust_id)
            if extra:
                urls = extra

        cr = classify_illust_full(info.tags, info.title, work.tags, work.cp_tags)
        cr.is_multi_page = info.page_count > 1
        category = cr.category
        dir_category = cr.dir_category
        title = info.title or "untitled"
        artist = info.artist_name or info.artist_account or "未知画师"

        self._log_discovery(cr, illust_id, title, work, download_root)
        if category == "未分类":
            self._log_unclassified(cr, info, illust_id, download_root, work)

        gallery_dir = ""
        if info.page_count > 1 or len(urls) > 1:
            safe_title = sanitize(title)
            if len(safe_title) > 40:
                safe_title = safe_title[:40]
            safe_artist = sanitize(artist)
            gallery_dir = f"{safe_title}_{safe_artist}_{illust_id}"

        is_old_illust = old_pages > 0
        is_new_group_pages = is_old_illust and info.page_count > old_pages

        start_page = old_pages if is_new_group_pages else 0
        downloaded = 0
        skipped_pages = []

        for idx, url in enumerate(urls):
            if idx < start_page and self.metadata.all_pages_downloaded(work.name, illust_id, info.page_count):
                skipped_pages.append(idx)
                continue
            if idx < start_page:
                skipped_pages.append(idx)
                continue
            if not is_new_group_pages and self.metadata.is_downloaded(work.name, illust_id, idx):
                skipped_pages.append(idx)
                continue

            target_dir = get_target_dir(download_root, work.name, dir_category)
            if gallery_dir:
                target_dir = target_dir / gallery_dir
            target_dir.mkdir(parents=True, exist_ok=True)

            temp_path = target_dir / f"_temp_{illust_id}_p{idx}"

            if not self.client.download_file(url, temp_path, self.settings.max_retries):
                continue

            try:
                w, h, resolution, orientation, ext = get_image_info(temp_path)
            except Exception as e:
                print(f"  读取图片信息失败: {e}")
                temp_path.unlink(missing_ok=True)
                continue

            page_idx = idx if info.page_count > 1 else 0
            if is_new_group_pages:
                filename = generate_new_filename(title, artist, illust_id, idx, orientation, ext)
            else:
                filename = generate_filename(title, artist, illust_id, page_idx, orientation, ext)
            final_path = target_dir / filename

            counter = 1
            stem = filename.rsplit(".", 1)[0]
            while final_path.exists():
                final_path = target_dir / f"{stem}_{counter}.{ext}"
                counter += 1

            try:
                temp_path.rename(final_path)
            except Exception as e:
                print(f"  文件保存失败: {e}")
                temp_path.unlink(missing_ok=True)
                continue
            downloaded += 1

            self.metadata.mark_downloaded(work.name, illust_id, idx)

            record = DownloadRecord(
                work_name=work.name,
                image_name=Path(filename).stem,
                tag=category,
                artist=artist,
                page_index=page_idx,
                resolution=resolution,
                orientation=orientation,
                source="P站",
                illust_id=illust_id,
                download_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
            self.metadata.save_record_to_csv(record, csv_path)
            print(f"[{self._ts()}][{progress}/{progress_total}][OK] {filename}")

        if skipped_pages:
            if downloaded == 0:
                print(f"[{self._ts()}][{progress}/{progress_total}][Skip] id={illust_id} {title[:30]} ({artist}) (全{len(skipped_pages)}页已下载)")
            else:
                print(f"[{self._ts()}][{progress}/{progress_total}][Skip] id={illust_id} p{skipped_pages[0]}-p{skipped_pages[-1]} ({len(skipped_pages)}页已下载)")

        return downloaded, len(skipped_pages), max(info.page_count, len(urls))

    # ==================== Logging ====================

    def _log_discovery(self, cr, illust_id: int, title: str, work, download_root: Path):
        illust_tag_names = cr.detected
        if len(illust_tag_names) >= 2:
            combo = "x".join(sorted(illust_tag_names))
            known_cps = {cp.name for cp in work.cp_tags}
            if combo not in known_cps:
                cp_path = download_root / work.name / "_潜在CP.txt"
                existing = set()
                if cp_path.exists():
                    existing = set(cp_path.read_text(encoding="utf-8").splitlines())
                entry = f"{combo} (id={illust_id})"
                if entry not in existing:
                    with open(cp_path, "a", encoding="utf-8") as f:
                        f.write(entry + "\n")

    def _log_unclassified(self, cr, info, illust_id: int, download_root: Path, work):
        uc_dir = download_root / work.name / "未分类"
        uc_dir.mkdir(parents=True, exist_ok=True)
        log_path = uc_dir / "_原因记录.txt"

        tags_str = ", ".join(info.tags[:15])
        detected_str = ", ".join(sorted(cr.detected)) if cr.detected else "(无)"
        entry = (
            f"作品ID: {illust_id}\n"
            f"标题: {info.title}\n"
            f"画师: {info.artist_name}\n"
            f"图片标签: {tags_str}\n"
            f"匹配到的标签: {detected_str}\n"
            f"原因: {cr.reason}\n"
            f"P站URL: https://www.pixiv.net/artworks/{illust_id}\n"
            f"---\n"
        )
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(entry)

    def _log_nsfw(self, illust_id: int, title: str, category: str, score: float,
                  download_root: Path, work):
        audit_dir = download_root / work.name / "_待审核"
        audit_dir.mkdir(parents=True, exist_ok=True)
        log_path = audit_dir / "_审核记录.txt"
        entry = (
            f"作品ID: {illust_id}\n"
            f"标题: {title}\n"
            f"原始分类: {category}\n"
            f"NSFW评分: {score:.3f}\n"
            f"P站URL: https://www.pixiv.net/artworks/{illust_id}\n"
            f"---\n"
        )
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(entry)
