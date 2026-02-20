"""
Robot Eye Animation — Continuous eye animation on OLED display.

5-second loop: Center → Slow left → Center → Slow right → Blink → repeat.
Runs in a daemon thread. Pausable via pause()/resume().
"""

import logging
import threading
import time

logger = logging.getLogger(__name__)

# Eye geometry constants
REF_EYE_HEIGHT = 40
REF_EYE_WIDTH = 40
REF_SPACE_BETWEEN = 10
REF_CORNER_RADIUS = 10


class EyeAnimation:
    """Continuous robot eye animation running in a background thread."""

    def __init__(self, oled):
        self._oled = oled
        self._running = threading.Event()
        self._running.set()  # Start in "running" state
        self._alive = True
        self._thread = None

        # Eye state
        self._left_eye_height = REF_EYE_HEIGHT
        self._left_eye_width = REF_EYE_WIDTH
        self._right_eye_height = REF_EYE_HEIGHT
        self._right_eye_width = REF_EYE_WIDTH

        center_x = self._oled.width // 2
        center_y = self._oled.height // 2
        self._left_eye_x = center_x - REF_EYE_WIDTH // 2 - REF_SPACE_BETWEEN // 2
        self._left_eye_y = center_y
        self._right_eye_x = center_x + REF_EYE_WIDTH // 2 + REF_SPACE_BETWEEN // 2
        self._right_eye_y = center_y

    def start(self):
        """Start the animation thread."""
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("Eye animation thread started")

    def pause(self):
        """Pause animation (for feature processing)."""
        self._running.clear()
        logger.debug("Animation paused")

    def resume(self):
        """Resume animation."""
        self._running.set()
        logger.debug("Animation resumed")

    def stop(self):
        """Stop the animation thread permanently."""
        self._alive = False
        self._running.set()  # Unblock if paused
        if self._thread:
            self._thread.join(timeout=3)
        logger.info("Eye animation thread stopped")

    def _loop(self):
        """Main animation loop — 5-second cycle."""
        try:
            self._center_eyes()
            while self._alive:
                # Wait if paused
                self._running.wait()
                if not self._alive:
                    break

                try:
                    # Phase 1: Center (0.8s)
                    self._center_eyes()
                    self._sleep_check(0.8)

                    # Phase 2: Slow look left (1.0s)
                    self._look_left()
                    self._sleep_check(1.0)

                    # Phase 3: Center (0.8s)
                    self._center_eyes()
                    self._sleep_check(0.8)

                    # Phase 4: Slow look right (1.0s)
                    self._look_right()
                    self._sleep_check(1.0)

                    # Phase 5: Center + Blink (0.4s)
                    self._center_eyes()
                    self._sleep_check(0.2)
                    self._blink()
                    self._sleep_check(0.2)

                except Exception as e:
                    logger.error("Animation cycle error: %s", e)
                    time.sleep(0.5)

        except Exception as e:
            logger.error("Animation loop crashed: %s", e)

    def _sleep_check(self, duration):
        """Sleep in small increments, checking alive and running status."""
        end_time = time.time() + duration
        while time.time() < end_time and self._alive and self._running.is_set():
            time.sleep(0.05)

    def _draw_eyes(self):
        """Render current eye state to OLED."""
        try:
            image, draw = self._oled.get_image_and_draw()
            w = self._oled.width
            h = self._oled.height

            # Clear
            draw.rectangle((0, 0, w, h), fill=0)

            # Left eye
            lx = int(self._left_eye_x - self._left_eye_width / 2)
            ly = int(self._left_eye_y - self._left_eye_height / 2)
            draw.rounded_rectangle(
                (lx, ly, lx + self._left_eye_width, ly + self._left_eye_height),
                radius=REF_CORNER_RADIUS,
                fill=255,
            )

            # Right eye
            rx = int(self._right_eye_x - self._right_eye_width / 2)
            ry = int(self._right_eye_y - self._right_eye_height / 2)
            draw.rounded_rectangle(
                (rx, ry, rx + self._right_eye_width, ry + self._right_eye_height),
                radius=REF_CORNER_RADIUS,
                fill=255,
            )

            self._oled.update()
        except Exception as e:
            logger.error("Draw eyes failed: %s", e)

    def _center_eyes(self):
        """Reset eyes to center position."""
        self._left_eye_height = REF_EYE_HEIGHT
        self._left_eye_width = REF_EYE_WIDTH
        self._right_eye_height = REF_EYE_HEIGHT
        self._right_eye_width = REF_EYE_WIDTH

        center_x = self._oled.width // 2
        center_y = self._oled.height // 2
        self._left_eye_x = center_x - REF_EYE_WIDTH // 2 - REF_SPACE_BETWEEN // 2
        self._left_eye_y = center_y
        self._right_eye_x = center_x + REF_EYE_WIDTH // 2 + REF_SPACE_BETWEEN // 2
        self._right_eye_y = center_y

        self._draw_eyes()

    def _look_left(self):
        """Smoothly move eyes to the left."""
        steps = 8
        dx = -10  # Total pixels to move left
        step_dx = dx / steps

        for i in range(steps):
            if not self._alive or not self._running.is_set():
                return
            self._left_eye_x += step_dx
            self._right_eye_x += step_dx
            self._draw_eyes()
            time.sleep(0.04)

    def _look_right(self):
        """Smoothly move eyes to the right."""
        steps = 8
        dx = 10  # Total pixels to move right
        step_dx = dx / steps

        for i in range(steps):
            if not self._alive or not self._running.is_set():
                return
            self._left_eye_x += step_dx
            self._right_eye_x += step_dx
            self._draw_eyes()
            time.sleep(0.04)

    def _blink(self):
        """Quick blink animation."""
        speed = 12
        for _ in range(3):
            if not self._alive or not self._running.is_set():
                return
            self._left_eye_height -= speed
            self._right_eye_height -= speed
            self._draw_eyes()
            time.sleep(0.02)

        for _ in range(3):
            if not self._alive or not self._running.is_set():
                return
            self._left_eye_height += speed
            self._right_eye_height += speed
            self._draw_eyes()
            time.sleep(0.02)
