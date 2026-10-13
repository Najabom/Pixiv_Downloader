from fastapi import APIRouter

from webui.backend.services.ui_config import load_ui_config, save_ui_config

router = APIRouter()


@router.get("/")
async def get_ui_config():
    return load_ui_config()


@router.put("/")
async def update_ui_config(payload: dict):
    config = load_ui_config()
    config.update(payload)
    save_ui_config(config)
    return config
