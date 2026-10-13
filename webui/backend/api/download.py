from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio
import json

from webui.backend.services.download_service import service

router = APIRouter()


@router.post("/start")
async def start_download():
    service.start()
    return {"status": "started"}


@router.post("/stop")
async def stop_download():
    service.stop()
    return {"status": "stopped"}


@router.get("/status")
async def get_status():
    return service.status()


@router.get("/stream")
async def stream_logs():
    async def event_generator():
        loop = asyncio.get_event_loop()
        while True:
            msg = await loop.run_in_executor(None, service.queue.get)
            yield f"data: {msg}\n\n"
            try:
                data = json.loads(msg)
                if data.get("type") in ("done", "error"):
                    break
            except Exception:
                pass

    return StreamingResponse(event_generator(), media_type="text/event-stream")
