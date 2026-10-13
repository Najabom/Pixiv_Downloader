import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "ui_config.json"


def load_ui_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"global_background_source": ""}


def save_ui_config(config: dict):
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
