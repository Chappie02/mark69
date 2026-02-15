"""
Download required models for offline operation.

This script will:
- Download the Gemma GGUF model from the provided URL
- Download YOLOv8 nano weights
- Download Whisper (tiny.en) and sentence-transformers embeddings via huggingface_hub (if available)

Usage:
    python3 download_models.py

Files are saved under `models/` (and `models/stt/`, `models/embeddings/` as subfolders).
"""

import os
import sys
import shutil
import requests
from pathlib import Path

# Optional progress bar
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

# Try to import huggingface_hub for reliable model downloads
try:
    from huggingface_hub import snapshot_download
    HAS_HF = True
except Exception:
    HAS_HF = False

MODELS_DIR = Path(__file__).parent / "models"
STT_DIR = MODELS_DIR / "stt"
EMBED_DIR = MODELS_DIR / "embeddings"

# URLs and identifiers
GEMMA_URL = "https://huggingface.co/unsloth/gemma-3-4b-it-GGUF/resolve/main/gemma-3-4b-it-IQ4_XS.gguf"
GEMMA_FILENAME = "gemma-3-4b-it-IQ4_XS.gguf"

# YOLOv8 nano weights release (ultralytics assets)
YOLO_URL = "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt"
YOLO_FILENAME = "yolov8n.pt"

# Whisper and embedding model repo IDs
WHISPER_REPO = "openai/whisper-tiny.en"
EMBED_REPO = "sentence-transformers/all-MiniLM-L6-v2"

# Helper functions

def ensure_dirs():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    STT_DIR.mkdir(parents=True, exist_ok=True)
    EMBED_DIR.mkdir(parents=True, exist_ok=True)


def download_stream(url: str, dest: Path, chunk_size: int = 8192):
    """Download a file with streaming and optional progress bar."""
    print(f"Downloading {url} -> {dest}")
    r = requests.get(url, stream=True, timeout=30)
    r.raise_for_status()
    total = int(r.headers.get('content-length', 0))
    if HAS_TQDM and total:
        with open(dest, 'wb') as f, tqdm(total=total, unit='iB', unit_scale=True) as bar:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    bar.update(len(chunk))
    else:
        with open(dest, 'wb') as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)


def download_gemma():
    dest = MODELS_DIR / GEMMA_FILENAME
    if dest.exists():
        print(f"Gemma model already present: {dest}")
        return dest
    try:
        download_stream(GEMMA_URL, dest)
        print(f"Gemma downloaded to {dest}")
        return dest
    except Exception as e:
        print(f"Failed to download Gemma: {e}")
        return None


def download_yolo():
    dest = MODELS_DIR / YOLO_FILENAME
    if dest.exists():
        print(f"YOLO weights already present: {dest}")
        return dest
    try:
        download_stream(YOLO_URL, dest)
        print(f"YOLO weights downloaded to {dest}")
        return dest
    except Exception as e:
        print(f"Failed to download YOLO weights: {e}")
        return None


def download_hf_snapshot(repo_id: str, dest_dir: Path):
    """Download a Hugging Face repo snapshot to dest_dir using huggingface_hub if available."""
    if not HAS_HF:
        print("huggingface_hub not available; skipping HF model download. Install with: pip install huggingface_hub")
        return None
    try:
        print(f"Downloading HF model {repo_id} to {dest_dir} (this may take a while)")
        path = snapshot_download(repo_id=repo_id, cache_dir=str(dest_dir), local_files_only=False)
        print(f"Downloaded {repo_id} to {path}")
        return Path(path)
    except Exception as e:
        print(f"Failed to download {repo_id}: {e}")
        return None


def main():
    ensure_dirs()

    # 1) Gemma GGUF
    gemma_path = download_gemma()

    # 2) YOLO weights
    yolo_path = download_yolo()

    # 3) Whisper tiny.en
    if HAS_HF:
        whisper_path = download_hf_snapshot(WHISPER_REPO, STT_DIR)
    else:
        print("Skipping Whisper download (huggingface_hub missing). You can install with: pip install huggingface_hub")
        whisper_path = None

    # 4) Embeddings
    if HAS_HF:
        embed_path = download_hf_snapshot(EMBED_REPO, EMBED_DIR)
    else:
        print("Skipping embeddings download (huggingface_hub missing). You can install with: pip install huggingface_hub")
        embed_path = None

    print('\nSummary:')
    print(f"  Gemma: {gemma_path}")
    print(f"  YOLO: {yolo_path}")
    print(f"  Whisper: {whisper_path}")
    print(f"  Embeddings: {embed_path}")

    print('\nDone. Models saved under models/.')

if __name__ == '__main__':
    main()
