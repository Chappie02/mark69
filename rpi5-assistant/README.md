# RPi5 Multimodal AI Assistant

**A fully offline multimodal AI assistant for Raspberry Pi 5 with push-to-talk voice interaction, object detection, local LLM, persistent memory, and continuous animated presence.**

## 🎯 Features

- **Push-to-Talk Voice Interaction**: Hold K1 button to record and process speech
- **Offline Speech Recognition**: faster-whisper (tiny.en) for fast CPU transcription
- **Local LLM Inference**: Gemma 2B 4-bit GGUF with llama.cpp
- **YOLOv8 Object Detection**: Real-time detection on Raspberry Pi 5 (nano model)
- **Persistent Memory**: ChromaDB RAG system with semantic search
- **Continuous Animation**: 5-second eye animation loop running independently
- **OLED Display**: Real-time status and animation on 128x64 I2C SSD1306
- **Three-Button Interface**: Push-to-talk, object detection, image capture
- **Fully Offline**: No internet required, runs entirely on Raspberry Pi 5
- **Non-Blocking Design**: Animation, buttons, and audio never freeze

## 📋 Hardware Requirements

### Raspberry Pi
- **Board**: Raspberry Pi 5 (4GB RAM minimum)
- **OS**: Raspberry Pi OS (bullseye or bookworm)
- **Power**: USB-C 5V/5A minimum

### Display
- **SSD1306 OLED**: 128x64 pixels, 0.96"
- **Interface**: I2C (GPIO 2/3, i2c-1 bus)
- **Address**: 0x3C

### Audio
- **Microphone**: USB microphone (auto-detected)
- **Speaker**: USB speaker or 3.5mm audio (via USB adapter)
- **Sample Rate**: 16kHz, 16-bit mono

### Buttons (3-Button Dial Switch)
- **K1 (GPIO17, Pin 11)**: Push-to-talk (hold to record)
- **K2 (GPIO27, Pin 13)**: Object detection
- **K3 (GPIO22, Pin 15)**: Capture image only
- All buttons use internal pull-up, active LOW

### Camera
- **Picamera2**: Official Raspberry Pi camera v3 or v2
- **Resolution**: 640x480 for detection

## 🚀 Installation

### 1. System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3-pip python3-dev python3-venv \
  libatlas-base-dev libjasper-dev libtiff5 libjasper1 libharfbuzz0b \
  libwebp6 libtiff5 libjasper1 libhdf5-dev libharfbuzz0b libwebp6 \
  libopenjp2-7 libtiff5 libopenjp2-7 \
  libblas-dev liblapack-dev libharfbuzz0b libwebp6 \
  libatlas-base-dev libopenblas-dev liblapack-dev \
  i2c-tools espeak-ng alsa-utils

# Enable I2C and Camera
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_legacy 0
sudo raspi-config nonint do_camera 0

# Reboot
sudo reboot
```

### 2. Create Virtual Environment

```bash
cd ~/Desktop/mark69/rpi5-assistant

# Create venv (use Python 3.11+)
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### 3. Download Models

```bash
# Create models directory
mkdir -p models

# Download Gemma 2B 4-bit GGUF (2.2GB)
wget -O models/gemma-2b-it-q4_k_m.gguf \
  https://huggingface.co/TheBloke/Gemma-2B-it-GGUF/resolve/main/gemma-2b-it-q4_k_m.gguf

# Whisper will auto-download on first run (141MB for tiny.en)

# YOLO will auto-download on first run (6.2MB for nano)
```

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt

# Note: Installation takes 10-15 minutes on RPi5
# Some packages may need compilation
```

### 5. Test Hardware

```bash
# Test I2C
i2cdetect -y 1

# Test camera
libcamera-hello --list-cameras

# Test audio
aplay --list-devices
arecord -d 3 test.wav && aplay test.wav
```

## 🎮 Usage

### Run Assistant

```bash
source venv/bin/activate
python main.py
```

### Button Controls

1. **K1 (Push-to-Talk)**: 
   - Press and hold to record speech
   - Release to process
   - Assistant queries RAG memory and generates response
   - Response played through speaker

2. **K2 (Object Detection)**:
   - Press to capture image
   - Runs YOLOv8 inference
   - Stores detection in memory
   - LLM explains what was detected
   - Speaks explanation

3. **K3 (Capture Only)**:
   - Press to capture and save image
   - No processing, just storage

### Display Feedback

- **Status messages** on top line
- **Emoji/icons** show current state
- **Continuous eye animation** in background
- **Eyes move** according to 5-second loop

### Animation Loop (5 seconds)

1. Eyes centered (1 sec)
2. Slow shift left (1 sec)
3. Return to center (1 sec)
4. Slow shift right (1 sec)
5. Small blink effect (1 sec)

Then repeats forever, independent of all other processing.

## 📂 Project Structure

```
rpi5-assistant/
├── main.py              # Entry point, orchestration
├── config.py            # All configuration and constants
├── requirements.txt     # Python dependencies
├── README.md           # This file
│
├── core/               # Core state and control
│   ├── state.py        # Shared thread-safe state
│   ├── controller.py   # Main controller, orchestration
│   └── __init__.py
│
├── hardware/           # Hardware drivers
│   ├── buttons.py      # GPIO button input
│   ├── oled.py         # SSD1306 display driver
│   ├── animation.py    # Eye animation engine
│   └── __init__.py
│
├── audio/              # Audio processing
│   ├── recorder.py     # Audio capture (PyAudio)
│   ├── stt.py          # Speech-to-text (faster-whisper)
│   ├── tts.py          # Text-to-speech (pyttsx3)
│   └── __init__.py
│
├── ai/                 # AI/ML models
│   ├── llm.py          # LLM inference (llama.cpp)
│   ├── vision.py       # Object detection (YOLOv8)
│   ├── rag.py          # RAG memory (ChromaDB)
│   ├── embeddings.py   # Text embeddings
│   └── __init__.py
│
├── storage/            # Data storage
│   ├── images/         # Captured images
│   ├── vectordb/       # ChromaDB persistent storage
│   └── models/         # AI models (not in repo, downloaded)
│
└── models/             # Downloaded models
    └── gemma-2b-it-q4_k_m.gguf  # LLM model (2.2GB)
