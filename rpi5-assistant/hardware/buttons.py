import logging
import RPi.GPIO as GPIO
import threading

K1 = 17  # Push-to-talk
K2 = 27  # Object detection
K3 = 22  # Capture only

class ButtonHandler:
    def __init__(self, k1_cb=None, k2_cb=None, k3_cb=None):
        self.logger = logging.getLogger("rpi5-assistant")
        try:
            GPIO.setmode(GPIO.BCM)
            for pin in [K1, K2, K3]:
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self.k1_cb = k1_cb
            self.k2_cb = k2_cb
            self.k3_cb = k3_cb
            GPIO.add_event_detect(K1, GPIO.BOTH, callback=self._k1_event, bouncetime=100)
            GPIO.add_event_detect(K2, GPIO.FALLING, callback=self._k2_event, bouncetime=200)
            GPIO.add_event_detect(K3, GPIO.FALLING, callback=self._k3_event, bouncetime=200)
            self.logger.info("Buttons initialized.")
        except Exception as e:
            self.logger.error(f"Button init failed: {e}")

    def _k1_event(self, channel):
        if GPIO.input(K1) == 0:
            if self.k1_cb:
                self.k1_cb(pressed=True)
        else:
            if self.k1_cb:
                self.k1_cb(pressed=False)

    def _k2_event(self, channel):
        if self.k2_cb:
            self.k2_cb()

    def _k3_event(self, channel):
        if self.k3_cb:
            self.k3_cb()

    def cleanup(self):
        GPIO.cleanup()
