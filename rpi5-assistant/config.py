"""
Centralized configuration for RPi5 Multimodal Assistant
"""

import os
from pathlib import Path

# =============================================
# PATHS
# =============================================
PROJECT_ROOT = Path(__file__).parent
STORAGE_DIR = PROJECT_ROOT / "storage"
IMAGES_DIR = STORAGE_DIR / "images"
VECTORDB_DIR = STORAGE_DIR / "vectordb"
MODELS_DIR = PROJECT_ROOT / "models"

# Create directories if they don't exist
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
VECTORDB_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# =============================================
# GPIO PINS (BCM MODE)
# =============================================
GPIO_MODE = "BCM"
BUTTON_K1 = 17  # Push-to-talk (hold) - GPIO17 (Pin 11)
BUTTON_K2 = 27  # Object detection - GPIO27 (Pin 13)
BUTTON_K3 = 22  # Capture only - GPIO22 (Pin 15)

# Buttons are active LOW with pull-up resistors
BUTTON_ACTIVE_LOW = True

# =============================================
# OLED DISPLAY (SSD1306, 128x64, I2C)
# =============================================
OLED_ADDRESS = 0x3C
OLED_I2C_BUS = 1
OLED_WIDTH = 128
OLED_HEIGHT = 64

# =============================================
# ANIMATION
# =============================================
# 5-second continuous loop
ANIMATION_LOOP_TIME = 5.0
ANIMATION_FPS = 30
ANIMATION_FRAME_TIME = 1.0 / ANIMATION_FPS

# Eye animation parameters
EYE_CENTER_Y = 32
EYE_LEFT_X = 40
EYE_RIGHT_X = 88
EYE_RADIUS = 6
PUPIL_OFFSET_MAX = 4

# =============================================
# AUDIO
# =============================================
# Using USB microphone and USB speaker
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHUNK_SIZE = 1024
AUDIO_CHANNELS = 1
AUDIO_FORMAT = "int16"
AUDIO_DEVICE_INDEX = None  # Auto-detect; can be set to USB device index
AUDIO_INPUT_DEVICE = "default"
AUDIO_OUTPUT_DEVICE = "default"

# Recording timeout and max duration
MAX_RECORD_DURATION = 30  # seconds
RECORD_TIMEOUT = 0.5  # silence timeout in seconds

# =============================================
# STT (Speech-to-Text)
# =============================================
# Using faster-whisper (offline, CPU)
STT_MODEL = "tiny.en"  # Use "base.en" or "small.en" for better accuracy
STT_DEVICE = "cpu"
STT_COMPUTE_TYPE = "int8"  # For 4GB RAM optimization

# =============================================
# LLM (llama.cpp)
# =============================================
# Gemma 4-bit GGUF model
LLM_MODEL_PATH = str(MODELS_DIR / "gemma-3-4b-it-IQ4_XS.gguf")
LLM_N_CTX = 2048  # Context window
LLM_N_GPU_LAYERS = 0  # RPi5 doesn't have dedicated GPU, but can try some offloading
LLM_N_THREADS = 4
LLM_TEMPERATURE = 0.7
LLM_TOP_P = 0.9
LLM_MAX_TOKENS = 512
LLM_VERBOSE = False

# System prompt for LLM
LLM_SYSTEM_PROMPT = """You are a helpful, offline AI assistant running on a Raspberry Pi 5 robot. 
You have access to a memory system (RAG) and can detect objects using computer vision.
Keep responses concise and helpful. Always be friendly and informative.
When you don't know something, say so clearly."""

# =============================================
# VISION (YOLOv8)
# =============================================
YOLO_MODEL = "yolov8n"  # nano model for efficiency
YOLO_CONFIDENCE_THRESHOLD = 0.5
YOLO_IOU_THRESHOLD = 0.45
YOLO_DEVICE = "cpu"  # CPU inference

# Camera resolution
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# =============================================
# RAG (ChromaDB)
# =============================================
RAG_COLLECTION_NAME = "assistant_memory"
RAG_EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Lightweight, efficient
RAG_SIMILARITY_THRESHOLD = 0.5
RAG_TOP_K = 3  # Retrieve top 3 most relevant chunks

# =============================================
# TEXT-TO-SPEECH
# =============================================
# Using pyttsx3 (offline, no external dependencies)
TTS_RATE = 150  # Words per minute
TTS_VOLUME = 0.9
TTS_VOICE_INDEX = 0  # 0 = default (usually male), 1+ = other voices if available

# =============================================
# THREADING
# =============================================
# Number of worker threads (keep minimal)
ANIMATION_THREAD_ENABLED = True
BUTTON_THREAD_ENABLED = True
CONTROLLER_THREAD_ENABLED = True

# Thread sleep times to reduce CPU usage
BUTTON_POLL_INTERVAL = 0.05  # 50ms button polling
CONTROLLER_POLL_INTERVAL = 0.1  # 100ms controller check
ANIMATION_FRAME_INTERVAL = 1.0 / 30  # 30 FPS

# =============================================
# LOGGING
# =============================================
LOG_LEVEL = "INFO"
LOG_FILE = PROJECT_ROOT / "assistant.log"

# =============================================
# SYSTEM LIMITS (4GB RAM Optimization)
# =============================================
MAX_MEMORY_MB = 1024  # Soft limit for memory usage
YOLO_BATCH_SIZE = 1  # Process one image at a time
EMBEDDINGS_BATCH_SIZE = 32  # ChromaDB batch size
