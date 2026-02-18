## Model Downloads

### LLM (Gemma)
- Visit: https://huggingface.co/google/gemma-2b-it-GGUF
- Download: `gemma-2b-it-q4_K_M.gguf` (or compatible GGUF quantized file)
- Place in `models/` as `gemma.gguf`

### YOLOv8
- Visit: https://github.com/ultralytics/assets/releases/latest
- Download: `yolov8n.pt` (nano) or `yolov8s.pt` (small) for best Pi 5 performance
- Place in `models/` as `yolo.pt`
- Example:
  ```sh
  cd models
  wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -O yolo.pt
  ```

### Speech-to-Text (STT)
- Recommended: [Vosk Model](https://alphacephei.com/vosk/models)
- Download: `vosk-model-small-en-us-0.15` (or language of choice)
- Extract and place the folder in `models/` as `stt/`
- Example:
  ```sh
  cd models
  wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
  unzip vosk-model-small-en-us-0.15.zip
  mv vosk-model-small-en-us-0.15 stt
  ```

### Text-to-Speech (TTS)
- Recommended: [Coqui TTS](https://github.com/coqui-ai/TTS) or [espeak-ng](https://github.com/espeak-ng/espeak-ng)
- For Coqui TTS, download a pre-trained model (see their docs) and place in `models/tts/`
- For espeak-ng, install via apt:
  ```sh
  sudo apt install espeak-ng
  ```

# rpi5-assistant

A fully offline, multimodal AI assistant for Raspberry Pi 5 (4GB RAM).

## Features
- OLED 0.96" animated eyes (SSD1306, I2C)
- 3-button dial switch (Push-to-talk, Object detection, Capture)
- USB microphone and speaker
- Pi Camera (Picamera2)
- Offline LLM (llama.cpp, Gemma)
- YOLOv8 object detection
- ChromaDB-based RAG (conversations, object logs)
- Robust error handling: system never crashes if a module fails

## Hardware GPIO Mapping (BCM)
- K1 (Push-to-talk): GPIO17
- K2 (Object detection): GPIO27
- K3 (Capture only): GPIO22

## Project Structure
```
rpi5-assistant/
├── main.py
├── config.py
│
├── core/
│   ├── controller.py
│   ├── state.py
│   └── logger.py
│
├── hardware/
│   ├── buttons.py
│   ├── oled.py
│   └── animation.py
│
├── audio/
│   ├── recorder.py
│   ├── stt.py
│   └── tts.py
│
├── ai/
│   ├── llm.py
│   ├── vision.py
│   ├── rag.py
│   └── embeddings.py
│
├── storage/
│   ├── images/
│   └── vectordb/
└── models/
```

## Boot Sequence
1. Initialize logger
2. Initialize OLED
3. Start animation thread (5s eye loop, never freezes)
4. Initialize buttons
5. Initialize: Audio, LLM, YOLO, RAG (each logs success/failure, never crashes)

## Animation
- 5-second loop: center, left, center, right, blink
- Uses Pillow + adafruit-circuitpython-ssd1306
- Runs in a daemon thread, never blocks main logic

## Button Actions
- **K1 (Push-to-talk):**
  - Hold: Record audio
  - Release: STT → RAG → LLM → TTS
- **K2 (Object detection):**
  - Capture image, run YOLO, store detection, explain with LLM, speak
- **K3 (Capture only):**
  - Capture image, save to storage/images

## Error Handling
- All modules use try/except and log errors
- System continues running even if any module fails

## Requirements
- Raspberry Pi 5 (4GB+ recommended)
- Python 3.9+
- RPi.GPIO, Pillow, adafruit-circuitpython-ssd1306, llama-cpp-python, ultralytics, chromadb, picamera2, etc.


## Setup
1. Install dependencies:
  ```sh
  sudo apt update
  sudo apt install python3-pip python3-pil python3-picamera2 i2c-tools
  pip install RPi.GPIO pillow adafruit-circuitpython-ssd1306 llama-cpp-python ultralytics chromadb
  ```
2. Enable I2C on Raspberry Pi (raspi-config)
3. Download and place models as described above (LLM, YOLO, STT, TTS)
4. Run:
  ```sh
  python3 main.py
  ```

## License
MIT
