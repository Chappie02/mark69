"""
Controller — Orchestrates features with strict separation.

Each handler is independent, catches all exceptions,
and always returns the system to animation idle state.
"""

import logging
import time
import threading

logger = logging.getLogger(__name__)


class Controller:
    """Feature orchestrator — connects buttons to AI features."""

    def __init__(self, oled, animation, vision, recorder, stt, llm, tts):
        self._oled = oled
        self._animation = animation
        self._vision = vision
        self._recorder = recorder
        self._stt = stt
        self._llm = llm
        self._tts = tts
        self._processing_lock = threading.Lock()

    # ─────────────────────────────────────────────
    # FEATURE 1: Object Detection (K2)
    # ─────────────────────────────────────────────

    def handle_object_detection(self):
        """K2 pressed — detect objects via YOLO."""
        try:
            logger.info("=== FEATURE 1: Object Detection ===")
            self._animation.pause()
            self._oled.show_text("Detecting...")

            image_path, label = self._vision.detect_first_object()

            if label:
                self._oled.show_text(f"Detected:\n{label}")
                logger.info("Object detected: %s", label)
                self._tts.speak(f"I see a {label}")
            else:
                self._oled.show_text("No object\ndetected")
                logger.info("No object detected")
                self._tts.speak("I don't see any objects")

        except Exception as e:
            logger.error("Object detection error: %s", e)
            self._oled.show_text("Error!")

        finally:
            time.sleep(1)
            self._animation.resume()
            logger.info("=== Object Detection Complete ===")

    # ─────────────────────────────────────────────
    # FEATURE 2: Image Capture (K3)
    # ─────────────────────────────────────────────

    def handle_image_capture(self):
        """K3 pressed — capture and save image."""
        try:
            logger.info("=== FEATURE 2: Image Capture ===")
            self._animation.pause()
            self._oled.show_text("Capturing...")

            filepath = self._vision.capture_and_save_image()

            if filepath:
                self._oled.show_text("Image Saved")
                logger.info("Image saved: %s", filepath)
            else:
                self._oled.show_text("Capture\nFailed")
                logger.error("Image capture failed")

        except Exception as e:
            logger.error("Image capture error: %s", e)
            self._oled.show_text("Error!")

        finally:
            time.sleep(1.5)
            self._animation.resume()
            logger.info("=== Image Capture Complete ===")

    # ─────────────────────────────────────────────
    # FEATURE 3: LLM Chat (K1 push-to-talk)
    # ─────────────────────────────────────────────

    def handle_chat_start(self):
        """K1 pressed — enter chat mode, start recording."""
        try:
            logger.info("=== FEATURE 3: Chat Mode — Recording ===")
            self._animation.pause()
            self._oled.clear()
            self._oled.show_text("Listening...")
            self._recorder.start_recording()

        except Exception as e:
            logger.error("Chat start error: %s", e)
            self._oled.show_text("Error!")
            self._animation.resume()

    def handle_chat_stop(self):
        """K1 released — process recording through STT → LLM → TTS."""
        try:
            logger.info("=== Chat Mode — Processing ===")
            self._oled.show_text("Processing...")

            # Stop recording
            audio_path = self._recorder.stop_recording()

            if not audio_path:
                self._oled.show_text("No audio\ncaptured")
                self._tts.speak("I didn't hear anything")
                return

            # Speech-to-text
            self._oled.show_text("Transcribing...")
            text = self._stt.transcribe(audio_path)

            if not text:
                self._oled.show_text("Could not\nunderstand")
                self._tts.speak("I couldn't understand that")
                return

            logger.info("User said: '%s'", text)
            self._oled.show_text(f"You: {text}")
            time.sleep(0.5)

            # LLM response — stream tokens to OLED
            self._oled.show_text("Thinking...")
            full_response = ""

            for token in self._llm.chat(text):
                full_response += token
                self._oled.show_text_streaming(full_response)

            logger.info("LLM response: '%s'", full_response.strip())

            # Speak the response
            if full_response.strip():
                self._tts.speak(full_response.strip())

        except Exception as e:
            logger.error("Chat processing error: %s", e)
            self._oled.show_text("Error!")

        finally:
            time.sleep(1)
            self._animation.resume()
            logger.info("=== Chat Mode Complete ===")
