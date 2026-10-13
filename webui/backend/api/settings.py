import re
from fastapi import APIRouter, HTTPException

from src.config_loader import load_settings, PROJECT_ROOT
from src.pixiv_client import PixivClient
from webui.backend.schemas.schemas import SettingsOut, SettingsUpdate, CookieUpdate

router = APIRouter()


@router.get("/", response_model=SettingsOut)
async def get_settings():
    s = load_settings()
    return SettingsOut(
        download_dir=s.download_dir,
        max_search_pages=s.max_search_pages,
        request_delay=s.request_delay,
        max_retries=s.max_retries,
        max_workers=s.max_workers,
        nsfw_enabled=s.nsfw_enabled,
        nsfw_threshold=s.nsfw_threshold,
        nsfw_device=s.nsfw_device,
        global_exclude_tags=s.global_exclude_tags,
        pixiv_refresh_token=s.pixiv_refresh_token,
        pixiv_cookie_string=s.pixiv_cookie_string,
    )


@router.put("/", response_model=SettingsOut)
async def update_settings(payload: SettingsUpdate):
    yaml_path = PROJECT_ROOT / "config" / "settings.yaml"
    text = yaml_path.read_text(encoding="utf-8")

    if payload.download_dir is not None:
        text = re.sub(r'download_dir:\s*"[^"]*"', f'download_dir: "{payload.download_dir}"', text)
    if payload.max_search_pages is not None:
        text = re.sub(r'max_search_pages:\s*\d+', f'max_search_pages: {payload.max_search_pages}', text)
    if payload.request_delay is not None:
        text = re.sub(r'request_delay:\s*[\d.]+', f'request_delay: {payload.request_delay}', text)
    if payload.max_retries is not None:
        text = re.sub(r'max_retries:\s*\d+', f'max_retries: {payload.max_retries}', text)
    if payload.max_workers is not None:
        text = re.sub(r'max_workers:\s*\d+', f'max_workers: {payload.max_workers}', text)
    if payload.nsfw_enabled is not None:
        text = re.sub(r'enabled:\s*(true|false)', f'enabled: {str(payload.nsfw_enabled).lower()}', text)
    if payload.nsfw_threshold is not None:
        text = re.sub(r'threshold:\s*[\d.]+', f'threshold: {payload.nsfw_threshold}', text)
    if payload.nsfw_device is not None:
        text = re.sub(r'device:\s*"\w+"', f'device: "{payload.nsfw_device}"', text)
    if payload.global_exclude_tags is not None:
        tag_lines = "\n".join(f'  - "{t}"' for t in payload.global_exclude_tags) if payload.global_exclude_tags else "  []"
        text = re.sub(
            r'global_exclude_tags:.*?(?=\n\S|\Z)',
            f'global_exclude_tags:\n{tag_lines}',
            text, flags=re.DOTALL, count=1,
        )

    yaml_path.write_text(text, encoding="utf-8")
    return await get_settings()


@router.post("/cookie", response_model=SettingsOut)
async def update_cookie(payload: CookieUpdate):
    yaml_path = PROJECT_ROOT / "config" / "settings.yaml"
    text = yaml_path.read_text(encoding="utf-8")
    text = re.sub(r'cookie_string:\s*".*"', f'cookie_string: "{payload.cookie_string}"', text, count=1)
    yaml_path.write_text(text, encoding="utf-8")
    return await get_settings()


@router.post("/test-login")
async def test_login():
    s = load_settings()
    client = PixivClient(
        refresh_token=s.pixiv_refresh_token,
        cookie_string=s.pixiv_cookie_string,
        request_delay=s.request_delay,
    )
    return {"authenticated": client.is_authenticated}
