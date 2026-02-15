# Offline Multimodal AI Assistant (Raspberry Pi 5)

A fully offline, button-driven robotic assistant with animated OLED eyes. Runs on Raspberry Pi 5 (4GB RAM) with no cloud services and no wake word.

## Features

- **Push-to-Talk (K1)** — Hold to record, release to transcribe → LLM → speak response
- **Object detection (K2)** — Capture image, YOLOv8 detection, LLM explains the object
- **Capture (K3)** — Save current camera frame to `images/` with timestamp
- **OLED eyes** — State-driven animation: idle, listening, thinking, detecting, success, error

## Hardware

| Component | Details |
|-----------|--------|
| Board | Raspberry Pi 5 (4GB) |
| Display | 0.96" SSD1306 128×64 OLED (I2C) |
| K1 | GPIO 5 — Push-to-Talk |
| K2 | GPIO 6 — Object detection |
| K3 | GPIO 13 — Capture & save |
| Camera | Picamera2 |
| Audio in | USB microphone |
| Audio out | USB speaker |

## Software layout

```
assistant/
  main.py          # Entry; wires buttons, eyes, state, workers
  eyes.py          # OLED animation thread (state-driven)
  buttons.py       # GPIO poll thread (K1/K2/K3)
  audio.py         # Record / play WAV (PyAudio)
  stt.py           # Vosk offline STT
  tts.py           # Piper (preferred) or pyttsx3
  llm.py           # llama-cpp-python (Gemma 3 4B IT GGUF 4-bit)
  vision.py        # Picamera2 + YOLOv8
  state_manager.py # State machine (IDLE, LISTENING, THINKING, …)
  config.py        # Paths, GPIO, model paths
```

## Setup

1. **System (Raspberry Pi OS)**

   - Enable I2C: `sudo raspi-config` → Interface Options → I2C → Enable
   - Install system deps (e.g. `libportaudio2`, `portaudio19-dev` for PyAudio)

2. **Python**

   ```bash
   cd /path/to/mark69
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Models**

   - **LLM**: Place Gemma 3 4B IT GGUF (4-bit) at  
     `models/llama/gemma-3-4b-it-Q4_K_M.gguf`  
     (or set `LLAMA_MODEL_PATH` in `assistant/config.py`.)

   - **STT**: Download a Vosk small English model and extract to  
     `models/vosk/`  
     (e.g. directory name like `vosk-model-small-en-us-0.15`).

   - **TTS**: Option A — Install [Piper](https://github.com/rhasspy/piper) and place model + config in  
     `models/piper/`  
     (e.g. `en_US-lessac-medium.onnx` and `.onnx.json`).  
     Option B — Use pyttsx3 only (espeak); no extra files.

   - **YOLO**: `yolov8n.pt` is downloaded automatically by ultralytics on first run, or place it in `models/yolo/yolov8n.pt`.

4. **Wiring**

   - OLED: SDA → GPIO 2, SCL → GPIO 3, VCC → 3.3V, GND → GND  
   - K1, K2, K3: One side to GPIO 5, 6, 13 (BCM); other side to GND (active-low).

## Run

From project root:

```bash
source venv/bin/activate
python -m assistant.main
```

Or:

```bash
python assistant/main.py
```

Exit with Ctrl+C.

## Button logic

- **K1 (hold)**  
  - Press: state → LISTENING, wake-up eyes, start recording.  
  - Release: stop recording → THINKING → STT → LLM → TTS → play → IDLE.

- **K2**  
  - Press: state → DETECTING, capture + YOLOv8.  
  - No object: speak “I could not detect any object clearly.”, ERROR eyes, then IDLE.  
  - Object: THINKING → LLM “Explain what a &lt;object&gt; is…” → TTS → SUCCESS eyes → IDLE.

- **K3**  
  - Press: capture frame, save to `images/capture_YYYYMMDD_HHMMSS.jpg`, blink, stay IDLE.

## Configuration

Edit `assistant/config.py` for:

- GPIO pins (K1, K2, K3)
- Model paths (LLM, Vosk, Piper, YOLO)
- LLM context size, threads, max tokens
- OLED eye geometry and animation intervals

## Constraints

- Fully offline; no cloud APIs.
- Button-only; no wake word.
- Animation and button polling run in separate threads so the eyes keep updating during STT/LLM/TTS.

## License

Use and modify as needed for your project.
