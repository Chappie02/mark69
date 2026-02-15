"""
Configuration for the offline multimodal robotic AI assistant.
Raspberry Pi 5, 4GB. Fully offline.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
IMAGES_DIR = PROJECT_ROOT.parent / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# GPIO (BCM mode). Buttons active LOW, pull_up=True
# ---------------------------------------------------------------------------
GPIO_K1_PTT = 17   # Pin 11 - Push-to-Talk
GPIO_K2_DETECT = 27  # Pin 13 - Object Detection
GPIO_K3_CAPTURE = 22  # Pin 15 - Capture Only

# ---------------------------------------------------------------------------
# OLED SSD1306 (128x64, I2C)
# ---------------------------------------------------------------------------
OLED_WIDTH = 128
OLED_HEIGHT = 64
OLED_I2C_ADDR = 0x3C
OLED_I2C_BUS = 1

# ---------------------------------------------------------------------------
# LLM (llama.cpp, Gemma 3 4B IT GGUF 4-bit)
# ---------------------------------------------------------------------------
LLM_MODEL_PATH = PROJECT_ROOT.parent / "models" / "gemma-3-4b-it-Q4_K_M.gguf"
LLM_CONTEXT_SIZE = 2048
LLM_MAX_TOKENS = 256
LLM_TEMP = 0.7
LLM_TOP_P = 0.9
LLM_N_THREADS = 4

# ---------------------------------------------------------------------------
# STT (Vosk, offline)
# ---------------------------------------------------------------------------
VOSK_MODEL_PATH = PROJECT_ROOT.parent / "models" / "vosk-model-small-en-us-0.15"
SAMPLE_RATE = 16000
RECORD_CHANNELS = 1
RECORD_CHUNK_MS = 4000  # Process in 4s chunks for Vosk

# ---------------------------------------------------------------------------
# TTS (Piper or fallback espeak, offline)
# ---------------------------------------------------------------------------
PIPER_MODEL_PATH = PROJECT_ROOT.parent / "models" / "piper" / "en_US-lessac-medium"
TTS_RATE = 150
TTS_VOLUME = 1.0

# ---------------------------------------------------------------------------
# Vision (YOLOv8, CPU)
# ---------------------------------------------------------------------------
YOLO_MODEL_PATH = PROJECT_ROOT.parent / "models" / "yolov8n.pt"
YOLO_CONF_THRESH = 0.4
YOLO_IOU_THRESH = 0.45

# ---------------------------------------------------------------------------
# Animation timing (seconds)
# ---------------------------------------------------------------------------
BLINK_INTERVAL_MIN = 3.0
BLINK_INTERVAL_MAX = 5.0
SACCADE_INTERVAL = 0.5
SUCCESS_HOLD_SEC = 1.0
ERROR_DOUBLE_BLINK_DELAY = 0.15
