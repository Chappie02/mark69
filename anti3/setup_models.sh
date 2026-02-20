#!/bin/bash
# ============================================================
# Raspberry Pi 5 Offline AI Assistant — Model Download Script
# ============================================================
# Downloads all required models for offline operation.
# Usage: bash setup_models.sh
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODELS_DIR="$SCRIPT_DIR/assistant/models"

echo "============================================"
echo "  AI Assistant — Model Setup"
echo "============================================"
echo ""
echo "Models directory: $MODELS_DIR"
echo ""

mkdir -p "$MODELS_DIR"
mkdir -p "$MODELS_DIR/piper"

# ── 1. YOLOv8 Nano Model ─────────────────────

YOLO_MODEL="$MODELS_DIR/yolo.pt"
if [ -f "$YOLO_MODEL" ]; then
    echo "[✓] YOLOv8 model already exists"
else
    echo "[↓] Downloading YOLOv8n model..."
    python3 -c "
from ultralytics import YOLO
model = YOLO('yolov8n.pt')
import shutil
shutil.move('yolov8n.pt', '$YOLO_MODEL')
print('YOLOv8n downloaded successfully')
"
    echo "[✓] YOLOv8n model downloaded"
fi
echo ""

# ── 2. TinyLlama 1.1B GGUF ───────────────────

LLM_MODEL="$MODELS_DIR/tinyllama-1.1b-chat.Q4_K_M.gguf"
if [ -f "$LLM_MODEL" ]; then
    echo "[✓] LLM model already exists"
else
    echo "[↓] Downloading TinyLlama 1.1B Q4_K_M (~670MB)..."
    wget -q --show-progress \
        "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf" \
        -O "$LLM_MODEL"
    echo "[✓] LLM model downloaded"
fi
echo ""

# ── 3. Whisper Tiny ───────────────────────────

echo "[i] Whisper 'tiny' model will auto-download on first run (~75MB)."
echo "    To pre-download:"
echo "    python3 -c \"from faster_whisper import WhisperModel; WhisperModel('tiny', device='cpu', compute_type='int8')\""
echo ""

# ── 4. Piper TTS Voice ───────────────────────

PIPER_MODEL="$MODELS_DIR/piper/en_US-lessac-medium.onnx"
PIPER_CONFIG="$MODELS_DIR/piper/en_US-lessac-medium.onnx.json"

if [ -f "$PIPER_MODEL" ]; then
    echo "[✓] Piper TTS model already exists"
else
    echo "[↓] Downloading Piper TTS voice model (~100MB)..."
    wget -q --show-progress \
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx" \
        -O "$PIPER_MODEL"
    wget -q --show-progress \
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json" \
        -O "$PIPER_CONFIG"
    echo "[✓] Piper TTS model downloaded"
fi
echo ""

# ── Summary ───────────────────────────────────

echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "Models:"
ls -lh "$MODELS_DIR"
echo ""
echo "Piper voices:"
ls -lh "$MODELS_DIR/piper/" 2>/dev/null || echo "  (none)"
echo ""
echo "Next: pip uninstall picamera2 -y  (use system package)"
echo "Then: cd $SCRIPT_DIR/assistant && python3 main.py"
echo ""
