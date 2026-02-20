"""
Button Handler — GPIO button listener using gpiod (Pi 5 compatible).

K1 (GPIO17): Push-to-talk hold — hold to record, release to process.
K2 (GPIO27): Object detection on press.
K3 (GPIO22): Image capture on press.

Buttons use internal pull-up, active LOW.
"""

import logging
import os
import threading
import time

logger = logging.getLogger(__name__)


class ButtonHandler:
    """GPIO button listener using gpiod with event polling."""

    K1_PIN = 17  # Push-to-talk
    K2_PIN = 27  # Object detection
    K3_PIN = 22  # Image capture

    CHIP_CANDIDATES = ["gpiochip4", "gpiochip0", "gpiochip1", "gpiochip2"]

    def __init__(self, on_detect=None, on_capture=None, on_chat_start=None, on_chat_stop=None):
        self._on_detect = on_detect
        self._on_capture = on_capture
        self._on_chat_start = on_chat_start
        self._on_chat_stop = on_chat_stop

        self._k1_pressed = False
        self._busy = threading.Lock()
        self._alive = True
        self._thread = None
        self._request = None

        self._init_gpio()

    def _find_chip(self):
        """Auto-detect the correct GPIO chip for Pi 5."""
        import gpiod

        for name in self.CHIP_CANDIDATES:
            path = f"/dev/{name}"
            if os.path.exists(path):
                try:
                    chip = gpiod.Chip(path)
                    info = chip.get_info()
                    logger.info("Found GPIO chip: %s (%s, %d lines)",
                                path, info.label, info.num_lines)
                    if info.num_lines > max(self.K1_PIN, self.K2_PIN, self.K3_PIN):
                        return chip
                    chip.close()
                except Exception:
                    continue

        for entry in sorted(os.listdir("/dev")):
            if entry.startswith("gpiochip"):
                path = f"/dev/{entry}"
                try:
                    chip = gpiod.Chip(path)
                    info = chip.get_info()
                    if info.num_lines > max(self.K1_PIN, self.K2_PIN, self.K3_PIN):
                        logger.info("Using GPIO chip: %s (%s)", path, info.label)
                        return chip
                    chip.close()
                except Exception:
                    continue

        return None

    def _init_gpio(self):
        """Initialize GPIO using gpiod and start polling thread."""
        try:
            import gpiod
            from gpiod.line_settings import LineSettings, Direction, Bias, Edge

            chip = self._find_chip()
            if chip is None:
                logger.error("No suitable GPIO chip found!")
                for entry in sorted(os.listdir("/dev")):
                    if entry.startswith("gpiochip"):
                        logger.error("  Available: /dev/%s", entry)
                return

            settings = LineSettings(
                direction=Direction.INPUT,
                bias=Bias.PULL_UP,
                edge_detection=Edge.BOTH,
            )

            self._request = chip.request_lines(
                consumer="assistant-buttons",
                config={
                    self.K1_PIN: settings,
                    self.K2_PIN: settings,
                    self.K3_PIN: settings,
                },
            )

            self._thread = threading.Thread(target=self._poll_events, daemon=True)
            self._thread.start()

            logger.info(
                "GPIO buttons initialized via gpiod (K1=%d PTT, K2=%d detect, K3=%d capture)",
                self.K1_PIN, self.K2_PIN, self.K3_PIN,
            )

        except Exception as e:
            logger.error("Failed to initialize GPIO: %s", e)
            self._request = None

    def _poll_events(self):
        """Poll for GPIO edge events in a background thread."""
        while self._alive:
            try:
                if not self._request:
                    break
                if self._request.wait_edge_events(timeout=0.5):
                    events = self._request.read_edge_events()
                    for event in events:
                        self._handle_event(event)
            except Exception as e:
                logger.error("Event poll error: %s", e)
                time.sleep(0.1)

    def _handle_event(self, event):
        """Route GPIO events to the appropriate handler."""
        try:
            line = event.line_offset
            is_press = (event.event_type == event.Type.FALLING_EDGE)
            is_release = (event.event_type == event.Type.RISING_EDGE)

            if line == self.K2_PIN and is_press:
                self._on_k2_press()
            elif line == self.K3_PIN and is_press:
                self._on_k3_press()
            elif line == self.K1_PIN:
                if is_press:
                    self._on_k1_press()
                elif is_release:
                    self._on_k1_release()

        except Exception as e:
            logger.error("Event handler error: %s", e)

    def _on_k2_press(self):
        """K2 — object detection."""
        if not self._busy.acquire(blocking=False):
            logger.debug("K2 ignored — busy")
            return
        try:
            logger.info("K2 pressed — object detection")
            if self._on_detect:
                self._on_detect()
        except Exception as e:
            logger.error("K2 handler error: %s", e)
        finally:
            self._busy.release()

    def _on_k3_press(self):
        """K3 — image capture."""
        if not self._busy.acquire(blocking=False):
            logger.debug("K3 ignored — busy")
            return
        try:
            logger.info("K3 pressed — image capture")
            if self._on_capture:
                self._on_capture()
        except Exception as e:
            logger.error("K3 handler error: %s", e)
        finally:
            self._busy.release()

    def _on_k1_press(self):
        """K1 pressed — start push-to-talk recording."""
        if not self._busy.acquire(blocking=False):
            logger.debug("K1 ignored — busy")
            return
        self._k1_pressed = True
        logger.info("K1 pressed — start recording")
        try:
            if self._on_chat_start:
                self._on_chat_start()
        except Exception as e:
            logger.error("K1 start error: %s", e)

    def _on_k1_release(self):
        """K1 released — stop recording and process."""
        if not self._k1_pressed:
            return
        self._k1_pressed = False
        logger.info("K1 released — stop recording")
        try:
            if self._on_chat_stop:
                self._on_chat_stop()
        except Exception as e:
            logger.error("K1 stop error: %s", e)
        finally:
            try:
                self._busy.release()
            except RuntimeError:
                pass

    def cleanup(self):
        """Clean up GPIO resources."""
        try:
            self._alive = False
            if self._thread:
                self._thread.join(timeout=2)
            if self._request:
                self._request.release()
                self._request = None
            logger.info("GPIO cleaned up")
        except Exception as e:
            logger.error("GPIO cleanup error: %s", e)
