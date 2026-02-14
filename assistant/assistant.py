#!/usr/bin/env python3
"""
Raspberry Pi 5 Offline Multimodal AI Assistant — Main controller.
State machine: idle -> listening | object_mode -> capturing -> processing -> idle.
Single main loop; OLED kept responsive; GPIO buttons trigger transitions.
"""

import logging
import sys
import time
from pathlib import Path
from typing import Optional

# Project root = directory containing the "assistant" package
_script_dir = Path(__file__).resolve().parent
if (_script_dir / "config.py").exists():
    ROOT = _script_dir.parent  # script inside assistant/
else:
    ROOT = _script_dir  # script next to assistant/ (e.g. run_assistant.py)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from assistant.config import (
    PROJECT_ROOT,
    IMAGES_DIR,
    LOG_FILE,
    LOG_LEVEL,
    GPIO_BUTTONS,
    GPIO_BUTTON_LISTEN,
    GPIO_BUTTON_OBJECT,
    GPIO_BUTTON_CAPTURE,
    RECORD_SECONDS_MAX,
)
from assistant.display.oled_ui import OLEDDisplay
from assistant.vision.camera import CameraCapture
from assistant.vision.yolo_detect import YOLODetector
from assistant.audio.stt import SpeechToText
from assistant.audio.tts import TextToSpeech
from assistant.llm.llama_engine import LlamaEngine
from assistant.memory.rag import RAGMemory

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("assistant")

# -----------------------------------------------------------------------------
# State machine
# -----------------------------------------------------------------------------
STATE_IDLE = "idle"
STATE_LISTENING = "listening"
STATE_OBJECT_MODE = "object_mode"
STATE_CAPTURING = "capturing"
STATE_PROCESSING = "processing"


