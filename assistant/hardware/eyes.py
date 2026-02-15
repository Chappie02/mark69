"""
Robot eye animations on OLED. State-driven; runs in dedicated thread.
Uses adafruit-circuitpython-ssd1306 + Pillow.
Animation must NEVER freeze during LLM or YOLO.
"""

import math
import random
import threading
import time
from typing import Optional

from PIL import Image, ImageDraw

from assistant.config import (
    BLINK_INTERVAL_MIN,
    BLINK_INTERVAL_MAX,
    SACCADE_INTERVAL,
    SUCCESS_HOLD_SEC,
    ERROR_DOUBLE_BLINK_DELAY,
)
from assistant.core.state_manager import State, StateManager
from assistant.core.event_bus import EventBus, Event
from assistant.hardware.display import Display


# Eye geometry (two eyes side by side on 128x64)
EYE_WIDTH = 28
EYE_HEIGHT = 24
EYE_GAP = 16
CENTER_X = 64
LEFT_EYE_CX = CENTER_X - (EYE_WIDTH // 2 + EYE_GAP // 2)
RIGHT_EYE_CX = CENTER_X + (EYE_WIDTH // 2 + EYE_GAP // 2)
EYE_CY = 32
PUPIL_R = 4
IRIS_R = 8
BLINK_CLOSE_RATIO = 0.85  # how much eye closes (0=full open, 1=line)


def _draw_eye(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    wx: int,
    hy: int,
    pupil_dx: int,
    pupil_dy: int,
    blink: float,
    happy: bool = False,
    focused: bool = False,
) -> None:
    """Draw one eye: oval white, iris, pupil; optional blink (0=open, 1=closed), happy lower curve, focused=taller."""
    if focused:
        hy = int(hy * 1.15)  # Slightly taller for LISTENING
    # Blink: reduce height
    h = max(2, int(hy * (1.0 - blink * BLINK_CLOSE_RATIO)))
    y0 = cy - h // 2
    y1 = cy + h // 2
    x0 = cx - wx // 2
    x1 = cx + wx // 2
    # Outline (white)
    draw.ellipse([x0, y0, x1, y1], outline=1, fill=1)
    if blink >= 0.99:
        return  # closed
    # Iris center (clamped inside eye)
    ix = cx + max(-wx // 3, min(wx // 3, pupil_dx))
    iy = cy + max(-hy // 3, min(hy // 3, pupil_dy))
    # Lower lid curve for "happy"
    if happy:
        draw.ellipse([x0, cy - 2, x1, y1 + 4], outline=0, fill=0)
        draw.ellipse([x0, y0, x1, y1], outline=1, fill=1)
    # Iris
    draw.ellipse(
        [ix - IRIS_R, iy - IRIS_R, ix + IRIS_R, iy + IRIS_R],
        outline=1,
        fill=0,
    )
    # Pupil
    draw.ellipse(
        [ix - PUPIL_R, iy - PUPIL_R, ix + PUPIL_R, iy + PUPIL_R],
        outline=1,
        fill=1,
    )


class EyeAnimationController:
    """
    Renders eyes in a loop in a separate thread.
    Reads state from StateManager; animations vary by state.
    """

    def __init__(self, display: Display, state_manager: StateManager, event_bus: EventBus):
        self._display = display
        self._state_manager = state_manager
        self._event_bus = event_bus
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        # Animation state
        self._saccade_x = 0
        self._saccade_y = 0
        self._blink = 0.0
        self._next_blink_at = time.monotonic() + random.uniform(BLINK_INTERVAL_MIN, BLINK_INTERVAL_MAX)
        self._success_until = 0.0
        self._error_double_blink_phase = 0
        self._error_phase_until = 0.0

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _run(self) -> None:
        while not self._stop.is_set():
            with self._lock:
                state = self._state_manager.state
            self._tick(state)
            time.sleep(0.05)  # ~20 FPS

    def _tick(self, state: State) -> None:
        now = time.monotonic()
        # Success: show happy then hold
        if state == State.SUCCESS:
            if self._success_until <= 0:
                self._success_until = now + SUCCESS_HOLD_SEC
            self._render_frame(0, 0, blink=0, happy=True, focused=False)
            return
        if self._success_until > 0 and now > self._success_until:
            self._success_until = 0
        # Error: double blink
        if state == State.ERROR:
            self._tick_error(now)
            return
        # Blink (idle / thinking half-blink)
        if state in (State.IDLE, State.THINKING) and now >= self._next_blink_at:
            self._blink = min(1.0, self._blink + 0.3)
            if self._blink >= 1.0:
                self._blink = 0.0
                self._next_blink_at = now + random.uniform(BLINK_INTERVAL_MIN, BLINK_INTERVAL_MAX)
        else:
            if self._blink > 0:
                self._blink = max(0, self._blink - 0.2)
        # Saccade by state
        if state == State.IDLE:
            self._saccade_x = int(3 * math.sin(now * 0.8))
            self._saccade_y = int(2 * math.sin(now * 0.5))
        elif state == State.LISTENING:
            self._saccade_x = 0
            self._saccade_y = 0
            self._blink = 0
        elif state == State.THINKING:
            self._saccade_x = int(5 * math.sin(now * 1.2))
            self._saccade_y = 0
            if random.random() < 0.02:
                self._blink = 0.5
        elif state == State.DETECTING:
            self._saccade_x = int(6 * math.sin(now * 2.0))
            self._saccade_y = int(2 * math.sin(now * 1.5))
        elif state == State.SPEAKING:
            self._saccade_x = int(3 * math.sin(now * 1.0))
            self._saccade_y = 0
        else:
            self._saccade_x = 0
            self._saccade_y = 0
        focused = state == State.LISTENING
        self._render_frame(self._saccade_x, self._saccade_y, self._blink, happy=False, focused=focused)

    def _tick_error(self, now: float) -> None:
        # Double blink then idle
        if self._error_double_blink_phase == 0:
            self._error_double_blink_phase = 1
            self._error_phase_until = now + 0.15
        if self._error_double_blink_phase == 1:
            self._render_frame(0, 0, blink=1, happy=False, focused=False)
            if now >= getattr(self, "_error_phase_until", now):
                self._error_double_blink_phase = 2
                self._error_phase_until = now + 0.15
        elif self._error_double_blink_phase == 2:
            self._render_frame(0, 0, blink=0, happy=False, focused=False)
            if now >= self._error_phase_until:
                self._error_double_blink_phase = 3
                self._error_phase_until = now + 0.15
        elif self._error_double_blink_phase == 3:
            self._render_frame(0, 0, blink=1, happy=False, focused=False)
            if now >= self._error_phase_until:
                self._error_double_blink_phase = 4
        else:
            self._render_frame(0, 0, blink=0, happy=False, focused=False)
            self._error_double_blink_phase = 0

    def _render_frame(
        self,
        dx: int,
        dy: int,
        blink: float,
        happy: bool,
        focused: bool = False,
    ) -> None:
        img = Image.new("1", (self._display.width, self._display.height), 0)
        draw = ImageDraw.Draw(img)
        _draw_eye(
            draw,
            LEFT_EYE_CX,
            EYE_CY,
            EYE_WIDTH,
            EYE_HEIGHT,
            dx,
            dy,
            blink,
            happy=happy,
            focused=focused,
        )
        _draw_eye(
            draw,
            RIGHT_EYE_CX,
            EYE_CY,
            EYE_WIDTH,
            EYE_HEIGHT,
            dx,
            dy,
            blink,
            happy=happy,
            focused=focused,
        )
        self._display.show_image(img)

    def trigger_success(self) -> None:
        with self._lock:
            self._success_until = time.monotonic() + SUCCESS_HOLD_SEC

    def trigger_capture_blink(self) -> None:
        """One quick blink for K3 capture."""
        with self._lock:
            self._blink = 1.0
