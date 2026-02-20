# 🤖 Raspberry Pi 5 Offline AI Assistant

A fully offline AI assistant for Raspberry Pi 5 (4GB RAM) featuring object detection, image capture, and LLM-powered voice chat — all running locally without internet.

---

## ✨ Features

| Feature | Trigger | Description |
|---------|---------|-------------|
| **Object Detection** | K2 (GPIO27) press | Captures image → YOLOv8 → speaks detected object |
| **Image Capture** | K3 (GPIO22) press | Saves timestamped photo to `storage/images/` |
| **LLM Chat** | K1 (GPIO17) hold | Push-to-talk → STT → LLM → streams tokens on OLED → TTS |

All three features are **completely isolated** — they never call each other.

A continuous **robot eye animation** runs on the OLED and pauses only during feature processing.

---

## 🔧 Hardware

| Component | Details |
|-----------|---------|
| Board | Raspberry Pi 5 (4GB RAM) |
| Display | 0.96" SSD1306 OLED (128×64, I2C) |
| Camera | Pi Camera Module (Picamera2) |
| Microphone | USB microphone |
| Speaker | USB speaker |
| Buttons | K1 (GPIO17) PTT, K2 (GPIO27) detect, K3 (GPIO22) capture |

### Wiring

```
SSD1306 OLED:
  VCC → 3.3V
  GND → GND
  SCL → GPIO3 (SCL)
  SDA → GPIO2 (SDA)

Buttons (active LOW, internal pull-up):
  K1 → GPIO17 (push-to-talk chat)
  K2 → GPIO27 (object detection)
  K3 → GPIO22 (image capture)
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
│   └── buttons.py       # GPIO button handler (gpiod)
├── audio/
│   ├── recorder.py      # USB mic recording
│   ├── stt.py           # Offline STT (faster-whisper)
│   └── tts.py           # Offline TTS (piper)
├── ai/
│   ├── vision.py        # YOLOv8 + Picamera2
│   └── llm.py           # LLM chat (llama.cpp)
├── models/              # AI models (auto-downloaded)
└── storage/images/      # Captured images
```

---

## 🚀 Installation

### 1. System Dependencies

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv python3-picamera2 \
    libopenblas-dev libasound2-dev portaudio19-dev \
    libgpiod-dev wget git i2c-tools

# Enable I2C and camera
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_camera 0
```

### 2. Python Environment

```bash
cd ~/Desktop/anti3
python3 -m venv --system-site-packages venv
source venv/bin/activate
pip install -r assistant/requirements.txt
```

> **Important:** Use `--system-site-packages` so the venv can access the system-installed `picamera2`. Do NOT install picamera2 via pip — the system package has proper camera bindings.

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
| **K1** | Hold → speak → release | Records speech → AI response on OLED + speaker |
| **K2** | Press | Detects objects, shows label, speaks it |
| **K3** | Press | Captures and saves image |

### Boot Sequence

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
| **GPIO** | Button event polling (daemon) |

Only 3 threads total.

---

## 🛡️ Error Handling

- Every handler wraps operations in `try/except/finally`
- Animation **always** resumes after any feature (success or failure)
- Model load failures are handled gracefully
- System never crashes — errors are logged and operation continues

---

## 🔍 Troubleshooting

| Issue | Solution |
|-------|----------|
| OLED not showing | `sudo i2cdetect -y 1` — should show `0x3c` |
| Camera not found | Check cable, run `libcamera-hello --list-cameras` |
| Camera `list index out of range` | `pip uninstall picamera2` — use system package |
| No audio input | `arecord -l` to list USB mics |
| No audio output | `aplay -l`, test: `speaker-test -t wav` |
| LLM out of memory | Use smaller GGUF model (Q2_K) |
| GPIO not working | Check wiring, verify `ls /dev/gpiochip*` |

---

## 📝 License

MIT License
