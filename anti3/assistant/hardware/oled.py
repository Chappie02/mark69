"""
OLED Display Driver — Thread-safe wrapper for SSD1306 128x64 OLED.
"""

import logging
import threading

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

WIDTH = 128
HEIGHT = 64


class OLEDDisplay:
    """Thread-safe OLED display controller."""

    def __init__(self):
        self._lock = threading.Lock()
        self._display = None
        self._image = Image.new("1", (WIDTH, HEIGHT))
        self._draw = ImageDraw.Draw(self._image)
        self._font = None
        self._init_display()

    def _init_display(self):
        """Initialize the physical OLED display."""
        try:
            import board
            import busio
            import adafruit_ssd1306

            i2c = busio.I2C(board.SCL, board.SDA)
            self._display = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c)
            self._display.fill(0)
            self._display.show()
            logger.info("OLED display initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize OLED display: %s", e)
            self._display = None

        try:
            self._font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10
            )
        except Exception:
            self._font = ImageFont.load_default()

    @property
    def width(self):
        return WIDTH

    @property
    def height(self):
        return HEIGHT

    def clear(self):
        """Clear the display."""
        try:
            with self._lock:
                self._draw.rectangle((0, 0, WIDTH, HEIGHT), fill=0)
                self._update()
        except Exception as e:
            logger.error("OLED clear failed: %s", e)

    def show_text(self, text, x=0, y=0, clear_first=True):
        """Display text on the OLED with word wrapping."""
        try:
            with self._lock:
                if clear_first:
                    self._draw.rectangle((0, 0, WIDTH, HEIGHT), fill=0)

                words = text.split()
                lines = []
                current_line = ""
                max_chars = 18

                for word in words:
                    test_line = f"{current_line} {word}".strip()
                    if len(test_line) <= max_chars:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = word

                if current_line:
                    lines.append(current_line)

                line_height = 12
                for i, line in enumerate(lines[:5]):
                    self._draw.text(
                        (x, y + i * line_height), line, fill=255, font=self._font
                    )

                self._update()
        except Exception as e:
            logger.error("OLED show_text failed: %s", e)

    def show_text_streaming(self, text):
        """Display streaming LLM text — shows last visible portion."""
        try:
            with self._lock:
                self._draw.rectangle((0, 0, WIDTH, HEIGHT), fill=0)

                max_chars = 18
                lines = []
                current_line = ""

                for char in text:
                    if char == "\n":
                        lines.append(current_line)
                        current_line = ""
                    elif len(current_line) >= max_chars:
                        lines.append(current_line)
                        current_line = char
                    else:
                        current_line += char

                if current_line:
                    lines.append(current_line)

                visible_lines = lines[-5:]
                line_height = 12
                for i, line in enumerate(visible_lines):
                    self._draw.text(
                        (0, i * line_height), line, fill=255, font=self._font
                    )

                self._update()
        except Exception as e:
            logger.error("OLED streaming text failed: %s", e)

    def show_image(self, image):
        """Display a PIL Image on the OLED."""
        try:
            with self._lock:
                if image.size != (WIDTH, HEIGHT):
                    image = image.resize((WIDTH, HEIGHT))
                if image.mode != "1":
                    image = image.convert("1")
                self._image = image
                self._draw = ImageDraw.Draw(self._image)
                self._update()
        except Exception as e:
            logger.error("OLED show_image failed: %s", e)

    def get_image_and_draw(self):
        """Return (image, draw) for direct drawing (used by animation)."""
        return self._image, self._draw

    def update(self):
        """Push current image buffer to display (thread-safe)."""
        try:
            with self._lock:
                self._update()
        except Exception as e:
            logger.error("OLED update failed: %s", e)

    def _update(self):
        """Internal update — must be called with lock held."""
        if self._display is not None:
            self._display.image(self._image)
            self._display.show()
