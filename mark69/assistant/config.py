"""
Configuration for the offline multimodal AI assistant.
Raspberry Pi 5, 4GB RAM — fully offline, button-driven.
"""

import os

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# GPIO (BCM numbering) — buttons
# ---------------------------------------------------------------------------
PIN_K1 = 5   # Push-to-Talk (hold)
PIN_K2 = 6   # Object Detection
PIN_K3 = 13  # Capture & Save Image

# ---------------------------------------------------------------------------
# OLED SSD1306 (I2C)
# ---------------------------------------------------------------------------
OLED_WIDTH = 128
OLED_HEIGHT = 64
OLED_I2C_ADDR = 0x3C  # common for SSD1306

# Eye geometry (reference from spec)
REF_EYE_HEIGHT = 40
REF_EYE_WIDTH = 40
REF_SPACE_BETWEEN_EYES = 10
REF_CORNER_RADIUS = 8

# Animation timing (seconds)
IDLE_BLINK_INTERVAL_MIN = 3.0
IDLE_BLINK_INTERVAL_MAX = 5.0
SUCCESS_HOLD_SEC = 1.0
SACCADE_INTERVAL_IDLE = (0.5, 1.5)
SACCADE_INTERVAL_THINKING = (0.4, 0.8)
SACCADE_INTERVAL_DETECTING = (0.15, 0.35)

# ---------------------------------------------------------------------------
# Audio
# ---------------------------------------------------------------------------
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SIZE = 1024
RECORD_FORMAT = "int16"

# ---------------------------------------------------------------------------
# STT (Vosk — offline)
# ---------------------------------------------------------------------------
VOSK_MODEL_DIR = os.path.join(PROJECT_ROOT, "models", "vosk")
# User should place Vosk small model in models/vosk (e.g. vosk-model-small-en-us-0.15)

# ---------------------------------------------------------------------------
# TTS (Piper — offline)
# ---------------------------------------------------------------------------
PIPER_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "piper", "en_US-lessac-medium.onnx")
PIPER_CONFIG_PATH = os.path.join(PROJECT_ROOT, "models", "piper", "en_US-lessac-medium.onnx.json")
# Fallback: use pyttsx3/espeak if Piper not available

# ---------------------------------------------------------------------------
# LLM (llama.cpp)
# ---------------------------------------------------------------------------
LLAMA_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "llama", "gemma-3-4b-it-Q4_K_M.gguf")
# Or user path to Gemma 3 4B IT GGUF 4-bit
LLAMA_CTX = 2048
LLAMA_N_THREADS = 2
LLAMA_N_GPU_LAYERS = 0  # CPU only for Pi
LLAMA_TEMP = 0.7
LLAMA_MAX_TOKENS = 256

# System prompt for personality
LLM_SYSTEM_PROMPT = """You are a small robotic assistant with a friendly, helpful personality.
You run on a Raspberry Pi and have a simple OLED face with animated eyes.
Keep responses concise (1-3 sentences) so they can be spoken aloud quickly.
Be warm and slightly playful."""

# ---------------------------------------------------------------------------
# Vision (YOLOv8 + Picamera2)
# ---------------------------------------------------------------------------
YOLO_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "yolo", "yolov8n.pt")
# ultralytics will download yolov8n.pt on first run if missing
YOLO_CONFIDENCE = 0.5
CAMERA_RESOLUTION = (640, 480)
CAMERA_FRAMERATE = 15
