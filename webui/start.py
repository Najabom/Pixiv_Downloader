import subprocess
import sys
import time
import webbrowser
import urllib.request
from pathlib import Path


def main():
    webui_dir = Path(__file__).parent
    project_root = webui_dir.parent
    dist_dir = webui_dir / "frontend" / "dist"

    if not dist_dir.exists():
        print("前端构建产物不存在，请先执行：cd webui/frontend && npm run build")
        sys.exit(1)

    print("启动 Pixiv Downloader WebUI ...")
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "webui.backend.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ],
        cwd=project_root,
    )

    print("等待后端就绪 ...")
    for _ in range(30):
        try:
            urllib.request.urlopen("http://127.0.0.1:8000")
            break
        except Exception:
            time.sleep(1)
    else:
        print("后端启动超时，请手动打开 http://127.0.0.1:8000")
        proc.wait()
        return

    print("地址：http://127.0.0.1:8000")
    try:
        webbrowser.open("http://127.0.0.1:8000")
    except Exception:
        pass

    proc.wait()


if __name__ == "__main__":
    main()
