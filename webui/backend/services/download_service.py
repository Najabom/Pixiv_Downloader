import io
import json
import threading
from contextlib import redirect_stdout
from queue import Queue

from src.downloader import Downloader


class _QueueWriter(io.TextIOBase):
    def __init__(self, queue: Queue):
        self.queue = queue
        self._buffer = ""

    def write(self, s: str) -> int:
        self._buffer += s
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            line = line.strip()
            if line:
                self.queue.put(json.dumps({"type": "log", "message": line}))
        return len(s)

    def flush(self):
        line = self._buffer.strip()
        if line:
            self.queue.put(json.dumps({"type": "log", "message": line}))
            self._buffer = ""


class DownloadService:
    def __init__(self):
        self._stop_event = threading.Event()
        self._running = False
        self._thread: threading.Thread | None = None
        self.queue: Queue = Queue()

    def start(self):
        if self._running:
            return
        self._stop_event.clear()
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def status(self):
        return {"running": self._running and not self._stop_event.is_set()}

    def _run(self):
        writer = _QueueWriter(self.queue)
        try:
            with redirect_stdout(writer):
                downloader = Downloader(stop_event=self._stop_event)
                downloader.run_all()
        except Exception as e:
            self.queue.put(json.dumps({"type": "error", "message": str(e)}))
        finally:
            self._running = False
            self.queue.put(json.dumps({"type": "done"}))


service = DownloadService()
