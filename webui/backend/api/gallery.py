from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse

from webui.backend.schemas.schemas import GalleryItem
from webui.backend.services import file_service

router = APIRouter()


def _image_url(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    return f"/api/gallery/image?path={path.replace(' ', '%20')}"


@router.get("/dashboard-backgrounds")
async def get_dashboard_backgrounds():
    bgs = file_service.get_dashboard_backgrounds()
    return {k: _image_url(v) for k, v in bgs.items()}


@router.get("/refresh")
async def refresh_gallery_index():
    count = file_service.refresh_index()
    return {"count": count}


@router.get("/works")
async def list_works_with_images():
    return {"works": file_service.get_works()}


@router.get("/categories")
async def list_categories(work: str):
    return {"categories": file_service.get_categories(work)}


@router.get("/subfolders")
async def list_subfolders(work: str, category: str):
    return {"subfolders": file_service.get_gallery_subfolders(work, category)}


@router.get("/random")
async def get_random(
    count: int = Query(1, ge=1, le=50),
    work: Optional[str] = None,
    category: Optional[str] = None,
    source_folder: Optional[str] = None,
    horizontal_only: bool = True,
    ignore_gallery_groups: bool = True,
):
    paths = file_service.get_random_images(
        count=count,
        horizontal_only=horizontal_only,
        ignore_gallery_groups=ignore_gallery_groups,
        work=work,
        category=category,
        source_folder=source_folder,
    )
    if not paths:
        raise HTTPException(status_code=404, detail="无图片")
    return {"paths": paths, "urls": [_image_url(p) for p in paths]}


@router.get("/")
async def get_gallery(
    work: Optional[str] = None,
    category: Optional[str] = None,
    subfolder: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    horizontal_only: bool = False,
    ignore_gallery_groups: bool = False,
):
    items, total = file_service.list_gallery(
        work=work,
        category=category,
        subfolder=subfolder,
        page=page,
        page_size=page_size,
        horizontal_only=horizontal_only,
        ignore_gallery_groups=ignore_gallery_groups,
    )
    return {
        "items": [GalleryItem(**item) for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/image")
async def serve_image(path: str):
    target = file_service.safe_path(path)
    if not target or not target.exists():
        raise HTTPException(status_code=404, detail="图片不存在")
    return FileResponse(str(target))


@router.get("/thumb")
async def serve_thumbnail(path: str, width: int = 400):
    thumb = file_service.get_thumbnail_path(path, width)
    if not thumb:
        raise HTTPException(status_code=404, detail="缩略图生成失败")
    return FileResponse(str(thumb), media_type="image/webp")
