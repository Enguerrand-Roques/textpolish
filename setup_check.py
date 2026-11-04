"""First-launch checks and the model download, without any UI: is Ollama
running, is the model there, is there room for it. The onboarding window
(platforms/macos/onboarding.py) shows these steps; this module does the work.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass

import requests

from config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_MODEL_CASUAL, OLLAMA_MODEL_PRO

MIN_OLLAMA = (0, 40)  # Gemma 4 needs Ollama 0.40 or later
MODEL_SPACE_GB = 5.0  # 4.3 GB model plus some margin
_OLLAMA_APPS = ("/Applications/Ollama.app", os.path.expanduser("~/Applications/Ollama.app"))


def _ollama_app() -> str | None:
    return next((p for p in _OLLAMA_APPS if os.path.isdir(p)), None)


def required_models() -> list[str]:
    return sorted({OLLAMA_MODEL_CASUAL, OLLAMA_MODEL_PRO, OLLAMA_MODEL})


def ollama_version() -> str | None:
    """Ollama's version if it is running, else None."""
    try:
        return requests.get(f"{OLLAMA_BASE_URL}/api/version", timeout=1).json().get("version")
    except (requests.RequestException, ValueError):
        return None


def version_ok(version: str) -> bool:
    parts = []
    for piece in version.split(".")[:2]:
        digits = "".join(c for c in piece if c.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts) >= MIN_OLLAMA


def ollama_installed() -> bool:
    return _ollama_app() is not None or shutil.which("ollama") is not None


def start_ollama(wait: float = 15.0) -> bool:
    """Start Ollama if it is installed but not running. True once it answers."""
    if ollama_version():
        return True
    app = _ollama_app()
    if app:
        subprocess.run(["open", "-g", "-a", app], check=False)
    elif shutil.which("ollama"):
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
    else:
        return False
    deadline = time.monotonic() + wait
    while time.monotonic() < deadline:
        if ollama_version():
            return True
        time.sleep(0.5)
    return False


def missing_models() -> list[str]:
    """Required models Ollama does not have yet (all of them if it is down)."""
    try:
        tags = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2).json().get("models", [])
    except (requests.RequestException, ValueError):
        return required_models()
    have = {m.get("name") for m in tags} | {m.get("model") for m in tags}
    return [m for m in required_models() if m not in have]


def free_space_gb(path: str = os.path.expanduser("~")) -> float:
    return shutil.disk_usage(path).free / 1e9


@dataclass
class Progress:
    done: int = 0          # bytes downloaded, all layers
    total: int = 0         # bytes to download, all layers
    speed: float = 0.0     # bytes per second, recent average
    status: str = ""

    @property
    def fraction(self) -> float:
        return self.done / self.total if self.total else 0.0

    @property
    def seconds_left(self) -> float | None:
        if not self.speed or not self.total:
            return None
        return (self.total - self.done) / self.speed


class PullError(RuntimeError):
    pass


def pull(model: str, on_progress: Callable[[Progress], None]) -> None:
    """Download *model* through Ollama, reporting progress. Ollama resumes a
    download that was interrupted, so calling it again continues it."""
    if free_space_gb() < MODEL_SPACE_GB:
        raise PullError(f"Not enough disk space: {MODEL_SPACE_GB:.0f} GB free needed, "
                        f"{free_space_gb():.1f} GB available.")
    layers: dict[str, tuple[int, int]] = {}  # digest -> (completed, total)
    progress = Progress()
    last_t, last_done = time.monotonic(), 0
    try:
        with requests.post(f"{OLLAMA_BASE_URL}/api/pull", json={"model": model, "stream": True},
                           stream=True, timeout=(5, 60)) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                if chunk.get("error"):
                    raise PullError(chunk["error"])
                progress.status = chunk.get("status", "")
                if chunk.get("digest") and chunk.get("total"):
                    layers[chunk["digest"]] = (chunk.get("completed", 0), chunk["total"])
                    progress.done = sum(c for c, _ in layers.values())
                    progress.total = sum(t for _, t in layers.values())
                now = time.monotonic()
                if now - last_t >= 1.0:
                    speed = (progress.done - last_done) / (now - last_t)
                    progress.speed = speed if not progress.speed else 0.7 * progress.speed + 0.3 * speed
                    last_t, last_done = now, progress.done
                if progress.status == "success":
                    progress.done = progress.total  # the last small layers report no progress
                    on_progress(progress)
                    return
                on_progress(progress)
    except requests.RequestException as e:
        raise PullError("The download stopped (network?). Try again: it resumes "
                        "where it stopped.") from e
    raise PullError("The download ended before it finished. Try again.")
