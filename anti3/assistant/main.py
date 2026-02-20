"""
Main Entry Point — Raspberry Pi 5 Offline AI Assistant.

Initializes all modules, starts animation and button listener,
and keeps the main thread alive for signal handling.
"""

import logging
import signal
import sys
import time

# ─────────────────────────────────────────
# Logging
# ─────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")


def main():
    """Initialize and run the AI assistant."""
    logger.info("=" * 50)
    logger.info("Raspberry Pi 5 Offline AI Assistant")
    logger.info("=" * 50)

    # ── Hardware ──────────────────────────

    logger.info("Initializing OLED display...")
    from hardware.oled import OLEDDisplay
    oled = OLEDDisplay()
    oled.show_text("Booting...")

    logger.info("Initializing eye animation...")
    from hardware.animation import EyeAnimation
    animation = EyeAnimation(oled)

    # ── AI Models ─────────────────────────

    logger.info("Loading vision model...")
    oled.show_text("Loading\nVision...")
    from ai.vision import ObjectDetector
    vision = ObjectDetector()

    logger.info("Loading LLM model...")
    oled.show_text("Loading\nLLM...")
    from ai.llm import LLMChat
    llm = LLMChat()

    # ── Audio ─────────────────────────────

    logger.info("Initializing audio...")
    oled.show_text("Loading\nAudio...")
    from audio.recorder import AudioRecorder
    from audio.stt import SpeechToText
    from audio.tts import TextToSpeech

    recorder = AudioRecorder()
    stt = SpeechToText()
    tts = TextToSpeech()

    # ── Controller ────────────────────────

    logger.info("Initializing controller...")
    from controller import Controller
    controller = Controller(
        oled=oled,
        animation=animation,
        vision=vision,
        recorder=recorder,
        stt=stt,
        llm=llm,
        tts=tts,
    )

    # ── Buttons ───────────────────────────

    logger.info("Initializing buttons...")
    from hardware.buttons import ButtonHandler
    buttons = ButtonHandler(
        on_detect=controller.handle_object_detection,
        on_capture=controller.handle_image_capture,
        on_chat_start=controller.handle_chat_start,
        on_chat_stop=controller.handle_chat_stop,
    )

    # ── Start Animation ───────────────────

    logger.info("Starting eye animation...")
    animation.start()
    oled.show_text("Ready!")
    time.sleep(1)

    logger.info("System ready — waiting for button inputs")
    logger.info("K1 (GPIO17): Hold = Push-to-Talk Chat")
    logger.info("K2 (GPIO27): Object Detection")
    logger.info("K3 (GPIO22): Image Capture")

    # ── Shutdown Handler ──────────────────

    shutdown_called = False

    def shutdown(signum, frame):
        nonlocal shutdown_called
        if shutdown_called:
            return
        shutdown_called = True

        logger.info("Shutting down...")
        animation.stop()
        vision.cleanup()
        buttons.cleanup()
        oled.show_text("Goodbye!")
        time.sleep(1)
        oled.clear()
        logger.info("Shutdown complete")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # ── Main Loop ─────────────────────────

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown(None, None)


if __name__ == "__main__":
    try:
        print("Starting AI Assistant...", flush=True)
        main()
    except Exception as e:
        import traceback
        print(f"\n{'='*50}", file=sys.stderr, flush=True)
        print(f"FATAL ERROR: {e}", file=sys.stderr, flush=True)
        print(f"{'='*50}", file=sys.stderr, flush=True)
        traceback.print_exc()
        sys.exit(1)