```

## ⚙️ Configuration

All settings in `config.py`:

- **GPIO Pins**: Button mappings, active levels
- **OLED Display**: Address, resolution, animation parameters
- **Audio**: Sample rate, device selection, chunk size
- **STT**: Model selection, device, compute type
- **LLM**: Model path, context window, temperature
- **YOLO**: Model type, confidence threshold
- **RAG**: Collection name, embedding model, similarity threshold
- **Threading**: Poll intervals, frame rates

## 🔧 Troubleshooting

### I2C Display Not Working

```bash
# Check I2C devices
i2cdetect -y 1

# Manually check connection
python3 << EOF
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
serial = i2c(bus=1, address=0x3C)
device = ssd1306(serial_interface=serial)
print("Display OK")
EOF
```

### Button Not Responding

```bash
# Check GPIO states
python3 << EOF
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
for pin in [17, 27, 22]:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    print(f"GPIO {pin}: {GPIO.input(pin)}")
    GPIO.cleanup()
EOF
```

### Camera Not Detected

```bash
libcamera-hello --list-cameras
libcamera-jpeg -o test.jpg
```

### Audio Issues

```bash
# List devices
arecord -l
aplay -l

# Test record/playback
arecord -d 3 test.wav && aplay test.wav
```

### Memory Usage Too High

- Reduce LLM context: `LLM_N_CTX` in config.py
- Use smaller STT model: Change `STT_MODEL = "tiny.en"`
- Reduce YOLO batch size: Already at 1
- Monitor with: `free -h` or `ps aux | grep python`

### Slow LLM Response

- Gemma 2B is designed for speed but still takes 5-30 seconds
- Reduce `LLM_MAX_TOKENS` to get faster responses
- Increase `LLM_TEMPERATURE` for faster but less coherent output
- Consider using quantized models

## 📊 Performance

**Typical timing on RPi5 (4GB):**

- Button debounce: 20ms
- Animation: 30 FPS (independent thread)
- Audio recording: Real-time
- STT (whisper tiny.en): 3-10 seconds per 5-second audio
- LLM generation: 10-30 seconds (Gemma 2B 4-bit)
- Object detection: 5-15 seconds (YOLOv8 nano)
- RAG query: <1 second

**Memory usage:**
- Base system: ~300MB
- With models loaded: ~1.2-1.5GB
- Peak during inference: ~1.8GB
- Still within 4GB limits with room for buffer

## 🔐 Security Notes

- All processing is local (no internet required)
- Models and code stay on device
- Audio and images stored locally only
- No telemetry or tracking

## 📚 Key Design Decisions

1. **Three Threads**: Animation, buttons, controller - minimal overhead
2. **Event-Driven**: Controller responds to button events asynchronously
3. **Non-Blocking**: Animation runs in dedicated thread, never freezes
4. **Modular Design**: Easy to replace any component
5. **Simulation Mode**: Gracefully handles missing hardware
6. **Efficient Models**: Quantized LLM, nano YOLO, lightweight embeddings

## 🎓 How It Works

### Push-to-Talk Workflow

1. K1 pressed → `ButtonManager` detects state change
2. Button event → Calls controller callback
3. Controller starts recording → `AudioRecorder` captures audio
4. K1 released → Recording stops, audio sent to STT
5. STT → `SpeechToText` converts to text
6. RAG query → `RAGMemory` retrieves relevant context
7. LLM generation → `LocalLLM` generates response with context
8. Store in memory → New interaction added to RAG
9. TTS → `TextToSpeech` speaks response
10. Display updates → Status shown on OLED
11. Animation continues → Eyes keep moving (independent)

### Animation Architecture

```
AnimationEngine (dedicated thread)
  └─ _animation_loop()
      ├─ Calculates eye positions based on loop progress
      ├─ Renders to OLED every 33ms (30 FPS)
      ├─ Updates app_state.animation_frame
      └─ Never blocks, never waits for other systems
```

The animation thread is completely independent. Even if LLM is thinking or audio is playing, the eyes keep moving smoothly.

## 🤝 Contributing

To extend the system:

1. Add new features to appropriate module
2. Keep components modular and independent
3. Use thread-safe access to shared state (`app_state`)
4. Add proper logging with `logging.getLogger(__name__)`
5. Handle errors gracefully with fallback behaviors

## 📝 License

This project is provided as-is for educational and personal use on Raspberry Pi systems.

## 🙏 Credits

- **Raspberry Pi Foundation**: RPi OS and libraries
- **OpenAI**: Whisper model
- **Google**: Gemma model
- **Ultralytics**: YOLOv8
- **Chroma**: ChromaDB
- **Meta**: Sentence-Transformers

---

**Status**: ✅ Fully functional on RPi5 (4GB)  
**Last Updated**: February 2026  
**Python Version**: 3.9+
