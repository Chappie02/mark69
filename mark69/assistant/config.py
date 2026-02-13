"""
Configuration for Raspberry Pi 5 Offline Multimodal AI Assistant.
Centralizes all hardware and software settings.
"""

import os
from pathlib import Path

# -----------------------------------------------------------------------------
# Project paths (assistant/ is project root when running from project_folder)
# -----------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
IMAGES_DIR = PROJECT_ROOT / "images"
MEMORY_DIR = PROJECT_ROOT / "memory" / "chroma_db"
LOG_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
MEMORY_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# GPIO (BCM numbering)
# -----------------------------------------------------------------------------
GPIO_BUTTON_LISTEN = 17   # K1 - Listening mode
GPIO_BUTTON_OBJECT = 27   # K2 - Object mode
GPIO_BUTTON_CAPTURE = 22  # K3 - Capture image

GPIO_BUTTONS = {
    "listen": GPIO_BUTTON_LISTEN,
    "object": GPIO_BUTTON_OBJECT,
    "capture": GPIO_BUTTON_CAPTURE,
}

# -----------------------------------------------------------------------------
# OLED (SSD1306 I2C)
# -----------------------------------------------------------------------------
OLED_I2C_ADDRESS = 0x3C
OLED_WIDTH = 128
OLED_HEIGHT = 64
OLED_PORT = 1  # I2C port on Pi (usually 1)

# -----------------------------------------------------------------------------
# Camera (Picamera2)
# -----------------------------------------------------------------------------
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FRAMERATE = 15

# -----------------------------------------------------------------------------
# Audio
# -----------------------------------------------------------------------------
# Recording
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SIZE = 1024
RECORD_SECONDS_MAX = 10
SILENCE_THRESHOLD = 500
SILENCE_DURATION = 1.5  # seconds of silence to stop

# Vosk STT model path (user must download and set)
VOSK_MODEL_PATH = os.environ.get("VOSK_MODEL_PATH", str(PROJECT_ROOT / "models" / "vosk-model-small-en-us-0.15"))

# Piper TTS model path (user must download)
PIPER_MODEL_PATH = os.environ.get("PIPER_MODEL_PATH", str(PROJECT_ROOT / "models" / "piper"))

# -----------------------------------------------------------------------------
# LLM (llama.cpp)
# -----------------------------------------------------------------------------
# Path to llama.cpp server or executable; user configures
LLAMA_CPP_SERVER_URL = os.environ.get("LLAMA_CPP_SERVER_URL", "http://127.0.0.1:8080")
LLAMA_MODEL_PATH = os.environ.get("LLAMA_MODEL_PATH", str(PROJECT_ROOT / "models" / "llama"))
LLAMA_CONTEXT_SIZE = 2048
LLAMA_MAX_TOKENS = 256
LLAMA_TEMPERATURE = 0.7

# -----------------------------------------------------------------------------
# YOLO
# -----------------------------------------------------------------------------
YOLO_MODEL_PATH = os.environ.get("YOLO_MODEL_PATH", "yolov8n.pt")  # nano for Pi
YOLO_CONFIDENCE = 0.4
YOLO_IOU_THRESHOLD = 0.45
YOLO_IMAGE_SIZE = 320  # smaller for Pi

# -----------------------------------------------------------------------------
# ChromaDB / RAG
# -----------------------------------------------------------------------------
CHROMA_PERSIST_DIR = str(MEMORY_DIR)
CHROMA_COLLECTION_CONV = "conversations"
CHROMA_COLLECTION_OBJECTS = "object_locations"

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FILE = LOG_DIR / "assistant.log"
