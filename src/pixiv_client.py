import time
from pathlib import Path
from typing import List, Optional
from pixivpy3 import AppPixivAPI
import requests

from .models import IllustInfo


class PixivClient:
    def __init__(self, refresh_token: str = "", cookie_string: str = "",
                 request_delay: float = 2.0):
        self.request_delay = request_delay
        self._last_request_time = 0.0
        self._authenticated = False
        self._use_app_api = False

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "application/json",
        })
        self.last_search_total = 0

        if refresh_token:
            self._try_app_auth(refresh_token)
        if not self._authenticated and cookie_string:
            self._use_web_session(cookie_string)

    def _try_app_auth(self, refresh_token: str):
        try:
            self.api = AppPixivAPI()
            self.api.auth(refresh_token=refresh_token)
            self._authenticated = True
            self._use_app_api = True
            print("Pixiv 登录成功 (App API)")
        except Exception as e:
            print(f"App API 登录失败: {e}")

    def _use_web_session(self, cookie_string: str):
        for item in cookie_string.split(";"):
            item = item.strip()
            if "=" in item:
                key, _, value = item.partition("=")
                key = key.strip()
                value = value.strip()
                if key:
                    self.session.cookies.set(key, value, domain=".pixiv.net")
        for attempt in range(3):
            try:
                resp = self.session.get("https://www.pixiv.net/ajax/user/self", timeout=15)
                if resp.status_code == 200:
                    data = resp.json()
                    if "userData" in data or data.get("error") is False or "body" in data:
                        self._authenticated = True
                        self._use_app_api = False
                        print("Pixiv 登录成功 (Web Session)")
                        return
            except Exception as e:
                if attempt < 2:
                    import time
                    time.sleep(3)
                else:
                    print(f"Web Session 验证失败: {e}")
        self._authenticated = False

    @property
    def is_authenticated(self) -> bool:
        return self._authenticated

    def _rate_limit(self):
        elapsed = time.time() - self._last_request_time
        if elapsed < self.request_delay:
            time.sleep(self.request_delay - elapsed)
        self._last_request_time = time.time()

    # ==================== Search ====================

    def search_illustrations(self, tag: str, max_pages: int = 999) -> List[dict]:
        if self._use_app_api:
            return self._search_app_api(tag, max_pages)
        else:
            return self._search_web_api(tag, max_pages)

    def search_single_page(self, tag: str, page: int) -> List[dict]:
        return self._search_web_api_page(tag, page)

    def _search_app_api(self, tag: str, max_pages: int) -> List[dict]:
        results: List[dict] = []
        page = 1
        while page <= max_pages:
            try:
                self._rate_limit()
                resp = self.api.search_illust(
                    word=tag, search_target="partial_match_for_tags",
                    sort="date_desc", offset=(page - 1) * 30,
                )
                if resp and "illusts" in resp:
                    illusts = resp["illusts"]
                    results.extend(illusts)
                if not resp or resp.get("next_url") is None:
                    break
                page += 1
            except Exception as e:
                print(f"  搜索失败 [tag={tag}, page={page}]: {e}")
                break
        return results

    def _search_web_api_page(self, tag: str, page: int) -> List[dict]:
        try:
            self._rate_limit()
            url = "https://www.pixiv.net/ajax/search/illustrations/" + requests.utils.quote(tag)
            params = {
                "word": tag, "order": "date_d", "mode": "all",
                "p": page, "s_mode": "s_tag", "type": "illust", "lang": "zh",
            }
            resp = self.session.get(url, params=params, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("error") is False:
                    total = data["body"]["illust"].get("total", 0)
                    self.last_search_total = total
                    illust_data = data["body"]["illust"]["data"]
                    return [self._normalize_web_illust(item) for item in illust_data]
        except Exception as e:
            print(f"  搜索失败 [tag={tag}, page={page}]: {e}")
        return []

    def _search_web_api(self, tag: str, max_pages: int) -> List[dict]:
        results: List[dict] = []
        page = 1
        while page <= max_pages:
            try:
                self._rate_limit()
                url = "https://www.pixiv.net/ajax/search/illustrations/" + requests.utils.quote(tag)
                params = {
                    "word": tag,
                    "order": "date_d",
                    "mode": "all",
                    "p": page,
                    "s_mode": "s_tag",
                    "type": "illust",
                    "lang": "zh",
                }
                resp = self.session.get(url, params=params, timeout=15)
                if resp.status_code != 200:
                    break
                data = resp.json()
                if data.get("error") is not False:
                    break
                illust_data = data["body"]["illust"]["data"]
                if not illust_data:
                    break
                normalized = [self._normalize_web_illust(item) for item in illust_data]
                results.extend(normalized)
                total = data["body"]["illust"].get("total", 0)
                self.last_search_total = total
                if len(results) >= total:
                    break
                page += 1
            except Exception as e:
                print(f"  搜索失败 [tag={tag}, page={page}]: {e}")
                break
        return results

    # ==================== Detail ====================

    def get_illust_detail(self, illust_id: int) -> Optional[dict]:
        if self._use_app_api:
            return self._detail_app_api(illust_id)
        else:
            return self._detail_web_api(illust_id)

    def _detail_app_api(self, illust_id: int) -> Optional[dict]:
        try:
            self._rate_limit()
            resp = self.api.illust_detail(illust_id)
            if resp and "illust" in resp:
                return resp["illust"]
        except Exception as e:
            print(f"  获取详情失败 [id={illust_id}]: {e}")
        return None

    def _detail_web_api(self, illust_id: int) -> Optional[dict]:
        try:
            self._rate_limit()
            resp = self.session.get(
                f"https://www.pixiv.net/ajax/illust/{illust_id}",
                timeout=15,
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            if data.get("error") is not False:
                return None
            detail = self._normalize_web_detail(data["body"])
            page_count = detail.get("page_count", 1)
            if page_count > 1:
                pages = self._get_web_pages(illust_id)
                if pages:
                    detail["meta_pages"] = [{"image_urls": {"original": url}} for url in pages]
            return detail
        except Exception as e:
            print(f"  获取详情失败 [id={illust_id}]: {e}")
        return None

    # ==================== Parse ====================

    @staticmethod
    def parse_illust_info(detail: dict) -> IllustInfo:
        tags = detail.get("tags", [])
        if isinstance(tags, list):
            if tags and isinstance(tags[0], dict):
                tags = [t.get("name", t.get("tag", "")) for t in tags]
            tags = [t for t in tags if t]
        elif isinstance(tags, dict):
            tags = [t.get("tag", "") for t in tags.get("tags", []) if t.get("tag")]

        user = detail.get("user", {})
        artist_name = user.get("name", "") or detail.get("artist_name", "") or detail.get("userName", "")
        artist_account = user.get("account", "") or detail.get("artist_account", "") or detail.get("userId", "")

        return IllustInfo(
            illust_id=int(detail.get("id", detail.get("illustId", 0))),
            title=detail.get("title", detail.get("illustTitle", "")),
            artist_name=str(artist_name),
            artist_account=str(artist_account),
            tags=tags,
            page_count=detail.get("page_count", detail.get("pageCount", 1)),
            width=detail.get("width", 0),
            height=detail.get("height", 0),
            illust_type=detail.get("type", detail.get("illustType", "illust")),
        )

    @staticmethod
    def get_original_urls(detail: dict) -> List[str]:
        urls: List[str] = []
        single = detail.get("meta_single_page")
        if single and single.get("original_image_url"):
            urls.append(single["original_image_url"])
        for mp in detail.get("meta_pages", []):
            original = mp.get("image_urls", {}).get("original") or mp.get("urls", {}).get("original")
            if original:
                urls.append(original)
        if not urls:
            original = detail.get("original_url", detail.get("urls", {}).get("original"))
            if original:
                urls.append(original)
        if not urls and detail.get("page_count", 1) > 1:
            alt = detail.get("alt", "")
            if "i.pximg.net" in alt:
                urls.append(alt)
        return urls

    def _get_web_pages(self, illust_id: int) -> List[str]:
        """Fetch all page URLs from web API pages endpoint."""
        try:
            self._rate_limit()
            resp = self.session.get(
                f"https://www.pixiv.net/ajax/illust/{illust_id}/pages",
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                pages = data.get("body", [])
                return [p.get("urls", {}).get("original", "") for p in pages if p.get("urls", {}).get("original")]
        except Exception as e:
            print(f"  获取多图页码失败 [id={illust_id}]: {e}")
        return []

    # ==================== Web API normalization ====================

    @staticmethod
    def _normalize_web_illust(item: dict) -> dict:
        tags_list = item.get("tags", [])
        return {
            "id": int(item["id"]),
            "title": item.get("title", ""),
            "type": "illust" if item.get("illustType", 0) != 2 else "manga",
            "image_urls": {
                "square_medium": item.get("url", ""),
                "medium": item.get("url", ""),
            },
            "user": {
                "id": int(item.get("userId", 0)),
                "name": item.get("userName", ""),
                "account": str(item.get("userId", "")),
            },
            "tags": [{"name": t, "translated_name": ""} for t in tags_list],
            "page_count": item.get("pageCount", 1),
            "width": item.get("width", 0),
            "height": item.get("height", 0),
            "total_bookmarks": item.get("bookmarkCount", 0),
        }

    @staticmethod
    def _normalize_web_detail(body: dict) -> dict:
        tags_raw = body.get("tags", {})
        if isinstance(tags_raw, dict):
            tags_list = tags_raw.get("tags", [])
            tags = [{"name": t.get("tag", ""), "translated_name": t.get("translation", {}).get("en", "")}
                    for t in tags_list]
        else:
            tags = [{"name": t, "translated_name": ""} for t in (tags_raw or [])]

        return {
            "id": int(body.get("illustId", 0)),
            "title": body.get("illustTitle", body.get("title", "")),
            "type": "ugoira" if body.get("illustType") == 2 else "illust",
            "user": {
                "id": int(body.get("userId", 0)),
                "name": body.get("userName", ""),
                "account": str(body.get("userId", "")),
            },
            "tags": tags,
            "page_count": body.get("pageCount", 1),
            "width": body.get("width", 0),
            "height": body.get("height", 0),
            "meta_single_page": {},
            "meta_pages": [],
            "original_url": body.get("urls", {}).get("original", ""),
        }

    # ==================== Download ====================

    def download_file(self, url: str, save_path: Path, retries: int = 3) -> bool:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        for attempt in range(retries):
            try:
                self._rate_limit()
                resp = self.session.get(
                    url,
                    headers={"Referer": "https://www.pixiv.net/"},
                    stream=True,
                    timeout=30,
                )
                if resp.status_code == 200:
                    with open(save_path, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return True
                else:
                    print(f"  HTTP {resp.status_code}: {url}")
            except Exception as e:
                if attempt < retries - 1:
                    wait = (attempt + 1) * 3
                    print(f"  下载失败，{wait}秒后重试 ... ({e})")
                    time.sleep(wait)
                else:
                    print(f"  下载彻底失败: {url} ({e})")
        return False
