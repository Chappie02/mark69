# Raspberry Pi 5 Offline Multimodal AI Assistant

State-machine-based assistant with OLED UI, offline STT/TTS, YOLO object detection, local LLM (llama.cpp), and ChromaDB RAG memory.

## Where Each File Goes

All paths are relative to the **project folder** (e.g. `mark69/assistant/` or wherever you place `assistant/`):

| Path | Purpose |
|------|--------|
| **assistant.py** | Main entry; state machine loop and GPIO. Run this. |
| **config.py** | Central config: GPIO pins, OLED I2C, paths, model paths, etc. |
| **requirements.txt** | Python dependencies. |
| **display/oled_ui.py** | SSD1306 OLED driver and UI (text, listening, tokens). |
| **display/animations.py** | Robot eye idle animation (non-blocking). |
| **vision/camera.py** | Picamera2 capture; saves to `images/`. |
| **vision/yolo_detect.py** | Ultralytics YOLO; Pi-optimized; saves original + annotated. |
| **audio/stt.py** | Offline STT (Vosk). |
| **audio/tts.py** | Offline TTS (Piper / pyttsx3). |
| **llm/llama_engine.py** | llama.cpp HTTP client; streaming for OLED. |
| **memory/rag.py** | ChromaDB: conversations + object locations (“Where is my bottle?”). |
| **images/** | Captured and annotated images. |
| **memory/chroma_db/** | ChromaDB persistent store (created at runtime). |
| **logs/** | Log file (created at runtime). |

## Hardware

- **Raspberry Pi 5**
- **OLED:** 0.96" SSD1306 I2C, address `0x3C`
- **Camera:** Pi Camera (Picamera2)
- **Mic:** USB microphone
- **Speaker:** USB or Bluetooth speaker
- **Buttons:**  
  - K1 = GPIO 17 → Listening  
  - K2 = GPIO 27 → Object Mode  
  - K3 = GPIO 22 → Capture

## Setup

1. **OS / I2C:** Enable I2C and (if needed) camera; reboot.
2. **Python:** Use a venv (recommended):
   ```bash
   cd /path/to/mark69
   python3 -m venv venv
   source venv/bin/activate
   pip install -r assistant/requirements.txt
   ```
3. **Models (you must provide):**
   - **Vosk:** Download a small English model, set `VOSK_MODEL_PATH` (or put in `assistant/models/vosk-model-small-en-us-0.15`).
   - **Piper:** Download Piper voice, set `PIPER_MODEL_PATH` (or put in `assistant/models/piper`).
   - **llama.cpp:** Run the server elsewhere (or on Pi) and set `LLAMA_CPP_SERVER_URL` (e.g. `http://127.0.0.1:8080`).
   - **YOLO:** Uses `yolov8n.pt` by default (downloads once); or set `YOLO_MODEL_PATH`.

4. **Run from project root** (parent of `assistant/`):
   ```bash
   python assistant/assistant.py
   ```
   Or:
   ```bash
   cd assistant && python -m assistant.assistant
   ```
   (from the folder that contains the `assistant` package).

## States

- **idle:** Robot eyes on OLED; wait for K1 or K2.
- **listening (K1):** “Listening…” → record → STT → LLM (stream on OLED) → TTS → store in RAG → idle.
- **object_mode (K2):** “Object Mode” → wait for K3.
- **capturing (K3):** Capture image → “Captured” → processing.
- **processing:** YOLO → LLM summary → TTS → store object location in RAG → idle.

## RAG / “Where is my bottle?”

Conversations and object locations (with image path) are stored in ChromaDB. Questions like “Where is my bottle?” are answered using this context plus the LLM.

## Notes

- **GPIO:** Buttons are polled; debounced (~0.4 s). Assumes active-low (pull-up, press = LOW).
- **Cleanup:** On exit (Ctrl+C), GPIO and all subsystems are cleaned up.
- **Performance:** Single main loop; OLED updates and animations are non-blocking; LLM and TTS run in the main thread (can be moved to threads later if needed).
