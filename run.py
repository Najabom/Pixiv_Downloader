#!/usr/bin/env python3
import os
import sys
import shutil
import time
import threading
import webbrowser
import urllib.request
from pathlib import Path


def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def first_run_init(base: Path):
    config_dir = base / "config"
    if config_dir.exists():
        return
    config_dir.mkdir(parents=True, exist_ok=True)

    if getattr(sys, "frozen", False):
        tmpl_dir = Path(sys._MEIPASS) / "templates"
    else:
        tmpl_dir = base / "templates"

    for name in ("settings.yaml", "works.yaml"):
        src = tmpl_dir / name
        dst = config_dir / name
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)

    print("首次运行：已创建 config/settings.yaml 和 config/works.yaml")
    print("请先编辑 config/settings.yaml 填入 Pixiv Cookie/Token，再使用下载功能")


def main():
    base = get_base_dir()
    os.chdir(base)

    print("=" * 50)
    print("  Pixiv Downloader WebUI 启动中...")
    print("=" * 50)

    first_run_init(base)

    # Add project root to path so src/ can be found
    sys.path.insert(0, str(base))

    from webui.backend.main import app
    import uvicorn

    port = 8000
    url = f"http://127.0.0.1:{port}"

    def run_server():
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

    t = threading.Thread(target=run_server, daemon=True)
    t.start()

    print("等待后端就绪 ...")
    for i in range(30):
        try:
            urllib.request.urlopen(url, timeout=1)
            break
        except Exception:
            time.sleep(1)
    else:
        print(f"启动超时。请手动打开 {url}")
        input("按 Enter 退出...")
        return

    print(f"\nWebUI 已启动: {url}")
    try:
        webbrowser.open(url)
    except Exception:
        pass

    print("CMD 窗口保持打开以显示后台日志。关闭此窗口将停止服务。\n")
    try:
        while t.is_alive():
            t.join(1)
    except KeyboardInterrupt:
        print("\n用户中断，退出。")


if __name__ == "__main__":
    main()
