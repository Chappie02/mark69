#!/usr/bin/env python3
"""
Download and prepare models for the Pi assistant.
Automates: Vosk (STT), Piper (TTS), YOLO (object detection), ChromaDB embedding model.
LLM (GGUF): not downloaded here — place your model in models/llama/model.gguf yourself.
"""

import os
import sys
import zipfile
import tarfile
import logging
from pathlib import Path
from typing import Optional
from urllib.request import urlretrieve

# Project root = directory that contains the "assistant" package (assistant/config.py)
_script_dir = Path(__file__).resolve().parent
if (_script_dir / "config.py").exists():
    # This script lives inside assistant/; parent is project root
    ROOT = _script_dir.parent
elif (_script_dir / "assistant" / "config.py").exists():
    # This script lives next to assistant/ (e.g. mark69/mark69/download_models.py)
    ROOT = _script_dir
else:
    ROOT = _script_dir.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Avoid shadowing: a file named assistant.py in ROOT would hide the assistant package
if (ROOT / "assistant.py").exists():
    print("Error: assistant.py in the project root shadows the assistant package.")
    print("Rename it to run_assistant.py (or similar), then run again:")
    print("  mv assistant.py run_assistant.py")
    print("  python download_models.py")
    sys.exit(1)

from assistant.config import (
    MODELS_DIR,
    VOSK_MODELS_DIR,
    VOSK_MODEL_PATH,
    PIPER_MODELS_DIR,
    PIPER_MODEL_PATH,
    YOLO_MODELS_DIR,
    YOLO_MODEL_PATH,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("download_models")

# -----------------------------------------------------------------------------
# URLs and options (skip with env: SKIP_VOSK=1, SKIP_PIPER=1, SKIP_YOLO=1, SKIP_EMBED=1)
# -----------------------------------------------------------------------------
VOSK_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
# Piper: small English voice from Hugging Face (direct resolve)
PIPER_VOICE = "en_US-lessac-medium"
PIPER_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US-lessac-medium"
PIPER_FILES = ["en_US-lessac-medium.onnx", "en_US-lessac-medium.onnx.json"]
YOLO_MODEL_NAME = "yolov8n.pt"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"


def _download_file(url: str, dest: Path, desc: str = "") -> bool:
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        log.info("Downloading %s -> %s", desc or url, dest)
        urlretrieve(url, dest, reporthook=_progress_hook(dest))
        return True
    except Exception as e:
        log.error("Download failed %s: %s", url, e)
        return False


def _progress_hook(dest: Path):
    def hook(block_num, block_size, total_size):
        if total_size <= 0:
            return
        done = block_num * block_size
        pct = min(100, 100 * done / total_size)
        if block_num % 50 == 0 or done >= total_size:
            mb = total_size / (1024 * 1024)
            log.info("  %.0f%% of %.1f MB", pct, mb)
    return hook


def download_vosk() -> bool:
    """Download and extract Vosk small English model."""
    if os.environ.get("SKIP_VOSK"):
        log.info("Skipping Vosk (SKIP_VOSK=1)")
        return True
    extract_to = VOSK_MODELS_DIR
    expected_dir = extract_to / "vosk-model-small-en-us-0.15"
    if expected_dir.exists() and (expected_dir / "am").is_dir():
        log.info("Vosk model already present: %s", expected_dir)
        return True
    zip_path = extract_to / "vosk-model-small-en-us-0.15.zip"
    if not zip_path.exists():
        if not _download_file(VOSK_URL, zip_path, "Vosk model"):
            return False
    log.info("Extracting Vosk archive...")
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(extract_to)
        zip_path.unlink(missing_ok=True)
    except Exception as e:
        log.error("Extract failed: %s", e)
        return False
    log.info("Vosk ready: %s", VOSK_MODEL_PATH)
    return True


def download_piper() -> bool:
    """Download Piper English voice (ONNX + JSON)."""
    if os.environ.get("SKIP_PIPER"):
        log.info("Skipping Piper (SKIP_PIPER=1)")
        return True
    onnx_path = Path(PIPER_MODEL_PATH)
    if onnx_path.exists():
        log.info("Piper model already present: %s", onnx_path)
        return True
    PIPER_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    for name in PIPER_FILES:
        url = f"{PIPER_BASE}/{name}"
        dest = PIPER_MODELS_DIR / name
        if dest.exists():
            continue
        if not _download_file(url, dest, f"Piper {name}"):
            return False
    log.info("Piper ready: %s", PIPER_MODEL_PATH)
    return True


# Official Ultralytics assets (yolov8n.pt; fallback: ultralytics cache)
YOLO_URL = "https://github.com/ultralytics/assets/releases/download/v8.4.0/yolov8n.pt"


def download_yolo() -> bool:
    """Download YOLO nano weights to models/yolo."""
    if os.environ.get("SKIP_YOLO"):
        log.info("Skipping YOLO (SKIP_YOLO=1)")
        return True
    dest = Path(YOLO_MODEL_PATH)
    if dest.exists():
        log.info("YOLO model already present: %s", dest)
        return True
    YOLO_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    if _download_file(YOLO_URL, dest, "YOLO yolov8n.pt"):
        log.info("YOLO ready: %s", dest)
        return True
    # Fallback: trigger ultralytics download so cache is primed; use cache path in config
    try:
        from ultralytics import YOLO
        log.info("Fallback: priming ultralytics cache for %s...", YOLO_MODEL_NAME)
        YOLO(YOLO_MODEL_NAME)
        log.info("YOLO cached by ultralytics. Set YOLO_MODEL_PATH=yolov8n.pt to use cache.")
    except Exception as e:
        log.error("YOLO fallback failed: %s", e)
    return False


def download_embedding_model() -> bool:
    """Pre-download SentenceTransformer model for ChromaDB RAG."""
    if os.environ.get("SKIP_EMBED"):
        log.info("Skipping embedding model (SKIP_EMBED=1)")
        return True
    try:
        from sentence_transformers import SentenceTransformer
        log.info("Downloading embedding model %s (used by ChromaDB)...", EMBED_MODEL_NAME)
        SentenceTransformer(EMBED_MODEL_NAME)
        log.info("Embedding model ready.")
        return True
    except Exception as e:
        log.error("Embedding model download failed: %s", e)
        return False


def main() -> int:
    log.info("Models directory: %s", MODELS_DIR)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    ok = True
    ok &= download_vosk()
    ok &= download_piper()
    ok &= download_yolo()
    ok &= download_embedding_model()
    log.info("LLM: place your .gguf file at models/llama/model.gguf (or set LLAMA_MODEL_PATH)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
