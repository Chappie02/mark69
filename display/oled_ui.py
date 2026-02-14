"""
OLED UI using luma.oled (SSD1306 I2C).
Handles all display states: idle animation, listening, object mode, captured, token streaming.
"""

import logging
import threading
from typing import Optional

from PIL import Image

from assistant.config import OLED_WIDTH, OLED_HEIGHT, OLED_I2C_ADDRESS, OLED_PORT
from assistant.display.animations import RobotEyeAnimation, frame_robot_eyes

logger = logging.getLogger(__name__)


class OLEDDisplay:
    """
    SSD1306 OLED display driver and UI.
    Thread-safe for show_text; animation runs from main thread or dedicated animator.
    """

    def __init__(self) -> None:
        self._device = None
        self._lock = threading.Lock()
        self._animation = RobotEyeAnimation(fps=10.0)
        self._initialized = False

    def init(self) -> bool:
        """Initialize I2C and SSD1306 device. Returns True on success."""
        try:
            from luma.oled.device import ssd1306
            from luma.core.interface.serial import i2c
            from luma.core.render import canvas

            serial = i2c(port=OLED_PORT, address=OLED_I2C_ADDRESS)
            self._device = ssd1306(serial, width=OLED_WIDTH, height=OLED_HEIGHT)
            self._initialized = True
            logger.info("OLED SSD1306 initialized at I2C 0x%02X", OLED_I2C_ADDRESS)
            return True
        except Exception as e:
            logger.exception("OLED init failed: %s", e)
            self._initialized = False
            return False

    def _display_image(self, image: Image.Image) -> None:
        """Display PIL Image (1-bit, 128x64). Must hold _lock if multi-threaded."""
        if not self._initialized or self._device is None:
            return
        try:
            if image.size != (OLED_WIDTH, OLED_HEIGHT):
                image = image.resize((OLED_WIDTH, OLED_HEIGHT), Image.Resampling.LANCZOS)
            if image.mode != "1":
                image = image.convert("1")
            self._device.display(image)
        except Exception as e:
            logger.debug("OLED display error: %s", e)

    def show_idle_frame(self, dt: float = 0.1) -> None:
        """Show one frame of robot eye animation (non-blocking). Call in idle loop."""
        with self._lock:
            frame = self._animation.next_frame(dt)
            self._display_image(frame)

    def show_text(
        self,
        text: str,
        wrap: bool = True,
        max_lines: int = 4,
        line_height: int = 14,
    ) -> None:
        """Show text on OLED, wrapped and truncated to max_lines."""
        with self._lock:
            img = self._render_text(text, wrap=wrap, max_lines=max_lines, line_height=line_height)
            self._display_image(img)

    def _render_text(
        self,
        text: str,
        wrap: bool = True,
        max_lines: int = 4,
        line_height: int = 14,
    ) -> Image.Image:
        """Render text to a 128x64 1-bit image."""
        from PIL import ImageDraw, ImageFont

        img = Image.new("1", (OLED_WIDTH, OLED_HEIGHT), 0)
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        except OSError:
            font = ImageFont.load_default()

        if not text:
            return img

        lines = []
        if wrap:
            words = text.split()
            current = ""
            for w in words:
                candidate = f"{current} {w}".strip() if current else w
                bbox = draw.textbbox((0, 0), candidate, font=font)
                if bbox[2] - bbox[0] <= OLED_WIDTH - 4:
                    current = candidate
                else:
                    if current:
                        lines.append(current)
                    current = w
            if current:
                lines.append(current)
        else:
            lines = text.split("\n")

        lines = lines[:max_lines]
        y = 2
        for line in lines:
            if y + line_height > OLED_HEIGHT:
                break
            draw.text((2, y), line[:20] if len(line) > 20 else line, font=font, fill=1)
            y += line_height

        return img

    def show_listening(self) -> None:
        self.show_text("Listening...")

    def show_object_mode(self) -> None:
        self.show_text("Object Mode\nPress K3 to capture")

    def show_captured(self) -> None:
        self.show_text("Captured")

    def show_processing(self) -> None:
        self.show_text("Processing...")

    def show_tokens(self, streamed_text: str) -> None:
        """Update display with streamed LLM output (last portion to fit)."""
        # Show last ~80 chars so user sees newest tokens
        if len(streamed_text) > 80:
            streamed_text = "..." + streamed_text[-77:]
        self.show_text(streamed_text, wrap=True, max_lines=4)

    def clear(self) -> None:
        """Clear display to black."""
        with self._lock:
            if self._initialized and self._device:
                img = Image.new("1", (OLED_WIDTH, OLED_HEIGHT), 0)
                self._display_image(img)

    def cleanup(self) -> None:
        """Release display resource."""
        with self._lock:
            self.clear()
            self._device = None
            self._initialized = False
            logger.info("OLED cleanup done")
