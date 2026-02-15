"""
OLED robot eyes — state-driven animation in a dedicated thread.
Uses SSD1306 128x64, non-blocking; state changes update behavior dynamically.
"""

import math
import random
import threading
import time
from typing import Optional

# Optional: allow running without hardware for testing
try:
    import board
    import busio
    import adafruit_ssd1306
    from PIL import Image, ImageDraw
    _HARDWARE_AVAILABLE = True
except (ImportError, NotImplementedError):
    _HARDWARE_AVAILABLE = False

from .config import (
    OLED_WIDTH,
    OLED_HEIGHT,
    REF_EYE_HEIGHT,
    REF_EYE_WIDTH,
    REF_SPACE_BETWEEN_EYES,
    REF_CORNER_RADIUS,
    IDLE_BLINK_INTERVAL_MIN,
    IDLE_BLINK_INTERVAL_MAX,
    SUCCESS_HOLD_SEC,
    SACCADE_INTERVAL_IDLE,
    SACCADE_INTERVAL_THINKING,
    SACCADE_INTERVAL_DETECTING,
)
from .state_manager import State, StateManager


class EyeDisplay:
    """
    Robot eyes on SSD1306. Animation runs in background thread.
    States: IDLE, LISTENING, THINKING, DETECTING, SUCCESS, ERROR.
    """

    def __init__(self, state_manager: StateManager) -> None:
        self._state_manager = state_manager
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

        # Geometry (mutable for animation)
        self._left_eye_x = OLED_WIDTH // 2 - REF_EYE_WIDTH // 2 - REF_SPACE_BETWEEN_EYES // 2
        self._right_eye_x = OLED_WIDTH // 2 + REF_EYE_WIDTH // 2 + REF_SPACE_BETWEEN_EYES // 2
        self._left_eye_y = OLED_HEIGHT // 2
        self._right_eye_y = OLED_HEIGHT // 2
        self._left_eye_h = REF_EYE_HEIGHT
        self._right_eye_h = REF_EYE_HEIGHT
        self._left_eye_w = REF_EYE_WIDTH
        self._right_eye_w = REF_EYE_WIDTH

        # Idle blink timer
        self._next_blink_at = time.monotonic() + random.uniform(
            IDLE_BLINK_INTERVAL_MIN, IDLE_BLINK_INTERVAL_MAX
        )
        # Saccade / thinking timers
        self._next_saccade_at = 0.0
        self._next_half_blink_at = 0.0

        self._display = None
        self._image = None
        self._draw = None
        if _HARDWARE_AVAILABLE:
            self._init_display()

    def _init_display(self) -> None:
        i2c = busio.I2C(board.SCL, board.SDA)
        self._display = adafruit_ssd1306.SSD1306_I2C(OLED_WIDTH, OLED_HEIGHT, i2c)
        self._image = Image.new("1", (OLED_WIDTH, OLED_HEIGHT))
        self._draw = ImageDraw.Draw(self._image)
        self._center_eyes()
        self._draw_eyes()

    def _center_eyes(self) -> None:
        self._left_eye_x = OLED_WIDTH // 2 - REF_EYE_WIDTH // 2 - REF_SPACE_BETWEEN_EYES // 2
        self._right_eye_x = OLED_WIDTH // 2 + REF_EYE_WIDTH // 2 + REF_SPACE_BETWEEN_EYES // 2
        self._left_eye_y = OLED_HEIGHT // 2
        self._right_eye_y = OLED_HEIGHT // 2
        self._left_eye_h = REF_EYE_HEIGHT
        self._right_eye_h = REF_EYE_HEIGHT
        self._left_eye_w = REF_EYE_WIDTH
        self._right_eye_w = REF_EYE_WIDTH

    def _draw_eyes(self) -> None:
        if not _HARDWARE_AVAILABLE or self._draw is None or self._display is None:
            return
        self._draw.rectangle((0, 0, OLED_WIDTH, OLED_HEIGHT), outline=0, fill=0)
        lx = self._left_eye_x - self._left_eye_w // 2
        ly = self._left_eye_y - self._left_eye_h // 2
        rx = self._right_eye_x - self._right_eye_w // 2
        ry = self._right_eye_y - self._right_eye_h // 2
        self._draw.rounded_rectangle(
            (lx, ly, lx + self._left_eye_w, ly + self._left_eye_h),
            radius=REF_CORNER_RADIUS,
            fill=255,
        )
        self._draw.rounded_rectangle(
            (rx, ry, rx + self._right_eye_w, ry + self._right_eye_h),
            radius=REF_CORNER_RADIUS,
            fill=255,
        )
        self._display.image(self._image)
        self._display.show()

    def _blink(self, steps: int = 4, step_delay: float = 0.02) -> None:
        speed = REF_EYE_HEIGHT // steps
        for _ in range(steps):
            self._left_eye_h = max(4, self._left_eye_h - speed)
            self._right_eye_h = max(4, self._right_eye_h - speed)
            self._draw_eyes()
            time.sleep(step_delay)
        for _ in range(steps):
            self._left_eye_h = min(REF_EYE_HEIGHT, self._left_eye_h + speed)
            self._right_eye_h = min(REF_EYE_HEIGHT, self._right_eye_h + speed)
            self._draw_eyes()
            time.sleep(step_delay)
        self._left_eye_h = REF_EYE_HEIGHT
        self._right_eye_h = REF_EYE_HEIGHT

    def _half_blink(self) -> None:
        target = REF_EYE_HEIGHT // 2
        for _ in range(2):
            self._left_eye_h = max(target, self._left_eye_h - 4)
            self._right_eye_h = max(target, self._right_eye_h - 4)
            self._draw_eyes()
            time.sleep(0.02)
        for _ in range(2):
            self._left_eye_h = min(REF_EYE_HEIGHT, self._left_eye_h + 4)
            self._right_eye_h = min(REF_EYE_HEIGHT, self._right_eye_h + 4)
            self._draw_eyes()
            time.sleep(0.02)
        self._left_eye_h = REF_EYE_HEIGHT
        self._right_eye_h = REF_EYE_HEIGHT

    def _double_blink(self) -> None:
        self._blink(steps=3, step_delay=0.03)
        time.sleep(0.05)
        self._blink(steps=3, step_delay=0.03)

    def _wakeup_animation(self) -> None:
        self._left_eye_h = 4
        self._right_eye_h = 4
        self._draw_eyes()
        for h in range(4, REF_EYE_HEIGHT, 2):
            self._left_eye_h = h
            self._right_eye_h = h
            self._draw_eyes()
            time.sleep(0.02)
        self._left_eye_h = REF_EYE_HEIGHT
        self._right_eye_h = REF_EYE_HEIGHT

    def _happy_eyes(self) -> None:
        self._draw_eyes()
        if not _HARDWARE_AVAILABLE or self._draw is None or self._display is None:
            time.sleep(SUCCESS_HOLD_SEC)
            return
        offset = REF_EYE_HEIGHT // 2
        # Lower eyelid smile shape (triangle cutout)
        self._draw.polygon(
            [
                (self._left_eye_x - REF_EYE_WIDTH // 2, self._left_eye_y + offset),
                (self._left_eye_x + REF_EYE_WIDTH // 2, self._left_eye_y + offset),
                (self._left_eye_x, self._left_eye_y + REF_EYE_HEIGHT // 2 + 4),
            ],
            fill=0,
        )
        self._draw.polygon(
            [
                (self._right_eye_x - REF_EYE_WIDTH // 2, self._right_eye_y + offset),
                (self._right_eye_x + REF_EYE_WIDTH // 2, self._right_eye_y + offset),
                (self._right_eye_x, self._right_eye_y + REF_EYE_HEIGHT // 2 + 4),
            ],
            fill=0,
        )
        self._display.image(self._image)
        self._display.show()
        time.sleep(SUCCESS_HOLD_SEC)
        self._center_eyes()
        self._draw_eyes()

    def _saccade(self, dx: Optional[int] = None) -> None:
        if dx is None:
            dx = random.randint(-8, 8)
        self._left_eye_x += dx
        # Keep eyes on screen; right follows left
        min_left = REF_EYE_WIDTH // 2 + 2
        max_left = OLED_WIDTH // 2 - REF_EYE_WIDTH - REF_SPACE_BETWEEN_EYES // 2 - 2
        self._left_eye_x = max(min_left, min(max_left, self._left_eye_x))
        self._right_eye_x = self._left_eye_x + REF_EYE_WIDTH + REF_SPACE_BETWEEN_EYES
        self._draw_eyes()
        time.sleep(0.08)
        self._left_eye_x -= dx
        self._left_eye_x = max(min_left, min(max_left, self._left_eye_x))
        self._right_eye_x = self._left_eye_x + REF_EYE_WIDTH + REF_SPACE_BETWEEN_EYES
        self._draw_eyes()

    def _listening_breathing(self, t: float) -> None:
        # Slight vertical scale (attentive look): subtle breathing
        scale = 1.0 + 0.06 * math.sin(t * 1.2)
        self._left_eye_h = int(REF_EYE_HEIGHT * scale)
        self._right_eye_h = int(REF_EYE_HEIGHT * scale)
        self._left_eye_h = max(32, min(REF_EYE_HEIGHT + 4, self._left_eye_h))
        self._right_eye_h = self._left_eye_h
        self._draw_eyes()

    def _detecting_compression(self) -> None:
        # Slight eye compression for searching
        scale = 0.92
        self._left_eye_h = int(REF_EYE_HEIGHT * scale)
        self._right_eye_h = self._left_eye_h
        self._draw_eyes()

    def run_idle(self, now: float) -> None:
        if now >= self._next_blink_at:
            self._blink()
            self._next_blink_at = now + random.uniform(IDLE_BLINK_INTERVAL_MIN, IDLE_BLINK_INTERVAL_MAX)
        if now >= self._next_saccade_at:
            self._saccade()
            self._next_saccade_at = now + random.uniform(*SACCADE_INTERVAL_IDLE)

    def run_listening(self, now: float) -> None:
        self._center_eyes()
        # Slightly taller = attentive; breathing does subtle scale variation
        self._listening_breathing(now)

    def run_thinking(self, now: float) -> None:
        if now >= self._next_saccade_at:
            dx = random.choice([-6, -4, 4, 6])
            self._saccade(dx)
            self._next_saccade_at = now + random.uniform(*SACCADE_INTERVAL_THINKING)
        if now >= self._next_half_blink_at:
            self._half_blink()
            self._next_half_blink_at = now + random.uniform(2.0, 4.0)

    def run_detecting(self, now: float) -> None:
        self._detecting_compression()
        if now >= self._next_saccade_at:
            self._saccade(random.randint(-6, 6))
            self._next_saccade_at = now + random.uniform(*SACCADE_INTERVAL_DETECTING)

    def _animation_loop(self) -> None:
        if _HARDWARE_AVAILABLE:
            self._center_eyes()
            self._draw_eyes()
        frame_delay = 0.05
        while not self._stop.is_set():
            now = time.monotonic()
            state = self._state_manager.state
            try:
                if state == State.IDLE:
                    self.run_idle(now)
                elif state == State.LISTENING:
                    self.run_listening(now)
                elif state == State.THINKING:
                    self.run_thinking(now)
                elif state == State.DETECTING:
                    self.run_detecting(now)
                elif state == State.SUCCESS:
                    self._happy_eyes()
                    self._state_manager.set_state(State.IDLE)
                elif state == State.ERROR:
                    self._double_blink()
                    self._state_manager.set_state(State.IDLE)
            except Exception:
                pass
            time.sleep(frame_delay)

    def play_wakeup(self) -> None:
        """Call when entering LISTENING from IDLE (after K1 press)."""
        if _HARDWARE_AVAILABLE:
            self._wakeup_animation()

    def play_blink_capture(self) -> None:
        """Quick blink for K3 capture."""
        self._blink(steps=3, step_delay=0.025)

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._animation_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
