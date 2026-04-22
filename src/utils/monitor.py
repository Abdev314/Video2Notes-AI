"""
Background resource monitor — logs CPU + RAM to a CSV while the pipeline runs.
"""

from __future__ import annotations

import csv
import threading
import time
from pathlib import Path

import psutil


class ResourceMonitor:
    """Sample CPU and RAM every N seconds, write to a CSV."""

    def __init__(self, output_path: Path, interval: float = 1.0):
        self.output_path = Path(output_path)
        self.interval = interval
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def __enter__(self):
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *args):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _run(self):
        with self.output_path.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["time", "cpu_percent", "ram_used_gb", "ram_total_gb"])

            start = time.time()
            while not self._stop.is_set():
                elapsed = time.time() - start
                cpu = psutil.cpu_percent(interval=None)
                mem = psutil.virtual_memory()
                writer.writerow([
                    round(elapsed, 2),
                    cpu,
                    round(mem.used / 1e9, 3),
                    round(mem.total / 1e9, 3),
                ])
                f.flush()
                self._stop.wait(self.interval)