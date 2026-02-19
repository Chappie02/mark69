import logging
import time
from dataclasses import dataclass
from enum import Enum, auto

try:
    import RPi.GPIO as GPIO
except Exception:  # pragma: no cover - not on Pi
    GPIO = None


class ButtonEventType(Enum):
    K2_OBJECT_DETECT = auto()
    K3_SHORT_CAPTURE = auto()
    K3_LONG_CHAT_START = auto()
    K3_LONG_CHAT_END = auto()


@dataclass
class ButtonEvent:
    event_type: ButtonEventType


class ButtonListener:
    """
    Single thread that monitors buttons and pushes ButtonEvent into a queue.

    - K2: object detection (single press)
    - K3: short press (< 1s) → image capture
          long press (>= 1s) → push-to-talk chat

    For long press chat:
      - On K3 press crossing 1s threshold: send K3_LONG_CHAT_START
      - On K3 release after long press:   send K3_LONG_CHAT_END
    """

    K2_PIN = 27  # Object detection
    K3_PIN = 22  # Capture / chat
    K1_PIN = 17  # Reserved / unused for now

    def __init__(self, event_queue) -> None:
        self.log = logging.getLogger("buttons")
        self.event_queue = event_queue

        self._k3_pressed = False
        self._k3_press_time = 0.0
        self._k3_long_sent = False

        try:
            if GPIO is None:
                raise RuntimeError("RPi.GPIO not available.")

            GPIO.setmode(GPIO.BCM)
            for pin in (self.K1_PIN, self.K2_PIN, self.K3_PIN):
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        except Exception as e:
            self.log.exception("Failed to initialize GPIO: %s", e)

    def _read_pin(self, pin: int) -> bool:
        """
        Returns True if button is pressed (active low).
        """
        if GPIO is None:
            return False
        try:
            return GPIO.input(pin) == GPIO.LOW
        except Exception:
            self.log.exception("Failed to read GPIO pin %s", pin)
            return False

    def run(self) -> None:
        self.log.info("Button listener thread started.")
        try:
            while True:
                self._poll_k2()
                self._poll_k3()
                time.sleep(0.01)
        except Exception:
            self.log.exception("Button listener crashed.")

    # -------------------------------------------------
    # K2 – object detection
    # -------------------------------------------------
    def _poll_k2(self) -> None:
        if GPIO is None:
            return
        try:
            pressed = self._read_pin(self.K2_PIN)
            if pressed:
                # simple edge detection debounce
                time.sleep(0.03)
                if self._read_pin(self.K2_PIN):
                    self.event_queue.put(ButtonEvent(ButtonEventType.K2_OBJECT_DETECT))
                    # wait for release
                    while self._read_pin(self.K2_PIN):
                        time.sleep(0.02)
        except Exception:
            self.log.exception("Error polling K2.")

    # -------------------------------------------------
    # K3 – short vs long press
    # -------------------------------------------------
    def _poll_k3(self) -> None:
        if GPIO is None:
            return
        try:
            pressed = self._read_pin(self.K3_PIN)
            now = time.time()

            if pressed and not self._k3_pressed:
                # rising edge (button just pressed)
                self._k3_pressed = True
                self._k3_press_time = now
                self._k3_long_sent = False

            if self._k3_pressed and not pressed:
                # falling edge (button released)
                duration = now - self._k3_press_time
                if duration < 1.0:
                    # short press → image capture
                    self.event_queue.put(
                        ButtonEvent(ButtonEventType.K3_SHORT_CAPTURE)
                    )
                else:
                    # long press end
                    if self._k3_long_sent:
                        self.event_queue.put(
                            ButtonEvent(ButtonEventType.K3_LONG_CHAT_END)
                        )
                self._k3_pressed = False
                self._k3_long_sent = False

            # Long press threshold: send start event once
            if self._k3_pressed and not self._k3_long_sent:
                duration = now - self._k3_press_time
                if duration >= 1.0:
                    self._k3_long_sent = True
                    self.event_queue.put(
                        ButtonEvent(ButtonEventType.K3_LONG_CHAT_START)
                    )
        except Exception:
            self.log.exception("Error polling K3.")

