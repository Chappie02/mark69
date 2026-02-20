# 🤖 Raspberry Pi 5 Offline AI Assistant

A fully offline AI assistant for Raspberry Pi 5 (4GB RAM) featuring object detection, image capture, and LLM-powered voice chat — all running locally without internet.

![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi%205-red)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Features

| Feature | Trigger | Description |
|---------|---------|-------------|
| **Object Detection** | K2 (GPIO27) | Captures image → YOLOv8 inference → speaks detected object |
| **Image Capture** | K3 short press (<1s) | Saves timestamped photo to `storage/images/` |
| **LLM Chat** | K3 hold (≥1s) | Push-to-talk → STT → LLM → streams tokens on OLED → TTS |

All three features are **completely isolated** — they never call each other.

A continuous **robot eye animation** runs on the OLED display and pauses only during feature processing.

---

## 🔧 Hardware

| Component | Details |
|-----------|---------|
| Board | Raspberry Pi 5 (4GB RAM) |
| Display | 0.96" SSD1306 OLED (128×64, I2C) |
| Camera | Pi Camera Module (via Picamera2) |
| Microphone | USB microphone |
| Speaker | USB speaker |
| Buttons | K1 (GPIO17), K2 (GPIO27), K3 (GPIO22) |

### Wiring

```
SSD1306 OLED:
  VCC → 3.3V
  GND → GND
  SCL → GPIO3 (SCL)
  SDA → GPIO2 (SDA)

Buttons (active LOW, pull-up):
  K1 → GPIO17 (reserved)
  K2 → GPIO27 (object detection)
  K3 → GPIO22 (capture / chat)
```

---

## 📁 Project Structure

```
assistant/
├── main.py              # Entry point
├── controller.py        # Feature orchestrator
├── hardware/
│   ├── oled.py          # OLED display driver
│   ├── animation.py     # Robot eye animation
│   └── buttons.py       # GPIO button handler
├── audio/
│   ├── recorder.py      # USB microphone recording
│   ├── stt.py           # Offline speech-to-text (Whisper)
│   └── tts.py           # Offline text-to-speech (Piper)
├── ai/
│   ├── vision.py        # YOLOv8 object detection
│   └── llm.py           # LLM chat (llama.cpp)
├── models/              # AI model files (auto-downloaded)
└── storage/
    └── images/           # Captured images
```

---

## 🚀 Installation

### 1. System Dependencies

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv \
    libopenblas-dev libasound2-dev portaudio19-dev \
    wget git i2c-tools

# Enable I2C
sudo raspi-config nonint do_i2c 0

# Enable camera
sudo raspi-config nonint do_camera 0
```

### 2. Python Environment

```bash
cd ~/Desktop/anti3
python3 -m venv venv
source venv/bin/activate
pip install -r assistant/requirements.txt
```

### 3. Install Piper TTS

```bash
pip install piper-tts
```

### 4. Download Models

```bash
bash setup_models.sh
```

This downloads:
- **YOLOv8n** (~6MB) — lightweight object detection
- **TinyLlama 1.1B Q4_K_M** (~670MB) — small LLM for chat
- **Piper TTS voice** (~100MB) — English voice model
- **Whisper tiny** (~75MB) — auto-downloads on first run

---

## ▶️ Usage

```bash
cd ~/Desktop/anti3/assistant
source ../venv/bin/activate
python3 main.py
```

### Controls

| Button | Action | Result |
|--------|--------|--------|
| **K2** | Press | Detects objects, shows label, speaks it |
| **K3** | Quick press (<1s) | Captures and saves image |
| **K3** | Hold ≥1s then release | Records speech → AI response on OLED + speaker |

### Startup Sequence

1. OLED shows "Booting..."
2. Models load (Vision → LLM → Audio)
3. OLED shows "Ready!"
4. Robot eye animation begins
5. System waits for button input

---

## 🧵 Threading Model

| Thread | Role |
|--------|------|
| **Main** | Initialization + feature processing |
| **Animation** | Continuous eye loop (daemon) |
| **GPIO** | Button interrupt callbacks |

Only 3 threads total. No thread pool or excessive threading.

---

## 🛡️ Error Handling

- Every feature handler wraps operations in `try/except`
- Errors are logged, never crash the system
- Animation **always** resumes after any feature completes (success or failure)
- Model load failures are handled gracefully with fallback messages
- Camera errors return the system to idle state

---

## 🔍 Troubleshooting

| Issue | Solution |
|-------|----------|
| OLED not showing | Check I2C: `sudo i2cdetect -y 1` (should show `0x3c`) |
| No audio input | Check USB mic: `arecord -l` |
| No audio output | Check speaker: `aplay -l`, test: `speaker-test -t wav` |
| Camera error | Check: `libcamera-hello --list-cameras` |
| LLM out of memory | Use a smaller GGUF model (Q2_K or smaller) |
| Buttons unresponsive | Verify GPIO wiring, check `gpio readall` |

---

## 📝 License

MIT License — See [LICENSE](LICENSE) for details.
