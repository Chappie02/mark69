"""
Button handling for K1 (Push-to-Talk), K2 (Object Detection), K3 (Capture).
Runs in a dedicated thread; callbacks are invoked on press/release.
"""

import threading
import time
from typing import Callable

try:
    import RPi.GPIO as GPIO
    _GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    _GPIO_AVAILABLE = False

from .config import PIN_K1, PIN_K2, PIN_K3


class ButtonHandler:
    """
    Listens to K1, K2, K3. K1 is hold-to-talk (report press and release);
    K2 and K3 are single press.
    """

    def __init__(
        self,
        on_k1_press: Callable[[], None],
        on_k1_release: Callable[[], None],
        on_k2_press: Callable[[], None],
        on_k3_press: Callable[[], None],
    ) -> None:
        self.on_k1_press = on_k1_press
        self.on_k1_release = on_k1_release
        self.on_k2_press = on_k2_press
        self.on_k3_press = on_k3_press
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._k1_was_pressed = False
        self._debounce_sec = 0.05

    def _read_k1(self) -> bool:
        if not _GPIO_AVAILABLE:
            return False
        return not GPIO.input(PIN_K1)  # Assume active-low (button pulls to GND)

    def _read_k2(self) -> bool:
        if not _GPIO_AVAILABLE:
            return False
        return not GPIO.input(PIN_K2)

    def _read_k3(self) -> bool:
        if not _GPIO_AVAILABLE:
            return False
        return not GPIO.input(PIN_K3)

    def _poll_loop(self) -> None:
        if _GPIO_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            for pin in (PIN_K1, PIN_K2, PIN_K3):
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        last_k2 = False
        last_k3 = False
        while not self._stop.is_set():
            k1 = self._read_k1()
            k2 = self._read_k2()
            k3 = self._read_k3()
            # K1: press / release
            if k1 and not self._k1_was_pressed:
                self._k1_was_pressed = True
                try:
                    self.on_k1_press()
                except Exception:
                    pass
            elif not k1 and self._k1_was_pressed:
                self._k1_was_pressed = False
                try:
                    self.on_k1_release()
                except Exception:
                    pass
            # K2: rising edge
            if k2 and not last_k2:
                try:
                    self.on_k2_press()
                except Exception:
                    pass
            last_k2 = k2
            # K3: rising edge
            if k3 and not last_k3:
                try:
                    self.on_k3_press()
                except Exception:
                    pass
            last_k3 = k3
            time.sleep(self._debounce_sec)

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        if _GPIO_AVAILABLE:
            try:
                GPIO.cleanup((PIN_K1, PIN_K2, PIN_K3))
            except Exception:
                pass