class Assistant:
    """Main assistant: state machine, GPIO, and subsystems."""

    def __init__(self) -> None:
        self.state = STATE_IDLE
        self.display = OLEDDisplay()
        self.camera = CameraCapture()
        self.yolo = YOLODetector()
        self.stt = SpeechToText()
        self.tts = TextToSpeech()
        self.llm = LlamaEngine()
        self.memory = RAGMemory()

        self._gpio_initialized = False
        self._running = True
        self._last_captured_path: Optional[Path] = None
        self._button_listen_pressed = False
        self._button_object_pressed = False
        self._button_capture_pressed = False
        self._debounce_until = 0.0

    def _gpio_setup(self) -> None:
        """Configure GPIO buttons (BCM) with pull-up; active low or high per wiring."""
        try:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            for name, pin in GPIO_BUTTONS.items():
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self._gpio_initialized = True
            logger.info("GPIO buttons configured: K1=%s K2=%s K3=%s", GPIO_BUTTON_LISTEN, GPIO_BUTTON_OBJECT, GPIO_BUTTON_CAPTURE)
        except Exception as e:
            logger.exception("GPIO setup failed: %s", e)
            self._gpio_initialized = False

    def _gpio_poll(self) -> None:
        """Poll buttons (non-blocking). Assumes active-low (press = 0)."""
        if not self._gpio_initialized:
            return
        try:
            import RPi.GPIO as GPIO
            self._button_listen_pressed = GPIO.input(GPIO_BUTTON_LISTEN) == GPIO.LOW
            self._button_object_pressed = GPIO.input(GPIO_BUTTON_OBJECT) == GPIO.LOW
            self._button_capture_pressed = GPIO.input(GPIO_BUTTON_CAPTURE) == GPIO.LOW
        except Exception as e:
            logger.debug("GPIO poll error: %s", e)

    def _gpio_cleanup(self) -> None:
        try:
            import RPi.GPIO as GPIO
            GPIO.cleanup()
            logger.info("GPIO cleanup done")
        except Exception as e:
            logger.debug("GPIO cleanup: %s", e)
        self._gpio_initialized = False

    def init_all(self) -> bool:
        """Initialize display, camera, YOLO, STT, TTS, LLM, RAG, GPIO."""
        ok = True
        ok &= self.display.init()
        self._gpio_setup()
        ok &= self.camera.init()
        ok &= self.yolo.init()
        ok &= self.stt.init()
        ok &= self.tts.init()
        ok &= self.llm.init()
        ok &= self.memory.init()
        return ok

    def run_idle(self, dt: float) -> None:
        """Idle: animate eyes, check buttons (debounced)."""
        self._gpio_poll()
        now = time.monotonic()
        if now < self._debounce_until:
            self.display.show_idle_frame(dt)
            return
        if self._button_listen_pressed:
            self._debounce_until = now + 0.4
            self.state = STATE_LISTENING
            return
        if self._button_object_pressed:
            self._debounce_until = now + 0.4
            self.state = STATE_OBJECT_MODE
            return
        self.display.show_idle_frame(dt)

    def run_listening(self) -> None:
        """Listening: record -> STT -> LLM (stream) -> TTS -> store in RAG -> idle."""
        self.display.show_listening()
        text = self.stt.listen_and_transcribe(duration_seconds=RECORD_SECONDS_MAX)
        if not text.strip():
            self.display.show_text("No speech detected")
            time.sleep(1.5)
            self.state = STATE_IDLE
            return

        # Optional: add RAG context for "where is my X?"
        context = self.memory.get_context_for_question(text)
        prompt = text
        if context:
            prompt = f"Context from memory:\n{context}\n\nUser question: {text}\n\nAnswer briefly:"

        self.display.show_text("Thinking...")
        full_response = ""
        try:
            for token in self.llm.stream_tokens(prompt, max_tokens=256):
                full_response += token
                self.display.show_tokens(full_response)
            if not full_response.strip():
                full_response = "I didn't get a response."
        except Exception as e:
            logger.exception("LLM error: %s", e)
            full_response = "Sorry, something went wrong."

        self.memory.add_conversation(text, full_response)
        self.display.show_text(full_response[:200])
        self.tts.speak(full_response)
        self.state = STATE_IDLE

    def run_object_mode(self) -> None:
        """Object mode: show message, wait for K3 to capture (debounced)."""
        self.display.show_object_mode()
        self._gpio_poll()
        now = time.monotonic()
        if now >= self._debounce_until and self._button_capture_pressed:
            self._debounce_until = now + 0.4
            self.state = STATE_CAPTURING

    def run_capturing(self) -> None:
        """Capture image, show Captured, run YOLO, summarize, speak, store in RAG, idle."""
        self.display.show_text("Capturing...")
        path = self.camera.capture()
        if path is None:
            self.display.show_text("Capture failed")
            time.sleep(2)
            self.state = STATE_IDLE
            return
        self._last_captured_path = path
        self.display.show_captured()
        time.sleep(0.5)
        self.state = STATE_PROCESSING

    def run_processing(self) -> None:
        """YOLO on last captured image, LLM summary, TTS, RAG, then idle."""
        if self._last_captured_path is None:
            self.state = STATE_IDLE
            return
        self.display.show_processing()
        labels, ann_path = self.yolo.detect(self._last_captured_path)
        if not labels:
            summary = "I didn't detect any objects in the image."
        else:
            obj_list = ", ".join(labels)
            self.memory.add_object_location(labels, str(self._last_captured_path), "")
            prompt = f"Briefly describe what is in the image in one sentence. Detected objects: {obj_list}."
            try:
                summary = self.llm.complete(prompt, max_tokens=80, stream=False)
                if not summary.strip():
                    summary = f"I see: {obj_list}."
            except Exception as e:
                logger.exception("LLM summary error: %s", e)
                summary = f"I see: {obj_list}."
        self.display.show_text(summary[:200])
        self.tts.speak(summary)
        self._last_captured_path = None
        self.state = STATE_IDLE

    def run_main_loop(self) -> None:
        """Single main loop: dispatch by state, keep OLED responsive."""
        last_t = time.monotonic()
        while self._running:
            t = time.monotonic()
            dt = t - last_t
            last_t = t

            if self.state == STATE_IDLE:
                self.run_idle(dt)
            elif self.state == STATE_LISTENING:
                self.run_listening()
            elif self.state == STATE_OBJECT_MODE:
                self.run_object_mode()
            elif self.state == STATE_CAPTURING:
                self.run_capturing()
            elif self.state == STATE_PROCESSING:
                self.run_processing()
            else:
                self.state = STATE_IDLE

            time.sleep(0.05)

    def cleanup(self) -> None:
        """Cleanup all subsystems and GPIO."""
        self._running = False
        self._gpio_cleanup()
        self.display.cleanup()
        self.camera.cleanup()
        self.yolo.cleanup()
        self.stt.cleanup()
        self.tts.cleanup()
        self.llm.cleanup()
        self.memory.cleanup()
        logger.info("Assistant cleanup complete")


def main() -> None:
    assistant = Assistant()
    if not assistant.init_all():
        logger.warning("Some subsystems failed to init; continuing anyway.")
    try:
        assistant.run_main_loop()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        assistant.cleanup()


if __name__ == "__main__":
    main()
