# Offline Multimodal Robotic AI Assistant (Raspberry Pi 5)

Fully offline, button-driven robotic assistant with OLED eyes, voice (STT/TTS), LLM (Gemma 3 4B), and YOLOv8 object detection. Runs on **Raspberry Pi 5 (4GB)**.

## Hardware

| Component | Spec |
|-----------|------|
| Board | Raspberry Pi 5 (4GB) |
| Display | 0.96" OLED SSD1306 (128×64, I2C) |
| Buttons | Three-speed dial: K1 (PTT), K2 (Detect), K3 (Capture) |
| Camera | Raspberry Pi Camera (Picamera2) |
| Audio In | USB Microphone |
| Audio Out | USB Speaker |

### GPIO (BCM)

- **K1** (Push-to-Talk): GPIO17 (Pin 11)  
- **K2** (Object Detection): GPIO27 (Pin 13)  
- **K3** (Capture Only): GPIO22 (Pin 15)  

Buttons are **active LOW**; `gpiozero` with `pull_up=True`.

## Project layout

```
assistant/
  main.py          # Entry point
  config.py        # Paths, GPIO, model paths, tuning
  core/
    state_manager.py   # State machine (IDLE, LISTENING, THINKING, …)
    event_bus.py       # In-process events
  hardware/
    buttons.py     # K1/K2/K3 via gpiozero
    display.py     # OLED SSD1306
    eyes.py        # State-driven eye animations (separate thread)
    camera.py      # Picamera2 capture
  audio/
    recorder.py    # USB mic → PCM for Vosk
    stt.py         # Vosk (offline STT)
    tts.py         # Piper / espeak (offline TTS)
  ai/
    llm.py         # llama.cpp (Gemma 3 4B IT GGUF 4-bit)
    vision.py      # YOLOv8 (CPU)
  utils/
    image_saver.py # Save captures to /images
```

## Setup (Raspberry Pi OS)

### 1. System

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv i2c-tools libportaudio2 portaudio19-dev
sudo raspi-config  # Enable I2C, Camera
```

### 2. I2C and OLED

```bash
sudo i2cdetect -y 1   # Confirm SSD1306 at 0x3C
pip install adafruit-circuitpython-ssd1306 Pillow
# If needed: pip install adafruit-blinka
```

### 3. Virtual environment and dependencies

```bash
cd /path/to/mark69
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Models (all under `models/`)

- **LLM**: Gemma 3 4B IT GGUF (4-bit), e.g.  
  `models/gemma-3-4b-it-Q4_K_M.gguf`  
  Download from Hugging Face (e.g. `google/gemma-3-4b-it-GGUF`).

- **STT**: Vosk small EN-US  
  `models/vosk-model-small-en-us-0.15`  
  From [alphacephei/vosk-api](https://github.com/alphacephei/vosk-api).

- **TTS**: Piper voice (optional)  
  e.g. `models/piper/en_US-lessac-medium` (with `.onnx` + config).  
  Fallback: `espeak` (`sudo apt install espeak`).

- **Vision**: YOLOv8 nano  
  `models/yolov8n.pt`  
  Ultralytics will download on first use if missing, or place the file manually.

### 5. Config

Edit `assistant/config.py` if your paths differ:

- `LLM_MODEL_PATH`, `VOSK_MODEL_PATH`, `PIPER_MODEL_PATH`, `YOLO_MODEL_PATH`
- `IMAGES_DIR` (default: `mark69/images`)

## Run

From project root (so `assistant` is a package):

```bash
source venv/bin/activate
export PYTHONPATH=/path/to/mark69
python -m assistant.main
```

Or:

```bash
cd /path/to/mark69
python -m assistant.main
```

## Behavior

- **K1 (hold)**: Push-to-talk → LISTENING → record from USB mic → on release: STT → LLM → TTS → IDLE. Eyes: listening → thinking → speaking.
- **K2**: Object detection → DETECTING → capture → YOLOv8 → if object: LLM explains “what is & uses” → TTS → SUCCESS (happy eyes) → IDLE; else ERROR (double blink) → IDLE.
- **K3**: Capture frame → save to `images/` with timestamp → blink → IDLE.

Animation runs in a **dedicated thread** and never blocks on LLM or YOLO.

## Constraints

- **Fully offline**: no cloud APIs, no wake word.
- **Button-driven only**: K1/K2/K3.
- **Non-blocking**: animation thread independent of processing.
- **State-driven**: all transitions in `state_manager.py`.

## License

Use and modify as needed for your project.
