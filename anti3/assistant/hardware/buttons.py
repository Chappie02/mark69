"""
Button Handler — GPIO button listener for K1, K2, K3.

K2 (GPIO27): Object detection on press.
K3 (GPIO22): Short press (<1s) = capture, Hold (>=1s) = LLM chat.
K1 (GPIO17): Currently unused (reserved).

Buttons use pull_up=True, active LOW.
"""

import logging
import threading
import time

logger = logging.getLogger(__name__)


class ButtonHandler:
    """GPIO button listener with press-duration detection for K3."""

    # Pin assignments (BCM mode)
    K1_PIN = 17  # Reserved
    K2_PIN = 27  # Object detection
    K3_PIN = 22  # Short press: capture  |  Hold: chat

    def __init__(self, on_detect=None, on_capture=None, on_chat_start=None, on_chat_stop=None):
        """
        Args:
            on_detect: Callback for K2 press (object detection).
            on_capture: Callback for K3 short press (image capture).
            on_chat_start: Callback when K3 hold begins (start recording).
            on_chat_stop: Callback when K3 is released after hold (stop recording).
        """
        self._on_detect = on_detect
        self._on_capture = on_capture
        self._on_chat_start = on_chat_start
        self._on_chat_stop = on_chat_stop

        self._k3_press_time = 0
        self._k3_held = False
        self._busy = threading.Lock()  # Prevent concurrent feature execution
        self._gpio = None

        self._init_gpio()

    def _init_gpio(self):
        """Initialize GPIO pins and event detection."""
        try:
            import RPi.GPIO as GPIO

            self._gpio = GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)

            # Setup pins with pull-up resistors
            GPIO.setup(self.K2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.K3_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            # K2: Object detection on falling edge
            GPIO.add_event_detect(
                self.K2_PIN, GPIO.FALLING,
                callback=self._on_k2_press,
                bouncetime=300,
            )

            # K3: Detect both press and release
            GPIO.add_event_detect(
                self.K3_PIN, GPIO.BOTH,
                callback=self._on_k3_event,
                bouncetime=50,
            )

            logger.info("GPIO buttons initialized (K2=%d, K3=%d)", self.K2_PIN, self.K3_PIN)
        except Exception as e:
            logger.error("Failed to initialize GPIO: %s", e)
            self._gpio = None

    def _on_k2_press(self, channel):
        """Handle K2 button press — object detection."""
        if not self._busy.acquire(blocking=False):
            logger.debug("K2 press ignored — system busy")
            return

        try:
            logger.info("K2 pressed — object detection")
            if self._on_detect:
                self._on_detect()
        except Exception as e:
            logger.error("K2 handler error: %s", e)
        finally:
            self._busy.release()

    def _on_k3_event(self, channel):
        """Handle K3 press/release — capture or chat."""
        try:
            if self._gpio is None:
                return

            # Active LOW: pressed = LOW (0), released = HIGH (1)
            if self._gpio.input(self.K3_PIN) == 0:
                # Button pressed
                self._k3_press_time = time.time()
                self._k3_held = False

                # Start a timer thread to detect hold
                threading.Thread(
                    target=self._k3_hold_check, daemon=True
                ).start()
            else:
                # Button released
                duration = time.time() - self._k3_press_time

                if self._k3_held:
                    # Was in chat mode — stop recording
                    logger.info("K3 released after hold (%.1fs) — stop recording", duration)
                    if self._on_chat_stop:
                        self._on_chat_stop()
                elif duration < 1.0:
                    # Short press — capture image
                    if not self._busy.acquire(blocking=False):
                        logger.debug("K3 short press ignored — system busy")
                        return
                    try:
                        logger.info("K3 short press (%.1fs) — image capture", duration)
                        if self._on_capture:
                            self._on_capture()
                    except Exception as e:
                        logger.error("K3 capture handler error: %s", e)
                    finally:
                        self._busy.release()

        except Exception as e:
            logger.error("K3 event handler error: %s", e)

    def _k3_hold_check(self):
        """Background check: if K3 is still held after 1 second, enter chat mode."""
        time.sleep(1.0)
        try:
            if self._gpio is None:
                return

            # Check if button is still pressed (active LOW)
            if self._gpio.input(self.K3_PIN) == 0:
                if not self._busy.acquire(blocking=False):
                    logger.debug("K3 hold ignored — system busy")
                    return

                self._k3_held = True
                logger.info("K3 held >= 1s — entering chat mode")
                if self._on_chat_start:
                    self._on_chat_start()
                # Note: busy lock is released in chat_stop handler via controller
        except Exception as e:
            logger.error("K3 hold check error: %s", e)

    def release_busy(self):
        """Release the busy lock (called by controller after chat completes)."""
        try:
            self._busy.release()
        except RuntimeError:
            pass  # Already released

    def cleanup(self):
        """Clean up GPIO resources."""
        try:
            if self._gpio:
                self._gpio.cleanup()
                logger.info("GPIO cleaned up")
        except Exception as e:
            logger.error("GPIO cleanup error: %s", e)
