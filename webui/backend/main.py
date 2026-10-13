import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    PROJECT_ROOT = Path(sys._MEIPASS)
else:
    PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from webui.backend.api import works, settings, download, gallery, stats, ui
from webui.backend.services import file_service

app = FastAPI(title="Pixiv Downloader WebUI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(works.router, prefix="/api/works", tags=["works"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])
app.include_router(download.router, prefix="/api/download", tags=["download"])
app.include_router(gallery.router, prefix="/api/gallery", tags=["gallery"])
app.include_router(ui.router, prefix="/api/ui", tags=["ui"])

file_service.refresh_index()

if getattr(sys, "frozen", False):
    frontend_dist = Path(sys._MEIPASS) / "dist_frontend"
else:
    frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"

if frontend_dist.exists():
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        index = frontend_dist / "index.html"
        if index.exists():
            return FileResponse(str(index))
        raise HTTPException(status_code=404)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("webui.backend.main:app", host="127.0.0.1", port=8000, reload=True)
