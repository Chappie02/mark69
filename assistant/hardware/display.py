"""
OLED SSD1306 128x64 I2C driver wrapper.
Uses adafruit-circuitpython-ssd1306 + Pillow for drawing.
"""

from typing import Optional

from PIL import Image

from assistant.config import OLED_HEIGHT, OLED_WIDTH, OLED_I2C_ADDR, OLED_I2C_BUS


class Display:
    """Thin wrapper over SSD1306. Handles init and show(image)."""

    def __init__(self) -> None:
        self._display = None
        self._width = OLED_WIDTH
        self._height = OLED_HEIGHT

    def init(self) -> bool:
        try:
            import board
            import busio
            import adafruit_ssd1306
            i2c = busio.I2C(board.SCL, board.SDA)
            self._display = adafruit_ssd1306.SSD1306_I2C(
                self._width, self._height, i2c, addr=OLED_I2C_ADDR
            )
            self._display.fill(0)
            self._display.show()
            return True
        except Exception:
            self._display = None
            return False

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def show_image(self, image: Image.Image) -> None:
        """Display PIL Image (1-bit or grayscale). Resize to 128x64 if needed."""
        if self._display is None:
            return
        if image.size != (self._width, self._height):
            image = image.resize((self._width, self._height), Image.Resampling.LANCZOS)
        if image.mode != "1":
            image = image.convert("1")
        self._display.image(image)
        self._display.show()

    def fill(self, color: int = 0) -> None:
        if self._display is not None:
            self._display.fill(color)
            self._display.show()
