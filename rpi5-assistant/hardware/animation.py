import threading
import time
from PIL import Image, ImageDraw
import logging
from .oled import OLED

class EyeAnimation:
    def __init__(self, oled: OLED):
        self.oled = oled
        self.running = False
        self.logger = logging.getLogger("rpi5-assistant")
        self.thread = threading.Thread(target=self._animate, daemon=True)

    def start(self):
        self.running = True
        self.thread.start()
        self.logger.info("Eye animation thread started.")

    def _animate(self):
        while self.running:
            try:
                # 1s center
                self._draw_eyes(offset=0, blink=False)
                time.sleep(1)
                # 1s left
                self._draw_eyes(offset=-20, blink=False)
                time.sleep(1)
                # 1s center
                self._draw_eyes(offset=0, blink=False)
                time.sleep(1)
                # 1s right
                self._draw_eyes(offset=20, blink=False)
                time.sleep(1)
                # 1s blink
                self._draw_eyes(offset=0, blink=True)
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Animation error: {e}")
                time.sleep(1)

    def _draw_eyes(self, offset=0, blink=False):
        W, H = 128, 64
        image = Image.new("1", (W, H))
        draw = ImageDraw.Draw(image)
        # Eye positions
        left_eye = (34 + offset, 32)
        right_eye = (94 + offset, 32)
        # Draw eyes
        for eye in [left_eye, right_eye]:
            x, y = eye
            draw.ellipse((x-18, y-18, x+18, y+18), outline=255, fill=0)
            if blink:
                draw.rectangle((x-12, y-2, x+12, y+8), fill=255)
            else:
                draw.ellipse((x-8, y-8, x+8, y+8), outline=255, fill=255)
        self.oled.show_image(image)
