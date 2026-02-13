"""
Non-blocking robot eye animation for OLED idle state.
Frame-based animation that can be advanced by the main loop.
"""

import logging
from typing import Tuple
from PIL import Image

logger = logging.getLogger(__name__)

# OLED dimensions
WIDTH = 128
HEIGHT = 64


def _draw_eye(
    img: Image.Image,
    cx: int,
    cy: int,
    eye_radius: int,
    pupil_offset: int,
    open_ratio: float = 1.0,
) -> None:
    """Draw a single eye (ellipse) with pupil. open_ratio 0..1 for blink."""
    from PIL import ImageDraw

    draw = ImageDraw.Draw(img)
    # Eye outline (white)
    r = int(eye_radius * open_ratio)
    if r < 2:
        r = 2
    draw.ellipse(
        [cx - eye_radius, cy - r, cx + eye_radius, cy + r],
        outline=1,
        fill=0,
    )
    # Pupil (filled circle, offset for look direction)
    pupil_r = max(1, eye_radius // 3)
    px = cx + pupil_offset
    py = cy
    draw.ellipse(
        [px - pupil_r, py - pupil_r, px + pupil_r, py + pupil_r],
        outline=1,
        fill=1,
    )


def frame_robot_eyes(phase: float) -> Image.Image:
    """
    Generate one frame of the robot eye animation.
    phase: 0.0 to 1.0 (or more), used for cycling look direction and blink.
    Returns a PIL Image (1-bit, size WIDTH x HEIGHT).
    """
    img = Image.new("1", (WIDTH, HEIGHT), 0)
    left_cx, cy = 40, HEIGHT // 2
    right_cx = WIDTH - 40

    # Smooth look left/right: pupil offset from -4 to +4
    import math
    t = phase * 2 * 3.14159
    pupil_offset = int(4 * math.sin(t))

    # Blink every ~3 seconds: short dip in open_ratio
    blink_phase = (phase * 2) % 1.0  # fast cycle for demo; use phase * 0.33 for ~3s
    if 0.92 < blink_phase:
        open_ratio = max(0.1, 1.0 - (blink_phase - 0.92) / 0.08 * 2)
    else:
        open_ratio = 1.0

    _draw_eye(img, left_cx, cy, 12, pupil_offset, open_ratio)
    _draw_eye(img, right_cx, cy, 12, pupil_offset, open_ratio)

    return img


class RobotEyeAnimation:
    """
    Non-blocking robot eye animation state.
    Call next_frame() each loop iteration; returns current frame image.
    """

    def __init__(self, fps: float = 10.0):
        self.fps = max(1.0, fps)
        self._phase = 0.0
        self._frame_delta = 1.0 / self.fps

    def advance(self, dt: float) -> None:
        """Advance animation by dt seconds."""
        self._phase += dt * 0.5  # slow cycle
        if self._phase > 1000.0:
            self._phase -= 1000.0

    def next_frame(self, dt: float = 0.1) -> Image.Image:
        """Advance time and return next frame (PIL Image, 1-bit)."""
        self.advance(dt)
        return frame_robot_eyes(self._phase)

    def reset(self) -> None:
        self._phase = 0.0
