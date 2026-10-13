from fastapi import APIRouter

from src.config_loader import load_works
from src.metadata import MetadataManager
from webui.backend.schemas.schemas import StatsOut
from webui.backend.services.file_service import calculate_storage

router = APIRouter()


@router.get("/", response_model=StatsOut)
async def get_stats():
    works = load_works()
    tag_count = sum(len(w.tags) for w in works)
    cp_count = sum(len(w.cp_tags) for w in works)
    mm = MetadataManager()
    total_downloads = sum(
        len(pages) for key, pages in mm.page_records.items() if key.endswith("_pages")
    )
    return StatsOut(
        work_count=len(works),
        tag_count=tag_count,
        cp_count=cp_count,
        total_downloads=total_downloads,
        total_storage_mb=calculate_storage(),
    )
