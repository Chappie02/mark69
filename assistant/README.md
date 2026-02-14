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
| **llm/llama_engine.py** | llama-cpp-python in-process LLM; streaming for OLED. |
| **download_models.py** | Script to download Vosk, Piper, YOLO, and embedding model (LLM you add yourself). |
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
3. **Models:**
   - **Automated (recommended):** From project root, run:
     ```bash
     python assistant/download_models.py
     ```
     This downloads **Vosk** (STT), **Piper** (TTS), **YOLO** (yolov8n.pt), and the **ChromaDB embedding** model into `assistant/models/`. Skip any with env vars: `SKIP_VOSK=1`, `SKIP_PIPER=1`, `SKIP_YOLO=1`, `SKIP_EMBED=1`.
   - **LLM (you provide):** Place your GGUF file at `assistant/models/llama/model.gguf`, or set `LLAMA_MODEL_PATH`. Not downloaded by the script.

4. **Run** from the directory that contains the `assistant/` folder (project root):
   ```bash
   python assistant/assistant.py
   ```
   Or:
   ```bash
   python assistant/download_models.py   # download models first
   ```
   If you have both `assistant.py` and an `assistant/` folder in the same directory, rename the file so it doesn’t shadow the package: `mv assistant.py run_assistant.py`, then run `python run_assistant.py` or `python assistant/assistant.py`.

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
