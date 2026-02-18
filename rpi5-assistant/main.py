import sys
import threading
import time
from core.logger import setup_logger
from hardware.oled import OLED
from hardware.animation import EyeAnimation
from hardware.buttons import ButtonHandler

logger = setup_logger()

def main():
    logger.info("System booting...")
    # OLED
    try:
        oled = OLED()
    except Exception as e:
        logger.error(f"OLED init failed: {e}")
        oled = None
    # Animation
    try:
        if oled:
            animation = EyeAnimation(oled)
            animation.start()
        else:
            logger.error("Animation not started: OLED unavailable.")
    except Exception as e:
        logger.error(f"Animation thread failed: {e}")
    # Buttons
    try:
        buttons = ButtonHandler()
    except Exception as e:
        logger.error(f"Button init failed: {e}")
        buttons = None
    # Audio
    try:
        import audio.recorder
        import audio.stt
        import audio.tts
        logger.info("Audio modules loaded.")
    except Exception as e:
        logger.error(f"Audio init failed: {e}")
    # LLM
    try:
        import ai.llm
        logger.info("LLM module loaded.")
    except Exception as e:
        logger.error(f"LLM init failed: {e}")
    # YOLO
    try:
        import ai.vision
        logger.info("YOLO module loaded.")
    except Exception as e:
        logger.error(f"YOLO init failed: {e}")
    # RAG
    try:
        import ai.rag
        logger.info("RAG module loaded.")
    except Exception as e:
        logger.error(f"RAG init failed: {e}")
    logger.info("System boot complete. Running main loop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        if buttons:
            buttons.cleanup()
        sys.exit(0)

if __name__ == "__main__":
    main()
