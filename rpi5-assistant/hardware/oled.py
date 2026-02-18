import logging
from adafruit_ssd1306 import SSD1306_I2C
from PIL import Image, ImageDraw
import board
import busio

class OLED:
    def __init__(self, width=128, height=64, i2c_addr=0x3C):
        self.width = width
        self.height = height
        self.i2c_addr = i2c_addr
        self.display = None
        self.logger = logging.getLogger("rpi5-assistant")
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            self.display = SSD1306_I2C(self.width, self.height, i2c, addr=self.i2c_addr)
            self.display.fill(0)
            self.display.show()
            self.logger.info("OLED initialized successfully.")
        except Exception as e:
            self.logger.error(f"OLED init failed: {e}")
            self.display = None

    def show_image(self, image: Image.Image):
        if self.display:
            try:
                self.display.image(image)
                self.display.show()
            except Exception as e:
                self.logger.error(f"OLED show_image failed: {e}")
